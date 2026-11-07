---
paths:
  - "modulos/**"
  - "ddd_core/**"
  - "territorios/**"
  - "tests/**"
---

# Diagnóstico local (sin descargar artefactos: desde la sesión cloud dan 403)

- El propietario sube con un script desde su Mac el grafo M03 y el M01 del run a una rama `diagnostico/*`
  (`lanzadores/subir_diagnostico_t02.sh` en la rama `lanzadores-mac`; acepta `ddd-state-<run>-M03` o `-M03U`).
- Copia ambos a `territorios/<t>/.cache/ddd/preparacion/<t>_2025/` y ejecuta el motor real:
  `python modulos/04_generar_semillas.py --params territorios/<t>/config/<t>_2025.yaml` (no `ddd_core.m04_seed_engine`,
  que omite la unidad flexible :F de 7.6.0) y
  `python modulos/05_optimizar_distritos.py --params …`. Las rutas se resuelven respecto al contrato: las copias
  temporales del contrato van en `territorios/<t>/config/`, nunca fuera.
- Antes de gastar una 00, prueba el cambio en local (M04+M05 tardan ~15 s) con el contrato temporal. Los volcados
  `diagnostico/*` traen M01 y M03 grafo, pero no `*_m03_particiones*` (las islas no corren).
- `ddd-audit-<run>` (KB) trae `block_causes.json`; el informe M05 está en `ddd-state-<run>-M05` (~80 MB).
- Instala siempre con `requirements.lock`: pandas 3 / geopandas 1.2 rompen M05 con «unidad partida».
- Pytest no viene instalado: `pip install -r requirements.lock pytest==8.4.2`. La suite entera pasa de 10 min
  (~15 min: en segundo plano); la CI usa `unittest` por módulos, y en local basta con los ficheros de materialización,
  política, gobernanza y contratos. `test_pipeline_adversarial_c07` y `test_pipeline_sintetico_m01_m06` fallan en
  local también en `main` (entorno); en CI pasan. Sin geopandas, `M05Determinism` de R015 da error en local.
- Regresión: los zip M04/M05 cambian de hash en cada ejecución (llevan fecha); compara el GeoJSON descomprimido
  (`unzip -p … | sha256sum`) y el informe con claves ordenadas.
- El «hard=N» del log de M05 cuenta también los exentos de suelo; la verdad está en `population_baseline_status` y en
  los no-PASS del informe.
- M05 escribe `ddd_unit_id` sin tipo OGR («Skipping field»): lee las unidades del M04 con
  `m04_seed_engine_v7411.load_geo`. Sin M01 (Andalucía, volcado del 28-10) se rehace con las secciones del M05 quitando
  las columnas `ddd_*` y `district_*`.
- No hagas `git stash` ni edites `ddd_core/` con una regresión en segundo plano: los procesos que arrancan cargan
  código a medias. `/usr/bin/time` no existe en la sesión cloud.
- En una sesión cloud limpia faltan pyproj, geopandas y gerrychain (y networkx, shapely, numpy, pandas): instálalos
  con pip, versiones de `requirements.lock`, antes de los tests del ensemble o de R015. Los contratos con
  `topology_bridges` o exenciones no valen para el ensemble.