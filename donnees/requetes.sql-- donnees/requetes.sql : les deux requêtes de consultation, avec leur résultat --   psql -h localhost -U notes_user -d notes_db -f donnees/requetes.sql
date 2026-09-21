-- donnees/requetes.sql : les deux requêtes de consultation, avec leur résultat
--   psql -h localhost -U notes_user -d notes_db -f donnees/requetes.sql

-- Requête 1 : les notes d'un étudiant (ici Lucas Martin, n° 1)
SELECT c.code, c.intitule, n.valeur, n.date_saisie
FROM note n
JOIN cours c ON c.id_cours = n.id_cours
WHERE n.id_etudiant = 1
ORDER BY c.code;

-- Résultat :
--   code   |        intitule         | valeur | date_saisie
-- ---------+-------------------------+--------+-------------
--  INFO301 | Algorithmique           |   8.00 | 2026-06-16
--  INFO302 | Bases de données        |  15.00 | 2026-06-16
--  INFO303 | Réseaux                 |   5.00 | 2026-06-16
--  INFO304 | Systèmes d'exploitation |  15.50 | 2026-06-16
--  INFO305 | Architecture            |  17.00 | 2026-06-16
--  INFO306 | Programmation web       |  12.50 | 2026-06-16
-- (6 lignes)

-- Requête 2 : les notes des étudiants d'un cours (ici INFO302, Bases de données)
SELECT e.nom, e.prenom, n.valeur
FROM note n
JOIN etudiant e ON e.id_etudiant = n.id_etudiant
JOIN cours c ON c.id_cours = n.id_cours
WHERE c.code = 'INFO302'
ORDER BY e.nom, e.prenom;

-- Résultat :
--    nom    | prenom  | valeur
-- ----------+---------+--------
--  Bertrand | Nathan  |  11.50
--  Blanc    | Noah    |  17.00
--  Bonnet   | Adam    |   9.00
--  David    | Manon   |   9.00
--  Dubois   | Thomas  |  10.00
--  Fournier | Enzo    |   6.50
--  Garcia   | Chloé   |  14.50
--  Girard   | Lola    |   9.50
--  Lambert  | Zoé     |  19.50
--  Laurent  | Emma    |   6.50
--  Lefebvre | Louis   |  13.50
--  Martin   | Lucas   |  15.00
--  Mercier  | Maxime  |  18.50
--  Michel   | Léa     |   7.00
--  Moreau   | Inès    |  11.00
--  Morel    | Camille |  12.00
--  Rousseau | Jade    |  14.50
--  Roux     | Jules   |  17.00
--  Simon    | Hugo    |  15.50
-- (19 lignes)
