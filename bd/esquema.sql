-- Base de datos biológica de insectos amazónicos.
-- Las 19 columnas provienen del documento "Proyecto Formativo IF", sección IX.
-- Se genera desde bd_insectos.xlsx con: python -m pipeline.bd

DROP TABLE IF EXISTS insectos;

CREATE TABLE insectos (
    ID                    TEXT PRIMARY KEY,
    Archivo_imagen        TEXT,
    Vistas_fotograficas   TEXT,
    Orden                 TEXT NOT NULL,
    Familia               TEXT,
    Nombre_cientifico     TEXT,
    Nombre_comun          TEXT,
    Cultivo_asociado      TEXT,
    Tipo_de_dano          TEXT,
    Hospedero             TEXT,
    Localidad             TEXT,
    Coordenadas           TEXT,
    Fecha                 TEXT,
    Colector              TEXT,
    Importancia_economica TEXT,
    Estado_biologico      TEXT,
    Fuente                TEXT,
    Verificado_por        TEXT,
    Observaciones         TEXT
);

CREATE INDEX idx_insectos_orden   ON insectos (Orden);
CREATE INDEX idx_insectos_familia ON insectos (Familia);
CREATE INDEX idx_insectos_cultivo ON insectos (Cultivo_asociado);
