## 2026-11-07 — T-54 — Fusión automática con `pruebas` en verde

Causa: el propietario activó «Allow auto-merge» y autorizó la fusión automática (07-11), pero GitHub solo deja activarlo
en una PR con checks pendientes y cada PR había que activarla o fusionarla a mano. Cambio: workflow nuevo «Fusión
automática» (`auto-merge.yml`, sin botón manual, `pull_request` hacia `main`): en toda PR no borrador del propio
repositorio activa el auto-merge (squash) ligado a su HEAD y, si ya está «clean», la fusiona directamente; con la
etiqueta `no-automerge` lo desactiva. Nunca usa `--admin`: el ruleset sigue exigiendo `pruebas` en verde. Usa el token
de la app de registro si están sus secretos, porque una fusión con `github.token` no dispara los workflows de push a
`main` (numeración del registro, pruebas en `main`). Skill `operador`: ya no fusiona a mano. Pruebas:
`tests/test_auto_merge.py` (4) y tests de workflows en verde.
