# Auditoría de entrada electoral — 19 territorios

Base de trabajo: PR #147, edición territorial `2025`.

La matriz mantiene tres estados independientes. **Elección identificada** sólo fija qué convocatoria corresponde al territorio. **Fuente adquirible** exige una ruta que `03 · Preparación de Resultados Electorales` pueda intentar realmente a la resolución requerida. **Paquete registrado** exige evidencia durable reutilizable; no se infiere de los dos estados anteriores.

| Territorio | Elección identificada | Fuente adquirible por `03` | Paquete registrado durable |
|---|---|---|---|
| Andalucía | Sí — Parlamento 2022 | No | No |
| Aragón | Sí — Cortes 2023 | No declarada en el registro común | Sí — evidencia electoral existente en catálogo |
| Principado de Asturias | Sí — Junta General 2023 | Sí — declaración GIPEYOP/mirror auditable con referencia oficial | Sí — evidencia electoral existente en catálogo |
| Islas Baleares | Sí — Parlament 2023 | No acreditada todavía | No |
| Canarias | Sí — Parlamento 2023 | No — la fuente autonómica localizada no alcanza todavía la resolución requerida | No |
| Cantabria | Sí — Parlamento 2023 | **Pendiente de prueba real** — declaración añadida en #147 con adaptador `gipeyop_polling_xlsx` | No |
| Castilla-La Mancha | Sí — Cortes 2023 | No | No |
| Castilla y León | Sí — Cortes 2026 | No declarada en el registro común | Sí — evidencia electoral existente en catálogo; revisar compatibilidad con el registro común |
| Cataluña | Sí — Parlament 2024 | No | No |
| Comunidad Valenciana | Sí — Corts 2023 | No | No |
| Extremadura | Sí — Asamblea 2025 | No utilizable todavía — declaración existente, pero las fuentes no superan adquisición + resolución | No |
| Galicia | Sí — Parlamento 2024 | Sí — declaración existente y adquisición ya acreditada | Sí — evidencia electoral existente en catálogo |
| Comunidad de Madrid | Sí — Asamblea 2023 | No | No |
| Región de Murcia | Sí — Asamblea Regional 2023 | No | No |
| Comunidad Foral de Navarra | Sí — Parlamento 2023 | No | No |
| País Vasco | Sí — Parlamento 2024 | No | No |
| La Rioja | Sí — Parlamento 2023 | No | No |
| Ceuta | Sí — Asamblea de Ceuta, locales 2023 | No | No |
| Melilla | Sí — Asamblea de Melilla, locales 2023 | No | No |

## Interacción con `00 · Ejecución Completa del Proyecto`

El registro común de 19 elecciones **no es una señal de disponibilidad electoral**. En el commit `61a011732debcd7ca2b77aa6b9309b81bfb35477`, Cantabria conserva `election_id=cantabria_parlamento_2023` pero no tiene declaración adquirible; la regresión exige que `resolve_publication_mode(..., "electoral")` degrade a `territorial_only`. El workflow ya convierte esa resolución en `run_prepare_electoral=false` y `run_incorporate=false`, por lo que los jobs electorales quedan omitidos y la cadena territorial puede continuar.

Tras esa prueba negativa, #147 añade para Cantabria una declaración separada que conecta el formato de mesa GIPEYOP con el adaptador compartido `gipeyop_polling_xlsx`. La mera presencia de `election_id` sigue sin ser suficiente: sólo la declaración materializada vuelve resoluble la entrada electoral.

## Cadena positiva exigida

Para cerrar Cantabria deben quedar acreditados, en este orden:

1. adquisición real por `03` de `Cantabria2023_mesas.xlsx`;
2. transformación mediante `gipeyop_polling_xlsx`;
3. paquete `ddd-electoral-package/1.0` con `decision=ACQUIRE`, procedencia y SHA-256;
4. registro durable en catálogo/evidencia;
5. segunda ejecución que reutilice el paquete (`REUSE`) sin nueva adquisición;
6. interacción final con `00`, demostrando que una fuente adquirible sí mantiene modo electoral y que una elección meramente identificada sigue degradando a ruta territorial.

## Estado de cierre

**NO-GO. PR #147 debe permanecer draft.** La separación de estados está implementada y las pruebas son descubribles por `unittest`, pero el cierre requiere CI verde y la adquisición real + registro durable + reutilización indicados arriba.
