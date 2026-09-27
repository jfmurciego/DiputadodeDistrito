# Auditoría de entrada electoral — 19 territorios

Base: PR #147. Esta matriz separa cinco evidencias; ninguna se infiere de otra. Un check verde no acredita 19/19.

## Resumen de cierre

- **19/19** territorios tienen identidad electoral registrada y una ruta técnica explícita hacia `03 · Preparación de Resultados Electorales`.
- **17/19** tienen cadena real acreditada hasta fuente durable + paquete + registro en copia.
- **Andalucía**: `PENDING_SIEL_SNAPSHOT` — ruta SIEL completa implementada; falta adquirir el snapshot real completo de 6.044 secciones y reconciliarlo.
- **Extremadura**: `BLOCKED_FINAL_GRANULAR_SOURCE` — existe granular provisional, pero no una fuente definitiva granular pública/reproducible.
- **Registro efectivo en producción** no se infiere del registro en copia y no forma parte de las nuevas pruebas de #147.


| Territorio | Elección correcta identificada | Datos reales adquiridos y validados | Fuente durable consumible por 03 | Paquete + registro probado en copia | Registro efectivo en producción | Bloqueo si falta |
|---|---|---|---|---|---|---|
| Andalucía | Sí — Parlamento 2026, 2026-05-17; SIEL `fconvocatoria=202605` acreditada | Parcial — SIEL oficial devuelve votos por candidatura en sección real; la adquisición completa de 6.044 secciones sigue pendiente. El provisional Minsait (4.128.575) no se usa como voto definitivo | No aún — `03` ya consume `ddd-siel-andalucia-2026-snapshot` y verifica identidad, dos huellas y ocho controles provinciales, pero falta producir el snapshot completo | Ruta técnica probada en sintético: paquete `ACQUIRE` + promoción en copia + preflight `registered=true`; paquete real todavía NO | No | Falta completar el snapshot SIEL y reconciliar secciones + CERA = BOJA 4.157.539. Procedimiento local reproducible en `docs/auditorias/SIEL_ANDALUCIA_2026_MANUAL.md`. |
| Aragón | Sí — Cortes 2026, 2026-02-08 | Sí — fuente materializada RTVE 2026, sección censal, SHA gobernado | Sí — contrato electoral materializado 2026 | Sí — reutilización materializada verificable; no requiere readquisición | Sí — `electoral_source_2025.json` registra `aragon_cortes_2026-02-08` | — |
| Principado de Asturias | Sí — Junta General 2023 | Sí | Sí — declaración propia | Sí, ruta real ya probada | Sí | — |
| Islas Baleares | Sí — Parlament 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Canarias | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Cantabria | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla-La Mancha | Sí — Cortes 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla y León | Sí — Cortes 2026, 2026-03-15 | Sí — producto materializado gobernado | Sí — contrato materializado | Sí — REUSE verificado, sin adquisición externa | Sí — evidencia existente | — |
| Cataluña | Sí — Parlament 2024, 2024-05-12 | Sí — mirror auditable del export Generalitat, 8.940 mesas geográficas / 5.117 secciones; 4 filas CERA reconciliadas aparte, reconciliación exacta | Sí — URL fijada a commit externo inmutable + referencias oficiales Generalitat | Sí — 5.117 secciones, 3.100.013 votos geográficos; 20.490 CERA reconciliados; paquete y registro en copia PASS | No | No se ha promovido en producción. |
| Comunidad Valenciana | Sí — Corts 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Extremadura | Sí — Asamblea 2025, 2025-12-21 | No — existe escrutinio provisional granular (966 secciones; 522.418 votos a candidaturas), pero no reconcilia con el definitivo | No definitiva — el repositorio granular oficial de prensa está gobernado como `provisional_only`, con credenciales y `promotion_allowed: false` | No | No | `BLOCKED_FINAL_GRANULAR_SOURCE`: delta +2.419 frente a DOE definitivo (524.837). No existe en la declaración una fuente pública granular definitiva seleccionable. |
| Galicia | Sí — Parlamento 2024 | Sí | Sí — declaración propia | Evidencia real previa; no es una de las diez pruebas EleccionesDB | Sí | — |
| Comunidad de Madrid | Sí — Asamblea 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Región de Murcia | Sí — Asamblea Regional 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Comunidad Foral de Navarra | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| País Vasco | Sí — Parlamento 2024 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| La Rioja | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Ceuta | Sí — Asamblea de Ceuta, locales 2023 | Sí — EleccionesDB / Ministerio del Interior | Sí — snapshot común verificado | Sí — 56 secciones, 33.753 votos, registro en copia PASS | No | No se ha promovido en producción. |
| Melilla | Sí — Asamblea de Melilla, locales 2023 | Sí — EleccionesDB / Ministerio del Interior | Sí — snapshot común verificado | Sí — 44 secciones, 29.148 votos, registro en copia PASS | No | No se ha promovido en producción. |

