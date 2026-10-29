"""Descarga y limpieza de los datos de siniestros viales de la Ciudad de Buenos Aires."""

import os
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/victimas-siniestros-viales"
ARCHIVOS = {"hechos": "siniestros_viales_hechos.csv", "victimas": "siniestros_viales_victimas.csv"}
SIN_DATO = {"", "SD", "S/D", "NA", "N/A", "NAN", "NONE", "SIN DATO", "SIN DATOS", "-"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def carpeta_datos():
    return Path(os.environ.get("SINIESTROS_DATOS", Path(__file__).resolve().parent.parent / "data"))


def descargar(destino=None):
    destino = Path(destino or carpeta_datos())
    destino.mkdir(parents=True, exist_ok=True)
    for archivo in ARCHIVOS.values():
        req = urllib.request.Request(f"{BASE}/{archivo}", headers={"User-Agent": "analisis-siniestros-viales-ar"})
        with urllib.request.urlopen(req, timeout=120) as r:
            contenido = r.read()
        (destino / archivo).write_bytes(contenido)
        # Se muestran las primeras líneas en el log para detectar cambios de formato en la fuente.
        cabecera = contenido[:4000].decode("utf-8", "replace").splitlines()[:3]
        print(f"Descargado {archivo} ({len(contenido):,} bytes)", *cabecera, sep="\n  ")


def _leer_csv(ruta):
    """Los CSV del GCBA cambiaron de separador y encoding entre ediciones: se detectan los dos."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(ruta, sep=None, engine="python", encoding=encoding, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    df.columns = [_normalizar(c).lower().replace(" ", "_") for c in df.columns]
    return df


def _normalizar(texto):
    if not isinstance(texto, str):
        return texto
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.upper().split())


def _limpiar_texto(serie):
    s = serie.map(_normalizar)
    return s.where(~s.isin(SIN_DATO))


def _numero(serie):
    return pd.to_numeric(serie.str.replace(",", ".", regex=False), errors="coerce")


def es_mortal(gravedad):
    return gravedad.fillna("").str.contains("MORTAL|FATAL")


# El GCBA renombró las columnas entre ediciones (por ejemplo fecha -> fecha_siniestro).
# Para cada nombre canónico se prueban los alias conocidos, en orden.
ALIAS_HECHOS = {
    "id_hecho": ["id_hecho", "id_siniestro"],
    "n_victimas": ["n_victimas", "numero_total_de_victimas"],
    "n_mortales": ["numero_victimas_mortal_siniestro"],
    "fecha": ["fecha", "fecha_siniestro"],
    "hora": ["hora", "hora_siniestro"],
    "hh": ["hh"],
    "comuna": ["comuna", "comuna_siniestro"],
    "tipo_de_calle": ["tipo_de_calle", "tipo_de_via_siniestro"],
    "longitud": ["longitud", "longitud_siniestro"],
    "latitud": ["latitud", "latitud_siniestro"],
    "participantes": ["participantes", "participantes_siniestro"],
    "victima": ["victima", "modo_desplazamiento_victima", "modo_desplazamiento_victima_siniestro"],
    "contraparte": ["contraparte", "modo_desplazamiento_acusado", "modo_desplazamiento_contraparte"],
    "gravedad": ["gravedad", "gravedad_siniestro"],
}
ALIAS_VICTIMAS = {
    "id_hecho": ["id_hecho", "id_siniestro"],
    "fecha": ["fecha", "fecha_siniestro"],
    "victima": ["victima", "modo_desplazamiento_victima"],
    "sexo_victima": ["sexo_victima"],
    "edad_victima": ["edad_victima"],
    "gravedad": ["gravedad", "gravedad_victima"],
    "rol_victima": ["rol_victima"],
}
SEXOS = {"M": "MASCULINO", "F": "FEMENINO", "X": "NO BINARIO"}


def _renombrar(df, alias):
    columnas = {}
    for canonico, candidatos in alias.items():
        encontrada = next((c for c in candidatos if c in df.columns), None)
        if encontrada is None:  # último recurso: una columna que empiece con el nombre canónico
            encontrada = next((c for c in df.columns if c.startswith(canonico) and c not in columnas), None)
        if encontrada is not None:
            columnas[encontrada] = canonico
    df = df.rename(columns=columnas)
    for canonico in alias:
        if canonico not in df:
            df[canonico] = pd.NA
    return df


def _fecha(serie):
    """Acepta dd/mm/aaaa (ediciones viejas) y aaaa-mm-dd (nuevas) sin confundir día y mes."""
    serie = serie.astype("string").str.strip().str[:10]
    iso = pd.to_datetime(serie, format="%Y-%m-%d", errors="coerce")
    local = pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(local)


def limpiar_hechos(df):
    df = _renombrar(df, ALIAS_HECHOS)
    df["fecha"] = _fecha(df["fecha"])
    df = df.dropna(subset=["fecha"])
    for c in ("victima", "contraparte", "gravedad", "tipo_de_calle", "participantes"):
        df[c] = _limpiar_texto(df[c].astype("string"))
    for c in ("n_victimas", "n_mortales", "hh", "latitud", "longitud"):
        df[c] = _numero(df[c].astype("string"))
    df["comuna"] = pd.to_numeric(df["comuna"].astype("string").str.extract(r"(\d+)")[0], errors="coerce")
    if df["hh"].isna().all():
        df["hh"] = pd.to_numeric(df["hora"].astype("string").str.extract(r"^\s*(\d{1,2})")[0], errors="coerce")
    df["hh"] = df["hh"].where(df["hh"].between(0, 23))
    df["anio"] = df["fecha"].dt.year
    df["dia_semana"] = pd.Categorical(df["fecha"].dt.day_of_week.map(dict(enumerate(DIAS))), DIAS, ordered=True)
    df["mortal"] = df["n_mortales"].fillna(0).gt(0) | es_mortal(df["gravedad"])
    # Coordenadas fuera de la Ciudad son errores de geocodificación.
    fuera = ~df["latitud"].between(-34.75, -34.5) | ~df["longitud"].between(-58.55, -58.3)
    df.loc[fuera, ["latitud", "longitud"]] = pd.NA
    return df.drop_duplicates("id_hecho")


def limpiar_victimas(df):
    df = _renombrar(df, ALIAS_VICTIMAS)
    df["fecha"] = _fecha(df["fecha"])
    df = df.dropna(subset=["fecha"])
    for c in ("victima", "sexo_victima", "gravedad", "rol_victima"):
        df[c] = _limpiar_texto(df[c].astype("string"))
    df["sexo_victima"] = df["sexo_victima"].replace(SEXOS)
    df["edad_victima"] = _numero(df["edad_victima"].astype("string")).where(lambda e: e.between(0, 110))
    df["anio"] = df["fecha"].dt.year
    df["mortal"] = es_mortal(df["gravedad"])
    return df


def cargar(carpeta=None):
    carpeta = Path(carpeta or carpeta_datos())
    hechos = limpiar_hechos(_leer_csv(carpeta / ARCHIVOS["hechos"]))
    victimas = limpiar_victimas(_leer_csv(carpeta / ARCHIVOS["victimas"]))
    return hechos, victimas
