# T-165 · Diseño de un constructor de semillas sobre el núcleo único de reglas

Fecha: 2026-11-10. Línea de fondo de D-48. Solo diseño: sin código de producción, sin tocar huellas, sin lanzamientos.
Base: `origin/main`; núcleo `ddd_motor2/reglas/` (T-160); batería T-132 (`docs/ESTUDIOS/T132_BATERIA_MOTOR/`);
divergencias T-137 (`docs/ESTUDIOS/T137_NUCLEO_REGLAS/INVENTARIO_DIVERGENCIAS.md`).

## 1. Cómo se construye hoy la semilla canónica

Cadena: M03 (grafo) → **M04 7.6.7** (`ddd_core/m04_seed_engine.py`, envuelve el núcleo 7.4.12/7.4.11) → **M05 7.4.4**
(`ddd_core/m05_opt_engine_v741.py`, voraz + recocido) → reparadores (`m05_population_repair`, `m05_swap_polish`,
`m05_private_annealing`). La «semilla» es la Formación inicial de M04 más el refinamiento de M05.

Pasos de M04 (por provincia/partición):
1. Preflight atómico fail-closed: condiciones necesarias de población y conectividad de átomos
   (`_atomic_population_necessary_conditions`, `_preflight_atomic_population_connectivity`) y partición conexa exacta
   de grupos duros (`_exact_connected_hard_partition`).
2. Núcleos urbanos cerrados (`m04_closed_target_cores`): se fijan primero y se reparan si quedan fuera de tolerancia.
3. Residuo abierto: `split_sequential` / `split_residual_first` / `hybrid_partition` (pelado `find_peel` con
   `max_starts` y, si falla o quedan ≤ 4 distritos, `grow_partition`: semillas lejanas por BFS y crecimiento voraz).
4. `rebalance` (30 000 iteraciones) con relleno por crecimiento directo (7.4.12).
5. Posproceso: enclaves dependientes (7.6.7), alivio de residuos sobre techo (`m04_overcap_residual_relief`),
   cesión de secciones del residuo a núcleos del mismo municipio (7.6.6).

### Reglas aplicadas fuera del núcleo (copias locales)
| Regla | Dónde vive hoy | Observación |
|---|---|---|
| Suelo/techo | `hard_limits` (M04, M05, reparadores) | comparación sin margen; el núcleo usa fracciones exactas |
| Exención de suelo | `population_floor_exemptions` (M04, canónico), copia propia en M05 | T-137: `zfill` y primera partición divergen |
| Contigüidad | `connected`/`components` repetidos en cada versión de M04 y M05 | sin puentes topológicos en algunas copias |
| Atomicidad municipal | `municipality_atomicity_limit_ratio` en M04; unidades `ddd_unit_id` | M05 solo mueve unidades enteras |
| R012 mixtos | M05: `max_mixed…` del contrato; reparadores: 1 fijo | mín/máx no se optimizan en M05 (se confía a M04) |
| Provincia única | M04 por construcción; M05 como regla dura | |
| Núcleos cerrados | M04/M05/`swap_polish` | el validador no los comprueba (el núcleo sí: `R-NUCLEO`) |
| Municipio de una unidad | id `{prov}:{mun}:…` en el canónico | el núcleo exige el campo, nunca el id |

Consecuencia: la validez de la semilla hoy es el resultado de ~11 versiones de heurística (`m04_seed_engine_v745`…`v7412`)
con reglas incrustadas; no hay una sola función «¿es admisible esta semilla?» que la guíe.

## 2. Qué dice la batería T-132 del generador alternativo

- Canónico: 71/71 PASS. Árbol (`recursive_tree_part` por provincia): **188/355 PASS, 30/71 territorios siempre válidos**.
- Si la semilla de árbol es admisible, ReCom da PASS siempre (188/188): el cuello de botella es solo la semilla.
- En los 167 fallos de `BANCO.csv`, 143 llevan `unit_universe` (el plan no cubre el universo de unidades; coincide con las
  provincias sin corte equilibrado, columna `arbol_provincias_infactibles`) y el resto son `population_cap/floor` por
  distrito y `municipality_mixed` (R012). No hay fallos de contigüidad: el árbol conserva la conexión por construcción.
- GerryChain de producción usa M04 como estado inicial solo en el 55 % de las ejecuciones (M04 no admisible en el 45 %): hoy
  cae a la semilla M05 canónica. Un constructor propio que fuese casi siempre admisible quitaría esa dependencia.
- El exacto (CP-SAT, T-136) resuelve territorios pequeños y medianos (hasta ~5 000 variables), no Madrid ni La Rioja.

## 3. Algoritmo propuesto: crecimiento de regiones con árboles + reparación guiada por el núcleo

Entrada: `Problema` y `Reglas` del núcleo (ya normalizados), K por provincia/partición, y una **semilla pública** `s`.
Salida: asignación `{unidad → distrito}` y un informe (`evaluar` del núcleo + trazas).

