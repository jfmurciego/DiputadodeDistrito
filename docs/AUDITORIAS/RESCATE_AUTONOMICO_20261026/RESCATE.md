# Rescate del checkout autonómico del 26-10-2026

Versión: 1.0.0. Fecha: 2026-10-28. Estado: trabajo recuperado; candidato sin integrar ni certificar.
Alcance: conservación exacta de trabajo perdido de Codex; no se desarrolla una corrección nueva. Origen: expediente nuevo, sin predecesor.
Cambios y motivo: recuperar 49 archivos sin commit del checkout aislado identificado por las sesiones originales y conservar su autoría, pruebas y límites.

## Localización y procedencia

Original: `/private/tmp/DDD_ejecutor_C_20261026`, rama `codex/ejecutor-c-territorial-20261026`, HEAD `43e0bc48f04b2ecf45af3b4981f43978fea415b8` (el SHA íntegro autoritativo está en manifest_recuperado.json). No estaba en DDD-distritos-autonomicos ni en su rama de rescate del 27-10. El original y su índice se mantienen sin cambios.

La sesión principal es `/Users/macbookpro/.codex/sessions/2026/10/26/rollout-2026-10-26T21-20-09-01a179de-d696-7051-a1d7-4d1ea2c43c9a.jsonl`. Su cwd inicial era el frente nacional, pero a las **20:21:29.490 UTC** ejecutó:

```sh
git worktree add -b codex/ejecutor-c-territorial-20261026 /private/tmp/DDD_ejecutor_C_20261026 origin/main
```

La misma sesión terminó a las **22:26:50.381 UTC**, línea 676, con `usage_limit_exceeded`. El revisor de aquella ejecución, sesión `rollout-2026-10-26T23-23-40-01a17a4f-e989-7121-9ced-d8f96e740cd2.jsonl`, quedó interrumpido a las **22:26:49.810 UTC**, línea 346. La sesión auxiliar `rollout-2026-10-26T21-23-13-01a179e1-a682-7522-a69e-e83eda5d27b4.jsonl` registra Tremp/Murcia. `sesiones_y_comandos.json` conserva rutas, hashes locales de los registros y comandos exactos seleccionados. La hora local del nombre del rollout no es su hora UTC.

Copia de rescate: `/private/tmp/DDD_rescate_autonomico_20261026`, rama **`rescate/autonomico-20261026`**, desde la misma base 43e0bc48. Solo se copian los 49 archivos cambiados o nuevos de aquel trabajo: **495.287 bytes**, máximo **72.172 bytes**. Ninguno supera 50 MB; no se incorporan inputs, cachés, resultados, bases originales, entornos ni carpetas de datos. Los tres pequeños fixtures de grafo y el fixture geométrico son parte de las regresiones recuperadas.

Se preserva también el trabajo auxiliar de Andalucía/Comunidad Valenciana y sus predecesores que coexistía en ese mismo checkout; está identificado en el manifiesto, sin atribuirle nueva validación ni aprobación. No se seleccionaron únicamente hunks que aparentaran funcionar: el rescate conserva el estado exacto encontrado. No se altera ningún motor o contrato adicional durante el rescate.

## Arreglos recuperados y líneas de la copia

