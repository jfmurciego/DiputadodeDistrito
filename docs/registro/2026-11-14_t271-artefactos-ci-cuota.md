## 2026-11-14 — T-271 — artefactos de diagnóstico de CI desacoplados de la cuota

- Causa: `main` en rojo en 439af6a sin ningún test fallido: suites 1-5, `contratos` y `docs` caían en «Failed to CreateArtifact:
  Artifact storage quota has been hit» al subir artefactos de diagnóstico. En suite (2), «el P30 exige PYTHONHASHSEED=0» y «la
  salida M05 no vuelve a su sha256 original» son salida esperada de tests que pasan (`ok`; «Ran 607 tests … OK (skipped=7)»).
- Cambio: `pruebas-plataforma.yml` 1.10.1. Los cinco upload-artifact (diagnóstico de suite, expedientes N08, contratos,
  documentación, producto) suben solo si el job falla (`if: failure()`), con `continue-on-error: true` y `retention-days: 1`.
  No cambia qué se comprueba. Ningún job de pruebas descarga artefactos de otro. Producción (00, 05, preparación, generación,
  Gestor, archivo, batería del motor) intacta.
- Pruebas: `tests/test_artefactos_ci_cuota.py` (falla con la 1.10.0, pasa con la 1.10.1), `test_workflow_safety`,
  `test_workflow_shell_syntax`, `test_ahorro_ci_pruebas`, `test_guardia_estado_vivo`, `test_design_a_*`, GovernanceHeaders.
- Riesgo: con éxito ya no queda la vista previa de la documentación ni el sitio verificado como artefacto (nadie los descargaba).
