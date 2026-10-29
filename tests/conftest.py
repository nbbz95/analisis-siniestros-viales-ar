"""Genera CSV sintéticos con el mismo esquema que los del GCBA para testear sin red."""

import numpy as np
import pandas as pd
import pytest

VEHICULOS = ["MOTO", "PEATON", "AUTO", "BICICLETA", "CARGAS", "PASAJEROS", "SD"]
GRAVEDAD = ["LEVE", "GRAVE", "MORTAL", "SD"]


def generar(carpeta, n=400, sep=",", encoding="utf-8", semilla=0):
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
    carpeta.mkdir(parents=True, exist_ok=True)
    hechos.to_csv(carpeta / "siniestros_viales_hechos.csv", index=False, sep=sep, encoding=encoding)
    victimas.to_csv(carpeta / "siniestros_viales_victimas.csv", index=False, sep=sep, encoding=encoding)
    return carpeta


@pytest.fixture
def datos_sinteticos(tmp_path):
    return generar(tmp_path / "data")
