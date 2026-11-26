## 2026-11-26 — T-505 — Squash sin «Co-authored-by» y guarda en el guardián

**Causa.** En las sesiones cloud git usa `user.email=noreply@anthropic.com`; `gh pr merge --squash` sin cuerpo deja que GitHub añada
«Co-authored-by» por cada autor distinto del que fusiona (#1018, #1019, #1026, #1028). Las fusiones REST con `commit_message` vacío no lo llevan.

**Cambio.** `auto-merge.yml` 1.3.4: fusiona por `PUT pulls/<n>/merge` (squash, `sha` = HEAD evaluado) con `commit_title` «<título> (#n)» y
`commit_message` vacío. `comprobar_guardian_main.py` 1.2.0: comprobación `coautores` (base..head); `p90-automatico.yml` 1.5.4 la ejecuta en el job
`guardian` de las PR. Copias en `legacy/`.

**Pruebas.** `tests/test_auto_merge.py`, `tests/test_comprobar_guardian_main.py` (`Coautores`), `tests/test_t366_p90_equivalencia.py` (ajustado a la nueva orden de fusión),
`test_t220_renombrado`, `GovernanceHeaders`, `comprobar_guardian_main.py todo`.

**Riesgos.** Toca el mecanismo de fusión: PR con `no-automerge`, la fusiona el propietario. A partir de ella, una PR con esas líneas en algún commit
falla el guardián (hay que reescribir el mensaje). Sin efecto en checkpoints ni huellas.
