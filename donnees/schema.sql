-- donnees/schema.sql : création du schéma (PostgreSQL)
-- À exécuter sur une base vide :
--   psql -h localhost -U notes_user -d notes_db -f donnees/schema.sql

DROP TABLE IF EXISTS note, cours, etudiant, enseignant, compte CASCADE;

-- COMPTE : tout le monde se connecte avec un compte (étudiant, enseignant ou superviseur)
CREATE TABLE compte (
    id_compte         SERIAL PRIMARY KEY,
    login             VARCHAR(50)  NOT NULL UNIQUE,  -- R5 : un login = un seul compte
    mot_de_passe_hash VARCHAR(100) NOT NULL,         -- empreinte bcrypt, jamais le mot de passe en clair
    role              VARCHAR(20)  NOT NULL
                      CHECK (role IN ('etudiant', 'enseignant', 'superviseur')),
    statut            VARCHAR(20)  NOT NULL DEFAULT 'en_attente'
                      CHECK (statut IN ('en_attente', 'valide'))   -- R6 : vérifié à la connexion
);

CREATE TABLE enseignant (
    id_enseignant SERIAL PRIMARY KEY,
    nom           VARCHAR(50)  NOT NULL,
    prenom        VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    id_compte     INTEGER      NOT NULL UNIQUE REFERENCES compte (id_compte)
);

CREATE TABLE etudiant (
    id_etudiant SERIAL PRIMARY KEY,
    nom         VARCHAR(50)  NOT NULL,
    prenom      VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    id_compte   INTEGER      NOT NULL UNIQUE REFERENCES compte (id_compte)
);

CREATE TABLE cours (
    id_cours      SERIAL PRIMARY KEY,
    code          VARCHAR(10)  NOT NULL UNIQUE,
    intitule      VARCHAR(100) NOT NULL,
    -- R1 : un cours a un seul enseignant (clé étrangère obligatoire)
    -- R2 : un enseignant peut avoir plusieurs cours (pas de UNIQUE sur cette colonne)
    id_enseignant INTEGER      NOT NULL REFERENCES enseignant (id_enseignant)
);

-- NOTE : relie un étudiant à un cours (R3 : plusieurs étudiants par cours, plusieurs cours par étudiant)
CREATE TABLE note (
    id_etudiant INTEGER      NOT NULL REFERENCES etudiant (id_etudiant),
    id_cours    INTEGER      NOT NULL REFERENCES cours (id_cours),
    valeur      NUMERIC(4,2) NOT NULL CHECK (valeur BETWEEN 0 AND 20),
    date_saisie DATE         NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (id_etudiant, id_cours)   -- R4 : au plus une note par étudiant et par cours
);
