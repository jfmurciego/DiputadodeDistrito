## 2026-11-07 — T-75 — Aplicar el metaagente v1.0 a DDD (documentación)

Causa: el metaagente v1.0 solo se usaba como referencia (skill `disenar-agente`); faltaban ADR del enfoque (§3),
fichas por rol (§7), estados de tarea y de efectos externos (§9), handoff (§23) y tabla de madurez (§25).
Cambio: nuevos `docs/ARQUITECTURA/ADR-001-enfoque.md`, `FICHAS_AGENTES.md` (con veredictos §4),
`ESTADOS_Y_HANDOFF.md` (casos #462, #453, #454, #458) y `MADUREZ.md`. Solo propuestas: no cambia agentes, skills,
workflows, código ni `PLAN.md`.
Pruebas: `comprobar_guardian_main.py todo` y `tests.test_r015_invariantes.GovernanceHeaders`.
Riesgos: ninguno en ejecución; las fichas reflejan `main` tras #471 y caducan con cada cambio de rol.
