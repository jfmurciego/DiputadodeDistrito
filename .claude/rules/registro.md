---
paths:
  - "docs/REGISTRO_DE_CAMBIOS.md"
  - "docs/PLAN.md"
  - "legacy/docs/REGISTRO_DE_CAMBIOS_*"
---

# Registro de cambios y plan

- El número de `docs/REGISTRO_DE_CAMBIOS.md` lo asigna el planificador: pregunta el último antes de añadir entradas.
- Cabecera: `Versión` = la de `Anterior` + 1 en el último componente; `Anterior` apunta a la copia en
  `legacy/docs/REGISTRO_DE_CAMBIOS_v<anterior>_<tarea>_<AAAAMMDD>.md`, que debe existir y tener esa versión.
  Lo comprueba la CI: `python herramientas/comprobar_guardian_main.py registro`.
- Entradas nuevas arriba: `## AAAA-MM-DD — T-xx — título`, con causa, cambio, pruebas y PR/run.
- Tras rebasar o fusionar `main`, busca marcas de conflicto (`<<<<<<<`, `>>>>>>>`): rompieron `main` en #422.
  La CI (`comprobar_guardian_main.py marcas`) y el hook de commit las bloquean.
- `docs/PLAN.md` solo lo edita el planificador.
