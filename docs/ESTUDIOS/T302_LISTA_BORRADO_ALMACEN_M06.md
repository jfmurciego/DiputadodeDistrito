# T-302 — Lista BORRAR/CONSERVAR de los almacen-m06-* (2026-11-14)

Estado: `archivar_almacen_m06` **aún no se ha lanzado** (índice `orchestracion/almacen_m06_r2.json` vacío): ninguna release está verificada en R2, así que **todas = CONSERVAR**. Nada se borra desde aquí.

Generada con `python herramientas/almacen_m06_r2.py listar --repo <r>` (cruza las releases vivas con el índice: BORRAR solo si TODOS sus assets, MANIFIESTO-*.tsv incluidos, están en el índice con clave `arc-p/m06/<asset>_<sha12>.<ext>` y el mismo sha256).

| Release | Assets | En R2 | Estado |
|---|---|---|---|
| `almacen-m06-aragon-40656036271` | 10 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |
| `almacen-m06-cantabria-40604431189` | 8 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |
| `almacen-m06-castilla_la_mancha-40604483629` | 8 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |
| `almacen-m06-extremadura-40656175842` | 10 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |
| `almacen-m06-galicia-40604535110` | 8 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |
| `almacen-m06-principado_de_asturias-40241852045` | 7 | 0 | CONSERVAR — NO VERIFICADO EN R2 → CONSERVAR |

Para pasar a BORRAR: (1) el Operador lanza «VER Verificación del motor» con `archivar_almacen_m06=true` (frase del propietario; deja el artefacto `bateria-almacen-m06-<run>` con ARCHIVO_ALMACEN_M06.json); (2) PR con `python herramientas/almacen_m06_r2.py indexar <ARCHIVO_ALMACEN_M06.json>`; (3) el propietario ejecuta `herramientas/borrar_almacen_m06.ps1 -WhatIf` y después sin `-WhatIf` (pide escribir BORRAR; salta y avisa de toda release no verificada). El script comprueba el índice versionado, no consulta R2 en vivo: el índice solo recibe entradas del job de archivado, que sube y verifica el sha256 (`r2_sha`/`r2_subir`).
Antes de borrar: ninguna 00 «Reutilizar» de esos seis territorios debe depender del release (la puerta lo lee hasta que sus callers pasen los secretos de R2).
