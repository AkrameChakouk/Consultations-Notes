# Étape 6 — Tests d'intégration

Ce document liste les tests effectués sur l'application complète (client + API + base de données), avec pour chaque cas l'action réalisée, le résultat attendu, et le résultat obtenu.

Les captures d'écran citées sont dans [`captures/`](captures/). Les comptes de démonstration ont le mot de passe `motdepasse123` (voir `donnees/peuplement.sql`).

## Test spécifique demandé par le sujet : un étudiant ne peut pas voir les notes d'un autre

C'est le test le plus important de cette étape : l'identité de l'utilisateur doit venir uniquement du jeton de connexion, jamais d'une information envoyée par le client.

| Action | Attendu | Obtenu |
|---|---|---|
| Se connecter en `lmartin` (étudiant), puis appeler `GET /api/mes-notes?id_etudiant=2` en ajoutant à la main le numéro d'un autre étudiant dans l'adresse | 200, et les notes renvoyées restent celles de Lucas Martin (le paramètre est ignoré) | 200, notes de Lucas Martin uniquement — le paramètre `id_etudiant` n'existe nulle part dans le code de la route ou du service, il ne peut donc pas être lu |
| Appeler `GET /api/mes-notes` sans jeton | 401 `non_authentifie` | 401 `non_authentifie` |
| Appeler `GET /api/mes-notes` avec un jeton falsifié (`jeton.falsifie`) | 401 `jeton_invalide` | 401 `jeton_invalide` |
| Se connecter en `sbenali` (enseignant) puis appeler `GET /api/cours/1/notes` (cours qui appartient à `kleroy`) | 403 `acces_refuse` | 403 `acces_refuse` — capture [`08_enseignant_cours_non_autorise.png`](captures/08_enseignant_cours_non_autorise.png) |

Ce comportement vient directement du code : `routes.py` lit l'identité avec `services.utilisateur_depuis_en_tete(request.headers.get("Authorization"))`, qui décode le jeton signé ; aucune route ne lit un identifiant d'étudiant envoyé par le client pour la route « mes notes ». Pour la route « notes d'un cours », `services.notes_d_un_cours` compare `cours["id_compte_enseignant"]` à `utilisateur["id_compte"]` (celui du jeton) avant de renvoyer quoi que ce soit.

## Couche métier (API) — 25 requêtes, testées avec les vrais `psycopg2` et `bcrypt`

Rejouées avec `bash exemples_requetes.sh` (voir `metier/exemples_requetes.sh`), sur la machine de développement, après installation des dépendances avec `pip install -r requirements.txt`.

