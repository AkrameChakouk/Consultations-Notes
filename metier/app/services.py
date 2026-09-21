"""Logique métier : authentification, autorisation et règles de consultation.

Ce fichier ne contient pas de SQL (voir repository.py) et ne connaît pas HTTP
(voir routes.py). Quand une règle est violée, il lève une ErreurMetier qui porte
le code HTTP à renvoyer.

Mécanisme d'authentification : un JETON SIGNÉ.
  1. À la connexion, on vérifie le mot de passe (bcrypt) et le statut du compte.
  2. Si tout est bon, on fabrique un jeton {id_compte, rôle} signé avec SECRET_KEY.
  3. Le client renvoie ce jeton à chaque requête : « Authorization: Bearer <jeton> ».
  4. L'identité de l'utilisateur vient TOUJOURS de ce jeton, jamais d'un paramètre
     envoyé par le client : personne ne peut donc consulter les notes d'un autre
     en changeant un numéro dans l'adresse.
Le jeton expire au bout de TOKEN_DUREE_SECONDES ; une signature falsifiée est refusée.
"""
import bcrypt
import psycopg2
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from . import config, repository

ROLES_INSCRIPTION = ("etudiant", "enseignant")   # le superviseur ne s'inscrit pas
PREFIXE_JETON = "Bearer "


class ErreurMetier(Exception):
    """Erreur prévue par les règles métier, avec le code HTTP correspondant."""

    def __init__(self, statut_http, code, message):
        super().__init__(message)
        self.statut_http = statut_http
        self.code = code
        self.message = message


# --- Outils internes ---------------------------------------------------------

def _serialiseur():
    return URLSafeTimedSerializer(config.SECRET_KEY, salt="jeton-consultation-notes")


def _texte(valeur, nom_champ):
    if not isinstance(valeur, str) or not valeur.strip():
        raise ErreurMetier(400, "requete_invalide", f"Le champ « {nom_champ} » est obligatoire.")
    return valeur.strip()


def _mot_de_passe_correct(mot_de_passe, empreinte):
    try:
        return bcrypt.checkpw(mot_de_passe.encode("utf-8"), empreinte.encode("ascii"))
    except ValueError:   # empreinte illisible ou mot de passe trop long
        return False


def _exiger_role(utilisateur, role):
    if utilisateur["role"] != role:
        raise ErreurMetier(403, "acces_refuse", "Votre rôle ne permet pas d'accéder à cette ressource.")


# --- Authentification ----------------------------------------------------------

def connecter(login, mot_de_passe):
    login = _texte(login, "login")
    if not isinstance(mot_de_passe, str) or mot_de_passe == "":
        raise ErreurMetier(400, "requete_invalide", "Le champ « mot_de_passe » est obligatoire.")

    compte = repository.trouver_compte_par_login(login)
    if compte is None:
        raise ErreurMetier(401, "identifiant_inconnu", "Identifiant inconnu.")
    if not _mot_de_passe_correct(mot_de_passe, compte["mot_de_passe_hash"]):
        raise ErreurMetier(401, "mot_de_passe_errone", "Mot de passe erroné.")
    if compte["statut"] != "valide":   # règle R6
        raise ErreurMetier(403, "compte_en_attente", "Compte en attente de validation.")

    jeton = _serialiseur().dumps({"id_compte": compte["id_compte"], "role": compte["role"]})
    identite = repository.trouver_identite(compte["id_compte"])
    nom_complet = f"{identite['prenom']} {identite['nom']}" if identite else compte["login"]
    return {"jeton": jeton, "role": compte["role"], "nom_complet": nom_complet}