| Territorio | Cambio encontrado | Archivos y líneas |
|---|---|---|
| Canarias — La Laguna, 38023 | Reconsideración del número de núcleos cerrados: de 2 a 3 cuando falla la primera búsqueda; preserva el residuo, gateways, cardinalidad y límites. El fixture del run 40241596981 contiene 113 secciones y 159.576 habitantes. | `ddd_core/m04_seed_engine_v7410.py`:180–219 (`_sequential_count`, `split_sequential`); regresión `tests/test_m04_residual_cardinality.py`:14–30. |
| Cataluña — Tremp, 25234 | Agrupa municipios completos mediante adyacencia física, previa acreditación administrativa y vínculo de fuente. Talarn 25215 conecta las cinco secciones de Tremp: seis secciones, 6.597 habitantes, sin añadir aristas ni convertir el contacto puntual en frontera. | `ddd_core/m04_administrative_atomic_groups.py`:35–143; integración `ddd_core/m04_seed_engine_v7410.py`:262–287; regresión `tests/test_m04_administrative_atomic_groups.py`:75–93. |
| Ceuta — fallo rango [5812.32, 5813.64] | Recupera la partición conexa demostrada por la búsqueda exacta y la entrega como solución ejecutable a Formación inicial; además reserva unidades para los distritos pendientes. El rango citado es el fallo antiguo, no una nueva tolerancia. | `ddd_core/m04_seed_engine.py`:220–292, 413–440 y 519–541; cardinalidad en `ddd_core/m04_seed_engine_v7410.py`:64–122; regresión `tests/test_m04_residual_cardinality.py`:32–53. |
| Región de Murcia — Yecla–Jumilla | Cambia M02 a EPSG:25830, conservando el umbral de 1 m², frontera mínima 1 m, buffer/simplify cero. Recupera las dos fronteras reales que EPSG:3035 convertía en falsos solapamientos. | `territorios/region_de_murcia/config/region_de_murcia_2025.yaml`:102; regresión `tests/test_murcia_m02_native_crs.py`:25–47; fixture y procedencia `tests/fixtures/murcia_m02_native_crs/`. |

Murcia: el expediente anterior conserva el replay M03 de 1.223 nodos, 3.420 aristas y un componente, frente a [1192,31]. Fuentes y logs completos siguen en `/private/tmp/ddd-c-evidence/`; no se incorporan los ZIP ni datasets al rescate. Esta ejecución vuelve a probar los dos contactos mínimos, no repite el replay territorial completo.

## Búsqueda efectuada y límites

Se inició en `/Users/macbookpro/Desarrollo`. Se inspeccionaron `git worktree list`, `git stash list` y `git log --all --since/--until` del repositorio común DiputadodeDistrito, y estados dirigidos de los checkouts aislados M05, Ejecutor C y el worktree de Codex d6b1. El stash común estaba vacío. Los commits del 26-10 no contenían este incremento: permanecía staged/unstaged/untracked en Ejecutor C.

Se recorrieron `/Users/macbookpro/Desarrollo`, `/private/tmp`, `/private/var/folders` y `~/.codex`: 547 candidatos con marcador .git y 2.499 textos modificados el 26-10 con coincidencias. `busqueda_local.json` conserva rutas, criterios y 166 errores de acceso. No se afirma que esos 547 marcadores sean repositorios válidos ni que todos se auditaran con Git. Se excluyeron dependencias, cachés y textos de más de 2 MB; las sesiones se leyeron expresamente por separado. Los accesos denegados no afectan al hallazgo positivo verificado por sesiones y bytes. No se borró nada.

## Verificación del rescate

`manifest_recuperado.json` fija los 49 SHA/tamaños. `original_status.txt`, `original_index_diff.patch` y `original_worktree_diff.patch` conservan incluso la separación staged/unstaged. La copia es byte por byte; no se ha completado ni corregido la implementación recuperada.

Regresiones reejecutadas en el mismo entorno GIS existente usado originalmente:

```sh
/Users/macbookpro/Desarrollo/DDD-control/planes/f10-compatibilidad-interanual-20261012/venv/bin/python -m unittest tests.test_m04_residual_cardinality tests.test_m04_administrative_atomic_groups tests.test_murcia_m02_native_crs
```

Resultado: **14 pruebas PASS**, en 9,136 segundos; `git diff --check` PASS sobre el código recuperado. Tras añadir los parches de conservación, la comprobación staged solo avisa de los espacios de contexto propios del formato diff en esos dos `.patch`; se preservan literalmente para mantener su identidad. `git diff --cached --check -- . ':!docs/AUDITORIAS/RESCATE_AUTONOMICO_20261026/*.patch'` PASS. El primer intento con Python de sistema falló por ausencia de geopandas, registrado aparte; no se instalaron dependencias. Los logs originales antes/después quedan preservados, pero no se presentan como pruebas nuevas. No se ejecutó producción territorial, CI, promoción ni certificación.

La revisión separada de conservación verifica identidad de la copia y límites; no equivale a aprobar la implementación para integración ni a demostrar que los cuatro territorios completos ya generen. El SHA del commit y la confirmación del push se informan en la entrega externa para evitar un documento que se autorreferencie.
