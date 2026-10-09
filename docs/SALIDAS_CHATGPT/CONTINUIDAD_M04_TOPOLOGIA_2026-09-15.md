# Continuidad — M04 tras depuración topológica de Aragón

**Fecha:** 2026-09-15  
**Responsable de esta intervención:** ChatGPT  
**HEAD de partida auditado:** `b523242a0a9ed7fd9a9d9a0d3f5140405e085ed7`  
**Objetivo:** desbloquear M04 sin volver a admitir contactos puntuales y dejar evidencia suficiente para que otra sesión continúe sin reconstruir el diagnóstico.

## 1. Incidente reproducido

El run GitHub `34948428986` reconstruyó correctamente las fuentes y produjo:

- M01: 1.463 secciones;
- M02: 4.063 aristas geométricas con `min_shared_border_m=1.0`;
- M03: 1.463 nodos, 4.063 aristas, 0 aislados;
- M04: `solución inicial mantiene 1 distritos fuera de suelo/techo`.

El fallo no está en Docker ni en GerryChain. M04 aborta antes de generar M05.

## 2. Reproducción independiente del fallo

Se reprodujo el grafo métrico a partir del GeoJSON oficial de secciones de Aragón con población 2025, en EPSG:25830, aplicando `touches` y longitud de frontera compartida >= 1 metro. El resultado fue exactamente **4.063 aristas**, igual que GitHub Actions.

Se reprodujo después el algoritmo activo M04 v7.4.5 con los parámetros vigentes:

- población total: 1.364.621;
- K=67;
- target=20.367,477612;
- suelo=16.293,982090;
- techo=35.643,085821;
- tolerancia ±12 %=2.444,097313;
- reparto provincial 11/7/49;
- atomicidad municipal 1,75 x target.

El único incumplimiento duro es el **distrito 16 de Teruel**, con **13.154 habitantes**, por debajo del suelo. La población de los siete distritos de Teruel producidos por la ruta primaria es:

`18.367 / 19.112 / 19.389 / 24.272 / 19.125 / 13.154 / 22.672`.

## 3. Causa técnica

No es falta de población ni imposibilidad matemática de Teruel. Es una mala elección de construcción inicial en `hybrid_partition` que el rebalanceo de movimientos simples ya no puede deshacer sobre el grafo depurado.

El distrito deficitario 16 queda topológicamente atrapado. Entre las unidades abiertas vecinas, la única unidad individual extraíble de un vecino sin romper su contigüidad es `44:44216:R`, con 18.154 habitantes. Moverla al 16 dejaría su distrito donante en aproximadamente 1.235 habitantes, por lo que el movimiento es inválido. Otras unidades fronterizas relevantes de los distritos 15 y 17 actúan como articulaciones: retirarlas individualmente desconecta el donante.

La eliminación de contactos puntuales no debe revertirse: ha hecho visible un mínimo local real del constructor M04.

## 4. Prueba de factibilidad sobre el mismo grafo

Se probó, sin cambiar unidades, K, cuotas, suelo, techo ni contigüidad, la ruta `grow_partition` ya existente en el propio motor seguida por el mismo `rebalance`.

Para Teruel produce:

`18.367 / 19.688 / 19.668 / 19.558 / 19.617 / 19.592 / 19.601`.

Todos los distritos cumplen el suelo/techo y además ±12 %. Aplicado al conjunto de Aragón, la reproducción obtiene:

- `hard_population_violations = 0`;
- `outside_target_tolerance = 0`;
- mínimo distrital = **18.237**;
- máximo distrital = **22.775**;
- cuotas provinciales intactas 11/7/49;
- mismo grafo de 4.063 aristas.

Por tanto el problema no requiere relajar topología ni contrato territorial.

## 5. Cambio implementado

Se añade `ddd_core/m04_seed_engine_v746.py` — **v7.4.6, Fallback determinista de crecimiento directo**.

Regla nueva, deliberadamente acotada:

1. se ejecuta exactamente la ruta v7.4.5;
2. si el rebalanceo termina con `hard=0`, no cambia nada;
3. solo si quedan violaciones duras, se reconstruyen las mismas unidades y el mismo K mediante `grow_partition`;
4. se ejecuta de nuevo el mismo `rebalance`;
5. la alternativa se acepta únicamente si la tupla objetivo mejora lexicográficamente;
6. se registra en el informe M04 la comparación de objetivos y poblaciones antes/después.

No se abren municipios atómicos, no se crean aristas, no se cruzan provincias y no se modifica K.

El wrapper canónico `ddd_core/m04_seed_engine.py` sube a **7.6.1** y pasa a componer el núcleo 7.4.6. Su predecesor 7.6.0 queda preservado en `legacy/ddd_core/m04_seed_engine_v7.6.0.py`.

Commits de implementación:

- `d45c7a1742c52d59951092ea5701ff3383624d6b` — nuevo núcleo 7.4.6;
- `1fd7eb610a595f781642a710891d5962b61b4472` — preservación legacy del wrapper 7.6.0;
- `4e16660a0e95386e899a62c4b51daf787717782a` — activación canónica del núcleo 7.4.6.

## 6. Estado de validación

La reproducción independiente sobre los datos de Aragón demuestra que la lógica propuesta resuelve exactamente el fallo observado de M04 con el grafo de 4.063 aristas.

La CI de GitHub se dispara automáticamente con el commit canónico. Debe comprobarse su resultado. Antes de esta intervención `main` ya tenía dos fallos de CI ajenos a M04: la prueba de `COMARCAS.csv` dentro de la imagen Docker, donde el fichero voluminoso está excluido, y una comprobación de `legacy/workflows` ejecutada dentro de una imagen que excluye `legacy/`. No confundir esos fallos con el cambio M04.

## 7. Siguiente punto de reenganche

La siguiente sesión debe proceder en este orden:

1. comprobar la CI del HEAD posterior a `4e16660`;
2. si solo persisten los dos fallos preexistentes, corregirlos sin tocar el algoritmo M04;
3. ejecutar **Aragón M01–M06** con el grafo de frontera >=1 m y fijar un nuevo baseline canónico;
4. actualizar el trinquete `0.099299365905`, que pertenece al grafo antiguo con contactos puntuales;
5. medir componentes geométricos reales de los 67 distritos;
6. solo después ejecutar **Aragón-10** de la galería GerryChain;
7. no ejecutar Aragón-50 hasta revisar telemetría, `unique_states`, calidad geométrica, población y retención comarcal.

## 8. Restricciones que no deben revertirse

- No volver `min_shared_border_m` a 0.
- No introducir puentes topológicos para hacer pasar M04.
- No relajar suelo/techo ni ±12 %.
- No saltar directamente a Aragón-50.
- No tratar el antiguo maxdev de Aragón como baseline válido tras cambiar el grafo.
- No confundir la galería de mejores candidatos con una distribución estadística de referencia; C-01 sigue abierto hasta conservar métricas de todos los estados visitados.