| Cas | Action | Attendu | Obtenu |
|---|---|---|---|
| 1a | Connexion avec un identifiant et un mot de passe valides (`lmartin`) | 200 + jeton | 200 |
| 1b | Connexion avec un identifiant inconnu | 401 `identifiant_inconnu` | 401 |
| 1c | Connexion avec le bon identifiant et un mauvais mot de passe | 401 `mot_de_passe_errone` | 401 |
| 1d | Connexion sur un compte en attente de validation (`cbouvet`) | 403 `compte_en_attente` | 403 |
| 2a | Inscription avec des informations valides | 201 | 201 |
| 2b | Inscription avec un login déjà utilisé | 409 `deja_existant` | 409 |
| 2c | Inscription avec des champs manquants | 400 `requete_invalide` | 400 |
| 2d | Connexion avec le compte tout juste créé (pas encore validé) | 403 `compte_en_attente` | 403 |
| 3a | `GET /api/mes-notes` en tant qu'étudiant avec des notes (`lmartin`) | 200, 6 notes | 200, 6 notes |
| 3b | `GET /api/mes-notes` sans jeton | 401 `non_authentifie` | 401 |
| 3c | `GET /api/mes-notes` avec un jeton invalide | 401 `jeton_invalide` | 401 |
| 3d | `GET /api/mes-notes` avec le jeton d'un enseignant | 403 `acces_refuse` | 403 |
| 3e | `GET /api/mes-notes` pour un étudiant sans aucune note (`cguerin`) | 200, liste vide | 200, liste vide |
| 3f | `GET /api/mes-notes?id_etudiant=2` avec le jeton de `lmartin` | 200, notes de Lucas Martin (paramètre ignoré) | 200, notes de Lucas Martin |
| 4a | `GET /api/mes-cours` en tant qu'enseignant (`sbenali`) | 200, 2 cours | 200, 2 cours |
| 4b | `GET /api/mes-cours` avec le jeton d'un étudiant | 403 `acces_refuse` | 403 |
| 5a | `GET /api/cours/2/notes` par l'enseignant propriétaire (`sbenali`) | 200, 19 notes | 200, 19 notes |
| 5b | `GET /api/cours/1/notes` par `sbenali` (cours d'un autre enseignant) | 403 `acces_refuse` | 403 |
| 5c | `GET /api/cours/999/notes` (cours inexistant) | 404 `cours_inexistant` | 404 |
| 5d | `GET /api/cours/2/notes` avec le jeton d'un étudiant | 403 `acces_refuse` | 403 |
| 6a | `GET /api/comptes-en-attente` en tant que superviseur (`admin`) | 200, liste des comptes en attente | 200 |
| 6b | `GET /api/comptes-en-attente` avec le jeton d'un étudiant | 403 `acces_refuse` | 403 |
| 6c | `POST /api/comptes-en-attente/<id>/validation` sur un compte en attente | 200 `Compte validé.` | 200 |
| 6d | `POST /api/comptes-en-attente/99999/validation` (identifiant inexistant) | 404 `compte_introuvable` | 404 |
| 6e | Connexion avec le compte validé à l'étape 6c | 200 + jeton | 200 |

## Couche présentation (client) — parcours dans le navigateur

Testés avec l'API et la base de données réellement démarrées (Flask + PostgreSQL), en suivant les parcours à la souris et au clavier dans Chrome.

### Parcours étudiant (E1 → E3)

| Action | Attendu | Obtenu |
|---|---|---|
| Ouvrir la page de connexion sans rien saisir, cliquer sur « Se connecter » | Message « Renseignez votre identifiant et votre mot de passe » | Conforme |
| Se connecter avec un identifiant inconnu | Bandeau rouge « Identifiant inconnu. » | Conforme — capture [`02_connexion_identifiant_inconnu.png`](captures/02_connexion_identifiant_inconnu.png) |
| Se connecter avec un compte en attente (`cbouvet`) | Bandeau orange « Compte en attente de validation. » | Conforme — capture [`03_connexion_compte_en_attente.png`](captures/03_connexion_compte_en_attente.png) |
| Se connecter avec `lmartin` | Redirection vers « Mes notes de cours », 6 lignes | Conforme — capture [`04_etudiant_mes_notes.png`](captures/04_etudiant_mes_notes.png) |
| Ouvrir directement `enseignant.html` ou `cours.html` en tant qu'étudiant connecté | Renvoyé automatiquement vers `etudiant.html` | Conforme |
| Se déconnecter, puis rouvrir `etudiant.html` sans être connecté | Renvoyé vers la page de connexion | Conforme |
| Se connecter avec un étudiant sans note (`cguerin`) | Message « Aucune note enregistrée » | Conforme — capture [`05_etudiant_notes_vide.png`](captures/05_etudiant_notes_vide.png) |

### Parcours enseignant (E1 → E4 → E5)

| Action | Attendu | Obtenu |
|---|---|---|
| Se connecter avec `sbenali` | « Mes enseignements » : 2 cours (INFO302, INFO305) avec leur nombre d'inscrits | Conforme — capture [`06_enseignant_mes_cours.png`](captures/06_enseignant_mes_cours.png) |
| Cliquer sur « Notes → » d'un cours | Tableau des étudiants et de leurs notes pour ce cours | Conforme — capture [`07_enseignant_notes_du_cours.png`](captures/07_enseignant_notes_du_cours.png) |
| Ouvrir `cours.html?id=1` (cours d'un autre enseignant) | Bandeau rouge « 403 : Vous n'êtes pas l'enseignant de ce cours. » | Conforme — capture [`08_enseignant_cours_non_autorise.png`](captures/08_enseignant_cours_non_autorise.png) |
| Ouvrir `cours.html?id=999` (cours inexistant) | Bandeau rouge « 404 : Ce cours n'existe pas. » | Conforme |
| Ouvrir un cours sans étudiant inscrit (INFO307) | Message « Aucun étudiant inscrit » | Conforme |
| Se connecter avec un enseignant sans cours (`pgauthier`) | Message « Aucun cours assigné » | Conforme |

### Parcours superviseur (E1 → E6)

| Action | Attendu | Obtenu |
|---|---|---|
| Se connecter avec `admin` | Liste des comptes en attente (login, nom, rôle) | Conforme — capture [`10_superviseur_comptes_en_attente.png`](captures/10_superviseur_comptes_en_attente.png) |
| Cliquer sur « Valider » pour un compte | Bandeau vert de confirmation, la ligne disparaît de la liste | Conforme |
| Valider tous les comptes en attente | Message « Aucune demande en attente » | Conforme — capture [`11_superviseur_liste_vide.png`](captures/11_superviseur_liste_vide.png) |
| Se connecter avec le compte tout juste validé | Connexion acceptée, redirection vers son espace | Conforme |

### Inscription (E2)

| Action | Attendu | Obtenu |
|---|---|---|
| Ouvrir « Créer un compte » | Formulaire nom / prénom / e-mail / login / mot de passe / rôle | Conforme — capture [`09_inscription.png`](captures/09_inscription.png) |
| Envoyer le formulaire complet | Bandeau vert « Demande enregistrée : le compte sera utilisable après validation par un superviseur. » | Conforme |
| Renvoyer le même login | Bandeau rouge « Ce login ou cet e-mail est déjà utilisé. » | Conforme |
| Envoyer un mot de passe de moins de 8 caractères | Bandeau rouge « Le mot de passe doit faire au moins 8 caractères. » | Conforme |
| Saisir un nom contenant du code (`<b onmouseover=...>`) | Le nom s'affiche comme du texte brut dans la liste du superviseur, sans exécuter de code | Conforme |

### États et robustesse

| Action | Attendu | Obtenu |
|---|---|---|
| Couper l'API puis se connecter | Bandeau rouge « Impossible de joindre le serveur. Vérifiez que l'API est démarrée. » | Conforme |
| Ralentir la réponse de l'API | La liste affiche l'état d'attente (roue qui tourne) avant les données | Conforme |
| Remplacer le jeton de session par une valeur invalide, recharger une page protégée | Retour automatique à la page de connexion avec un message | Conforme |
| Ouvrir l'application sur un écran de largeur téléphone (390 px) | Pas de défilement horizontal, menu et contenu lisibles | Conforme |
| Consulter la console du navigateur pendant tous les parcours ci-dessus | Aucune erreur JavaScript | Conforme |

## Procédure d'installation sur machine vierge

Testée en conditions réelles sur l'ordinateur d'Akrame (Ubuntu), qui ne possédait initialement ni PostgreSQL, ni `python3-venv`, ni `python3-pip`. Le détail est dans [`installation.md`](installation.md). Les paquets système manquants ont été identifiés par les messages d'erreur du terminal et installés avec `apt`, puis toute la procédure a fonctionné sans autre correction.
