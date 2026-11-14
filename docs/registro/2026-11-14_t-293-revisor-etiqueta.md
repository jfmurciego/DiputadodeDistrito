## 2026-11-14 — T-293 — Revisor de PR solo con la etiqueta `revisar-ia`

- Causa: `revisor-pr.yml` lanzaba Sonnet (30 turnos, cuota del propietario) en cada push de cada PR (26 ejecuciones en una semana) y duplicaba la revisión independiente del Coordinador.
- Cambio (1.1.0, autorizado por el propietario; solo disparadores, fallo cerrado y permisos intactos): el `if` de `comprobar` exige la etiqueta `revisar-ia` (a demanda = ponerla; evento `labeled` solo si la etiqueta es esa), PR no borrador y autor no Bot. Sin ello los tres jobs quedan «skipped» y el check `veredicto` que exige el ruleset `proteger-main` cuenta como cumplido; se mantienen los tipos de evento (+ `labeled`) para que el check exista en cada HEAD. `cancel-in-progress: false` con `queue: max` (exigido por test_operational_concurrency_gerrychain50) para que un push o una etiqueta ajena no maten una revisión en curso. Copia en `legacy/workflows/revisor-pr_v1.0.2_20261114.yml`.
- Auto-merge: sin efecto (solo mira `pruebas`). Sin `workflow_dispatch`: no se pidió y exigiría tocar permisos/lectura de la PR.
- Pruebas: `tests/test_agentes_ci.py` (nuevo test de disparadores y condición).
- Riesgos: la etiqueta `revisar-ia` hay que crearla en el repositorio; las PR de robots y borradores ya no reciben revisión automática.
