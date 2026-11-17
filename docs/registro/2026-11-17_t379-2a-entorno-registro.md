## 2026-11-17 — T-379 — PR 2a: secretos de la app de registro en entornos limitados a main (D-147, opción a; D-162, opción A)

- **Causa.** Los secretos `DDD_REGISTRO_APP_ID`/`KEY` son del repositorio: cualquier rama lanzada por la API los lee y puede escribir en
  `main` con la app (exenta del ruleset). La regla «una validación desde la rama no escribe en `main`» (diseño T-378 §10) era solo norma del
  código revisado.
- **Cambio.** Los 25 jobs que usan la app (inventario de §10 sobre `main` e7747ea, 9 ficheros: P10, P20, P30, P40, P70, P90, auto-merge, la 00 y
  Legislatura) declaran un entorno con los secretos: `registro` en 22; el `manifestar` de la 00, que corre en el humo de las PR, lo lleva solo
  fuera de `pull_request`. D-162 (opción A, tras el revisor): los jobs que ya tenían entorno NO se parten (partirlos rompía la atomicidad entre
  despliegue o borrado y registro): P40 `publicar` sigue en `github-pages` y P70 `podar` en `produccion` (sin entorno en simulación, sin
  registro); P40 `preparar` usa `produccion` para personas (T-41, misma condición) y `registro` para robots (antes, sin entorno). Por eso los
  secretos van también a `github-pages` y `produccion`. VERSIÓN de los 9 ficheros subida, con copia en `legacy/workflows/*_20261117.yml`.
- **Efectos.** Hasta mover los secretos, nada cambia en `main` (un entorno sin secretos deja ver los del repositorio). Después, toda 00 o P10-P30
  lanzada desde una rama ≠ `main` falla en los jobs con la app (en la 00: `actualizar_estado` y `manifestar`), como pide §10. Los tres entornos
  deben existir con su regla de ramas ANTES de fusionar: si no, GitHub crea el entorno sin regla y la garantía es nula.
- **Pruebas.** `tests/test_t379_2a_entorno_registro.py`: copias congeladas con sha256 y `deshacer(actual) == anterior` en los 9 ficheros; todo
  job con la app con un entorno de la lista; inventario de 25; ningún job con `registro` en una PR; P40/P70 sin jobs nuevos y con sus grupos;
  controles negativos. Las equivalencias T-368/T-372/T-375/T-376/T-377/T-332 comparan contra la versión sin la 2a (`tests/_t379_2a.py`).
- **No probado sin Actions.** Secretos de entorno en un job de un reutilizable llamado con `secrets: inherit`; rechazo desde una ref ≠ main.
