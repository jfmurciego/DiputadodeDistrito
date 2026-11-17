## 2026-11-17 — T-397b — Workflows sin botón con «_» al principio (D-159)

**Causa.** D-159: los workflows sin botón deben salir al final de la lista de Actions.
**Cambio.** Solo `name:`: `revisor-pr.yml` 1.1.2 «_P90 Automático — Revisor de PR»; `activacion-por-eleccion.yml` 1.1.3 «_P00 Campaña — Elección» (solo se lanza por API desde el Gestor, no desde botón). Copias en `legacy/workflows/`. **Pendiente:** `auto-merge.yml` y `preparacion-legislatura-vigente.yml` (turno exclusivo de T-379 2a, #888): siguiente PR tras fusionarla. Los 9 con botón y «P90 Automático» no cambian. Las 3 `_reutilizable-*` siguen «Interno · P<n>0»: las fija `test_corte_5_0_0_equivalencias` y no se ven como botón; declarado en el test.
**Comprobado (grep).** `workflow_run.workflows` apunta a «P90 Automático» y «P00 Campaña» (intactos); los lanzamientos usan el nombre de fichero (`.../workflows/<f>.yml/dispatches`), no el visible; `generar_equivalencias_5_0_0.py` y dos tests ajustados al «_».
**Prueba.** `tests/test_t397_nombres_workflows.py` (con botón «P…», sin botón «_P…», control negativo, `P90 Automático` intacto).
**Riesgos.** Ninguno de lógica. El historial previo queda bajo el nombre viejo.
