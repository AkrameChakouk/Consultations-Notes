"""Point d'entrée de la couche métier.

Démarrage (depuis le dossier metier/, avec les variables d'environnement définies) :
    python -m app.main
L'API écoute alors sur HOST:PORT (par défaut http://127.0.0.1:5000).
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from . import config
from .routes import api
from .services import ErreurMetier


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False   # accents lisibles dans les réponses JSON
    app.register_blueprint(api)

    @app.errorhandler(ErreurMetier)
    def erreur_metier(erreur):
        return jsonify({"erreur": erreur.code, "message": erreur.message}), erreur.statut_http

    @app.errorhandler(404)
    def introuvable(_erreur):
        return jsonify({"erreur": "introuvable", "message": "Cette adresse n'existe pas."}), 404

    @app.errorhandler(405)
    def methode_interdite(_erreur):
        return jsonify({"erreur": "methode_interdite", "message": "Méthode HTTP non autorisée ici."}), 405

    @app.errorhandler(HTTPException)
    def autre_erreur_http(erreur):
        return jsonify({"erreur": "requete_invalide", "message": erreur.description}), erreur.code

    @app.errorhandler(Exception)
    def erreur_inattendue(erreur):
        # On ne renvoie jamais le détail technique au client (il pourrait révéler la base).
        app.logger.exception(erreur)
        return jsonify({"erreur": "erreur_serveur", "message": "Erreur interne du serveur."}), 500

    @app.after_request
    def autoriser_le_client(reponse):
        """CORS : autorise le client (une autre adresse) à appeler cette API."""
        reponse.headers["Access-Control-Allow-Origin"] = config.CORS_ORIGINE
        reponse.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        reponse.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return reponse

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)
