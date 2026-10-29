"""Ejecuta el notebook completo contra datos sintéticos para detectar errores antes de publicar."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

from tests.conftest import generar

RAIZ = Path(__file__).resolve().parent.parent


def test_notebook_corre_de_punta_a_punta(tmp_path, monkeypatch):
    monkeypatch.setenv("SINIESTROS_DATOS", str(generar(tmp_path / "data", n=1500, sep=";", encoding="utf-8-sig", formato="nuevo")))
    nb = nbformat.read(RAIZ / "analisis.ipynb", as_version=4)
    NotebookClient(nb, timeout=300, resources={"metadata": {"path": str(RAIZ)}}).execute()
    salidas = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", [])]
    assert not [o for o in salidas if o.output_type == "error"]