**Fase 0 — Preparación (determinista, sin azar).**
- Contraer las unidades indivisibles (átomos: `ddd_unit_id`, núcleos urbanos cerrados, grupos administrativos) en nodos con
  peso; el grafo contraído usa `Problema.adyacencia(con_puentes)`.
- Dividir en subproblemas independientes por provincia/partición con su cuota (R-CUOTA, R-PROV); orden canónico por código.
- Cotas necesarias previas (reutilizando `enumerar.podar` del núcleo): ⌈P/techo⌉ ≤ k ≤ ⌊P/suelo⌋ por subproblema y
  componentes conexas; si no se cumplen, informe de infactibilidad por subproblema (nunca una semilla inválida silenciosa).

**Fase 1 — Construcción (azar acotado por `s`).**
Por subproblema, dos constructores en orden de coste, ambos con el generador pseudoaleatorio derivado de
`hash(s, territorio, subproblema, intento)`:
1. *Árbol generador aleatorio con corte equilibrado* (Wilson/Kruskal con pesos pseudoaleatorios): buscar aristas del árbol
   cuyo corte deje componentes dentro de [suelo, techo] y ajustadas a la tolerancia; descender recursivamente (tipo
   `recursive_tree_part`). Se usa el árbol mínimo de la inicial como base y se prueban hasta N árboles.
2. *Crecimiento de regiones desde K centros* (como `grow_partition`, pero eligiendo los centros por BFS y con desempate
   por `s`): cada región absorbe la unidad de frontera que mejor respeta suelo/techo; las unidades que no caben se
   difieren.
Los núcleos urbanos cerrados se asignan antes como distritos fijos (equivalente a `closed_target_cores`), y el
constructor opera sobre el residuo.

**Fase 2 — Reparación guiada por el núcleo (determinista dado el estado).**
Con `Estado` del núcleo (`ddd_motor2/reglas/estado.py`, violaciones incrementales por distrito, municipio, cuota y núcleo):
- Mientras haya violaciones duras: elegir la de mayor gravedad (techo > suelo > R012 > R-TOL) y el movimiento de unidad en
  frontera que más la reduce sin crear otra (el estado devuelve el delta exacto); desempates por código de unidad.
- Movimientos admitidos: mover una unidad de frontera; intercambio de dos unidades entre distritos adyacentes; en R012,
  mover el **municipio completo** (todas sus unidades del distrito mixto) a un único distrito.
- Parada: sin violaciones, o sin movimiento mejorante tras M pasadas (entonces nuevo intento de la Fase 1).
- Heurística de reparación de mixtos: ordenar los municipios partidos por exceso de distritos y agrupar sus unidades en
  el distrito de mayor población del municipio, siempre que la distancia al techo lo permita.

**Fase 3 — Certificación.** `evaluar(problema, reglas, asignacion)` debe dar `valido=True`; se registra `huella_reglas`
del núcleo. Si tras R intentos no hay semilla admisible, escalar a la semilla exacta (CP-SAT, T-136) cuando el tamaño lo
permita, o devolver `SEMILLA_NO_ADMISIBLE` con los códigos de violación (la batería ya los distingue).

**Después** del constructor, el plan se refina con M05/ReCom como hoy; el constructor no sustituye la optimización, solo el
paso «Formación inicial + baseline».

## 4. Invariantes

1. **Cobertura**: cada unidad exactamente una vez (R-ATOM, `unit_universe`).
2. **Conexión**: cada distrito conexo en el grafo (con puentes si el contrato los declara).
3. **Provincia única** y **cuotas**: K por provincia/partición exacta.
4. **Límites duros**: suelo/techo con la misma vara que el núcleo (exenciones comprendidas).
5. **R012**: mixtos ≤ `max_mixed…` del contrato; mín/máx por municipio.
6. **Núcleos cerrados** intactos.
7. **Semilla admisible por construcción**: la salida se acepta solo si `evaluar(...)` es PASS; si no, no hay salida.
8. **Sin lectura de datos oficiales de memoria**: solo el `Problema` construido desde la fuente con sha256.

## 5. Determinismo y semilla pública

- Misma entrada ⇒ mismo plan: la **entrada** es (huella del `Problema`, huella del `Reglas`/contrato, versión del
  constructor, semilla pública `s`, parámetros de intentos). Se publica `s` y la huella de entrada en el manifiesto; el plan
  se puede reproducir y auditar.
- Fuentes de variación prohibidas: orden de iteración de `set`/`dict` (se ordena todo por código), tiempo, hilos, `hash()`
  de Python (se usa SHA-256 sobre la tupla textual), versión de bibliotecas no fijada.
- PRNG propio y portable: derivación `SHA-256(s‖territorio‖subproblema‖intento) → entero → PRNG de implementación
  explícita` (p. ej. xorshift/PCG codificado en el módulo) para que no dependa de la versión de `random`/`numpy`.
