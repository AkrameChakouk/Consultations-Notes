#!/usr/bin/env bash
# Exemples de requêtes curl couvrant toutes les routes de l'API.
# Pré-requis : la base est peuplée (donnees/) et l'API tourne (python -m app.main).
# Usage : bash exemples_requetes.sh            (adresse par défaut http://127.0.0.1:5000)
#         API=http://127.0.0.1:5000 bash exemples_requetes.sh
# Tous les comptes de démonstration ont le mot de passe : motdepasse123

API="${API:-http://127.0.0.1:5000}"
JSON="Content-Type: application/json"

# Affiche un titre, puis lance curl en ajoutant le code HTTP obtenu à la fin.
requete() {
  local titre="$1"; shift
  echo
  echo "=== $titre"
  curl -s -w "\nHTTP %{http_code}\n" "$@"
}

# Se connecte et renvoie uniquement le jeton (utilise python3 pour lire le JSON).
jeton_de() {
  curl -s -X POST "$API/api/connexion" -H "$JSON" \
    -d "{\"login\":\"$1\",\"mot_de_passe\":\"motdepasse123\"}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin).get('jeton', ''))"
}

# ---------------------------------------------------------------- Route 1 : connexion
requete "1a. Connexion étudiant (attendu : 200 + jeton)" \
  -X POST "$API/api/connexion" -H "$JSON" -d '{"login":"lmartin","mot_de_passe":"motdepasse123"}'
requete "1b. Identifiant inconnu (attendu : 401)" \
  -X POST "$API/api/connexion" -H "$JSON" -d '{"login":"personne","mot_de_passe":"motdepasse123"}'
requete "1c. Mauvais mot de passe (attendu : 401)" \
  -X POST "$API/api/connexion" -H "$JSON" -d '{"login":"lmartin","mot_de_passe":"faux"}'
requete "1d. Compte en attente de validation (attendu : 403)" \
  -X POST "$API/api/connexion" -H "$JSON" -d '{"login":"cbouvet","mot_de_passe":"motdepasse123"}'

# ------------------------------------------------------------ Route 2 : inscription
LOGIN_NEUF="nouveau$(date +%s)"
requete "2a. Inscription (attendu : 201)" \
  -X POST "$API/api/inscription" -H "$JSON" \
  -d "{\"nom\":\"Test\",\"prenom\":\"Nouveau\",\"email\":\"$LOGIN_NEUF@exemple.fr\",\"login\":\"$LOGIN_NEUF\",\"mot_de_passe\":\"motdepasse123\",\"role\":\"etudiant\"}"
requete "2b. Même login (attendu : 409)" \
  -X POST "$API/api/inscription" -H "$JSON" \
  -d "{\"nom\":\"Test\",\"prenom\":\"Nouveau\",\"email\":\"autre$LOGIN_NEUF@exemple.fr\",\"login\":\"$LOGIN_NEUF\",\"mot_de_passe\":\"motdepasse123\",\"role\":\"etudiant\"}"
requete "2c. Champ manquant (attendu : 400)" \
  -X POST "$API/api/inscription" -H "$JSON" -d '{"login":"x"}'
requete "2d. Le nouveau compte ne peut pas encore se connecter (attendu : 403)" \
  -X POST "$API/api/connexion" -H "$JSON" -d "{\"login\":\"$LOGIN_NEUF\",\"mot_de_passe\":\"motdepasse123\"}"

# ------------------------------------------------------------ Route 3 : notes de l'étudiant
T_ETU=$(jeton_de lmartin)
requete "3a. Mes notes, étudiant connecté (attendu : 200, 6 notes)" \
  "$API/api/mes-notes" -H "Authorization: Bearer $T_ETU"
requete "3b. Sans jeton (attendu : 401)" \
  "$API/api/mes-notes"
requete "3c. Jeton falsifié (attendu : 401)" \
  "$API/api/mes-notes" -H "Authorization: Bearer jeton.falsifie"
T_ENS=$(jeton_de sbenali)
requete "3d. Un enseignant sur la route étudiant (attendu : 403)" \
  "$API/api/mes-notes" -H "Authorization: Bearer $T_ENS"
T_VIDE=$(jeton_de cguerin)
requete "3e. Étudiant sans aucune note (attendu : 200, liste vide)" \
  "$API/api/mes-notes" -H "Authorization: Bearer $T_VIDE"
requete "3f. Impossible de voir les notes d'un autre : un paramètre est ignoré (attendu : 200, notes de Lucas Martin)" \
  "$API/api/mes-notes?id_etudiant=2" -H "Authorization: Bearer $T_ETU"

# ------------------------------------------------------------ Route 4 : cours de l'enseignant
requete "4a. Mes cours, enseignant (attendu : 200)" \
  "$API/api/mes-cours" -H "Authorization: Bearer $T_ENS"
requete "4b. Un étudiant sur la route enseignant (attendu : 403)" \
  "$API/api/mes-cours" -H "Authorization: Bearer $T_ETU"

# ------------------------------------------------------------ Route 5 : notes d'un cours
requete "5a. Notes du cours 2 (INFO302) par son enseignant sbenali (attendu : 200)" \
  "$API/api/cours/2/notes" -H "Authorization: Bearer $T_ENS"
requete "5b. Notes du cours 1 (celui de kleroy) par sbenali (attendu : 403)" \
  "$API/api/cours/1/notes" -H "Authorization: Bearer $T_ENS"
requete "5c. Cours inexistant (attendu : 404)" \
  "$API/api/cours/999/notes" -H "Authorization: Bearer $T_ENS"
requete "5d. Un étudiant sur cette route (attendu : 403)" \
  "$API/api/cours/2/notes" -H "Authorization: Bearer $T_ETU"

# ------------------------------------------------------------ Route 6 : validation des comptes
T_ADMIN=$(jeton_de admin)
requete "6a. Comptes en attente, superviseur (attendu : 200)" \
  "$API/api/comptes-en-attente" -H "Authorization: Bearer $T_ADMIN"
requete "6b. Même route avec un étudiant (attendu : 403)" \
  "$API/api/comptes-en-attente" -H "Authorization: Bearer $T_ETU"
ID_NEUF=$(curl -s "$API/api/comptes-en-attente" -H "Authorization: Bearer $T_ADMIN" \
  | python3 -c "import sys, json; print(next(c['id_compte'] for c in json.load(sys.stdin)['comptes'] if c['login'] == '$LOGIN_NEUF'))")
requete "6c. Valider le nouveau compte (attendu : 200)" \
  -X POST "$API/api/comptes-en-attente/$ID_NEUF/validation" -H "Authorization: Bearer $T_ADMIN"
requete "6d. Valider un compte inexistant (attendu : 404)" \
  -X POST "$API/api/comptes-en-attente/99999/validation" -H "Authorization: Bearer $T_ADMIN"
requete "6e. Le nouveau compte peut maintenant se connecter (attendu : 200)" \
  -X POST "$API/api/connexion" -H "$JSON" -d "{\"login\":\"$LOGIN_NEUF\",\"mot_de_passe\":\"motdepasse123\"}"
