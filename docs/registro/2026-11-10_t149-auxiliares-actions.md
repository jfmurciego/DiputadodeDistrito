## 2026-11-10 — T-149 — Lista de Actions: los 4 workflows «- …» pasan a «Auxiliar — …»

Causa: el prefijo «- » de cuatro workflows manuales (Activación por Elección, Archivar artefactos en R2, Extraer
composición M06, Activación de Legislatura Vigente) los ordena por delante de los numerados en la lista de Actions.
Cambio: `name:` pasa a «Auxiliar — <nombre>»; `run-name`, nombres de fichero, numerados y notación de fases/módulos
no cambian. Único consumidor por `name:`: `tests/test_preparacion_legislatura_vigente.py` (actualizado); ningún
`workflow_run`, check obligatorio, herramienta ni huella los cita por nombre (las métricas leen el `run-name`).
Pruebas: `GovernanceHeaders` y `test_preparacion_legislatura_vigente` en verde. Riesgo: ninguno de ejecución; el
historial de runs antiguos conserva el nombre previo. Inventario de consolidación (solo informe) en
`docs/ESTUDIOS/T149_LISTA_ACTIONS/INVENTARIO.md`.

Ampliación (orden del Planificador vía Coordinador): se retiran el workflow muerto `notificar-finalizacion-orquestacion.yml`
(escuchaba un workflow inexistente) y la cadena sin llamador `_reutilizable-operacion-territorial.yml`,
`producir-territorio-por-contrato.yml`, `_reutilizable-auditoria-topologica.yml`, `orquestacion-durable.yml` y
`orquestacion-control.yml` (el 06 queda: lo llama la 00). Los dos reutilizables que se quedan pasan a
«Interno · Generación territorial» e «Interno · Publicador del sitio» (excepción temporal `workflow_call`).
Pruebas: se retiran o ajustan los tests que leían esos ficheros (≈25 métodos en 22 ficheros); no se encontró ningún
test que cargara lógica viva. Riesgo: se pierde la cobertura de texto de ese motor modular, sin uso en `main`.
Paso 6 (fusión automática y forense) no se toca.
