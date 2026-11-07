<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Estados de tarea y de efecto externo, y handoff (metaagente v1.0 §9, §23)
FECHA: 2026-11-07
ESTADO: candidato (propuesta; no cambia PLAN.md ni skills)
CAMBIOS: T-75. Propuesta mínima adaptada a docs/PLAN.md y a las líneas de cierre, con los casos reales del 07-11.
MOTIVO: aplicar el método del metaagente v1.0 sobre lo que existe (nivel N2).
ANTERIOR: ninguna (fichero nuevo)
-->

# Estados y handoff en DDD

**Estado de tarea** (columna nueva en la cola de `PLAN.md`; lo escribe el planificador, lo propone el Coordinador):
`PENDIENTE → LISTA → EN_CURSO → REVISIÓN → ESPERA_APROBACIÓN → HECHA`, con `BLOQUEADA` y `FALLIDA`.
Se omiten `RETRYABLE_FAILURE` (lo cubren los dos ciclos de reparación) y `CANCELLED` (= `FALLIDA` con motivo).

**Estado de efecto externo**, una línea por efecto (fusión, lanzamiento, publicación, archivo):
`PREPARADO → AUTORIZADO → EN_VUELO → CONFIRMADO`, o `RECHAZADO` / **`DESCONOCIDO`**. Regla: con `DESCONOCIDO`,
**reconciliar contra GitHub antes de reintentar** (estado real de la PR o del run) y una tarea no pasa a `HECHA`
con un efecto `DESCONOCIDO`.

| Caso real | Efecto | Estado que tuvo | Estado correcto | Qué habría evitado |
|---|---|---|---|---|
| #462, fusionada en pausa (`PLAN.md`: «queda abierta sin fusionar») | fusión | `CONFIRMADO` sin `AUTORIZADO` del propietario | `ESPERA_APROBACIÓN` | Fusión solo desde `AUTORIZADO` citando la orden; revertida en #467, reaplicada en #470 |
| #453, #454: auto-merge 1.0.0 con PR «clean» por actor exento | fusión | `CONFIRMADO` sin gate | `REVISIÓN` (falta `pruebas`) | Gate por check-run del SHA (T-54b) |
| #458: auto-merge 1.0.0 en `pull_request` con merge ref sin #457 | fusión | `CONFIRMADO` con gate de otra revisión | `REVISIÓN` | Gate ligado a la suite que dispara (T-54c); `main` rojo hasta #459 |

**Handoff** (§23 reducido a la línea de cierre; texto, no JSON):

`T-xx · estado · qué · PR #n@<sha7> · efectos: <efecto>=<estado> · siguiente · bloqueo · ref de autorización`

Ejemplo: `T-75 · REVISIÓN · ADR, fichas y madurez · PR #n@abc1234 · efectos: fusión=PREPARADO (no-automerge) ·
fusiona el propietario · ninguno · encargo del planificador 07-11`.
Campos del §23 que se conservan: `task_id`, `producer_revision` (sha), `acceptance` (criterio de hecho de
`PLAN.md`), `authorization_ref`, `on_unknown_effect=RECONCILE_BEFORE_RETRY`. Se omiten `run_id`, `attempt_id`,
`budget.reservation_id` y esquemas: no hay controlador que los valide.

Adopción: la decide el planificador (edita `PLAN.md`) y la aplican las skills `coordinador`, `operador` e
`implementador` en una PR propia; este documento no las cambia.
