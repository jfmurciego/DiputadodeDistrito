## 2026-11-14 — T-274A — guía del runner propio de GitHub Actions

- Causa: D-93 pasa la CI y las Campañas del repositorio privado a un runner propio; falta la guía de registro.
- Cambio: nuevo `docs/GUIA_RUNNER_PROPIO.md` 1.0.0 (Linux y Windows, etiquetas, seguridad en privado, `runs-on` detrás de una
  variable —solo descrito—, coste, mantenimiento y verificación). No toca workflows, catálogo, contratos ni territorios; la
  parte B (T-274) va tras T-220.
- Pruebas: `GovernanceHeaders` y `comprobar_guardian_main.py todo` en local.
- Riesgo: ninguno; solo documentación.
