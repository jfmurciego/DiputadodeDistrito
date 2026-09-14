# F1.3 — Tests y clasificación de workflows

**Fecha:** 2026-09-12

## Acción

- Los tests que leen JSON/CSV publicados se renombran como pruebas de integridad de evidencia; sus docstrings declaran que no reejecutan el pipeline.
- Los 46 workflows quedan clasificados como `activo`, `experimental` o `congelado`.
- Solo la CI global y las regresiones de Aragón y Castilla y León conservan disparadores `push`.
- El resto queda disponible por `workflow_dispatch`, evitando que cambios comunes lancen baterías experimentales no solicitadas.

## Verificación

- 46/46 workflows clasificados.
- 3 workflows con `push`.
- YAML válido en 46/46 workflows.
- Pruebas de evidencia R016 y gobernanza: PASS.