- Semilla pública: elegida y declarada antes de calcular (por ejemplo, un valor por contrato de territorio); se publica
  junto al resultado. Esto permite repetir y comprobar sin confianza en el operador.
- Prueba de determinismo: ejecutar dos veces (y en dos plataformas) y exigir plan idéntico (sha256 de la composición).

## 6. Cómo se mediría contra el canónico (batería T-132)

Se añadiría un generador `constructor` a `herramientas/bateria_motor.py` (cambio posterior, no en esta tarea) que reutiliza
las mismas entradas (`ENTRADAS.csv`), el mismo contrato y la misma validación de producción:

| Medida | Umbral de aceptación propuesto |
|---|---|
| Validez de la semilla (sin ReCom) | PASS en 71/71 territorios con las semillas 1-5 (hoy el árbol: 30/71) |
| Validez tras ReCom | 355/355 PASS |
| Determinismo | 2 ejecuciones idénticas en 71/71 |
| Concordancia con el núcleo | veredicto del núcleo = veredicto de `validar_ejecucion` (perfil «compatibilidad producción») en 71/71 |
| Calidad frente al canónico | igual o mejor en orden lexicográfico (fuera de tolerancia, desvío máximo), sobre los territorios válidos; Δ mixtos y Polsby-Popper como informativos |
| Tiempo | ≤ 2× el de M04+M05 en cada territorio; Madrid y La Rioja incluidos |
| Casos duros | los 41 territorios donde el árbol falla; Congreso Valladolid, Cádiz, Canarias, Madrid y La Rioja como subconjunto de control |

Procedimiento: (1) medir solo la semilla (tasa de admisible por territorio y causa de fallo por código del núcleo);
(2) medir semilla+M05 contra el canónico; (3) medir semilla+ReCom. Sin tocar M04/M05 hasta que (1)-(3) pasen.

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Átomos indivisibles grandes (Madrid, Valladolid) hacen que no exista corte equilibrado por árbol | Fase 0 con contracción; si falla, escalar a CP-SAT (T-136) en subproblemas ≤ ~5 000 variables |
| R012 + núcleos cerrados + tolerancia a la vez: la reparación entra en ciclos | Prioridad de violaciones; lista tabú por (unidad, distrito); tope M de pasadas; reintento |
| Calidad peor que la del canónico (el árbol «mejor de 5» empeora 8/43) | La semilla se mide solo en validez; la calidad la da M05/ReCom después; criterio de aceptación explícito |
| Diferencias de criterio (D-44) cambian el veredicto | El constructor recibe `Criterio`; la batería mide con el perfil por defecto y el de compatibilidad |
| Reproducibilidad entre plataformas | PRNG propio; sin `set` sin ordenar; prueba cruzada |
| Cambio de huellas M04/M05 al retirar el artesanal | Fase final separada y con permiso del propietario; aquí no se toca nada (`.claude/rules/huellas.md`) |
| Coste de mantenimiento de dos constructores durante la transición | Convivencia limitada por fases; retirada solo con 71/71 y dos ciclos sin regresiones |

## 8. Esfuerzo por fases

| Fase | Contenido | Esfuerzo | Salida |
|---|---|---|---|
| F0 | Contracción de átomos, cotas previas, división por provincia/partición, PRNG determinista (módulo en `ddd_motor2/`) | 2-3 días | tests de determinismo y cotas |
| F1 | Árbol generador + corte equilibrado + crecimiento de regiones | 3-4 días | semilla sin reparación; tasa de admisibles en la batería |
| F2 | Reparación guiada por `Estado` (movimientos, intercambios, municipio completo) | 4-6 días | objetivo: 71/71 admisible |
| F3 | Integración en `bateria_motor.py` (generador `constructor`) y medición contra el canónico | 2 días | informe tipo `RESUMEN_GENERADORES` |
| F4 | Escalado a CP-SAT para subproblemas pequeños, informe de infactibilidad | 2-3 días | casos duros |
| F5 | Sustitución de la Formación M04 en el canónico (M05 7.4.4/M04 7.6.7): huellas, checkpoints, modo de 00 | 3-5 días + decisión del propietario | solo con permiso; invalida M04/M05 y checkpoints |

Total orientativo F0-F4: 13-18 días de implementador, sin tocar producción; F5 es una decisión aparte. Línea de fondo: se
puede detener tras F1 con valor (medida de la brecha) sin comprometer F2+.

## 9. Decisiones que quedarían al propietario / Planificador

1. ¿Umbral de aceptación de F2 (71/71 admisible) y de F5 (calidad ≥ canónico)?
2. ¿Quién fija la semilla pública y dónde se publica (manifiesto del run)?
3. ¿Se permite el escalado a CP-SAT dentro del constructor o se mantiene como herramienta aparte?
