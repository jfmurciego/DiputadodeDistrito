## 2026-11-07 — T-54c — Fusión automática ligada a la suite de CI que la dispara; causa de #458

Causa (#458, T-65, fusionada a las 18:14:04 sin `pruebas`): no la fusionó la 1.1.0 sino la 1.0.0 de `auto-merge.yml`,
ejecutada por un `pull_request` de #458 a las 18:12:54 (30 s después de fusionarse #457) con una referencia de merge que
aún no incluía #457; activó el auto-merge nativo con el token de la app exenta del ruleset y GitHub fusionó sin
`pruebas`. El `pruebas` de su HEAD b833188c empezó a las 18:14:09 y acabó en failure: la 1.1.0 habría dado ESPERAR y
después NO. Ninguna otra PR abierta conserva un auto-merge nativo. Cambio: `auto-merge.yml` 1.2.0 solo actúa si el run
que lo dispara es de `pruebas-plataforma.yml` y pasa su `check_suite_id`; `decidir_auto_merge.py` 1.1.0 solo cuenta el
check-run `pruebas` de esa suite. Pruebas: `tests/test_auto_merge.py` con el caso real de #458 (sin `pruebas` a la hora
de la fusión → ESPERAR; el que llegó en failure → NO; un verde de otra suite no vale; sin disparador `pull_request` ni
auto-merge nativo).
