# Procédure d'installation

Cette procédure a été suivie sur une machine qui n'avait rien d'installé pour ce projet (Ubuntu, ni PostgreSQL, ni `python3-venv`, ni `python3-pip`). Les commandes manquantes ont été ajoutées au fur et à mesure, sans rien changer au code.

## 1. Récupérer le dépôt

```bash
git clone https://github.com/AkrameChakouk/Consultations-Notes.git
cd Consultations-Notes
```

## 2. Installer et démarrer PostgreSQL

```bash
sudo apt update
sudo apt install -y postgresql
sudo systemctl start postgresql
```

Créer le rôle et la base utilisés par le projet :

```bash
sudo -u postgres psql -c "CREATE ROLE notes_user WITH LOGIN PASSWORD 'notes_password';"
sudo -u postgres psql -c "CREATE DATABASE notes_db OWNER notes_user;"
```

Charger le schéma et les données de démonstration :

```bash
export PGPASSWORD=notes_password
psql -h localhost -U notes_user -d notes_db -f donnees/schema.sql
psql -h localhost -U notes_user -d notes_db -f donnees/peuplement.sql
```

## 3. Installer Python et les dépendances de l'API

Sur une machine sans `venv` ni `pip`, ces deux paquets système manquent et doivent être installés une fois :

```bash
sudo apt install -y python3-venv python3-pip
```

Puis, dans le dossier `metier/` :

```bash
cd metier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configurer et démarrer l'API

```bash
cp .env.example .env
# adapter .env si les identifiants de la base sont différents
set -a; source .env; set +a
python -m app.main
```

L'API écoute sur `http://127.0.0.1:5000`. La laisser tourner dans ce terminal.

Pour vérifier que tout fonctionne, dans un second terminal :

```bash
cd metier
bash exemples_requetes.sh
```

Chaque ligne affiche le code HTTP obtenu à côté du code attendu dans son titre ; les deux doivent correspondre (voir [`tests.md`](tests.md)).

## 5. Démarrer le client

Dans un troisième terminal :

```bash
cd client
python3 -m http.server 8080
```

Ouvrir `http://localhost:8080` dans un navigateur. Comptes de démonstration (mot de passe `motdepasse123`) : `lmartin` (étudiant), `sbenali` (enseignant), `admin` (superviseur).

## Résultat

Sur la machine de test, la seule difficulté rencontrée a été l'absence des paquets `python3-venv` et `python3-pip`, signalée clairement par le message d'erreur de `python3 -m venv`. Une fois ces deux paquets installés avec `apt`, la suite de la procédure (base de données, API, client) a fonctionné sans aucune autre correction.
