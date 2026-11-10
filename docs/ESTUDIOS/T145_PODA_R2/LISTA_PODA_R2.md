# T-145 — Lista de poda de R2 (solo propuesta; no se ha borrado nada)

Fuente: `orchestracion/archivo_r2.json` (623 entradas, 28,06 GB, a 2026-11-09T23:15Z) y `orchestracion/publicaciones_visor.json`.
Ficheros: `ola1_borrar.csv` (lista exacta) y `conservar_estado_completo.csv`.

## (a) Qué es redundante
- **Composición del archivo:** 246 `ddd-state-*` (27,6 GB, 32 runs de 19 territorios, todos subidos el 2026-11-07 17h por el archivista 1.0, antes de T-72) y 377 paquetes mínimos/auditorías (0,16 GB).
- **Inclusión (por construcción):** cada etapa del workflow generador restaura el estado anterior (`cache/`, `run/`, `sources/`), añade lo suyo y sube todo (`_reutilizable-generacion-territorial.yml`, pasos «Restaurar estado contractual» y «Empaquetar checkpoint acumulado», cadena M01→M02→M03→M03U→M04…M08). Los tamaños crecen sin excepción dentro de cada run (p. ej. Aragón 85→85→85→85→87→207→210→213→213 MB). Por tanto M08 ⊇ M07 ⊇ … ⊇ M01 salvo ficheros sobrescritos entre etapas (p. ej. `CHAIN_STATE.json`): son versiones intermedias sin valor de archivo. **No verificable desde la nube** sin abrir los ZIP (ver «Comprobación»).
- **Mismo contenido entre runs:** ningún sha256 se repite (los ZIP llevan marcas de tiempo). El indicio de fuentes idénticas es el tamaño de M01 (Castilla y León 96/96 MB, Navarra 93/93, La Rioja 76/76, Madrid 87/87), pero no prueba contenido igual.
- **Vigente:** run más reciente por territorio y tipo (`canonical_m06`/`canonical_m08`) del visor. De los 32 runs con estado en R2, **12 son vigentes**; los otros 20 están superados. Todos menos uno tienen su producto en `ddd-minimo-<run>-M06/M08` (o declarado en `incluye_m06_run`) y auditoría.
- **Excepción sin cobertura:** `principado_de_asturias/40132061626` (vigente) **no tiene paquete mínimo**: su M08 solo existe en R2.

## (b) Regla de conservación propuesta
Por territorio se conserva:
1. Todos los `ddd-minimo-*` (M06/M08) y `ddd-audit-*` (0,16 GB): son el producto y su evidencia.
2. M01 + grafo M03 para la batería: no hace falta conservar estados, `bateria_motor.py entradas` (T-132) los regenera desde fuente con sha256 en 32 min para los 71 territorios; la entrada de Huesca ya está en `diagnostico/t132-entradas`.
3. El estado completo (etapa más alta) solo del run **vigente**, y solo mientras aporte algo que no esté en el paquete mínimo (checkpoints M04/M05, caché): ola 2, decisión del propietario.
4. Todo lo demás (etapas intermedias de cualquier run; todo el estado de runs superados con paquete mínimo) se borra.

## (c) Lista a borrar (ola 1)
`ola1_borrar.csv`: **234 claves, 26,085 GB** (clave, territorio, run, etapa, tamaño, sha256, motivo, copia que conserva).
- 89 claves M01…M07/M03/M03U de los 12 runs vigentes: incluidas en la etapa más alta del mismo run (que se conserva).
- 145 claves de los 20 runs superados: producto en su paquete mínimo; el resto, reconstruible (batería M01-M03; 00 «Generar desde fuente» M04-M08; objetivo del propietario 08-11: motor repetible, no conservar resultados antiguos).
- Tras la ola 1 quedan 389 claves, ~1,98 GB.

