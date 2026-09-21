"""Accès aux données : c'est le SEUL fichier qui contient du SQL.

Toutes les requêtes sont paramétrées (%(nom)s) : les valeurs venant du client
ne sont jamais collées dans le texte SQL, ce qui empêche les injections SQL.
"""
from contextlib import contextmanager

import psycopg2

from . import config


@contextmanager
def _curseur():
    """Ouvre une connexion, la valide si tout va bien, l'annule sinon, puis la ferme."""
    connexion = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    try:
        curseur = connexion.cursor()
        yield curseur
        connexion.commit()
    except Exception:
        connexion.rollback()
        raise
    finally:
        connexion.close()


def _lignes(curseur):
    """Transforme le résultat d'un SELECT en liste de dictionnaires {colonne: valeur}."""
    colonnes = [colonne[0] for colonne in curseur.description]
    return [dict(zip(colonnes, ligne)) for ligne in curseur.fetchall()]


def _une_ligne(curseur):
    lignes = _lignes(curseur)
    return lignes[0] if lignes else None


# --- Comptes -----------------------------------------------------------------

def trouver_compte_par_login(login):
    with _curseur() as c:
        c.execute(
            """
            SELECT id_compte, login, mot_de_passe_hash, role, statut
            FROM compte
            WHERE login = %(login)s
            """,
            {"login": login},
        )
        return _une_ligne(c)


def trouver_identite(id_compte):
    """Nom et prénom du titulaire du compte (None pour le superviseur, qui n'a pas de fiche)."""
    with _curseur() as c:
        c.execute(
            """
            SELECT nom, prenom FROM etudiant WHERE id_compte = %(id_compte)s
            UNION ALL
            SELECT nom, prenom FROM enseignant WHERE id_compte = %(id_compte)s
            """,
            {"id_compte": id_compte},
        )
        return _une_ligne(c)


# Le nom de la table dépend du rôle : on le choisit dans cette liste fermée,
# jamais à partir d'un texte envoyé par le client.
_TABLE_PERSONNE = {"etudiant": "etudiant", "enseignant": "enseignant"}


def creer_demande_compte(login, empreinte, role, nom, prenom, email):
    """Crée d'un seul coup le compte (statut « en_attente ») et la fiche de la personne.

    Lève psycopg2.IntegrityError si le login ou l'e-mail existe déjà ;
    dans ce cas rien n'est créé.
    """
    table = _TABLE_PERSONNE[role]
    with _curseur() as c:
        c.execute(
            f"""
            WITH nouveau_compte AS (
                INSERT INTO compte (login, mot_de_passe_hash, role, statut)
                VALUES (%(login)s, %(empreinte)s, %(role)s, 'en_attente')
                RETURNING id_compte
            )
            INSERT INTO {table} (nom, prenom, email, id_compte)
            SELECT %(nom)s, %(prenom)s, %(email)s, id_compte FROM nouveau_compte
            """,
            {"login": login, "empreinte": empreinte, "role": role,
             "nom": nom, "prenom": prenom, "email": email},
        )


def lister_comptes_en_attente():
    with _curseur() as c:
        c.execute(
            """
            SELECT co.id_compte, co.login, co.role,
                   COALESCE(et.nom, en.nom) AS nom,
                   COALESCE(et.prenom, en.prenom) AS prenom
            FROM compte co
            LEFT JOIN etudiant et ON et.id_compte = co.id_compte
            LEFT JOIN enseignant en ON en.id_compte = co.id_compte
            WHERE co.statut = 'en_attente'
            ORDER BY co.id_compte
            """
        )
        return _lignes(c)


def valider_compte(id_compte):
    """Passe un compte en attente à « valide ». Renvoie False s'il n'y a rien à valider."""
    with _curseur() as c:
        c.execute(
            """
            UPDATE compte SET statut = 'valide'
            WHERE id_compte = %(id_compte)s AND statut = 'en_attente'
            RETURNING id_compte
            """,
            {"id_compte": id_compte},
        )
        return _une_ligne(c) is not None


# --- Consultation ------------------------------------------------------------

def notes_de_etudiant(id_compte):
    with _curseur() as c:
        c.execute(
            """
            SELECT co.code, co.intitule, n.valeur, n.date_saisie
            FROM note n
            JOIN etudiant e ON e.id_etudiant = n.id_etudiant
            JOIN cours co ON co.id_cours = n.id_cours
            WHERE e.id_compte = %(id_compte)s
            ORDER BY co.code
            """,
            {"id_compte": id_compte},
        )
        return _lignes(c)


def cours_de_enseignant(id_compte):
    with _curseur() as c:
        c.execute(
            """
            SELECT co.id_cours, co.code, co.intitule, COUNT(n.id_etudiant) AS nb_inscrits
            FROM cours co
            JOIN enseignant e ON e.id_enseignant = co.id_enseignant
            LEFT JOIN note n ON n.id_cours = co.id_cours
            WHERE e.id_compte = %(id_compte)s
            GROUP BY co.id_cours, co.code, co.intitule
            ORDER BY co.code
            """,
            {"id_compte": id_compte},
        )
        return _lignes(c)


def trouver_cours(id_cours):
    """Un cours et le compte de son enseignant (None si le cours n'existe pas)."""
    with _curseur() as c:
        c.execute(
            """
            SELECT co.id_cours, co.code, co.intitule, e.id_compte AS id_compte_enseignant
            FROM cours co
            JOIN enseignant e ON e.id_enseignant = co.id_enseignant
            WHERE co.id_cours = %(id_cours)s
            """,
            {"id_cours": id_cours},
        )
        return _une_ligne(c)


def notes_du_cours(id_cours):
    with _curseur() as c:
        c.execute(
            """
            SELECT e.id_etudiant, e.nom, e.prenom, n.valeur
            FROM note n
            JOIN etudiant e ON e.id_etudiant = n.id_etudiant
            WHERE n.id_cours = %(id_cours)s
            ORDER BY e.nom, e.prenom
            """,
            {"id_cours": id_cours},
        )
        return _lignes(c)
