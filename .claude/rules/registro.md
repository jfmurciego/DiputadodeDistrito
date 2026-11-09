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
- Una PR de rama larga (#441, #462) trae commits previos al squash de sus ancestras: add/add masivos. Resuélvelos con la
  versión de la RAMA si contiene el HEAD fusionado (`git merge-base --is-ancestor`).
- Un `git revert` de una PR con entrada de registro ya numerada borra la entrada y el guardian falla (el índice la
  referencia): restaura la entrada (`git checkout <commit> -- docs/registro/<fichero>`).

## Lecciones 08-11 (Coordinador)
- La primera línea de cada `docs/registro/*.md` debe ser «## AAAA-MM-DD — T-xx — título»; si no, el guardián falla.
- El hook `guardia_git` no frena `git commit -am` encadenado tras un merge: comprueba `git status` (marcas de conflicto) antes de commitear.
- Los ids T-xx los da solo el Planificador: el Coordinador reutilizó ids dos veces; pídelo antes de crear tarea.
- Una PR de plan con base vieja cae en `pruebas`: fusiona `origin/main` antes de pedir la fusión.
- Reproducir en local una PR de otro chat: un cambio solo local (rama sin empujar) se pierde al archivar el chat (T-91b); empuja o deja PR.
