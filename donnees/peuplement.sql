-- donnees/peuplement.sql : jeu de données fictif
-- À exécuter APRÈS schema.sql :
--   psql -h localhost -U notes_user -d notes_db -f donnees/peuplement.sql
--
-- Contenu : 1 superviseur, 4 enseignants valides + 1 en attente, 20 étudiants valides + 1 en attente,
-- 7 cours, 114 notes.
-- Cas limites : enseignant sans cours (Gauthier), étudiant sans note (Guérin),
-- cours sans inscrit (INFO307), comptes en attente (Bouvet, A. Martin).
-- Tous les comptes ont le même mot de passe de démonstration : motdepasse123
-- (seule son empreinte bcrypt est stockée).

-- Superviseur
INSERT INTO compte (login, mot_de_passe_hash, role, statut)
VALUES ('admin', '$2a$10$HEjLkVodndjgFM.iho1wFuFApIUeXxvzbGEyPWDKeJif0uZJcWLYa', 'superviseur', 'valide');

-- Enseignants (compte + fiche)
WITH v(nom, prenom, email, login, statut) AS (VALUES
    ('Benali',   'Sarah',  'sarah.benali@ecoleo.fr',   'sbenali',   'valide'),
    ('Leroy',    'Karim',  'karim.leroy@ecoleo.fr',    'kleroy',    'valide'),
    ('Fontaine', 'Nadia',  'nadia.fontaine@ecoleo.fr', 'nfontaine', 'valide'),
    ('Gauthier', 'Paul',   'paul.gauthier@ecoleo.fr',  'pgauthier', 'valide'),
    ('Bouvet',   'Claire', 'claire.bouvet@ecoleo.fr',  'cbouvet',   'en_attente')
), c AS (
    INSERT INTO compte (login, mot_de_passe_hash, role, statut)
    SELECT login, '$2a$10$HEjLkVodndjgFM.iho1wFuFApIUeXxvzbGEyPWDKeJif0uZJcWLYa', 'enseignant', statut
    FROM v
    RETURNING id_compte, login
)
INSERT INTO enseignant (nom, prenom, email, id_compte)
SELECT v.nom, v.prenom, v.email, c.id_compte
FROM v JOIN c USING (login)
ORDER BY c.id_compte;

-- Étudiants (compte + fiche)
WITH v(nom, prenom, email, login, statut) AS (VALUES
    ('Martin',   'Lucas',     'lucas.martin@etu.ecoleo.fr',     'lmartin',   'valide'),
    ('Dubois',   'Thomas',    'thomas.dubois@etu.ecoleo.fr',    'tdubois',   'valide'),
    ('Moreau',   'Inès',      'ines.moreau@etu.ecoleo.fr',      'imoreau',   'valide'),
    ('Laurent',  'Emma',      'emma.laurent@etu.ecoleo.fr',     'elaurent',  'valide'),
    ('Simon',    'Hugo',      'hugo.simon@etu.ecoleo.fr',       'hsimon',    'valide'),
    ('Michel',   'Léa',       'lea.michel@etu.ecoleo.fr',       'lmichel',   'valide'),
    ('Lefebvre', 'Louis',     'louis.lefebvre@etu.ecoleo.fr',   'llefebvre', 'valide'),
    ('Garcia',   'Chloé',     'chloe.garcia@etu.ecoleo.fr',     'cgarcia',   'valide'),
    ('Roux',     'Jules',     'jules.roux@etu.ecoleo.fr',       'jroux',     'valide'),
    ('David',    'Manon',     'manon.david@etu.ecoleo.fr',      'mdavid',    'valide'),
    ('Bertrand', 'Nathan',    'nathan.bertrand@etu.ecoleo.fr',  'nbertrand', 'valide'),
    ('Morel',    'Camille',   'camille.morel@etu.ecoleo.fr',    'cmorel',    'valide'),
    ('Fournier', 'Enzo',      'enzo.fournier@etu.ecoleo.fr',    'efournier', 'valide'),
    ('Girard',   'Lola',      'lola.girard@etu.ecoleo.fr',      'lgirard',   'valide'),
    ('Bonnet',   'Adam',      'adam.bonnet@etu.ecoleo.fr',      'abonnet',   'valide'),
    ('Lambert',  'Zoé',       'zoe.lambert@etu.ecoleo.fr',      'zlambert',  'valide'),
    ('Mercier',  'Maxime',    'maxime.mercier@etu.ecoleo.fr',   'mmercier',  'valide'),
    ('Rousseau', 'Jade',      'jade.rousseau@etu.ecoleo.fr',    'jrousseau', 'valide'),
    ('Blanc',    'Noah',      'noah.blanc@etu.ecoleo.fr',       'nblanc',    'valide'),
    ('Guérin',   'Clara',     'clara.guerin@etu.ecoleo.fr',     'cguerin',   'valide'),
    ('Martin',   'Alexandre', 'alexandre.martin@etu.ecoleo.fr', 'amartin',   'en_attente')
), c AS (
    INSERT INTO compte (login, mot_de_passe_hash, role, statut)
    SELECT login, '$2a$10$HEjLkVodndjgFM.iho1wFuFApIUeXxvzbGEyPWDKeJif0uZJcWLYa', 'etudiant', statut
    FROM v
    RETURNING id_compte, login
)
INSERT INTO etudiant (nom, prenom, email, id_compte)
SELECT v.nom, v.prenom, v.email, c.id_compte
FROM v JOIN c USING (login)
ORDER BY c.id_compte;

-- Cours (INFO307 n'aura aucun inscrit ; Gauthier n'a aucun cours)
INSERT INTO cours (code, intitule, id_enseignant)
SELECT v.code, v.intitule, e.id_enseignant
FROM (VALUES
    ('INFO301', 'Algorithmique',               'Leroy'),
    ('INFO302', 'Bases de données',            'Benali'),
    ('INFO303', 'Réseaux',                     'Leroy'),
    ('INFO304', 'Systèmes d''exploitation',    'Fontaine'),
    ('INFO305', 'Architecture',                'Benali'),
    ('INFO306', 'Programmation web',           'Fontaine'),
    ('INFO307', 'Gestion de projet',           'Leroy')
) AS v(code, intitule, nom_enseignant)
JOIN enseignant e ON e.nom = v.nom_enseignant
ORDER BY v.code;

-- Notes : les 19 premiers étudiants ont une note dans les 6 premiers cours (19 x 6 = 114 notes).
-- L'étudiante Guérin (n° 20) n'a aucune note ; le cours INFO307 (n° 7) n'a aucun inscrit.
-- La valeur est calculée à partir d'une empreinte md5 : elle a l'air aléatoire (entre 5 et 19,5)
-- mais reste toujours identique d'une exécution à l'autre.
INSERT INTO note (id_etudiant, id_cours, valeur, date_saisie)
SELECT e.id_etudiant,
       c.id_cours,
       5 + (('x' || substr(md5(e.id_etudiant::text || '-' || c.id_cours::text), 1, 4))::bit(16)::int % 30) * 0.5,
       DATE '2026-06-15' + (e.id_etudiant % 5)
FROM etudiant e
CROSS JOIN cours c
WHERE e.id_etudiant <= 19
  AND c.id_cours <= 6;
