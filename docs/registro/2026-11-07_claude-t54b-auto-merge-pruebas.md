## 2026-11-07 — T-54b — La fusión automática exige `pruebas` en success sobre el HEAD exacto

Causa: `auto-merge.yml` 1.0.0 fusionó #453 (12 s después de crearse) y #454 (60 s) sin `pruebas`. Con el token de la app
ddd-registro, actor exento del ruleset `proteger-main`, la PR salía «clean» al instante y la rama «si ya está clean,
fusiona» se saltaba el check obligatorio. Cambio: `auto-merge.yml` 1.1.0 se dispara con `workflow_run` al terminar
«Pruebas de la Plataforma» en una PR, consulta el check-run `pruebas` del SHA exacto y solo fusiona (squash,
`--match-head-commit`) si está en success; pendiente o en failure no hace nada. Ya no activa el auto-merge nativo ni mira
`mergeable_state`, y ejecuta el código de `main`, nunca el de la PR. La decisión está en
`herramientas/decidir_auto_merge.py` 1.0.0 (PR abierta, no borrador, hacia `main`, del propio repositorio, sin
`no-automerge`, HEAD = SHA evaluado y último `pruebas` de ese SHA en success). Pruebas: `tests/test_auto_merge.py` (7:
pendiente → no fusiona; failure → no; success → fusiona; clean sin `pruebas` → no; exclusiones; forma del workflow).
