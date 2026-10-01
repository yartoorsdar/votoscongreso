"""Base SQLite del proyecto (data/votos.db): esquema, migraciones y normalización de nombres."""
import sqlite3, pathlib, re, unicodedata

DB = pathlib.Path(__file__).resolve().parent.parent / "data" / "votos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS diputados(id INTEGER PRIMARY KEY, nombre TEXT, nombre_norm TEXT, bloque_id INTEGER, bloque TEXT);
CREATE TABLE IF NOT EXISTS sesiones(id INTEGER PRIMARY KEY, tipo TEXT, numero INTEGER, descripcion TEXT, fecha TEXT, scraped INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS votaciones(id INTEGER PRIMARY KEY, sesion_id INTEGER, numero INTEGER, pregunta TEXT, fecha TEXT, iniciativa TEXT, scraped INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS votos(votacion_id INTEGER, diputado_nombre TEXT, nombre_norm TEXT, estado TEXT, voto TEXT, PRIMARY KEY(votacion_id, nombre_norm));
CREATE TABLE IF NOT EXISTS decretos(numero TEXT PRIMARY KEY, fecha TEXT, resumen TEXT, iniciativas TEXT);
CREATE TABLE IF NOT EXISTS iniciativas(numero TEXT PRIMARY KEY, fecha TEXT, resumen TEXT);
CREATE TABLE IF NOT EXISTS iniciativa_detalle(numero TEXT PRIMARY KEY, id_interno INTEGER, titulo TEXT, fecha TEXT, ponentes TEXT, pasos TEXT, notas TEXT,
  decreto TEXT, decreto_fecha TEXT, decreto_id TEXT, decreto_pdf TEXT, pdf TEXT);
CREATE TABLE IF NOT EXISTS alias_nombre(nombre_norm TEXT PRIMARY KEY, diputado_id INTEGER, metodo TEXT);
CREATE TABLE IF NOT EXISTS sesiones_excluidas(id INTEGER PRIMARY KEY, motivo TEXT);
CREATE TABLE IF NOT EXISTS bloque_anio(diputado_id INTEGER, anio INTEGER, bloque_id INTEGER, bloque TEXT, PRIMARY KEY(diputado_id, anio));
CREATE INDEX IF NOT EXISTS ix_votos_n ON votos(nombre_norm);
CREATE INDEX IF NOT EXISTS ix_vot_ini ON votaciones(iniciativa);
"""

# Columnas añadidas después de la primera versión: se agregan solas a bases ya existentes.
COLUMNAS_NUEVAS = [("votaciones", "decreto", "TEXT"), ("votaciones", "hora", "TEXT")]


def conn():
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    for tabla, col, tipo in COLUMNAS_NUEVAS:
        if col not in [r[1] for r in c.execute(f"PRAGMA table_info({tabla})")]:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
    c.commit()
    return c


def norm(s):
    """Clave de nombre independiente de tildes, mayúsculas y orden: 'Apellidos Nombres' == 'Nombres Apellidos'."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(sorted(re.sub(r"[^a-z ]", " ", s).split()))
