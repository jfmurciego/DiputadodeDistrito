# Auditoría de entrada electoral — 19 territorios

Base: PR #147. Esta matriz separa cinco evidencias; ninguna se infiere de otra. Un check verde no acredita 19/19.

## Estados verificables

Los estados terminales de una cadena territorial son `PASS`, `BLOCKED` y `FAIL`. `COMPLETE` / `INCOMPLETE` describen la cobertura del conjunto y **no sustituyen** al resultado territorial.

- **PASS** — la elección está identificada; los datos reales usados por #147 están adquiridos y validados con su estado de fuente explícito; existe una fuente durable consumible por `03`; el paquete electoral termina en `ACQUIRE` o `REUSE`; y el mismo paquete puede registrarse correctamente en una copia de trabajo del catálogo. No implica que la fuente sea definitiva ni que el paquete sea elegible para producción; esa elegibilidad se declara por separado.
- **BLOCKED** — la cadena no puede avanzar hasta paquete + registro en copia porque falta una condición externa o contractual conocida y verificable, no porque una validación haya sido ignorada. Debe existir un código/razón causal concreto y evidencia del requisito ausente. La no elegibilidad para producción se informa separadamente y no invalida por sí sola la prueba de copia de #147.
- **FAIL** — se intentó ejecutar una fase que debía poder completarse y terminó por error de código, estructura, identidad, huella, reconciliación o contrato. Un HTTP fallido sólo es `FAIL` si el contrato exigía que esa adquisición fuese realizable en ese contexto; no se convierte en éxito ni en ausencia de datos por inferencia.
- **COMPLETE** — los 19 territorios tienen exactamente un estado terminal verificable (`PASS`, `BLOCKED` o `FAIL`) y para cada uno existe evidencia suficiente para reproducir por qué terminó así. `COMPLETE` no implica que los 19 sean `PASS`.
- **INCOMPLETE** — al menos un territorio carece todavía de estado terminal o su evidencia es insuficiente para sostenerlo. También aplica cuando existe una ruta técnica o una muestra parcial pero falta cerrar la cadena real exigida.
- **Falta de estado terminal** — si un job/run acaba cancelado, queda en cola, expira, no instancia la fase esperada o termina sin producir una decisión territorial explícita, el territorio es `INCOMPLETE`; no se infiere `PASS`, `BLOCKED` ni `FAIL` a partir del silencio.

Para la aceptación funcional de #147, `COMPLETE` es condición necesaria pero no suficiente: Work debe revisar separadamente cuántos territorios están en `PASS`, cuáles en `BLOCKED` y si algún `FAIL` permanece abierto.

## Regla de procedencia al registrar

La identidad de una fuente electoral se conserva con esta prioridad:

1. **Declaración explícita** cuando el paquete fue producido por el camino genérico gobernado por esa declaración.
2. **Contrato electoral materializado** cuando ya existe un contrato verificable en el territorio; este camino preserva la procedencia fuerte de Aragón y Castilla y León.
3. **Registro electoral común** sólo como fallback para adaptadores compartidos que no dependen de una declaración ni de un contrato materializado, como EleccionesDB y SIEL.

El adaptador realmente usado por `03` gobierna qué procedencia puede registrarse. Una declaración existente no se atribuye a un paquete producido por EleccionesDB/SIEL. El promotor rechaza además declaraciones cuyo `territory_id` o `election_id` no coincidan con la promoción.

## Resumen de cierre

- **19/19** territorios tienen identidad electoral registrada y una ruta técnica explícita hacia `03 · Preparación de Resultados Electorales`.
- Estado territorial actual: **18 PASS / 1 BLOCKED**.
- **18 PASS** — cadena real acreditada hasta fuente durable + paquete + registro en copia.
- **Andalucía = PASS en copia / producción bloqueada** — fuente `PROVISIONAL`, paquete real y registro en copia PASS; `production_eligible=false`.
- **Extremadura = BLOCKED / `BLOCKED_FINAL_GRANULAR_SOURCE`** — existe granular provisional, pero no se ha integrado en esta PR como paquete registrable.
- **Registro efectivo en producción** no se infiere del registro en copia y no forma parte de las nuevas pruebas de #147.


