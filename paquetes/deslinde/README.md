# Deslinde 1.0.0

Delimitación reproducible de distritos uninominales desde secciones censales: trazado canónico + 10 cadenas ReCom
ponderado (GerryChain 1.0) + elección D8 + mapa vigente como candidato opcional. La definición formal está en
[`docs/ARQUITECTURA/DESLINDE_1_0.md`](../../docs/ARQUITECTURA/DESLINDE_1_0.md) del repositorio Diputado de Distrito.
Los mapas no tienen valor oficial.

## Instalar

```bash
pip install -r requirements-deslinde.lock --no-deps   # el entorno de la prueba de equivalencia (bit a bit)
pip install --no-deps -e .
```

`pyproject.toml` declara rangos compatibles; la reproducibilidad bit a bit solo está garantizada con el lock.

## Usar

```bash
PYTHONHASHSEED=0 python -m deslinde competir --contrato contrato.yaml --grafo m03_grafo.json \
  --composicion m06_composicion.csv --atributos m06_secciones.geojson.zip --territorio NAC22 \
  --partidos partidos_judiciales.csv --comarcas comarcas_agrarias.csv --areas areas_movilidad_2019.csv \
  [--vigente vigente.csv] --out salida/
```

O desde Python: `deslinde.api.competir(...)` devuelve el resumen (estado, ganador, `huella_resultado`, semilla pública,
tablas con su sha256, entorno) y escribe `COMPETICION.json`, `COMPETICION.md` y `DESLINDE.json`; `deslinde.api.aceptar`
da la aceptación mínima.

- **Entradas**: contrato materializado (`validation` con K, suelo, techo y tolerancia; `generation_state.source_inputs`
  con los sha256 del padrón y del seccionado), grafo M03 de secciones, composición M06 del trazado canónico y, si hay,
  sus atributos por sección. El vigente (columnas `seccion,distrito`) es opcional.
- **Código oficial**: `NACnn` (CPRO del INE) o `AUTnn` (CODAUTO). Con él y los dos sha256 del contrato se derivan las
  semillas públicas (`ddd-semilla-publica/2`).
- **Tablas de naturalidad**: las aporta quien ejecuta (no se empaquetan datos de terceros): partidos judiciales
  (`codigo_ine,id_partido`), comarcas agrarias (`codigo_ine,id_comarca`) y áreas de movilidad EM-1 del INE
  (`id_area_geo,id_grupo,tipo`).
- `PYTHONHASHSEED=0` es obligatorio y efectivo: no uses `python -I` ni `-E`, que lo ignoran (la CLI sale con 6).

## Mapas

[`MAPAS.json`](MAPAS.json) vincula por sha256 los mapas regenerados con esta versión. Está vacío hasta que se regeneren.

## Licencia y cita

Apache-2.0 ([`LICENSE`](LICENSE)). Cita: [`CITATION.cff`](CITATION.cff); serie Zenodo 10.5281/zenodo.24093967.
