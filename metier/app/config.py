"""Configuration de la couche métier.

Rien n'est écrit en dur : la base de données, les identifiants et la clé secrète
viennent obligatoirement des variables d'environnement (voir .env.example).
Seuls l'adresse d'écoute de l'API et les réglages sans danger ont une valeur par défaut.
"""
import os


def _obligatoire(nom):
    valeur = os.environ.get(nom)
    if not valeur:
        raise RuntimeError(
            f"Variable d'environnement manquante : {nom}. "
            "Copier .env.example en .env, l'adapter, puis lancer : set -a; source .env; set +a"
        )
    return valeur


# --- Base de données (obligatoire) -----------------------------------------------
DB_HOST = _obligatoire("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = _obligatoire("DB_NAME")
DB_USER = _obligatoire("DB_USER")
DB_PASSWORD = _obligatoire("DB_PASSWORD")

# --- Serveur (adresse et port d'écoute de l'API) -----------------------------------
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5000"))

# --- Jeton d'authentification ------------------------------------------------------
# La clé sert à signer les jetons : obligatoire, à garder secrète.
SECRET_KEY = _obligatoire("SECRET_KEY")
TOKEN_DUREE_SECONDES = int(os.environ.get("TOKEN_DUREE_SECONDES", "3600"))

# --- Client autorisé à appeler l'API (CORS) ------------------------------------------
# "*" = tout le monde (pratique en développement). En déploiement : l'adresse du client.
CORS_ORIGINE = os.environ.get("CORS_ORIGINE", "*")
