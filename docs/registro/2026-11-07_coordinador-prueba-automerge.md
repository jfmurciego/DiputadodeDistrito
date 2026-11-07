## 2026-11-07 — Coordinador — prueba de la fusión automática

Causa: verificar que `auto-merge.yml` (1.2.0) solo fusiona tras el check-run `pruebas` en success sobre el HEAD.
Cambio: solo esta entrada de registro. Pruebas: comparación de `completed_at` de `pruebas` con `merged_at`. Riesgos: ninguno.
