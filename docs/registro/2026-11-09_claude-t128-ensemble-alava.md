## 2026-11-09 — T-128 (paso 1) — El runner del ensemble imprime el motivo del fallo de cada candidato

Autorización: orden del Planificador (09-11), tarea T-128. No se lanza ni se publica nada.
Causa: el 06 42492992797 (Álava) falló en 5 jobs `generate` con «executed 0, failed 2»; el motivo solo está en `failure.json` (artefacto, 403 desde cloud). La CRS de la plantilla (EPSG:3035) coincide con el contrato de Álava, así que esa sospecha no se confirma; sin `.cache` de Álava no se pudo reproducir en local.
Cambio: `ddd_ensemble/runner.py` escribe `CANDIDATE_FAILED <id> profile=<p> <Tipo>: <message>` por stderr en ambos `except`; test `tests/test_ensemble_fallo_en_log.py`.
Siguiente: relanzar el 06 de Álava (Operador) y leer la causa en el log del job.
Riesgos: ninguno; no toca motor ni huellas.
