# Recuperación persistente de las 14 fuentes territoriales

Versión: 1.0.0. Nombre: Recuperación local integral. Fecha: 2026-10-08.
Alcance: fuentes oficiales, conservación y consumo local explícito.
Estado: LOCAL_ONLY; sin nueva elegibilidad productiva.
Cambios: nuevo almacén, manifiesto, adaptador y pruebas dirigidas.
Motivo: conservar los bytes de los artifacts inventariados sin nueva adquisición.
Origen: `4e5e3be53364874d0e056ade64d64ab6471b28b7`. Predecesor: ninguno.

## Resultado verificable

**14/14 RECOVERED_VERIFIED; 76.717.002 bytes de ZIP originales (73,163 MiB).**
No quedan paquetes bloqueados. Melilla fue el piloto; siguieron La Rioja,
Galicia y los once restantes. El preflight confirmó rama `codex/fuentes-oficiales`,
HEAD de referencia y worktree limpio, unos 13 GiB libres y acceso de lectura
a las catorce referencias exactas. No se repitieron las auditorías previas.

Almacén definitivo: `/Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas/`.
Los objetos están en `objects/<artifact_sha256>/artifact.zip`; los receipts exactos
en `receipts/<receipt_sha256>.json`. El ZIP original contiene `manifest.json` y
`prepared_sources.zip`: conservarlo conserva también los bytes exactos interiores.
El manifiesto local está en `recovery-manifest.json`; su copia en Git es
`docs/AUDITORIAS/recuperacion_local_14_paquetes_2026-10-08.json`.
SHA-256 del manifiesto: `92c6acc0f29a4e1897de6c6f69bc025f0cf11722ebb4aa36e69a534b9ad3130c`.

Ocupación persistente medida: 75.048 KiB asignados por `du -sk` (73,289 MiB).
Contenido lógico: 76.717.002 bytes de ZIP, 15.357 de receipts y 42.089 de manifiesto,
total 76.774.448 bytes. Las copias temporales de descarga no son el almacén.
Los ZIP no se incorporan a Git. No se sobrescriben objetos discrepantes.

| Territorio | Bytes ZIP | Resultado |
|---|---:|---|
| Principado de Asturias | 1.663.660 | RECOVERED_VERIFIED |
| Islas Baleares | 7.865.466 | RECOVERED_VERIFIED |
| Canarias | 8.669.104 | RECOVERED_VERIFIED |
| Cantabria | 699.409 | RECOVERED_VERIFIED |
| Castilla-La Mancha | 12.413.530 | RECOVERED_VERIFIED |
| Cataluña | 14.493.802 | RECOVERED_VERIFIED |
| Galicia | 3.745.544 | RECOVERED_VERIFIED |
| Comunidad de Madrid | 4.060.247 | RECOVERED_VERIFIED |
| Región de Murcia | 1.725.771 | RECOVERED_VERIFIED |
| Comunidad Foral de Navarra | 6.257.751 | RECOVERED_VERIFIED |
| País Vasco | 14.138.865 | RECOVERED_VERIFIED |
| La Rioja | 653.639 | RECOVERED_VERIFIED |
| Ceuta | 90.652 | RECOVERED_VERIFIED |
| Melilla | 239.562 | RECOVERED_VERIFIED |

## Identidades y verificaciones

El SHA de artifact acredita el ZIP exterior servido por GitHub; `package_sha256`
acredita `prepared_sources.zip`. `territorial_identity_sha256` es el hash canónico
contractual de territorio, edición, años, paquete e identidad de compatibilidad.
Las tres identidades permanecen distintas. Cada entrada conserva los tres hashes,
tamaño remoto, URLs públicas de procedencia, run, artifact ID, commit fuente,
receipt, fecha de recuperación, ubicación física y comprobaciones realizadas.
No se conservan tokens ni URLs firmadas de transferencia en estos archivos.

Se comprueban tamaño y SHA exterior, estructura exacta, CRC de ambos ZIP,
rutas y tipos seguros sin enlaces, manifest, hash interior, receipt original,
identidad territorial recalculada, digest e identidad de compatibilidad y
`validate_prepared_package`, incluidos hashes de cada fuente materializada.
Edición lógica: 2025; población y seccionado: 2023 en los catorce casos.
Los estados del manifiesto son `RECOVERED_VERIFIED`, `RECOVERED_INVALID`,
`UNAVAILABLE` y `PENDING`. La primera importación escribe las catorce entradas PENDING
antes de procesar y actualiza atómicamente el progreso por paquete. Una reimportación
conserva las entradas previas mientras las revalida; utiliza el objeto persistido
si ya no existe la descarga temporal. Un inventario diferente no sobrescribe el
manifiesto previo. Una interrupción no descataloga entradas ya conservadas.

