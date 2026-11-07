## 2026-11-07 — T-72 — Archivo en origen de M06/M08

- Causa: los M06/M08 solo vivían como artefactos de Actions (14 días) y el archivista copiaba después: ninguno de
  los 49 M06 provinciales publicados está en R2 y T-67 solo recuperó 16 composiciones de 65.
- Cambio: `herramientas/archivo_origen.py` 1.0.0 (núcleo y clientes R2 del archivista, con reintentos). El job
  «registrar» del reutilizable territorial (1.3.0) sube `ddd-state-<run>-M06` a R2 con sha256, lo anota en
  `orchestracion/archivo_r2.json` y escribe la composición del run en `datos/composicion/runs/<t>_<run>.csv`
  (clave `runs` del MANIFEST, validada contra el GeoJSON M06 del estado). El del electoral (1.2.0) sube
  `ddd-state-<run>-M08` y escribe los votos por partido en `datos/resultados/runs/<t>_<run>_partidos.csv`
  (`partidos_runs`), con la composición del run territorial. Si R2 falla: `ARCHIVO_R2_FAILED` y el run no queda verde.
  La composición del run va en `runs/` y no en `<t>.csv` para no desalinear la del M06 publicado.
- Check: `tests/test_archivo_origen.py::RepositorioReal` falla si un M06 publicado no tiene copia de su run en R2 ni
  composición en git; las 49 actuales quedan en `configuracion/excepciones_archivo_origen.json` (las vacía T-71).
- Pruebas: subida simulada con sha256, fallo de R2, composición válida/inválida, votos por partido, check rojo/verde;
  gobernanza y tests de workflows en local.
- Riesgos: toca la 00 (`no-automerge`); validación real con una 00 de prueba (Operador).
