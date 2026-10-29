import pandas as pd
import pytest

from siniestros.datos import cargar, es_mortal

from tests.conftest import generar


def test_carga_y_tipos(datos_sinteticos):
    hechos, victimas = cargar(datos_sinteticos)
    assert pd.api.types.is_datetime64_any_dtype(hechos["fecha"])
    assert hechos["id_hecho"].is_unique
    assert hechos["hh"].between(0, 23).all()
    assert victimas["edad_victima"].dropna().between(0, 110).all()


def test_sin_dato_pasa_a_nulo(datos_sinteticos):
    hechos, victimas = cargar(datos_sinteticos)
    assert "SD" not in set(hechos["victima"].dropna())
    assert "SD" not in set(victimas["sexo_victima"].dropna())
    assert hechos["comuna"].isna().any()


def test_coordenadas_fuera_de_caba_se_descartan(datos_sinteticos):
    hechos, _ = cargar(datos_sinteticos)
    assert pd.isna(hechos.loc[hechos["id_hecho"] == "2019-00000", "latitud"]).all()


@pytest.mark.parametrize(("sep", "encoding"), [(";", "latin-1"), (",", "utf-8-sig")])
def test_detecta_separador_y_encoding(tmp_path, sep, encoding):
    _, victimas = cargar(generar(tmp_path / "d", sep=sep, encoding=encoding))
    assert "rol_victima" in victimas
    assert victimas["rol_victima"].str.contains("ACOMPANANTE").any()  # sin tildes ni eñes


def test_es_mortal():
    s = pd.Series(["MORTAL", "LEVE", None, "FATAL"])
    assert es_mortal(s).tolist() == [True, False, False, True]