def utilisateur_depuis_en_tete(en_tete_authorization):
    """Retrouve l'utilisateur à partir de l'en-tête « Authorization: Bearer <jeton> »."""
    if not en_tete_authorization or not en_tete_authorization.startswith(PREFIXE_JETON):
        raise ErreurMetier(401, "non_authentifie", "Authentification requise.")
    jeton = en_tete_authorization[len(PREFIXE_JETON):].strip()
    try:
        donnees = _serialiseur().loads(jeton, max_age=config.TOKEN_DUREE_SECONDES)
    except SignatureExpired:
        raise ErreurMetier(401, "jeton_expire", "Session expirée, reconnectez-vous.") from None
    except BadSignature:
        raise ErreurMetier(401, "jeton_invalide", "Jeton invalide.") from None
    return {"id_compte": donnees["id_compte"], "role": donnees["role"]}


def inscrire(nom, prenom, email, login, mot_de_passe, role):
    nom = _texte(nom, "nom")
    prenom = _texte(prenom, "prenom")
    email = _texte(email, "email")
    login = _texte(login, "login")
    if "@" not in email:
        raise ErreurMetier(400, "requete_invalide", "L'adresse e-mail n'est pas valide.")
    if role not in ROLES_INSCRIPTION:
        raise ErreurMetier(400, "requete_invalide", "Le rôle doit être « etudiant » ou « enseignant ».")
    if (not isinstance(mot_de_passe, str) or len(mot_de_passe) < 8
            or len(mot_de_passe.encode("utf-8")) > 72):
        raise ErreurMetier(400, "requete_invalide", "Le mot de passe doit faire entre 8 et 72 caractères.")

    empreinte = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    try:
        repository.creer_demande_compte(login, empreinte, role, nom, prenom, email)
    except psycopg2.IntegrityError as erreur:
        if erreur.pgcode == "23505":   # violation d'unicité (login ou e-mail déjà pris)
            raise ErreurMetier(409, "deja_existant", "Ce login ou cet e-mail est déjà utilisé.") from None
        raise
    return {"message": "Demande enregistrée : le compte sera utilisable après validation par un superviseur."}


# --- Consultation --------------------------------------------------------------

def notes_de_l_etudiant(utilisateur):
    _exiger_role(utilisateur, "etudiant")
    notes = repository.notes_de_etudiant(utilisateur["id_compte"])
    return {"notes": [
        {"code": n["code"], "intitule": n["intitule"],
         "valeur": float(n["valeur"]), "date_saisie": n["date_saisie"].isoformat()}
        for n in notes
    ]}


def cours_de_l_enseignant(utilisateur):
    _exiger_role(utilisateur, "enseignant")
    return {"cours": repository.cours_de_enseignant(utilisateur["id_compte"])}


def notes_d_un_cours(utilisateur, id_cours):
    _exiger_role(utilisateur, "enseignant")
    cours = repository.trouver_cours(id_cours)
    if cours is None:
        raise ErreurMetier(404, "cours_inexistant", "Ce cours n'existe pas.")
    if cours["id_compte_enseignant"] != utilisateur["id_compte"]:   # l'enseignant doit posséder le cours
        raise ErreurMetier(403, "acces_refuse", "Vous n'êtes pas l'enseignant de ce cours.")
    notes = repository.notes_du_cours(id_cours)
    return {
        "cours": {"id_cours": cours["id_cours"], "code": cours["code"], "intitule": cours["intitule"]},
        "notes": [
            {"id_etudiant": n["id_etudiant"], "nom": n["nom"], "prenom": n["prenom"],
             "valeur": float(n["valeur"])}
            for n in notes
        ],
    }


# --- Validation des comptes (superviseur) ----------------------------------------

def comptes_en_attente(utilisateur):
    _exiger_role(utilisateur, "superviseur")
    return {"comptes": repository.lister_comptes_en_attente()}


def valider_compte(utilisateur, id_compte):
    _exiger_role(utilisateur, "superviseur")
    if not repository.valider_compte(id_compte):
        raise ErreurMetier(404, "compte_introuvable", "Aucun compte en attente avec cet identifiant.")
    return {"message": "Compte validé."}
