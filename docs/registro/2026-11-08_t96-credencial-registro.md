## 2026-11-08 — T-96 — Credencial de registro en los pushes PENDING/pre-M04 a main

**Causa.** Run 42463443610 (00 Congreso Ceuta): la 01 falla en «Persistir diagnóstico con el escritor concurrente común» con
`GH013 ... Required status check "veredicto" is expected` (PUSH_RETRY_EXHAUSTED). El ruleset `proteger-main` solo exime a admin y a la
app de registro (5568103); `generation_pending` empujaba con `github.token` (app 15368), sin «Credencial de registro».

**Cambio.** `preparacion-fuentes.yml` 1.4.10 y `_reutilizable-generacion-territorial.yml` 1.3.2: paso «Credencial de registro» tras el checkout de `generation_pending`.
`tests/test_credencial_registro.py` incluye `persistir_evidencia_pre_m04_operacional` entre los empujadores (antes no lo detectaba).
No se toca el ruleset ni los bypass.

**Auditoría** (workflow · job · credencial): preparacion-fuentes · generation_pending · github.token → corregido;
_reutilizable-generacion-territorial · pre_m04_evidence y pre_m04_diagnostic · github.token (corregido (autorizado por el Coordinador));
resto de pushers · app de registro.

**Pruebas.** `test_credencial_registro` falla antes (3 jobs) y pasa después; gobernanza de cabeceras en verde.
**Efecto.** Basta relanzar la 01/00 (modo «Ejecutar desde el principio»).
