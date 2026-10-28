# M05: búsqueda ampliada y experimento de Madrid

**Versión:** 1.0.0 — 2026-10-09  
**Estado:** EXPERIMENTAL / INCOMPLETO; no apto para integración  
**Alcance:** evaluación local de una búsqueda genérica M05 ante violaciones poblacionales duras.  
**Cambios/motivo:** registra el comportamiento del candidato v1.7.0 y sus límites observados en el checkpoint auténtico de Madrid.  
**Predecesor:** documento nuevo; no existe versión anterior.

## Evidencia de entrada y referencia

- HEAD de referencia: `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`.
- Run: `37325328346`; checkpoint M05: `11353290857`.
- SHA-256 del ZIP M05: `6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c`.
- Partición M05: 135 distritos, 4.479 unidades/secciones y 6.871.903 habitantes.
- Distrito 110: 17.401 habitantes; firma dura inicial `(1, 23321)`.
- Se decodificó mediante `herramientas/repro_reparador_rioja_cantabria.py`; el decodificador verificó el SHA-256 antes de exponer asignaciones, unidades y grafo.

La revisión independiente de Work acredita una secuencia experimental distinta del motor: 82 transferencias, distrito 110 en 59.654 habitantes y `hard=0`. La tolerancia fina pasó de 18 a 25 distritos fuera de banda. Esa secuencia demuestra factibilidad, pero no se codificó ni se usó como semilla de la búsqueda.

## Comportamiento del candidato

El candidato v1.7.0 activa la búsqueda ampliada solo cuando la reparación original deja infracciones duras. Usa transferencias unitarias, validación existente de provincia, municipio, contigüidad del donante y firma dura monotónica, respeta unidades urbanas congeladas, y devuelve estados `REPAIRED`, `EXHAUSTED` o `INCONCLUSIVE` con límites y telemetría. Las claves de estado compactadas reducen el consumo de memoria. Los resultados siguientes no prueban imposibilidad; las ejecuciones con poda son inconclusas.

| Límite experimental | Estados generados / expandidos | Profundidad máxima | Poda | Memoria trazada | Resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| 90 s, beam 4 por distrito, versión inicial | 13.797 / 309 | — | 13.445 | 260,7 MiB | INCONCLUSIVE por tiempo; firma dura sin cambio |
| 120 s, beam 2, claves compactadas | 57.941 / 1.821 | 33 | 54.542 | 58,8 MiB | INCONCLUSIVE por tiempo; firma dura sin cambio |
| 300 s, 200.000 estados, beam 2 | 125.287 / 4.461 | 74 | 120.612 | 117,6 MiB | INCONCLUSIVE por tiempo; firma dura sin cambio |
| 600 s, 300.000 estados, beam 2 | 166.661 / 6.212 | 100 | 160.450 | 152,4 MiB | INCONCLUSIVE: frontera retenida agotada tras poda |

En la última corrida, el límite de tiempo configurado fue 600 s; la frontera retenida terminó a los 499,8 s. Hubo poda de estados, por lo que el vaciado de esa frontera no constituye agotamiento exhaustivo del espacio de búsqueda. La firma dura permaneció `(1, 23321)`. El motor devolvió la mejor mejora secundaria de la fase original: 18 fuera de tolerancia y desviación total relativa de 10,24359 frente a 10,25117 antes. No alcanzó la reparación dura ni la secuencia experimental de 82 movimientos.

El candidato todavía no cumple el criterio mínimo de aceptación en Madrid. La siguiente revisión debe mejorar la política de selección de estados o la exploración de cadenas preparatorias y volver a probar el checkpoint auténtico. No debe declararse imposible la reparación.

## Regresiones y límites

- `tests.test_m05_population_repair`: 27 PASS.
- `tests.test_m05_auto_population_repair`: 6 PASS.
- Ocho pruebas estructurales y de obstrucción reutilizadas de `tests.test_repro_reparador_rioja_cantabria`: PASS.
- Replay directo de la partición Rioja con el motor actual: asignaciones conservadas y firma dura `(0, 0)`.
- Checkpoint Cantabria M06 reutilizado: SHA verificado y decodificación consistente, 460 secciones y 115 unidades. El expediente existente no ejecuta una nueva reparación M05 para Cantabria.
- El replay histórico exacto de Rioja está ligado al SHA previo del motor y rechaza correctamente el código cambiado con `REPAIR_CODE_DIFFERS_FROM_RUN`; no se alteró ese control ni la evidencia histórica.
- `git diff --check`: PASS.

No se ejecutaron `00`, workflows, M04 productivo ni publicación. No se creó commit ni PR. El estado local queda como candidato experimental incompleto, pendiente de decisión de Work y de revisión independiente.
