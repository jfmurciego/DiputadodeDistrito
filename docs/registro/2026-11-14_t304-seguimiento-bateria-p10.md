## 2026-11-14 — T-304 — Seguimiento de T-303: REUSE previo, poda sobre el paquete P10 y limpieza

**Causa.** Menores de la revisión de #759: REUSE se comprobaba después de ejecutar `ejecutar_fuentes_workflow`; `podar_r2.tiene_entrada` seguía exigiendo `bateria/entradas/<t>/`, que ya nada escribe (bloquearía la poda de M01-M03); `LISTA_PODA_R2.md` describía la entrada mínima retirada; el workflow subía `NACIONALES.json`, que ya no se genera.

**Cambio.** `bateria_motor.py` 1.4.1: antes de ejecutar nada, `resolve_source_action` con `official_available=False` (solo REUSE o BLOCK, nunca ACQUIRE); si no es REUSE, `FALLO_ADQUISICION` con `BATERIA_PAQUETE_P10_NO_REUTILIZABLE` sin ejecutar el ejecutor de fuentes ni M01-M03 (la comprobación posterior del log se conserva). `podar_r2.py` 1.1.0: `tiene_entrada` comprueba que el paquete P10 del territorio (`arc-e/paquetes-p10/<package_sha256>.zip`, `package_sha256` del contrato, id viejo o nuevo) existe en R2 con sha256; lista y reglas de borrado no cambian y la poda no se abre. `LISTA_PODA_R2.md` actualizado. `bateria-motor.yml` 1.2.1: sin `NACIONALES.json`. Copias en `legacy/`.

**Pruebas.** `tests.test_t298_espejo_ine` (paquete que la política no reutilizaría: nada se ejecuta; política sin fuente oficial; clave del paquete por contrato con id viejo y nuevo), `test_podar_r2`, `test_bateria_motor`, `test_workflow_safety`, `GovernanceHeaders`.

**Riesgos.** La poda ola 1 sigue sin ejecutarse: M01-M03 solo saldrán de un territorio cuando su paquete P10 esté archivado en R2.
