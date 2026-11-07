---
paths:
  - "docs/REGISTRO_DE_CAMBIOS.md"
  - "docs/registro/**"
  - "docs/PLAN.md"
  - "legacy/docs/REGISTRO_DE_CAMBIOS_*"
---

# Registro de cambios y plan

- Desde T-46 (registro 1.0.105, la última con número manual) nadie edita `docs/REGISTRO_DE_CAMBIOS.md`: cada PR
  añade su entrada en `docs/registro/AAAA-MM-DD_<rama>.md`, sin número (formato en `docs/registro/README.md`):
  `## AAAA-MM-DD — T-xx — título` y causa, cambio, pruebas y PR/run.
- Al fusionar en `main`, el workflow «Numeración del Registro» (`numerar-registro.yml`, app de registro) asigna el
  número consecutivo, reescribe la cabecera (`Versión` = `Anterior` + 1, copia en `legacy/docs/`) y el índice.
  La CI (`comprobar_guardian_main.py registro`) comprueba la cabecera, el formato de las entradas y el índice.
- Ya no se pide número al planificador; dos PR abiertas no chocan en el registro.
- Tras rebasar o fusionar `main`, busca marcas de conflicto (`<<<<<<<`, `>>>>>>>`): rompieron `main` en #422.
  La CI (`comprobar_guardian_main.py marcas`) y el hook de commit las bloquean.
- `docs/PLAN.md` solo lo edita el planificador.
