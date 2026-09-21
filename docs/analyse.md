# Étape 1 — Dossier d'analyse

## 1. Acteurs

| Acteur | Rôle |
|---|---|
| Visiteur | Non connecté : peut se connecter ou demander un compte |
| Étudiant | Consulte ses propres notes, cours par cours |
| Enseignant | Consulte ses cours et les notes des étudiants de ses cours |
| Superviseur | Valide les demandes de création de compte (c'est un compte comme les autres) |

Périmètre : consultation uniquement. La saisie des notes, la gestion des inscriptions aux cours et la modification du profil sont hors sujet ; ces données sont chargées par un script de peuplement.

## 2. Cas d'usage

| Acteur | Cas d'usage | Écran |
|---|---|---|
| Visiteur | Demander un compte (étudiant ou enseignant) | E2 |
| Tous | Se connecter | E1 |
| Étudiant | Consulter ses notes | E3 |
| Enseignant | Consulter ses cours | E4 |
| Enseignant | Consulter les notes d'un de ses cours | E5 |
| Superviseur | Valider un compte en attente | E6 |

Enchaînements : étudiant E1 → E3 ; enseignant E1 → E4 → E5 ; superviseur E1 → E6.

## 3. Cas d'erreur et états vides

| Cas | Écran | Comportement | Code HTTP |
|---|---|---|---|
| Identifiant inconnu | E1 | Message « Identifiant inconnu » | 401 |
| Mot de passe erroné | E1 | Message « Mot de passe erroné » | 401 |
| Compte en attente | E1 | Message « Compte en attente de validation » | 403 |
| Enseignant sans cours | E4 | Message « Vous n'assurez aucun cours actuellement » | 200, liste vide |
| Étudiant sans note | E3 | Message « Aucune note pour le moment » | 200, liste vide |
| Cours sans inscrit | E5 | Message « Aucun étudiant inscrit à ce cours » | 200, liste vide |
| Enseignant demandant un cours qui n'est pas le sien | E5 | Message « 403 : Non autorisé » | 403 |
| Cours inexistant | E5 | Message d'erreur | 404 |

Tous ces cas sont dessinés dans le prototype Figma.

## 4. Règles de gestion

| Règle | Énoncé | Traduction dans le modèle |
|---|---|---|
| R1 | Un cours est animé par un seul enseignant | Clé étrangère obligatoire dans COURS |
| R2 | Un enseignant peut animer plusieurs cours | Cardinalité (1,n) côté ENSEIGNANT |
| R3 | Plusieurs étudiants suivent un même cours | Association plusieurs-à-plusieurs (inscription) |
| R4 | Un étudiant a au plus une note par cours | Clé primaire composée (étudiant, cours) dans NOTE |
| R5 | Un compte correspond à une seule personne | Contrainte d'unicité sur le login |
| R6 | Un compte non validé ne peut pas se connecter | Attribut de statut, vérifié à l'authentification |

## 5. Données

COMPTE (login unique, empreinte du mot de passe, rôle, statut), ENSEIGNANT, ÉTUDIANT, COURS, INSCRIPTION, NOTE. Le mot de passe est stocké sous forme d'empreinte (bcrypt), jamais en clair.