**Se conserva** (`conservar_estado_completo.csv`, 12 claves, 1,812 GB): etapa más alta de los 12 runs vigentes. Incluye Asturias 40132061626 (única copia del M08; no entra en ninguna ola).
**Ola 2 (opcional, propietario):** las 11 restantes de ese fichero (~1,76 GB) si se decide que checkpoints/caché son regenerables; dejaría ~0,2 GB. Asturias 40132061626 solo tras generar su paquete mínimo (requiere credenciales R2; subida, no solo lectura).

## (d) Nada irrecuperable en la lista
Se excluyó: lo que no tiene paquete mínimo (Asturias 40132061626), los paquetes mínimos y auditorías, y cualquier clave de un run vigente en su etapa más alta. Reconstruibilidad: M01-M03 = fuentes oficiales con sha256 (batería); M04-M08 = motor determinista por semilla y versión, relanzable con la 00 (coste de cómputo, no de datos). Verifica antes de borrar que cada clave del CSV sigue en R2 con ese sha256 y que la «copia que conserva» existe con el suyo.

## Comprobación opcional previa a la ola 1 (no lanzada)
Workflow manual `workflow_dispatch` de solo lectura, con `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`/`R2_ACCOUNT_ID`/`R2_BUCKET`: para un run por clase (p. ej. Aragón 40979465420, Asturias 40979477771, Galicia 41044499258) baja sus ZIP M01…M08, y por cada pareja consecutiva lista los ficheros con sha256 y comprueba que `lista(Mn) ⊆ lista(Mn+1)` salvo `run/CHAIN_STATE.json` y `compatibility/*`; escribe el informe a `$GITHUB_STEP_SUMMARY`. Sin `contents: write`, sin subir ni borrar. No se añade a `.github/workflows/` en esta PR (fichero compartido).

## (e) Que el origen deje de subir estados completos
**Ya está hecho:** desde el archivista 1.1.0 (T-72) `seleccionar` solo admite `es_final` (M06/M08) y `archivar` con `empaquetar_minimo` sube `ddd-minimo-*` en lugar del ZIP de estado; `archivo_origen.py r2` (1.0.1) hace lo mismo y `--sustituye-m06-run` retira el M06 cubierto por el M08. Las 246 claves de estado son todas del 2026-11-07 17h (versión 1.0); no hay ninguna posterior. Cambio residual propuesto (sin aplicar): en `cubierto_por_m08`/`seleccionar`, que el archivista tampoco suba el paquete mínimo M06 si el run tiene M08 vivo ni auditorías duplicadas (`ddd-audit-electoral`), y que `archivar-artefactos-r2.yml` imprima en el resumen el total de R2 y falle por encima de 8 GB (decisión del propietario, T-72b).

## Bloqueos
- Borrar y la comprobación de contenidos exigen credenciales R2 (Operador, con la frase del propietario y lista aprobada, PLAN §R2).
- Generar el paquete mínimo de Asturias 40132061626 también.

## Condición añadida por T-132 (PR #601)
La «entrada mínima» de la batería (`bateria/entradas/<territorio>/<huella>.zip`, solo `ENTRADAS.json` + M01 secciones + grafo M03; índice `bateria/ARCHIVO_ENTRADAS.json`) se extrae con `--desde-r2` de `ddd-state-<run>-M03` (luego M03U) del run más reciente de `archivo_r2.json`. Por tanto, **las claves M01/M02/M03/M03U de la ola 1 no se borran de un territorio hasta que su entrada mínima conste en `ARCHIVO_ENTRADAS.json`** (un territorio puede salir en la ola 1 en cuanto la tenga). Si falta, se conserva el M03 (o M03U) del run más reciente de ese territorio. Esto solo retrasa las filas M01-M03U (≈ 4/9 del tamaño de cada run), no el resto de la ola.

Solo se suben entradas reconstruidas desde fuente: los territorios cuyo M03 se reutiliza de R2 no tienen mínima y sus M01-M03U no se podan hasta que `archivar` suba también la mínima extraída de esos estados (cambio de T-132 propuesto, una línea).
