# Entradas del registro de cambios

Cada PR deja aquí su entrada, en un fichero propio y **sin número**:

- Nombre: `AAAA-MM-DD_<rama>.md`, con la rama en minúsculas y `/` cambiada por `-`
  (p. ej. `2026-11-08_claude-t48-revisor-ci.md`).
- Primera línea: `## AAAA-MM-DD — T-xx — título` (la misma fecha del nombre).
- Cuerpo: causa, cambio, pruebas y PR/run, como en las entradas históricas de `docs/REGISTRO_DE_CAMBIOS.md`.
- Sin `Versión:` ni cabecera `<!-- … -->`.

No se edita `docs/REGISTRO_DE_CAMBIOS.md` a mano. Al fusionar en `main`, el workflow «Numeración del Registro»
(`.github/workflows/numerar-registro.yml`, con la app de registro) asigna el número consecutivo, actualiza la cabecera
y el índice del registro y deja la copia anterior en `legacy/docs/`. La CI (`comprobar_guardian_main.py registro`)
comprueba el formato de las entradas y del índice. Para ver lo pendiente: `python herramientas/numerar_registro.py --comprobar`.
