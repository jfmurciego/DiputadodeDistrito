## 2026-11-17 — T-379 — PR 2a: entorno `registro` para la app de registro (D-147, opción a)

- **Causa.** Los secretos `DDD_REGISTRO_APP_ID`/`KEY` son del repositorio: cualquier rama lanzada por la API los lee y puede escribir en
  `main` con la app (exenta del ruleset). La regla «una validación desde la rama no escribe en `main`» (diseño T-378 §10) era solo norma del
  código revisado.
- **Cambio.** Los 25 jobs que usan la app (inventario de §10 sobre `main` e7747ea, 9 ficheros: P10, P20, P30, P40, P70, P90, auto-merge, la 00 y
  Legislatura) declaran `environment: registro`. El `manifestar` de la 00, que corre en el humo de las PR, lo lleva solo fuera de `pull_request`.
  Un job admite un solo entorno, así que se parten los que ya tenían uno: P40 `aprobar` (puerta `produccion`, misma condición T-41) → `preparar`
  (registro); P40 `publicar` (github-pages) deja el parche del commit del registro como artefacto de 1 día y el job nuevo `registrar` lo aplica
  y empuja con los mismos reintentos (exit 48); P70 `podar` (produccion, ahora `contents: read`) → `registrar_poda` (registro), desde el
  artefacto del informe y la misma base. VERSIÓN de los 9 ficheros subida, con copia en `legacy/workflows/*_20261117.yml`.
- **Sin efecto hasta mover los secretos.** Con los secretos aún en el repositorio, un job con entorno sin secretos los lee igual. Pasos del
  propietario: crear `registro` (sin revisores ni temporizador, ramas de despliegue = `main`) antes de fusionar; copiar los dos secretos al
  entorno; humo real verde (incluido un reutilizable llamado); solo después borrar los del repositorio (§16.3).
- **Pruebas.** `tests/test_t379_2a_entorno_registro.py`: copias congeladas con sha256 y `deshacer(actual) == anterior` en los 9 ficheros; todo
  job con la app con `registro`; inventario de 25; ningún job con `registro` en una PR; jobs partidos de P40/P70; controles negativos.
  `test_t372_p40_equivalencia` y `test_t368_p70_equivalencia` comparan contra la versión sin la 2a (`tests/_t379_2a.py`).
- **No probado sin Actions.** Secretos de entorno en un job de un reutilizable llamado con `secrets: inherit`; rechazo desde una ref ≠ main;
  salidas de un job `podar` fallido a medias hacia `registrar_poda`; parche binario de P40 aplicado con `git am`.
