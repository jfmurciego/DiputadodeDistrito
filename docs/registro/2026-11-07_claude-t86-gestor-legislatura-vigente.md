## 2026-11-07 — T-86 — Gestor de Campañas listo para la legislatura vigente

- Causa: orden del propietario (07-11) de dejar el Gestor listo para lanzar la legislatura vigente nacional y autonómica.
- Cambio: `configuracion/legislatura_vigente.yaml` (71 territorios, clave T-03, fecha y fuente de resultados), generado
  por `herramientas/legislatura_vigente.py` desde `registro_electoral.yaml`, `preparacion_legislatura_vigente.yaml` y
  el BOE-A-2023-18907, con sha256 de las fuentes. `gestor-campanas.yml` 1.3.0: modos `plan` (en seco, también en cada
  PR) y `lanzar` por ámbito (legislatura completa, nacional, autonómicas, comunidad, provincias): un clic de `produccion`,
  territorio de prueba, concurrencia limitada, 00 → cadena electoral → 05 (D-3), relevo `continuar` como bot. El modo
  `matriz` conserva la campaña anterior. Skill `lanzar-campana`.
- Pruebas: `tests.test_legislatura_vigente` (configuración, plan, lanzamiento simulado, workflow) y los del Gestor,
  diseño A y gobernanza.
- Riesgos: sin validación real hasta la campaña de un territorio que pedirá el Coordinador. La 05 no lleva el run en el
  nombre: el Gestor publica de una en una.
