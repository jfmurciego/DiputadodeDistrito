# A2 — corrección del descarte de estados preparatorios en M05

**Fecha:** 2026-10-10  
**Estado:** `INCONCLUSIVE`; no cumple `hard=1 → hard=0`; pendiente de revisión independiente.  
**Dictamen de A2:** no declarar `DONE_REVIEW`.

## Identidad y evidencias preservadas

- Repositorio/HEAD de partida: `jfmurciego/DiputadodeDistrito`, `42163cd8cebd120db9ab9fd1329c32ccdd87cf36` (`codex/distritos-autonomicos`).
- Implementación A2 previa preservada byte por byte en `legacy/core/m05_population_repair_v1.7.0_2026-10-09.py`, SHA-256 `6d0c70b27bad3cd02d0ffef66af891969d3bbfce31025dc01f86c9d30571336b`.
- Código candidato v1.8.0: `ddd_core/m05_population_repair.py`, SHA-256 `19cbcffd70268f7eebfb75cb625bbea29bd66fade4d5a78ea819a0da91e1f2c8`.
- Test actualizado: `tests/test_m05_population_repair.py`, SHA-256 `57d8c7faa88fdc606cdda99f64b084e3f81741aef7bc2df7aa9a0d5c36ad4e52`.
- Checkpoint auténtico: `/Users/macbookpro/Downloads/artifact-11353290857.zip`, SHA-256 `6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c`.
- Testigo previamente validado: `/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/solucion_validada.json`, SHA-256 `6e832b1c6f35891d104f04ffdeedcb1fd7c7481a3598015b42aaf43f61d6091a`.
- Salidas completas v1.7 y v1.8: `benchmark_madrid_v17.json`, `benchmark_madrid_v18.json`. La traza controlada del quinto prefijo y los scripts usados están en este directorio. Se conserva la investigación original en `docs/AUDITORIAS/NACHO_2026-10-10/` y sus expedientes relacionados; no se reescribieron.

## Causa comprobada

El quinto movimiento del testigo (`28:28003:M`, distrito 91 → 125) sí se genera desde el padre ya expandido. No falla admisión de transferencia y no es una colisión de deduplicación. La implementación v1.7 ordenaba todo el lote por ranking poblacional y retenía solo el beam global; la selección perdía este prefijo preparatorio entre miles de candidatos con el mismo hard `(1, 23321)`. El hijo tenía posición 577/4.127 frente a un beam de 128. La rama de búsqueda también contempla que un estado nunca se expanda: si queda fuera de la frontera seleccionada, no generará sus movimientos descendientes.

En el replay del estado real con v1.8, la quinta selección encontró el prefijo dentro de 4.902 candidatos, todos con hard `(1, 23321)`, y lo conservó (`selected_target=true`). En esta ejecución el ranking observado fue 1.066; el orden de candidatos varía al cambiar la frontera de generaciones previas. El expediente `traza_seleccion_quinto_prefijo.json` contiene la salida completa.

## Diferencia aplicada

`_select_expanded_frontier` conserva la mitad superior del ranking existente y reserva el resto del ancho ya autorizado para la mejor continuación por padre que repite el handoff donante/receptor previo. Los padres se recorren en orden determinista de frontera; las plazas no usadas vuelven al ranking global. El ancho máximo no aumenta, el estado continúa sujeto a deduplicación y cada transferencia sigue validándose con las restricciones territoriales existentes. La firma hard temporal puede permanecer igual o no mejorar; solo una asignación completa que supera `_verify_final_constraints` con hard cero se devuelve como `REPAIRED`.

La lógica está en `ddd_core/m05_population_repair.py:342`; la detección de hard cero y la verificación final están alrededor de las líneas 667 y 757–758. Regresiones añadidas: cadena sintética con movimiento preparatorio (`tests/test_m05_population_repair.py:143`), condición histórica del quinto hijo en beam controlado (`:163`), repetibilidad con semilla fija (`:192`) y límites de hard final en las pruebas de reparación.

## Benchmark reproducible de Madrid

Arranque utilizado (Python 3.11 del entorno; no ejecuta workflows ni campañas):

```sh
python3 docs/AUDITORIAS/M05_A2_2026-10-10/reproducir_benchmark.py
```

