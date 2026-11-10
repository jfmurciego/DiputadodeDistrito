## 2026-11-10 — T-149 — Lista de Actions: los 4 workflows «- …» pasan a «Auxiliar — …»

Causa: el prefijo «- » de cuatro workflows manuales (Activación por Elección, Archivar artefactos en R2, Extraer
composición M06, Activación de Legislatura Vigente) los ordena por delante de los numerados en la lista de Actions.
Cambio: `name:` pasa a «Auxiliar — <nombre>»; `run-name`, nombres de fichero, numerados y notación de fases/módulos
no cambian. Único consumidor por `name:`: `tests/test_preparacion_legislatura_vigente.py` (actualizado); ningún
`workflow_run`, check obligatorio, herramienta ni huella los cita por nombre (las métricas leen el `run-name`).
Pruebas: `GovernanceHeaders` y `test_preparacion_legislatura_vigente` en verde. Riesgo: ninguno de ejecución; el
historial de runs antiguos conserva el nombre previo. Inventario de consolidación (solo informe) en
`docs/ESTUDIOS/T149_LISTA_ACTIONS/INVENTARIO.md`.
