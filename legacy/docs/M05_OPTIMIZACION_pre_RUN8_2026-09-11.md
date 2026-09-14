# M05 — Optimizar distritos

## Propósito
M05 modifica fronteras de la solución M04 para mejorar el equilibrio poblacional sin violar las reglas estructurales. M04 construye una solución territorial válida; M05 busca una solución mejor dentro de ese espacio válido.

## Restricciones duras R012
1. exactamente 67 distritos;
2. cardinalidad provincial fija: Huesca 11, Teruel 7, Zaragoza 49;
3. ningún distrito puede cruzar una provincia;
4. contigüidad estricta por grafo M03;
5. población entre 0,80×target y 1,75×target;
6. movimientos únicamente de `ddd_unit_id` completas;
7. los distritos `ddd_closed_urban` no reciben ni ceden unidades;
8. disciplina municipal final: un municipio que cabe bajo techo no se fragmenta; un municipio sobredimensionado conserva las reglas de partición/mestizaje definidas por R012.

Una transición que viole suelo/techo, provincia, contigüidad, atomicidad de unidad o cierre urbano es inválida y no puede formar parte de la búsqueda.

## Objetivo canónico
La comparación de soluciones completas es lexicográfica:
1. número de violaciones de suelo/techo;
2. magnitud de las violaciones duras;
3. número de distritos fuera de ±12 %;
4. máximo desvío poblacional relativo;
5. error cuadrático poblacional global.

Las restricciones territoriales y la disciplina municipal se verifican además en la puerta de calidad global. La geometría nunca se optimiza a partir de resultados electorales.

## Estrategia de búsqueda — v7.3.0
M05 separa **selección del producto** de **exploración del espacio de soluciones**.

### Fase A — greedy determinista
Se enumeran movimientos de unidad completa entre distritos adyacentes de la misma provincia. Solo se aplica un movimiento si:
- mantiene suelo y techo de donante y receptor;
- mantiene conectados ambos distritos;
- respeta cierres urbanos y atomicidad;
- mejora estrictamente el objetivo canónico.

Entre los movimientos que mejoran se selecciona determinísticamente el mejor.

### Fase B — escape de mínimo local
Si tras el greedy quedan distritos fuera de ±12 %, se activa un recocido simulado reproducible limitado a las provincias afectadas.

La fase de exploración puede aceptar temporalmente una solución peor respecto de ±12 % para atravesar un mínimo local. Sin embargo:
- nunca puede violar una restricción dura;
- usa semilla y parámetros explícitos en configuración;
- penaliza movimientos innecesarios mediante `churn` respecto de M04;
- conserva permanentemente la mejor solución encontrada según el objetivo canónico;
- la salida de M05 siempre es esa mejor solución, nunca el último estado explorado.

Esta distinción es esencial: exigir que cada transición mejore el objetivo hizo que v7.2.0 quedara bloqueada en el Run #7 aunque existiera una secuencia territorialmente válida hacia `fuera_12=0`.

## Entradas
Grafo M03, asignación M04, población, provincia, `ddd_unit_id`, `ddd_closed_urban`, suelo/techo, tolerancia ±12 %, límites de búsqueda, semilla, pesos de energía y temperaturas del recocido.

## Productos
`aragon_2025_m05_distritos_optimizados.geojson.zip`: asignación geográfica completa.

`M05/asignacion_optimizada.csv`: las 1.463 secciones con distrito optimizado y contexto administrativo.

`aragon_2025_m05_informe.json`: objetivos inicial, post-greedy y final; movimientos greedy/recocido; unidades finalmente alteradas; provincia activa; parámetros de búsqueda; restricciones y métricas poblacionales.

## Auditoría exigida
Debe poder compararse M04 y M05 sección por sección y `ddd_unit_id` por `ddd_unit_id`.

No se exige que cada transición interna de la fase exploratoria mejore el objetivo canónico; eso volvería a introducir el mínimo local de v7.2.0. Sí se exige que **toda transición preserve las restricciones duras**, que la trayectoria sea reproducible y que **el producto final seleccionado sea la mejor solución encontrada según el objetivo canónico**.

La aceptación definitiva corresponde a la validación reproducible en GitHub Actions, no a una ejecución local del asistente.

## Estado actual
Run #7 `34588834266` es la última referencia GitHub: estructura R012 PASS, pero M05 v7.2.0 dejó `fuera_12=1` y aceptó 0 movimientos. La causa está documentada en `docs/AUDITORIAS/AUDITORIA_M05_RUN7_2026-09-11.md`.

M05 v7.3.0 implementa R014 — escape determinista de mínimos locales. Una prueba diagnóstica sobre los artefactos exactos del Run #7 alcanzó `hard=0` y `fuera_12=0` manteniendo provincia, contigüidad y disciplina municipal. Está pendiente de ratificación por una nueva ejecución GitHub.
