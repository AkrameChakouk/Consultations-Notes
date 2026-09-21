"""Routes HTTP : reçoivent la requête, appellent la logique métier, renvoient du JSON.

Il n'y a ni SQL ni règle métier ici. Les erreurs (ErreurMetier) sont transformées
en réponses JSON par le gestionnaire d'erreurs déclaré dans main.py.

Les 6 routes :
    POST /api/connexion                            tout le monde
    POST /api/inscription                          tout le monde
    GET  /api/mes-notes                            étudiant
    GET  /api/mes-cours                            enseignant
    GET  /api/cours/<id>/notes                     enseignant propriétaire du cours
    GET  /api/comptes-en-attente                   superviseur
    POST /api/comptes-en-attente/<id>/validation   superviseur
(les deux dernières forment la 6e route : « validation des comptes »)
"""
from flask import Blueprint, jsonify, request

from . import services

api = Blueprint("api", __name__, url_prefix="/api")


def _corps_json():
    corps = request.get_json(silent=True)
    if not isinstance(corps, dict):
        raise services.ErreurMetier(400, "requete_invalide", "Le corps de la requête doit être un objet JSON.")
    return corps


def _utilisateur():
    """L'appelant, identifié par son jeton (en-tête Authorization), jamais par un paramètre."""
    return services.utilisateur_depuis_en_tete(request.headers.get("Authorization"))


@api.post("/connexion")
def connexion():
    corps = _corps_json()
    return jsonify(services.connecter(corps.get("login"), corps.get("mot_de_passe")))


@api.post("/inscription")
def inscription():
    corps = _corps_json()
    resultat = services.inscrire(
        corps.get("nom"), corps.get("prenom"), corps.get("email"),
        corps.get("login"), corps.get("mot_de_passe"), corps.get("role"),
    )
    return jsonify(resultat), 201


@api.get("/mes-notes")
def mes_notes():
    return jsonify(services.notes_de_l_etudiant(_utilisateur()))


@api.get("/mes-cours")
def mes_cours():
    return jsonify(services.cours_de_l_enseignant(_utilisateur()))


@api.get("/cours/<int:id_cours>/notes")
def notes_du_cours(id_cours):
    return jsonify(services.notes_d_un_cours(_utilisateur(), id_cours))


@api.get("/comptes-en-attente")
def comptes_en_attente():
    return jsonify(services.comptes_en_attente(_utilisateur()))


@api.post("/comptes-en-attente/<int:id_compte>/validation")
def validation_compte(id_compte):
    return jsonify(services.valider_compte(_utilisateur(), id_compte))
