# T-302 — Lista BORRAR/CONSERVAR de los almacen-m06-* (2026-11-14)

Estado: el Operador lanzó «VER Verificación del motor» con `archivar_almacen_m06=true` (run 43634668489, job `archivar_almacen_m06`: 51 archivados, 0 fallos). El ARCHIVO_ALMACEN_M06.json (51 objetos: 45 zips + 6 MANIFIESTO-*.tsv; sha256 del fichero `85278e8f76bc3e68449957f47f177f516b306642b98b5b058f09d8c3ccfcc7c4`, copia de la rama `planificador/archivo-almacen-m06`) se indexó en `orchestracion/almacen_m06_r2.json` con `indexar`. Nada se borra desde aquí.

Comprobado en local el 2026-11-14: las 51 claves son `arc-p/m06/<asset>_<sha12>.<ext>` con sha12 igual al del sha256 registrado, y `listar` (cruza las releases vivas, con su digest de GitHub, con el índice) da las 6 en BORRAR. No se ha consultado R2 en vivo: la presencia en R2 se apoya en el job de archivado, que sube y verifica el sha256.

Generada con `python herramientas/almacen_m06_r2.py listar --repo <r>` (BORRAR solo si TODOS sus assets, MANIFIESTO-*.tsv incluidos, están en el índice con la clave y el mismo sha256).

| Release | Assets | En R2 | Estado |
|---|---|---|---|
| `almacen-m06-aragon-40656036271` | 10 | 10 | BORRAR |
| `almacen-m06-cantabria-40604431189` | 8 | 8 | BORRAR |
| `almacen-m06-castilla_la_mancha-40604483629` | 8 | 8 | BORRAR |
| `almacen-m06-extremadura-40656175842` | 10 | 10 | BORRAR |
| `almacen-m06-galicia-40604535110` | 8 | 8 | BORRAR |
| `almacen-m06-principado_de_asturias-40241852045` | 7 | 7 | BORRAR |

Siguiente paso: el propietario ejecuta `herramientas/borrar_almacen_m06.ps1 -WhatIf` y después sin `-WhatIf` (pide escribir BORRAR; salta y avisa de toda release no verificada). El script comprueba el índice versionado, no consulta R2 en vivo.

Antes de borrar: ninguna 00 «Reutilizar» de esos seis territorios debe depender del release (la puerta lo lee hasta que sus callers pasen los secretos de R2).
