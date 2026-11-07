---
paths:
  - ".github/workflows/**"
  - ".dockerignore"
  - "Dockerfile"
---

# Workflows y CI

- Los workflows son compartidos: avisa a la otra sesión antes de tocarlos. Cabecera VERSIÓN y copia en
  `legacy/workflows/<nombre>_v<anterior>.yml`.
- Los nombres visibles y la lista de workflows con `workflow_dispatch` están fijados en
  `tests/test_design_a_catalogo.py` y `tests/test_design_a_matriz_sintetica.py` (diseño A); `pruebas-plataforma.yml`
  no puede tener botón manual (`tests/test_workflow_safety.py`). Todo bloque `run:` pasa `bash -n`.
- El ruleset de `main` solo exige el job `pruebas`. «Require branches to be up to date» bloquearía toda PR mientras
  haya 00 registrando; exigir PR en `main` rechaza los registros de los robots (`GH013`).
- `Duplicate header: "Authorization"` (HTTP 400): credencial de registro mal combinada con actions/checkout; checkout
  v6+ guarda su token en un include (`includeIf.gitdir:`), no en `http.extraheader`; hay que quitar ambos (#381→#386).
- La imagen Docker de CI excluye `legacy/` salvo lo declarado en `.dockerignore`. Si un test lee una copia de
  `legacy/`, añádela allí o el test no debe depender de ella.
- Una fusión o un push con `github.token` no dispara los workflows de push a `main` (numeración, pruebas en main): usa el
  token de la app de registro.
- Un job solo admite un `environment`: la puerta humana va en el job previo (no en `_reutilizable-publicar-sitio`, que
  ya usa github-pages). En los reutilizables, `github.workflow` es el del caller (evita un segundo clic).
  `environment: ${{ cond && 'produccion' || '' }}` evita la espera en los bots.
- Al fusionar `main`, los ficheros añadidos en las dos ramas dan conflicto AA: toma el de `main` y reaplica.
- Los clientes de la API de GitHub y de R2 llevan reintentos con backoff ante 5xx.
- Workflow nuevo con push a `main`: «Credencial de registro» justo tras el checkout y `concurrency` con `queue: max`
  (tests `test_credencial_registro` y `test_operational_concurrency_gerrychain50`).
- Un workflow manual nuevo va también en las listas de `test_design_a_matriz_sintetica` y
  `test_codauto_preparation_contract` (causa del rojo de #458).
- Nunca auto-merge nativo ni decidir por `mergeable_state` con actores exentos del ruleset (app ddd-registro): fusiona sin
  los checks obligatorios y la PR sale «clean» al instante (#453, #454).
- Un evento `pull_request` ejecuta el workflow de la referencia de merge de la PR: justo tras cambiar un workflow en `main`,
  una PR con la referencia vieja ejecuta la versión anterior (#458 la fusionó la 1.0.0 30 s después de entrar la 1.1.0).
- Fusión segura: `workflow_run` al terminar `pruebas-plataforma`; check-run `pruebas` del SHA exacto y de la check_suite
  que dispara (`workflow_run.check_suite_id`); `--match-head-commit` (#457, #460).
- `dashboard/index.html` y `publicado/dashboard/index.html` deben ser idénticos; el publicador copia cada página enlazada (#459, #451).