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
        cabecera = contenido[:400].decode("utf-8", "replace").splitlines()[:3]
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


def limpiar_hechos(df):
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])
    for c in ("victima", "contraparte", "gravedad", "tipo_de_calle", "participantes"):
        if c in df:
            df[c] = _limpiar_texto(df[c])
    for c in ("n_victimas", "hh", "comuna", "latitud", "longitud"):
        if c in df:
            df[c] = _numero(df[c])
    if "hh" not in df or df["hh"].isna().all():
        df["hh"] = pd.to_datetime(df.get("hora"), format="mixed", errors="coerce").dt.hour
    df["anio"] = df["fecha"].dt.year
    df["dia_semana"] = pd.Categorical(df["fecha"].dt.dayofweek.map(dict(enumerate(DIAS))), DIAS, ordered=True)
    df["mortal"] = es_mortal(df["gravedad"])
    # Coordenadas fuera de la Ciudad son errores de geocodificación.
    fuera = ~df["latitud"].between(-34.75, -34.5) | ~df["longitud"].between(-58.55, -58.3)
    df.loc[fuera, ["latitud", "longitud"]] = pd.NA
    return df.drop_duplicates("id_hecho")


def limpiar_victimas(df):
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])
    for c in ("victima", "sexo_victima", "gravedad", "rol_victima"):
        if c in df:
            df[c] = _limpiar_texto(df[c])
    df["edad_victima"] = _numero(df["edad_victima"]).where(lambda e: e.between(0, 110))
    df["anio"] = df["fecha"].dt.year
    df["mortal"] = es_mortal(df["gravedad"])
    return df


def cargar(carpeta=None):
    carpeta = Path(carpeta or carpeta_datos())
    hechos = limpiar_hechos(_leer_csv(carpeta / ARCHIVOS["hechos"]))
    victimas = limpiar_victimas(_leer_csv(carpeta / ARCHIVOS["victimas"]))
    return hechos, victimas