## Estado efectivo de producción

En el catálogo operativo de esta rama sólo cuatro territorios tienen `electoral_source_prepared: true` con evidencia durable existente:

- **Aragón** — `territorios/aragon/evidencia/catalogo/electoral_source_2025.json`, run `36136639133`, elección `aragon_cortes_2026-02-08`.
- **Principado de Asturias** — `territorios/principado_de_asturias/evidencia/catalogo/electoral_source_2025.json`, run `36136631352`, elección `asturias_jgpa_2023`.
- **Castilla y León** — `territorios/castilla_y_leon/evidencia/fuente_electoral_2026_procedencia.json`, elección `castilla_y_leon_cortes_2026-03-15`.
- **Galicia** — `territorios/galicia/evidencia/catalogo/electoral_source_2025.json`, run `36136559051`, elección `galicia_parlamento_2024`.

Para los otros quince territorios, cualquier paquete o registro producido por las pruebas de #147 es **registro en copia de trabajo**, no producción. La PR no debe alterar esa distinción.

## Snapshot común EleccionesDB

El adaptador común cubre doce identidades electorales: Islas Baleares, Canarias, Cantabria, Castilla-La Mancha, Comunidad de Madrid, Región de Murcia, Comunidad Foral de Navarra, La Rioja, Comunidad Valenciana, País Vasco, Ceuta y Melilla. Ceuta y Melilla comparten físicamente la elección nacional de EleccionesDB 247 (Locales 2023), pero se aíslan por código de comunidad autónoma 18 y 19. El workflow diagnóstico descarga el export upstream una sola vez, construye un SQLite compacto y publica `ddd-eleccionesdb-snapshot` durante 90 días. `03 · Preparación de Resultados Electorales` recupera ese artefacto y exige la huella interna declarada antes de usarlo.

Huella interna gobernada del SQLite: `668f8eeefe0c19f427367ee2b44f0050c30b93d39f7300fad3d6f381966d91fc`. El snapshot contiene 11 elecciones físicas de EleccionesDB y 12 identidades territoriales lógicas.

La prueba de CI construye los doce paquetes con el mismo snapshot y registra cada uno exclusivamente en una copia de trabajo del catálogo. Ese registro de prueba **no es registro efectivo en producción**.

## Cataluña 2024

La CI de #147 adquiere el CSV de mesas desde un mirror GitHub fijado a commit y lo contrasta contra referencias oficiales de la Generalitat. El adaptador rechaza cualquier fichero que no reproduzca exactamente 8.940 mesas geográficas, 5.117 secciones geográficas, 3.183.137 votantes totales, 3.120.503 votos a candidaturas totales y 20.490 votos CERA no geocodificables y los totales por candidatura declarados. La prueba real produce paquete y registro únicamente en copia de trabajo.

## Andalucía 2026

La ruta técnica ya está integrada en `03 · Preparación de Resultados Electorales`: identifica `andalucia_parlamento_2026`, recupera un artefacto `ddd-siel-andalucia-2026-snapshot`, exige identidad electoral, SHA-256 de secciones y CERA, ocho controles provinciales reconciliados y total oficial 4.157.539. El adaptador genera contrato electoral común y paquete `ACQUIRE`. La promoción en copia mediante el registro electoral común está cubierta por prueba; esto **no acredita todavía datos reales completos ni registro en producción**. Si GitHub Actions no completa la adquisición, el procedimiento local canónico está documentado en `docs/auditorias/SIEL_ANDALUCIA_2026_MANUAL.md`.

## Bloqueos definitivos pendientes

Extremadura no está bloqueada por ausencia de datos provisionales: el fichero granular existe. Está bloqueada porque ese fichero **no es definitivo** y difiere de la proclamación oficial. El repositorio oficial de prensa queda explícitamente gobernado como `provisional_only`, `promotion_allowed: false` y requiere credenciales. La evidencia cuantitativa se mantiene en `docs/auditorias/bloqueos_fuentes_definitivas_2026-09-27.md`.

## Criterio de cierre

#147 permanece **INCOMPLETA / NO FUSIONAR**. La cadena real queda cerrada hasta paquete+registro en copia para 17 territorios. Andalucía tiene ya ruta técnica completa y registro en copia probado de forma sintética, pero sigue pendiente el snapshot SIEL real completo; Extremadura permanece bloqueada por falta de fuente definitiva granular reproducible. Ningún registro de copia se considera producción. No ejecutar territorios ni promover registros para cerrar esta prueba.
