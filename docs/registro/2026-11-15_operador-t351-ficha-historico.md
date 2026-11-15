## 2026-11-15 — T-351 — Ficha del paso A del histórico al día (condición previa, orden tras r4, topes y avisos)

Causa: la ficha `2026-11-14_historico-paso-a-49x6` (#811) tenía «Pendiente de código (T-342)», que ya está cerrado. Además le faltaban T-343, T-345, D-119 a D-122, el orden respecto a la campaña r4 y los avisos al momento.

Cambio: solo documentación, en `docs/autorizaciones/2026-11-14_historico-paso-a-49x6.md`.
- Condición previa: las PR #796, #799, #804, #812, #813 y #816, todas en main, y las decisiones D-119 a D-122, con D-121 en `configuracion/decisiones_propietario/D-121.json`. La puerta parte de 312/312 acreditadas.
- Se quita el pendiente de T-342.
- El lanzamiento va DESPUÉS del cierre de r4 (COMPLETADA con su P50): una sola campaña a la vez, sobre los mapas publicados.
- Gasto semanal (D-46) medido al pedir la frase; tope de 15.000 min/semana con aviso al 70 %.
- La frase se pide solo tras el cierre de r4 (definido una vez) y caduca a los 7 días.
- Una puerta en rojo nunca se reintenta.
- La parada incluye los cambios del histórico en `main`.
- Avisos al Planificador por run (D-122).

Sin frase y sin nada lanzado.

Pruebas: no aplica (documentación).
