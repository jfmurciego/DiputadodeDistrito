# Auditoría de entrada electoral — 19 territorios

Base: PR #147. Esta matriz separa cinco evidencias; ninguna se infiere de otra. Un check verde no acredita 19/19.

| Territorio | Elección correcta identificada | Datos reales adquiridos y validados | Fuente durable consumible por 03 | Paquete + registro probado en copia | Registro efectivo en producción | Bloqueo si falta |
|---|---|---|---|---|---|---|
| Andalucía | Sí — Parlamento 2026, 2026-05-17 | No — existe escrutinio provisional granular (6.044 secciones; 4.128.575 votos a candidaturas), pero no reconcilia con el definitivo | No definitiva | No | No | El provisional Minsait difiere en 28.964 votos del total definitivo BOJA (4.157.539). Falta fuente pública/reproducible definitiva a sección/mesa; SIEL se diagnostica aparte sin convertir un timeout en ausencia de datos. |
| Aragón | Sí — Cortes 2026, 2026-02-08 | Sí — fuente materializada RTVE 2026, sección censal, SHA gobernado | Sí — contrato electoral materializado 2026 | Sí — reutilización materializada verificable; no requiere readquisición | Sí — `electoral_source_2025.json` registra `aragon_cortes_2026-02-08` | — |
| Principado de Asturias | Sí — Junta General 2023 | Sí | Sí — declaración propia | Sí, ruta real ya probada | Sí | — |
| Islas Baleares | Sí — Parlament 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Canarias | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Cantabria | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla-La Mancha | Sí — Cortes 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla y León | Sí — Cortes 2026, 2026-03-15 | Sí — producto materializado gobernado | Sí — contrato materializado | Sí — REUSE verificado, sin adquisición externa | Sí — evidencia existente | — |
| Cataluña | Sí — Parlament 2024, 2024-05-12 | Sí — mirror auditable del export Generalitat, 8.944 mesas / 5.121 secciones, reconciliación exacta | Sí — URL fijada a commit externo inmutable + referencias oficiales Generalitat | Sí — 5.121 secciones, 3.120.503 votos, paquete y registro en copia PASS | No | No se ha promovido en producción. |
| Comunidad Valenciana | Sí — Corts 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Extremadura | Sí — Asamblea 2025, 2025-12-21 | No — existe escrutinio provisional granular (966 secciones; 522.418 votos a candidaturas), pero no reconcilia con el definitivo | No definitiva | No | No | El provisional Minsait difiere en 2.419 votos del total definitivo DOE (524.837). El DOE definitivo sólo publica circunscripción y el repositorio de prensa granular exige credenciales. |
| Galicia | Sí — Parlamento 2024 | Sí | Sí — declaración propia | Evidencia real previa; no es una de las diez pruebas EleccionesDB | Sí | — |
| Comunidad de Madrid | Sí — Asamblea 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Región de Murcia | Sí — Asamblea Regional 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Comunidad Foral de Navarra | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| País Vasco | Sí — Parlamento 2024 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| La Rioja | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Ceuta | Sí — Asamblea de Ceuta, locales 2023 | Sí — EleccionesDB / Ministerio del Interior | Sí — snapshot común verificado | Sí — 56 secciones, 33.753 votos, registro en copia PASS | No | No se ha promovido en producción. |
| Melilla | Sí — Asamblea de Melilla, locales 2023 | Sí — EleccionesDB / Ministerio del Interior | Sí — snapshot común verificado | Sí — 44 secciones, 29.148 votos, registro en copia PASS | No | No se ha promovido en producción. |

## Snapshot común EleccionesDB

El adaptador común cubre doce identidades electorales: Islas Baleares, Canarias, Cantabria, Castilla-La Mancha, Comunidad de Madrid, Región de Murcia, Comunidad Foral de Navarra, La Rioja, Comunidad Valenciana, País Vasco, Ceuta y Melilla. Ceuta y Melilla comparten físicamente la elección nacional de EleccionesDB 247 (Locales 2023), pero se aíslan por código de comunidad autónoma 18 y 19. El workflow diagnóstico descarga el export upstream una sola vez, construye un SQLite compacto y publica `ddd-eleccionesdb-snapshot` durante 90 días. `03 · Preparación de Resultados Electorales` recupera ese artefacto y exige la huella interna declarada antes de usarlo.

Huella interna gobernada del SQLite: `668f8eeefe0c19f427367ee2b44f0050c30b93d39f7300fad3d6f381966d91fc`. El snapshot contiene 11 elecciones físicas de EleccionesDB y 12 identidades territoriales lógicas.

La prueba de CI construye los doce paquetes con el mismo snapshot y registra cada uno exclusivamente en una copia de trabajo del catálogo. Ese registro de prueba **no es registro efectivo en producción**.

## Cataluña 2024

La CI de #147 adquiere el CSV de mesas desde un mirror GitHub fijado a commit y lo contrasta contra referencias oficiales de la Generalitat. El adaptador rechaza cualquier fichero que no reproduzca exactamente 8.944 mesas, 5.121 secciones, 3.183.137 votantes, 3.120.503 votos a candidaturas y los totales por candidatura declarados. La prueba real produce paquete y registro únicamente en copia de trabajo.

## Bloqueos definitivos pendientes

Andalucía y Extremadura no están bloqueadas por ausencia de datos provisionales: ambos ficheros granulares existen. Están bloqueadas porque esos ficheros **no son resultados definitivos** y sus totales difieren de las proclamaciones oficiales. La evidencia cuantitativa se mantiene en `docs/auditorias/bloqueos_fuentes_definitivas_2026-09-27.md`.

## Criterio de cierre

#147 permanece **INCOMPLETA / NO FUSIONAR**. A fecha de esta evidencia, la cadena de entrada electoral queda cerrada hasta paquete+registro en copia para 17 territorios; Andalucía y Extremadura permanecen bloqueadas por falta de una fuente definitiva, granular y reproducible. Ningún registro de copia se considera producción. No ejecutar territorios ni promover registros para cerrar esta prueba.
