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