La transferencia usa solo artifact IDs y runs del inventario: el conector GitHub
devuelve los bytes mediante una referencia de archivo temporal, y curl los conserva.
La restricción de DNS del sandbox exigió ejecutar la transferencia fuera de él.
No hubo errores de identidad, expiración o integridad ni reintentos de tales errores.

El Python por defecto carecía de GeoPandas: fue un fallo ambiental de validación,
no una discrepancia de bytes. Se resolvió usando Miniforge local existente,
`/usr/local/Caskroom/miniforge/base/bin/python3` (Python 3.13, GeoPandas 1.1.2).
No se instaló ninguna dependencia. Las primeras pruebas mostraron una diferencia
`/var` frente a `/private/var` en el fixture de macOS; se corrigió canonicalizando
su directorio temporal. No se cambió ningún contrato para lograr el resultado.

## Reproducción y consumidor

El adaptador nuevo no modifica resolutores, receipts, declaraciones, catálogos ni
la ruta productiva. La selección exige almacén, territorio, edición, identidad
territorial y hash de paquete explícitos. Solo una coincidencia exacta es válida;
se vuelven a verificar ZIP y receipt antes de entregar una copia preparada.
No contiene cliente HTTP, adquisición automática ni promoción. Devuelve errores
deterministas ante ausencia, ambigüedad, corrupción o incompatibilidad.

Ejemplo offline con la identidad exacta de Melilla:

```bash
/usr/local/Caskroom/miniforge/base/bin/python3 -m herramientas.almacen_fuentes_local \
  --store /Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas read \
  --territory-id melilla --edition 2025 \
  --territorial-identity-sha256 a081d54716398cb02e74a62857279d8057a333320470e89e9a2dbf77c573911d \
  --package-sha256 cc427ca1d5ce00ecac5c70678773fd2c2592129af1b7203151ed5ebd2a86f95b \
  --destination /private/tmp/ddd-consumo-melilla
```

El destino debe estar ausente; es una copia de trabajo. Puede ser cualquier
directorio autorizado, mientras los originales permanecen en el almacén.
Para trasladar físicamente el almacén, regenerar deliberadamente las rutas del
manifiesto local, preservando sus identidades; no se remapean silenciosamente.

Pruebas dirigidas:

```bash
DDD_LOCAL_STORE=/Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas \
  /usr/local/Caskroom/miniforge/base/bin/python3 -m unittest tests.test_almacen_fuentes_local -v
/usr/local/Caskroom/miniforge/base/bin/python3 -m herramientas.verificar_almacen_fuentes_local \
  --store /Users/macbookpro/Desarrollo/DDD-almacen/fuentes-preparadas \
  --output /private/tmp/ddd-verificacion-offline.json
git diff --check
```

Once pruebas PASS: dos territorios sin red y originales intactos; SHA incorrecto
con tamaño distinto y con igual tamaño; identidad y edición exactas; receipt
contradictorio/corrupto; identidad recalculada contra receipt falsificado; edición
interior incompatible; ausencia, ambigüedad y estado no verificado; ZIP peligroso;
importación atómica, reimportación sin descargas, interrupción y objeto conflictivo.
Salida conservada: `pruebas_recuperacion_local_2026-10-08.txt`.
Los casos con datos requieren `DDD_LOCAL_STORE`: sin esa variable se omiten
explícitamente y no acreditan validación del almacén.

Un proceso nuevo, diferente del descargador/importador, volvió a abrir el
manifiesto y consumió **14/14** paquetes con conexiones de socket prohibidas.
Reverificó contenidos y hashes; todos los archivos originales quedaron idénticos.
Evidencia: `verificacion_offline_14_paquetes_2026-10-08.json`.
El manifiesto versionado es el vínculo entre el commit de código y los datos;
su SHA también está en la evidencia offline. El commit se identifica por el
historial Git que contiene estos archivos, evitando autorreferencia imposible.

## Puertas y límites

Commit local: pruebas dirigidas y trazabilidad conforme a la separación de puertas
autorizada. Integración: revisión del HEAD final, versionado y CI pertinentes,
además de autorización. Producción: autorización expresa y contratos vigentes;
esta recuperación no modifica certificaciones ni elegibilidad histórica.
Las herramientas nuevas son aditivas, versión 1.0.0 y sin predecesor sustituido.
No se alteran contratos compartidos; su uso por los frentes autonómico y nacional
sería una integración posterior explícita, no un cambio realizado en ellos.
No se ejecutaron suite completa, optimizadores, M04–M08, workflows ni territorios.
Push, PR, merge, modificación de main, adquisición oficial y publicación: NO.

La primera revisión separada detectó pérdida del catálogo al reimportar sin copias
temporales. Se corrigió y se añadió regresión sobre reimportación e interrupción.
El dictamen final separado se documenta en el expediente de revisión de esta entrega.
Siguiente acción de mayor valor: someter este consumidor aditivo y el manifiesto
exacto a la puerta de integración autorizada, con CI pertinente.
