# F10 — conciliación de originales oficiales: Aragón, Castilla y León y Extremadura

**Versión:** 1.0.0 — **Fecha:** 2026-10-20 — **Estado:** evidencia candidata, sin promoción.
**Alcance:** escrutinios oficiales 2026 de Aragón y Castilla y León; búsqueda de resultado definitivo granular de Extremadura 2025.
**Cambio:** adquisición local, manifiesto SHA-256, normalización determinista y validación canónica de paquete electoral.
**Motivo:** cerrar las comprobaciones aritméticas y dejar delimitados los gaps administrativos restantes.
**Predecesor:** expedientes de descubrimiento de fuentes #286/#287 y `CIERRE_EJECUCION_Y_DEPENDENCIAS.md`.

## Aragón — 8 de febrero de 2026

Se preservan los tres XLS provinciales definitivos del Gobierno de Aragón y el CSV oficial Open Data de 30.326 filas. El procesador reconstruye CUSEC y candidaturas, verifica las identidades provincia/municipio/distrito del CSV y contrasta cada total CUSEC-candidatura con el escrutinio provincial. Resultado: **cero diferencias**. Las ecuaciones de mesa `votos = candidaturas + blancos + nulos` pasan para las 2.221 filas provinciales.

| Provincia | Candidaturas geográficas | CERA separado | Total candidaturas | Votos totales | Nulos | Blancos |
|---|---:|---:|---:|---:|---:|---:|
| Huesca | 104.927 | 879 | 105.806 | 108.309 | 1.073 | 1.430 |
| Teruel | 66.349 | 371 | 66.720 | 68.265 | 872 | 673 |
| Zaragoza | 485.449 | 3.009 | 488.458 | 497.996 | 4.326 | 5.212 |
| **Total** | **656.725** | **4.259** | **660.984** | **674.570** | **6.271** | **7.315** |

El conjunto tiene 1.463 CUSEC geográficos. Queda el gap de identidad temporal ya trazado: `5002501003` aporta 608 votos y no tiene correspondencia acreditada con INE 2025; `2221301003` está en el universo territorial 2025 y no figura en el resultado electoral oficial. El cotejo CSV↔XLS verifica el resultado publicado, pero no acredita transferencia ni equivalencia administrativa. **Adquisición y conciliación: PASS. Crosswalk y admisibilidad electoral: BLOCKED.**

La fuente Open Data contiene un nombre de candidatura con mojibake (`ESPAÃ‘A`); el código de candidatura y la comparación íntegra contra los XLS respaldan la normalización a PCTE. El texto original se conserva sin cambios.

## Castilla y León — 15 de marzo de 2026

Se preservan el CSV oficial de resultados por mesa, la ficha de metadatos del portal, la publicación BOCYL del escrutinio y las correcciones de 8 y 11 de junio. Se procesaron **67.006 filas y 4.489 mesas**; las ecuaciones por mesa pasan sin fallos. Los agregados provinciales por candidatura concilian con el escrutinio corregido.

El conjunto suma **1.236.753 votos a candidaturas**, de los cuales **11.782** corresponden a los **19 códigos CERA** mantenidos separados. Las correcciones del 8 de junio quedan comprobadas: PANCAL-URCI tiene 0 votos en Salamanca y Zamora; PREPAL tiene 311 y 333 respectivamente. La corrección del 11 de junio completa la publicación de un anexo y no cambia esas cifras.

La reconciliación registrada contiene 3.528 identidades electorales, 3.504 coincidentes con el universo INE 2025, 24 result-only y dos territoriales-only. Los 19 códigos CERA explican 11.782 votos result-only. Persisten cinco códigos geográficos result-only (`2408904017`, `2408906020`, `3702301002`, `4217302016`, `4701001012`) con **3.874 votos**, y dos códigos territoriales-only (`3412004006`, `3710701002`). Los candidatos espaciales de expedientes anteriores no acreditan transferencia electoral. **Adquisición y conciliación: PASS. Crosswalk y admisibilidad electoral: BLOCKED.**

## Extremadura — 21 de diciembre de 2025

Se verifican el HTML y PDF del DOE que publican el escrutinio definitivo agregado: Badajoz **326.196**, Cáceres **198.641**, total **524.837** votos a candidaturas. El conjunto granular provisional existente suma **522.418**; la diferencia es **2.419** y permanece sin asignar.

La búsqueda oficial localizó el acuerdo final del DOE/Junta Electoral, el índice electoral de la JEC, el documento CERA y el DOE que publica los modelos de actas. No se encontró un archivo público de resultados definitivos por mesa: el acuerdo localizado es agregado provincial; la publicación de actas es un **modelo en blanco**, no las actas cumplimentadas. Esto no prueba que los documentos no existan. La evidencia faltante concreta son las actas definitivas de escrutinio por mesa/candidatura, incluidas correcciones y CERA, o una exportación oficial granular equivalente. Los custodios identificados son las Juntas Electorales Provinciales de Badajoz y Cáceres y la Junta Electoral de Extremadura.

La solicitud institucional ya fue remitida por el titular según el expediente precedente; esta ejecución no la reenvió. **Fuente definitiva agregada: verificada. Granular definitivo y conciliación de los 2.419 votos: BLOCKED_EXTERNAL.**

## Productos y límites

- Los originales y sus URLs, tamaños y SHA-256 están en `originales/` y `procesados/manifest_procesamiento.json`.
- Los CSV normalizados son deterministas y preservan las claves electorales; el control CERA de Aragón está aparte.
- Los contratos candidatos derivados de los contratos vigentes pasan `validar_paquete_electoral.py` en modo `READY_PACKAGE` con identidad de elección exacta y hash coincidente. Son candidatos aislados: no se registran en el catálogo ni sustituyen receipts históricos.
- El resultado completo, hashes y salidas del consumidor están en `procesados/resultado_procesamiento.json`.
- `estado_derivado_f10.py` sobre el HEAD base continúa en **15/19 ADMISSIBLE**, **14/19 PASS conjunto** y **F10 PENDING**; no se editó la matriz ni se declaró transición por estos candidatos.
- No se modificaron M01–M06, no se redistribuyeron votos, no se fusionó ni promovió ninguna fuente, y no se ejecutaron distritos ni producción.
- Los originales se comparan byte a byte con sus SHA-256; la comprobación whitespace del diff excluye esa carpeta de copias auténticas para no reescribir terminadores de línea de la fuente.
