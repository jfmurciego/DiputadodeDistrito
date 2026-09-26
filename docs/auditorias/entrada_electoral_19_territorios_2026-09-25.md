# Auditoría de entrada electoral — 19 territorios

Base: PR #147. Esta matriz separa cinco evidencias; ninguna se infiere de otra. Un check verde no acredita 19/19.

| Territorio | Elección correcta identificada | Datos reales adquiridos y validados | Fuente durable consumible por 03 | Paquete + registro probado en copia | Registro efectivo en producción | Bloqueo si falta |
|---|---|---|---|---|---|---|
| Andalucía | Sí — Parlamento 2026, 2026-05-17 | No | No | No | No | Falta fuente 2026 definitiva, granular y verificable integrada en 03. |
| Aragón | Sí — Cortes 2026, 2026-02-08 | Evidencia previa; no acreditada por el adaptador común de #147 | Vía materializada previa | No en esta prueba | Sí — evidencia existente | Falta reconciliar explícitamente la evidencia existente con la identidad 2026 en la ruta común. |
| Principado de Asturias | Sí — Junta General 2023 | Sí | Sí — declaración propia | Sí, ruta real ya probada | Sí | — |
| Islas Baleares | Sí — Parlament 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Canarias | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Cantabria | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla-La Mancha | Sí — Cortes 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla y León | Sí — Cortes 2026, 2026-03-15 | Sí — producto materializado gobernado | Sí — contrato materializado | Sí — REUSE verificado, sin adquisición externa | Sí — evidencia existente | — |
| Cataluña | Sí — Parlament 2024, 2024-05-12 | No | No | No | No | EleccionesDB no aporta filas válidas para esta elección y falta otra fuente integrada. |
| Comunidad Valenciana | Sí — Corts 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Extremadura | Sí — Asamblea 2025, 2025-12-21 | No | No utilizable | No | No | Las fuentes declaradas no superan adquisición + resolución requerida. |
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

## Criterio de cierre

#147 permanece **INCOMPLETA / NO FUSIONAR** hasta que los territorios pendientes dispongan de fuente utilizable y se acredite la cadena correspondiente. No ejecutar territorios ni promover los registros de copia a producción para cerrar esta prueba.
