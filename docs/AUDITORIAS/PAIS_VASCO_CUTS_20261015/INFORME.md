# País Vasco — PV-CUT-01

**Estado:** `NEGATIVE_BOUNDED` para esta estrategia y presupuesto; no hay candidata territorial.

## Identidad y procedencia

La evidencia original persistente está en `/Users/macbookpro/Desarrollo/DDD_PV_A2_G1_EVIDENCIAS/`. El manifiesto contiene 146 archivos; los 146 tamaños y SHA-256 coinciden. Los ZIP M03/M04/M05 pasan `unzip -t` y coinciden con los hashes del manifiesto. El M04 auténtico del run `37458584767` es `11412416951-M04.zip` (SHA-256 `56979163e7b14ead11682e194277cc3b96ed54c8db3c62fe7857de8952d8a83d`). La entrada directa del modelo es el GeoJSON M04 cacheado (SHA-256 `4a3d363de1c81381900eebecbc10c5ccc1e0beced11d1c385ca9d135978d7c13`). El grafo M03 tiene SHA-256 `8d3f19d66bb718a772ca75c36c18165b547c26a6a67f7ba10afa5213f2a2b316`.

El problema contiene 1.713 secciones, 281 unidades, K=75 y 2.227.684 habitantes; 29 unidades urbanas congeladas forman 29 distritos completamente congelados. El código es una herramienta experimental separada, sin cambios al código productivo ni al A2 integrado. Script ejecutado: `pv_iterative_connectivity_cuts.py`, SHA-256 `af12a93466d449d9446d2e28ac904064dfa94e1c5c793e7200858e86dddac65c`. Runtime: Python 3.11.14, NumPy 2.4.2, SciPy 1.17.0. Presupuesto preregistrado: 120 s wall, 100.000 nodos acumulados, 12 resoluciones y límite virtual de 6 GiB.

## Hallazgo de implementación y validez

La primera corrida no se acepta: el generador de dominios no fijaba unidades congeladas individuales dentro de un distrito mixto. Su reporte queda preservado como `result_pre_fix_invalid.json`; no se usó para ninguna conclusión territorial. Se corrigió el dominio para cada unidad congelada y se agregó una aserción que aborta si alguna no queda fijada a su distrito original. El preregistro registra esta enmienda. La segunda corrida es la única evidencia válida del ensayo.

## Resultado corregido

`result.json` registra 11 incumbentes conectados al modelo de restricciones excepto por la conectividad: los 11 fueron rechazados por cortes porque aún tenían entre dos y cuatro distritos desconectados. Los objetivos de unidades movidas fueron aproximadamente `2, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6`; se generaron 72 cortes válidos. La duodécima resolución agotó el tiempo disponible sin incumbente. Contadores: 10 nodos acumulados; duración medida 120,122 s; terminación `SOLVER_NO_INCUMBENT`. No se obtuvo asignación conectada, no se escribió `candidate_assignment.json` y no se ejecutaron M06 ni validadores sobre los incumbentes desconectados.

La secuencia cuantifica que, bajo objetivo de minimizar cambios, excluir mapas desconectados fuerza la búsqueda desde 2 hasta 5–6 movimientos, pero aún deja varios distritos desconectados. El método separador de cortes resultó más pequeño que el modelo de flujo probado anteriormente (13.773 variables, 23.869 restricciones base), aunque no encontró un incumbente final dentro del límite. Esto favorece investigar cómo construir conexiones con compensación simultánea; no demuestra infactibilidad global ni la causa completa de las cadenas históricas.

## Limitaciones instrumentales

No se guardaron las asignaciones por incumbente ni resúmenes de sus poblaciones/congelaciones. Por eso los objetivos y desconexiones se conservan como telemetría del solver, pero ninguna de esas asignaciones se presenta como candidata auditada. La corrida se detuvo por presupuesto; no equivale a infeasibilidad.

El campo `max_rss_bytes` de `result.json` es incorrecto por un defecto de medición: en macOS `ru_maxrss` ya está expresado en bytes y el script lo multiplicó por 1024. Su número se debe ignorar; el límite virtual de 6 GiB sí se fijó antes de ejecutar, pero no se dispone de una medición válida de RSS máximo. El límite de wall del solver fue 120 s; la duración del orquestador fue 120,122 s por el coste de retorno/serialización al terminar el solver. El resultado permaneció dentro de una desviación de 0,11% del tope y queda declarada.

## Siguiente paso útil

No repetir este corte incremental ni ampliar presupuesto automáticamente. Antes de un ensayo nuevo, diseñar un mecanismo que preserve y audite cada incumbente y que dirija los cambios hacia conexiones provinciales respetando márgenes de población; presupuesto y criterio deben preregistrarse. La revisión independiente de este ensayo está solicitada y pendiente.

## Actualización independiente — revisión del método PV-CUT-01

El revisor independiente identificó que el corte de conectividad sin raíz utilizado aquí era inválido: podía excluir una solución conectada cuyo distrito futuro coincidiera exactamente con el componente `S`. Por tanto, el resultado del ensayo corregido —11 incumbents desconectados y agotamiento de presupuesto— **no constituye evidencia válida sobre el método global**. Se conservan sus artefactos como historial, pero su clasificación queda sustituida por `NO_GO_ALGORITHM_INVALID_CUT`. El defecto de pinning de unidades congeladas de la primera corrida también permanece registrado; no se utiliza ninguna de las dos corridas para inferir factibilidad.

La investigación posterior es PV-CUT-02, documentada por separado en `INFORME_ROOTED_02.md`; no debe mezclarse con la telemetría de CUT-01.

La matriz consolidada de los ensayos 01–10, incluyendo invalidación del corte sin raíz y revisión PASS_ACOTADO del corte rooted, está en `MATRIZ_EXPERIMENTOS.md`. No existe en este momento una estrategia conectada pendiente de ejecutar con el mismo modelo: los métodos anteriores cubren annealing, flujo exacto, patches, relajación, cortes iterativos y objetivo de compactación; los resultados negativos son acotados y no se extrapolan a infactibilidad global.