El script importa el decodificador autenticado de `/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/madrid110.py` y el checkpoint de la ruta declarada. Límites idénticos al ensayo A2 anterior: 180 s, 640 MiB, 400.000 estados, 400.000 intentos de candidato, profundidad 96, radio 8 y beam 128 (2 por distrito antes del tope global). Sin cambios de contrato ni de datos.

| Métrica | A2 previa v1.7 | v1.8 candidata |
|---|---:|---:|
| Resultado / terminación | `INCONCLUSIVE` / presupuesto de candidatos | `INCONCLUSIVE` / presupuesto de candidatos |
| Hard inicial → final | `(1, 23321) → (1, 23321)` | `(1, 23321) → (1, 23321)` |
| Hard violations finales | 1 | 1 |
| Distritos fuera de ±12 % | 18 | 18 |
| Candidatos intentados | 400.000 | 400.000 |
| Estados únicos nuevos | 40.433 | 46.126 |
| Estados expandidos | 1.328 | 1.326 |
| Estados seleccionados acumulados / pendientes | campo no medido | 1.329 / 4 |
| Estados deduplicados | campo no medido | 11.514 |
| Estados descartados por beam/ola incompleta | 36.291 (telemetría anterior) | 44.797 |
| Profundidad alcanzada | 11 | 11 |
| Tiempo de búsqueda | 104,44 s | 101,42 s (101,68 s wall) |
| Pico memoria trazada | 49,249 MiB | 57,610 MiB |
| Pico RSS proceso (macOS) | no registrado | 170.311.680 bytes (~162,4 MiB) |
| CPU proceso | no registrado | 99,99 s |

El número secundario de outliers no cambia; no es el criterio principal. La búsqueda mejoró la cobertura y seleccionó el prefijo concreto, pero volvió a agotar el presupuesto antes de expandirlo hasta una solución: la siguiente limitación causal acreditada es la cobertura de la frontera bajo 400.000 intentos. La solución validada de 82 movimientos acredita que existe una ruta, no que el reparador corregido la encuentre. No se aumentan límites ni se reutiliza el testigo como solución del benchmark.

El candidato final no incorpora reparaciones parciales: `steps=[]`, `hard_limits_met=false`, `outcome=INCONCLUSIVE`. Las comprobaciones estructurales notificadas por el decodificador pasan; la infracción dura permanece y por ello el estado no se certifica como reparado.

## Pruebas y límites de validación

- `python3 -m unittest tests.test_m05_population_repair -q`: 31 pruebas, PASS.
- La prueba sintética acredita que el movimiento preparatorio deja el hard temporal en 1 y permite alcanzar hard 0; la última asignación pasa verificación de límites duros.
- La reproducción determinista compara asignación, pasos y contadores con semilla fija; excluye tiempo y memoria, que son observables variables.
- `tests.test_repro_reparador_rioja_cantabria`: la suite exacta no puede pasar su replay porque el harness aborta con `REPAIR_CODE_DIFFERS_FROM_RUN` al exigir identidad de código del run histórico. Como comprobación funcional separada, ejecuté el fixture La Rioja con el código actual y `max_depth=0`, aislando únicamente esa guarda de identidad en memoria: `NO_FEASIBLE_REPAIR_FOUND`, `QUEUE_EMPTY`, cero reparaciones, asignación idéntica, estructura válida y distritos congelados preservados. No se cambió el harness, la identidad histórica ni el contrato.
- `tests.test_m05_auto_population_repair`: no se pudo importar porque falta `geopandas` en el Python del entorno. No se instaló ninguna dependencia.
- La revisión independiente de este cambio está solicitada y pendiente. No se declara integración, publicación ni commit.

## Siguiente paso acotado

La selección arregla la pérdida sistemática del quinto prefijo, pero el ensayo termina con hard 1 por agotamiento de intentos y no cumple A2. El siguiente análisis debe aislar por qué la nueva ruta seleccionada no llega a expandirse hasta el siguiente handoff bajo el límite vigente; cualquier cambio adicional debe mantener iguales datos, contratos y presupuestos y volver a demostrar hard cero. No se reabre la investigación territorial ni se propone aumentar la búsqueda.
