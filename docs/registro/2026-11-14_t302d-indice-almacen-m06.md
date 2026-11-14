## 2026-11-14 — T-302 — Índice R2 de los almacen-m06-* con el archivado del run 43634668489

Causa: el archivado a R2 (run 43634668489, 51 objetos, 0 fallos) dejó su ARCHIVO_ALMACEN_M06.json solo como artefacto; el índice versionado seguía vacío y las 6 releases en CONSERVAR.
Cambio: `orchestracion/almacen_m06_r2.json` con los 51 objetos (45 zips + 6 MANIFIESTO), generado con `almacen_m06_r2.py indexar`; entrada: ARCHIVO_ALMACEN_M06.json de la rama `planificador/archivo-almacen-m06` (sha256 `85278e8f76bc3e68449957f47f177f516b306642b98b5b058f09d8c3ccfcc7c4`; el JSON no se copia a esta PR). `docs/ESTUDIOS/T302_LISTA_BORRADO_ALMACEN_M06.md` actualizada: `listar` da las 6 en BORRAR.
Pruebas: `listar` en local contra las releases vivas (digests de GitHub); 51 claves con sha12 coherente. No se consultó R2 en vivo.
Riesgos: sin 00 ni cambio de huellas; no se borra nada (lo hace el propietario con el .ps1).
