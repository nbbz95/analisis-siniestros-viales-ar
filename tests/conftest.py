"""Genera CSV sintéticos con el mismo esquema que los del GCBA para testear sin red."""

import numpy as np
import pandas as pd
import pytest

VEHICULOS = ["MOTO", "PEATON", "AUTO", "BICICLETA", "CARGAS", "PASAJEROS", "SD"]
GRAVEDAD = ["LEVE", "GRAVE", "MORTAL", "SD"]


def generar(carpeta, n=400, sep=",", encoding="utf-8", semilla=0, formato="viejo"):
    rng = np.random.default_rng(semilla)
    fechas = pd.Timestamp("2019-01-01") + pd.to_timedelta(rng.integers(0, 365 * 5, n), unit="D")
    hechos = pd.DataFrame(
        {
            "id_hecho": [f"2019-{i:05d}" for i in range(n)],
            "n_victimas": rng.integers(1, 3, n),
            "fecha": fechas.strftime("%d/%m/%Y"),
            "aaaa": fechas.year,
            "hora": [f"{h:02d}:{m:02d}:00" for h, m in zip(rng.integers(0, 24, n), rng.integers(0, 60, n))],
            "hh": rng.integers(0, 24, n).astype(str),
            "comuna": rng.choice([str(c) for c in range(1, 16)] + ["SD"], n),
            "tipo_de_calle": rng.choice(["AVENIDA", "CALLE", "AUTOPISTA", "GRAL PAZ"], n),
            "longitud": rng.uniform(-58.5, -58.35, n).round(6).astype(str),
            "latitud": rng.uniform(-34.7, -34.55, n).round(6).astype(str),
            "victima": rng.choice(VEHICULOS, n, p=[0.4, 0.2, 0.15, 0.1, 0.05, 0.05, 0.05]),
            "contraparte": rng.choice(["AUTO", "CARGAS", "PASAJEROS", "MOTO", "OBJETO FIJO"], n),
            "gravedad": rng.choice(GRAVEDAD, n, p=[0.7, 0.2, 0.05, 0.05]),
        }
    )
    hechos.loc[0, "latitud"] = "0"  # coordenada inválida a propósito
    victimas = pd.DataFrame(
        {
            "id_hecho": hechos["id_hecho"],
            "fecha": hechos["fecha"],
            "aaaa": hechos["aaaa"],
            "victima": hechos["victima"],
            "sexo_victima": rng.choice(["MASCULINO", "FEMENINO", "SD"], n, p=[0.65, 0.3, 0.05]),
            "edad_victima": np.where(rng.random(n) < 0.05, "SD", rng.integers(1, 90, n).astype(str)),
            "gravedad": hechos["gravedad"],
            "rol_victima": rng.choice(["CONDUCTOR", "PASAJERO_ACOMPAÑANTE", "PEATON", "CICLISTA"], n),
        }
    )
    if formato == "nuevo":
        hechos, victimas = _a_formato_nuevo(hechos, victimas)
    carpeta.mkdir(parents=True, exist_ok=True)
    hechos.to_csv(carpeta / "siniestros_viales_hechos.csv", index=False, sep=sep, encoding=encoding)
    victimas.to_csv(carpeta / "siniestros_viales_victimas.csv", index=False, sep=sep, encoding=encoding)
    return carpeta


def _a_formato_nuevo(hechos, victimas):
    """Esquema de la edición 2019-2025: columnas con sufijo _siniestro, fechas ISO y sexo en una letra."""
    iso = lambda s: pd.to_datetime(s, format="%d/%m/%Y").dt.strftime("%Y-%m-%d")
    mortales = (hechos["gravedad"] == "MORTAL").astype(int)
    hechos = pd.DataFrame(
        {
            "id_siniestro": hechos["id_hecho"],
            "numero_total_de_victimas": hechos["n_victimas"],
            "numero_victimas_mortal_siniestro": mortales,
            "fecha_siniestro": iso(hechos["fecha"]),
            "anio_siniestro": hechos["aaaa"],
            "hora_siniestro": hechos["hora"],
            "comuna_siniestro": "COMUNA " + hechos["comuna"],
            "tipo_de_via_siniestro": hechos["tipo_de_calle"],
            "longitud_siniestro": hechos["longitud"],
            "latitud_siniestro": hechos["latitud"],
            "modo_desplazamiento_victima": hechos["victima"],
            "modo_desplazamiento_acusado": hechos["contraparte"],
        }
    )
    victimas = pd.DataFrame(
        {
            "id_siniestro": victimas["id_hecho"],
            "fecha_siniestro": iso(victimas["fecha"]),
            "anio_siniestro": victimas["aaaa"],
            "modo_desplazamiento_victima": victimas["victima"],
            "sexo_victima": victimas["sexo_victima"].replace({"MASCULINO": "M", "FEMENINO": "F"}),
            "edad_victima": victimas["edad_victima"],
            "GRAVEdad_victima": victimas["gravedad"],
            "rol_victima": victimas["rol_victima"],
            "fecha_fallecimiento_victima": "",
        }
    )
    return hechos, victimas


@pytest.fixture(params=["nuevo", "viejo"])
def datos_sinteticos(tmp_path, request):
    if request.param == "nuevo":
        return generar(tmp_path / "data", sep=";", encoding="utf-8-sig", formato="nuevo")
    return generar(tmp_path / "data")