| Territorio | Elección correcta identificada | Datos reales adquiridos y validados | Fuente durable consumible por 03 | Paquete + registro probado en copia | Registro efectivo en producción | Bloqueo si falta |
|---|---|---|---|---|---|---|
| Andalucía | Sí — Parlamento 2026, 2026-05-17 | Sí — CSV Minsait/EleccionesDB: 154.358 filas, 10.403 mesas, 6.044 secciones, 27 candidaturas, 4.128.575 votos | Sí — URL durable + SHA-256 `13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21`; `03` usa `minsait_csv/1.0` | Sí — run `36319863920`; paquete SHA-256 `a6aa80296d0ef5ecbddd3437d9e8d50a040d81271fe13ab9c1a8b21e5db21b30`; registro en copia PASS | No | Fuente `PROVISIONAL`, `production_eligible=false`; registro productivo bloqueado por contrato. |
| Aragón | Sí — Cortes 2026, 2026-02-08 | Sí — fuente materializada RTVE 2026, sección censal, SHA gobernado | Sí — contrato electoral materializado 2026 | Sí — reutilización materializada verificable; no requiere readquisición | Sí — `electoral_source_2025.json` registra `aragon_cortes_2026-02-08` | — |
| Principado de Asturias | Sí — Junta General 2023 | Sí | Sí — declaración propia | Sí, ruta real ya probada | Sí | — |
| Islas Baleares | Sí — Parlament 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Canarias | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Cantabria | Sí — Parlamento 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Castilla y León | Sí — Cortes 2026, 2026-03-15 | Sí — producto materializado gobernado | Sí — contrato materializado | Sí — REUSE verificado, sin adquisición externa | Sí — evidencia existente | — |
| Castilla-La Mancha | Sí — Cortes 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Cataluña | Sí — Parlament 2024, 2024-05-12 | Sí — mirror auditable del export Generalitat, 8.940 mesas geográficas / 5.117 secciones; 4 filas CERA reconciliadas aparte, reconciliación exacta | Sí — URL fijada a commit externo inmutable + referencias oficiales Generalitat | Sí — 5.117 secciones, 3.100.013 votos geográficos; 20.490 CERA reconciliados; paquete y registro en copia PASS | No | No se ha promovido en producción. |
| Comunidad Valenciana | Sí — Corts 2023 | Sí — EleccionesDB | Sí — snapshot común verificado | Sí | No | No se ha promovido en producción. |
| Extremadura | Sí — Asamblea 2025, 2025-12-21 | No — existe escrutinio provisional granular (966 secciones; 522.418 votos a candidaturas), pero no reconcilia con el definitivo | No definitiva — el repositorio granular oficial de prensa está gobernado como `provisional_only`, con credenciales y `promotion_allowed: false` | No | No | `BLOCKED_FINAL_GRANULAR_SOURCE`: delta +2.419 frente a DOE definitivo (524.837). No existe en la declaración una fuente pública granular definitiva seleccionable. |
| Galicia | Sí — Parlamento 2024 | Sí | Sí — declaración propia | Evidencia real previa; no pertenece al adaptador común de doce identidades EleccionesDB | Sí | — |
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

## Detalle de los tres casos críticos

| Territorio | Fuente usada / estado | Clasificación | Resolución | Cobertura / votos | SHA-256 | Paquete | Registro en copia |
|---|---|---|---|---|---|---|---|
| Cataluña | Export Parlament 2024 de la Generalitat, servido desde mirror GitHub fijado a commit | **verified_mirror** con referencias oficiales Generalitat; no se presenta como descarga oficial primaria | mesa → agregación a sección | 8.940 mesas geográficas; 5.117 secciones; 3.100.013 votos geográficos + 20.490 CERA = 3.120.503 | `511ed5cf4f7afa31063355614a7982e95943fe8fe67f707a3b4dbb810357a96a` | PASS / `ACQUIRE` | PASS |
| Andalucía | CSV Minsait/EleccionesDB ya disponible | **PROVISIONAL / provisional_mirror**, explícitamente no elegible para producción | mesa → agregación a sección | 154.358 filas; 10.403 mesas; 6.044 secciones; 27 candidaturas; 4.128.575 votos | fuente `13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21`; paquete `a6aa80296d0ef5ecbddd3437d9e8d50a040d81271fe13ab9c1a8b21e5db21b30` | PASS / `ACQUIRE` | PASS — run `36319863920`, sólo copia |
| Extremadura | Minsait/EleccionesDB granular + DOE definitivo de contraste | granular = **PROVISIONAL / no promocionable**; DOE = **fuente oficial definitiva de contraste**, pero sólo circunscripción | 966 secciones provisional; definitivo sólo circunscripción | 522.418 provisional vs 524.837 definitivo; delta +2.419 | provisional: `d09a4ad4be094f230ed84e17160fbfc801f5d0c2f51e3d931073a06cc094003d` | NO | NO |

## Andalucía 2026

La ruta activa de `03 · Preparación de Resultados Electorales` usa el CSV Minsait/EleccionesDB ya disponible y gobernado por SHA-256. El adaptador común `minsait_csv/1.0` verifica CCAA 01, ocho provincias, 6.044 secciones, 10.403 mesas y 4.128.575 votos a candidaturas, agrega mesa→sección y genera contrato electoral común y paquete `ACQUIRE`. El paquete declara `source_status=PROVISIONAL` y `production_eligible=false`. Por tanto puede probarse y registrarse en una **copia de trabajo**, pero el job productivo de registro queda bloqueado por contrato.

## Bloqueos definitivos pendientes

Extremadura no está bloqueada por ausencia de datos provisionales: el fichero granular existe. Está bloqueada porque ese fichero **no es definitivo** y difiere de la proclamación oficial. El repositorio oficial de prensa queda explícitamente gobernado como `provisional_only`, `promotion_allowed: false` y requiere credenciales. La evidencia cuantitativa se mantiene en `docs/auditorias/bloqueos_fuentes_definitivas_2026-09-27.md`.

## Criterio de cierre

#147 permanece **NO FUSIONAR** hasta que Work autorice y se compruebe la CI terminal del HEAD final. La cadena real queda cerrada hasta paquete+registro en copia para **18 territorios**; Extremadura permanece BLOCKED. Andalucía está acreditada en copia mediante run `36319863920`, pero sigue explícitamente no elegible para producción. Ningún registro de copia se considera producción.
