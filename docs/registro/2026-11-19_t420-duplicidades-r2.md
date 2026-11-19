## 2026-11-19 — T-420 — Duplicidades en R2 (solo lectura)

- Causa: el propietario quiere saber cuántas duplicidades hay en R2, empezando por arc-e (T-416, D-176).
- Cambio: `herramientas/listar_r2.py` 1.1.0, `--duplicados [--json RUTA] [--verificar-indices]`: grupos por (ETag, tamaño) de todo el bucket, sobrantes, bytes recuperables y claves (arc-e primero). ETag multiparte («-N») no se toma por md5: solo sha256 de metadatos (*.json, INDEX, manifiestos); el resto, «no_verificable». Sin banderas, salida idéntica.
- Pruebas: `tests/test_t420_duplicidades_r2.py` (bucket simulado, multiparte).
- Pendiente (tras T-418): P74 de `p70-archivo.yml` necesita pasar `--duplicados --json` y `--verificar-indices`; no se ha tocado el workflow.
- Efectos: solo lectura; no borra ni mueve nada. Sin impacto en huellas.
