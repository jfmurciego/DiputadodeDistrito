## 2026-11-16 — T-370 — P50 Publicación académica sustituye a «Publicar versión de mapa»

**Causa.** D-133 (paso 4): un botón sin parámetros técnicos y una Release por lote (un DOI por versión de la serie, D-88/D-94).

**Cambio.** Nuevo `.github/workflows/p50-publicacion-academica.yml` 1.0.0 («P50 Publicación académica»). Sustituye a `publicar-version-mapa.yml` 1.1.2
(borrado; copia en `legacy/workflows/publicar-version-mapa_v1.1.2_20261116.yml`). Botón: `territorios` (códigos separados por comas o `todos` = los publicados en el visor).
- `herramientas/p50_resolver.py` (nuevo): resuelve cada territorio a su M06 vigente de `orchestracion/publicaciones_visor.json` y baja el blob con
  `gh api …/git/blobs/<sha>` verificando el sha256 del visor (fallo cerrado; errores a stderr). Ya no se usa el artefacto de Actions (caduca a 14 días).
- Versión automática: 1.0.0 la primera; sube la menor si cambia el mapa (territorio → sha256 del M06) respecto de la última Release `mapas-v*` (guardado en su asset `MAPAS.json`);
  se NIEGA con `P50_MAPA_SIN_CAMBIOS` si no cambia, y con `P50_SIN_MAPAS_PREVIO` si la última Release no trae `MAPAS.json`.
- Una Release por lote, `mapas-v<versión>`, con un paquete `ddd-<t>-v<V>.tar.gz` por territorio (mismo contenido y empaquetado determinista que antes: `LINAJE.json` con dos campos añadidos,
  `m06_blob_sha` y `m06_sha256`; `SHA256SUMS` interno idéntico), `SHA256SUMS` de los paquetes y `MAPAS.json`. Atestación SLSA sobre todos los paquetes. Entorno `publicacion` y permisos del job iguales.
  El job `resolver` solo lee. Sin `workflow_call`.
- `cadena-publicacion.yml` 1.1.0 (copia 1.0.1 en `legacy/`): se quita el job `version_mapa` y la entrada `version` (con su validación y la comprobación de la etiqueta): la 05 ya no lanza P50.
- Equivalencias del corte regeneradas (`generar_equivalencias_5_0_0.py` 1.1.2); `LEEME_KIT.md`.

**Pruebas.** `tests/test_t370_p50_equivalencia.py`: compara con la copia congelada (`tests/fixtures/t370_workflows/`, sha256; sin skipTest) entorno, permisos, acciones, empaquetado, manifiesto y atestación;
controles negativos; resolutor (versiones, negativa, territorios, CLI rc/stderr) y pasos bajo `bash -eo pipefail`. Actualizados `test_design_a_catalogo`, `test_design_a_matriz_sintetica`,
`test_codauto_preparation_contract`, `test_etiquetas_territoriales_humanas`, `test_resolver_cadena_publicacion`.

**Lo que se pierde respecto de 1.1.2 (declarado).** `production_run_id` queda `None` en `LINAJE.json`; ya no hay atadura al mismo `source_sha` y run que el visor (D-14: la 05 no lanza P50, el
commit es el de `main` al pulsar); `SHA256SUMS` de la Release es ahora el de los tarballs (el interno de cada paquete es el de antes); Release por lote en vez de una por territorio; sin `workflow_call`.
Versión repetida: el resolutor une las Releases publicadas (los borradores no se ven con `contents: read`) con las etiquetas `mapas-v*` del repositorio y falla cerrado con `P50_TAG_EXISTE` si la candidata ya existe.

**No probado en Actions.** Heredoc de Python dentro del `while`; `download-artifact` del plan; `attest-build-provenance` con glob de varios tarballs; `gh release create` con varios assets; blob M06 (~50 MB) en memoria;
listado de Releases/etiquetas con `GITHUB_TOKEN`; Zenodo con una Release multi-territorio; «todos» con el entorno `publicacion`.

**Riesgos.** No se ha ejecutado en Actions (NO se lanza hasta cumplir D-88; el primer uso real es del Operador con frase del propietario). Cambia el nombre de la Release (`mapas-v<V>` en lugar de `mapa-<t>-v<V>`)
y que M06 sale del blob del visor (solo lo publicado). La 05 «Cadena» mantiene su comprobación de M06 vivo (preexistente). Sin efectos en motor, huellas ni checkpoints.
