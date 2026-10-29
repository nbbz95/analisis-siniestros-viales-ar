# Siniestros viales en la Ciudad de Buenos Aires

Análisis exploratorio de los siniestros viales con víctimas en CABA desde 2019, con datos abiertos del GCBA. El notebook se ejecuta en GitHub Actions con los datos oficiales y se publica como informe web.

**Informe:** https://nbbz95.github.io/analisis-siniestros-viales-ar/

## Preguntas

1. ¿Cómo evolucionaron los siniestros y las víctimas año a año?
2. ¿Quiénes son las víctimas más vulnerables (medio de transporte, edad, sexo)?
3. ¿En qué días y horarios se concentran los siniestros mortales?
4. ¿Dónde ocurren (mapa, tipo de vía, comuna)?

Los números del texto se calculan al ejecutar el notebook, así el informe se actualiza solo cuando el GCBA publica datos nuevos.

## Estructura

```
analisis.ipynb        # el análisis, con gráficos y conclusiones
siniestros/datos.py   # descarga y limpieza (reutilizable y testeada)
scripts/descargar.py  # baja los CSV oficiales a data/
tests/                # tests de limpieza + ejecución completa del notebook con datos sintéticos
```

## Limpieza de datos

- Detecta separador y encoding, porque los CSV del GCBA cambiaron entre ediciones.
- Normaliza textos (mayúsculas, sin tildes) y convierte `SD` (sin dato) en nulo.
- Descarta edades imposibles y coordenadas fuera de la Ciudad.
- Deduplica hechos por `id_hecho`.

## Correr localmente

```bash
pip install -r requirements.txt pytest
python -m pytest -q
python scripts/descargar.py
jupyter lab analisis.ipynb
```

## Stack

Python, pandas, matplotlib, Jupyter, nbconvert, pytest, GitHub Actions y GitHub Pages.

Fuente: [Buenos Aires Data, Siniestros viales](https://data.buenosaires.gob.ar/dataset/victimas-siniestros-viales) (CC BY 4.0).
