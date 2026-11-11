<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Definición formal de Deslinde 1.0
FECHA: 2026-11-11
ESTADO: candidato (documento; describe el código de main ee8e776, no lo cambia)
CAMBIOS: fichero nuevo (T-255).
MOTIVO: D-84 (nombre y composición de Deslinde 1.0) y D-86 (2): definición formal publicada de las reglas, la elección
  D8 y la semilla, sacada solo del código y de las decisiones registradas.
ANTERIOR: ninguna (fichero nuevo)
-->

# Deslinde 1.0 — delimitación reproducible de distritos uninominales

**Qué es (D-84, `docs/PLAN.md:121`).** Deslinde 1.0 = trazado canónico + 10 cadenas ReCom + elección D8 + mapa vigente
como candidato. Hoy está implementado como «motor 2» en `ddd_motor2/` (motor nuevo de D-48); el código **no se
renombra antes del corte 5.0.0** (D-84). Tras el corte vienen la optimización (D-85) y el paquete independiente (D-86).

Todas las citas son a `main` en `ee8e776`. Versiones de los ficheros citados: `reglas/modelo.py` 1.0.0,
`reglas/evaluar.py` 1.0.0, `reglas/metodo.py` 1.0.0, `naturalidad_clave.py` 1.1.0, `semilla.py` 1.0.1,
`competicion.py` 1.4.0, `competir.py` 1.2.0, `generadores.py` 1.2.1, `produccion.py` 1.1.0, `adaptadores.py` 1.2.0,
`exhaustivo.py` y `calidad.py` 1.0.0, `herramientas/bateria_motor.py` 1.2.4, `docs/ARQUITECTURA/ACEPTACION_MOTOR2.md`
1.1.0, `configuracion/politica_generacion_territorial_2025.yaml` 1.7.4.

## 1. Entradas y salidas

**Entradas** (por territorio y edición):
- Contrato del territorio (`territorios/<t>/config/<t>_<edición>.yaml`), con los umbrales que el materializador copia de
  la política (`.claude/rules/contratos.md`). Bloque `validation` (K, suelo, techo, tolerancia, exenciones, provincia
  única, disciplina municipal, núcleos cerrados, contigüidad) y `generation_state.source_inputs` (sha256 del padrón y
  del seccionado, ancla de la semilla).
- Grafo M03 de secciones (`*_m03_grafo.json`, aristas con `shared_border_m`) y `topology_bridges` del contrato, que van
  aparte como `puentes` (`adaptadores.py`, cabecera «ENTRADA ÚNICA»).
- Composición M06 del canónico (CSV: `CUSEC_KEY`, `district_id`, `section_pop`, `ddd_unit_id`, `ddd_closed_urban`) y su
  GeoJSON de secciones; en producción es el M06 que acaba de producir el run (`produccion.py`, «QUÉ HACE · competir»).
- Mapa vigente publicado `datos/composicion/<t>.csv` (`generadores.py:273-300`, clase `Vigente`).
- Tablas de naturalidad: `configuracion/partidos_judiciales.csv`, `docs/ESTUDIOS/T64_*/comarcas_agrarias.csv`,
  `datos/movilidad/**` (`produccion.py:67-69`, `DATOS_NATURALIDAD`).

**Salidas** (`produccion.py:246-300`): en `<run>/p30_motor2/`, `COMPETICION.{json,md}` (todos los candidatos juzgados)
y `P30.json` (ganador, generador, validez, `huella_resultado`, `semilla_publica`, huella `motor2`, entorno, bloque
`vigente`, `composicion_m06_sha256`, métricas del ganador y del canónico). Estados: `P30_GANA_CANONICO`,
`P30_GANA_OTRO_PLAN` (reescribe la entrada de M06 con el plan ganador y `rehacer_m06=true`) o `P30_SIN_GANADOR_VALIDO`
(sale con 3; nunca se publica un plan inválido). `verificar` comprueba que el M06 rehecho es el ganador (si no, 4) y
restaura byte a byte la salida M05 (si no, 5).

## 2. Reglas núcleo: «plan válido»

Una sola definición ejecutable: `ddd_motor2/reglas/` (solo stdlib; diseño en `docs/ARQUITECTURA/NUCLEO_REGLAS.md`).
Entrada única de las reglas: `Reglas.desde_contrato(cfg, criterio)` (`reglas/modelo.py:239-295`), que **falla**
(`ErrorContrato`) si el contrato no declara K, suelo, techo o tolerancia: no hay valores por defecto ocultos
(`modelo.py:205-211`). Comparaciones exactas: poblaciones enteras y límites como fracciones (`modelo.py:297-300`).

Sea `P` la población total del territorio y `o = P/K` el objetivo (regional; también con cuotas por provincia o isla).
Suelo `s·o`, techo `c·o`, tolerancia absoluta `t·o`, con `s`, `c`, `t` = `population_floor_ratio`,
`population_cap_ratio`, `target_tolerance_ratio` del contrato. Defectos de la política: 0,80 / 1,75 / 0,12 y
atomicidad 1,75 (`politica_generacion_territorial_2025.yaml:22-26`), con excepciones por territorio en
`population_limits` (p. ej. Melilla 0,50/0,50; provincias del Congreso 0,85/1,15/0,15/1,15).

Un plan (unidad → distrito) es válido si y solo si `evaluar` no devuelve ninguna violación (`reglas/evaluar.py:179-225`):

| Código | Regla | Fuente |
|---|---|---|
| R-ATOM | Toda unidad asignada y ninguna desconocida. La unidad es atómica: el adaptador da `ErrorDatos` si una unidad aparece repartida entre distritos | `evaluar.py:152-159`; `adaptadores.py` cabecera |
| R-K | Exactamente K distritos (`validation.expected_districts`) | `evaluar.py:160-161` |
| R-POB-SUELO | Población del distrito ≥ `s·o`, salvo distrito exento | `evaluar.py:108-110` |
| R-POB-TECHO | Población ≤ `c·o` (sin exenciones) | `evaluar.py:111-112` |
| R-TOL | Solo con `Criterio.tolerancia="dura"`; el criterio aprobado es «métrica» (D-44), así que la tolerancia **no es regla**: es el primer término de la elección | `evaluar.py:113-115`; `modelo.py:173`; D-44 |
| R-CONTIG | Distrito conexo en el grafo de unidades, contando los puentes (`contiguidad_con_puentes=True`) si `require_graph_contiguity` (por defecto sí) | `evaluar.py:116-117`; `modelo.py:183, 293` |
| R-PROV | Si `require_single_province_per_district`, una sola provincia por distrito; la clave es obligatoria en el contrato (`provincia_defecto="obligatoria"`, D-44) | `evaluar.py:118-121`; `modelo.py:255-261` |
| R-CUOTA | Con provincia única, nº de distritos por provincia = `province_districts` | `evaluar.py:137-141` |
| R-MUN-MIN / R-MUN-MAX | Con `require_municipality_discipline`, un municipio de población `p` está en entre `⌈p/techo⌉` y `⌈p/o⌉` distritos (mín. 1) | `evaluar.py:97-101, 125-131` |
| R-MUN-MIXTOS | Un municipio partido no puede estar en más de `max_mixed_districts_per_split_municipality` distritos mixtos (con más de un municipio); por defecto 1 (D-44, D-66) | `evaluar.py:132-133`; `modelo.py:270-275` |
| R-NUCLEO | Con `preserve_closed_urban` (por defecto sí), cada núcleo cerrado forma **exactamente** un distrito | `evaluar.py:144-149, 211-214` |

Precisiones:
- **Atomicidad de unidades.** Las unidades son las del M04 (`ddd_unit_id`); un municipio de hasta
  `municipality_atomicity_limit_ratio × o` no se parte. Fuera del Congreso y sin `connected_internal_units`, la cadena
  y el vigente usan «piezas finas»: una unidad por sección en los municipios mayores que ese umbral (T-218, D-79;
  `generadores.py:160-172`). El núcleo no comprueba el umbral: lo da la construcción de unidades.
- **Núcleos cerrados.** Son los distritos de referencia formados solo por unidades `ddd_closed_urban`; la referencia es
  el distrito inicial del M04 (`adaptadores.referencia_desde_m04`, 1.2.0) o, si falta, la composición del canónico, la
  misma para todos los candidatos (`competicion.py:308-310`). Sin referencia y con unidades cerradas, el candidato es
  `ERROR_DATOS`.
- **Exenciones de suelo** (`evaluar.py:62-78`): por municipio (`population_floor_exempt_municipalities`, INE de 5 cifras:
  basta uno en el distrito) o por partición (`population_floor_exempt_partitions`: todas las particiones del distrito
  exentas, `exencion_particion="todas"`, D-44). No eximen del techo.
- **Campo municipal de R012**: `unidad_r012` si el contrato usa `partitioning.strategy=connected_internal_units`; si no,
  el municipio, con desglose por municipio en grupos atómicos multimunicipales (`modelo.py:277-279, 98-102`).
- **Huella de las reglas**: `Reglas.huella()` = sha256 de su forma canónica (`modelo.py:302-314`).

## 3. Elección: criterio D8

Decisión D-68 (`docs/PLAN.md:105`) y D-79 (`:116`); estudios `docs/ESTUDIOS/T179_naturalidad_nacional/`,
`T196_BATERIA_D8/`, `T211_ponderado_autonomicas/`. Cada candidato se ordena por una clave lexicográfica (menor es
mejor; `competicion.py:138-143` y `naturalidad_clave.py:64-79`):

1. evaluable (fallo del generador, `ERROR_DATOS` o `ERROR_CONTRATO` van detrás de todo);
2. número de violaciones duras del núcleo (0 = válido);
3. distritos fuera de tolerancia, `|p − o| > t·o`, contados contra el objetivo **regional** del contrato
   (`Natural.fuera_regional`, `naturalidad_clave.py:103-108`; D-68, T-211);
4. exceso sobre el 8 % del mayor desvío relativo entre los distritos **dentro** de tolerancia: `max(0, máx − 0,08)`
   (`TOPES["D8"]`, `naturalidad_clave.py:43, 76-78`). El tope **solo sirve para elegir**; no es regla (cabecera, l. 26);
5. partidos judiciales + comarcas agrarias repartidos en más de un distrito (`partidas`, l. 47-56);
6. frontera cortada entre distritos, en km con 3 decimales (`corte_km`, l. 59-61; suma de `shared_border_m` del M03);
7. desvío máximo relativo;
8. huella del plan (partición sin etiquetas, `calidad.huella_plan`);
9. orden del candidato (canónico 0, vigente 1, cadenas, exhaustivo).

Con cuotas de varias circunscripciones, los términos 4 y 7 se miden contra el objetivo de la circunscripción de cada
distrito (`Natural.desvios`, l. 93-101); el término 3, contra el regional. Con una circunscripción coinciden.
Ganador: `min(candidatos, key=Candidato.clave)` (`competicion.py:355`).

## 4. Semilla pública y reproducibilidad

**Semilla** (D-50, `docs/PLAN.md:87`; `ddd_motor2/semilla.py`, esquema `ddd-semilla-publica/1`):

    semilla_i = int(sha256("ddd-semilla-publica/1|<sha padrón>|<sha seccionado>|<territorio>|<i>")[:16], 16) mod (2^31 − 2) + 1,  i = 1..N

Ancla: sha256 de los roles `population` y `target_sectioning` de `generation_state.source_inputs`; si falta alguno o no
es un sha256 válido, `ErrorContrato` y no se ejecuta nada (nunca semilla fija; `semilla.py:222-236`). Semillas repetidas
→ error explícito (l. 248-249). Hoy `<territorio>` es el nombre de carpeta del contrato (`produccion._territorio`,
`produccion.py:91-95`); D-61/6 prevé el código de la tabla maestra: ver Puntos abiertos.

**Huella del resultado** (`competicion.py:177-183`): sha256 de reglas, semillas, enumeración exacta y, por candidato,
id, semilla, estado, huella del plan y sha256 de su composición. Misma entrada ⇒ misma huella (criterio (a) de
`ACEPTACION_MOTOR2.md`).

**Huella del motor `motor2`** (`produccion.py:79-87`): sha256 de `ddd_motor2/**/*.py`, de las tablas de
`DATOS_NATURALIDAD` (incluido `datos/composicion/*.csv`, T-223), de la función (`FUNCION="D8"`) y de N
(`CADENAS=10`), fijados en el código sin opción en la línea de órdenes (`produccion.py:63-64`). Va a la capa `motor2` de
`compatibility/motor.json`: un M06 de otra configuración no se reutiliza.

**Entorno**: `competir` falla cerrado sin `PYTHONHASHSEED=0` (`P30_ENTORNO_NO_REPRODUCIBLE`, sale con 6;
`produccion.py:339-340`); el flujo lo fija (`_reutilizable-generacion-territorial.yml:526`). `P30.json` guarda Python,
`PYTHONHASHSEED`, versiones de numpy, pandas, shapely, geopandas, pyogrio, pyproj, gerrychain, networkx, rustworkx,
scipy y GEOS (`produccion.py:71-72, 219-234`). La batería instala `requirements.lock` y gerrychain `--no-deps` con los
pines de `requirements-ensemble.lock` (`bateria-motor.yml:101-205`; T-181).

## 5. Candidatos de la competición

`competicion.competir` (`competicion.py:291-363`), vía `competir_publico` con las N semillas públicas:

| Orden | Candidato | Qué es |
|---|---|---|
| 0 | **canónico** | P30: el M06 del propio run (`CanonicoDelRun`); batería: M04 + M05 canónico 7.4.4 + M06 (`generadores.Canonico`) |
| 1 | **vigente** | `datos/composicion/<t>.csv` sobre las filas del canónico (con piezas finas). Solo compite si es representable, tiene **exactamente** las secciones de la entrada (si no, `VIGENTE_OTRO_SECCIONADO`, 1.2.1) y es válido. Si incumple el núcleo (R-NUCLEO o R-MUN-MIXTOS), **vigente reparado** (D-66): reparación mínima y determinista, máx. 20 pasos, sin crear infracciones nuevas, y se juzga de nuevo (`generadores.py:194-269, 329-347`). No compite con la función A |
| 2..N+1 | **ponderado** ×N (N=10, D-67 provisional) | Cadena ReCom de GerryChain (`naturalidad_competicion.cadena`, l. 300-350): 300 pasos, `epsilon = t`, árbol de expansión ponderado con recargos 0,5 (partido judicial) / 0,3 (comarca agraria) / 0,2 (área de movilidad) / 0,3 (frontera corta) (`generadores.py:356-357`), el núcleo como restricción en cada paso y `rng = semilla_i`; devuelve el mejor estado por D8. Si el vigente compite, la mitad final de las semillas parte de él y el resto del canónico (`competicion.py:329-331`) |
| último | **exhaustivo** (si aplica) | Enumeración exacta de todos los planes válidos sobre las unidades del canónico si termina dentro de `presupuesto_nodos=200 000` (`Criterio.metodo="presupuesto"`, `modelo.py:177-178`; `exhaustivo.py:41-70`) |

Ganador: el primero por la clave D8 (§3) entre todos. Como el canónico (y el vigente válido) compiten, la clave del
ganador nunca es peor que la suya (aserción `competicion.py:356`). Sin ningún candidato válido, `P30_SIN_GANADOR_VALIDO`.

## 6. Criterios de aceptación

`docs/ARQUITECTURA/ACEPTACION_MOTOR2.md` 1.1.0 (T-194, T-212) y `herramientas/bateria_motor.py`
(`criterio_aceptacion`, l. 1006-1041; `aceptacion`, l. 1044). Aceptación = todos a la vez:
- todos los territorios presentes y con ganador válido;
- **comprobación 1**: clave de elección del ganador nunca peor que la del canónico (`frente_al_canonico != "empeora"`,
  `competir.comparar`, sin huella ni orden);
- **comprobación 2**: recuento bruto de distritos fuera de tolerancia del ganador (el del contrato) nunca mayor que el del
  vigente publicado (`peor_que`, l. 759-765; T-212, T-228/T-229). Desvío máximo mayor que el del vigente = aviso, no
  bloquea. `SIN_VIGENTE` y `NO_EVALUABLE` constan por nombre y **no hay aceptación**; `UN_DISTRITO` vale;
- cadenas evaluables, sin `FALLO_GENERADOR`, y nº de candidatos = 1 + N (+1 exhaustivo) (+1 si el vigente compite)
  (T-222);
- huella real igual en dos ejecuciones en `congreso_soria`, `congreso_alava` y `melilla` (`HUELLA_REAL`, l. 726);
- en CI (`tests/test_motor2_aceptacion.py`): huellas fijas (a), ganador certificado por
  `herramientas/certificador_exacto` (b), `COMPETIDOR.csv` sin empeoras (c) y casos adversos rechazados (d).

## 7. Límites conocidos: qué NO garantiza Deslinde 1.0

- **No es un óptimo demostrado.** Es el mejor de un conjunto finito de candidatos (canónico, vigente, 10 cadenas de 300
  pasos). Óptimo demostrado o cota con resolutor exacto es el paso 3 de la hoja de ruta (D-86); el encargo de esta tarea
  lo sitúa en Deslinde 1.1/2.0 (D-87/D-88, no registradas: Puntos abiertos).
- **El exhaustivo no es el óptimo D8**: la enumeración guarda el mejor plan por la regla de calidad A (`calidad.py`:
  duras → fuera → desvío → ECM → huella; `exhaustivo.py:55-56`), no por D8; ese plan compite después con la clave D8.
- **La tolerancia no es regla** (D-44): un mapa válido puede tener distritos fuera de tolerancia; Deslinde solo los
  minimiza en la elección.
- **Óptimo local respecto a la atomicidad del contrato**: no parte municipios que el contrato declara atómicos ni
  unidades M04 en el Congreso o con `connected_internal_units` (T-211 (a)/(b): parte de la mejora del laboratorio no es
  alcanzable).
- **Naturalidad aproximada**: partidos judiciales y comarcas agrarias por el municipio de la unidad; la frontera es la
  `shared_border_m` del M03 (0 si falta).
- **Reproducibilidad bit a bit** solo con las mismas entradas, `PYTHONHASHSEED=0` y el mismo entorno; con el motor real
  no corre en CI (`ACEPTACION_MOTOR2.md`, «Límite conocido»).
- Con la función A el vigente no compite (`produccion.generadores_por_defecto`, l. 236-243).
- El criterio (e) «mismo mapa con id viejo y nuevo» (D-60) está en `skip` hasta el corte.

## Puntos abiertos (no resueltos aquí)

1. **D-87, D-88 y D-89 no están registradas** en `docs/PLAN.md` ni en ningún fichero de `main` (`ee8e776`); en `PLAN.md`
   la última es D-86. Las referencias a «Deslinde 1.1/2.0» y a «paquete independiente después del corte» vienen solo
   del encargo de T-255; D-86 (`PLAN.md:123`) dice «paquete independiente … tras la optimización».
2. **Territorio en la semilla**: D-61 (`PLAN.md:98`) y `CORTE_5_0_0.md:291` fijan «el código de la tabla maestra vía
   resolutor»; el código usa el nombre de carpeta del contrato (`produccion.py:91-95`). `T180_CADENAS/README.md` ya lo
   señala («no está aplicada»). Cambiarlo cambiará todas las semillas y huellas.
3. **N en la aceptación de CI frente a producción**: `ACEPTACION_MOTOR2.md` y `tests/test_motor2_aceptacion.py:37` usan
   `N_CADENAS = 5`; producción y D-84 usan 10 (`produccion.py:64`, `competir.py` por defecto 10) y
   `competir_publico` tiene 5 por defecto (`competicion.py:367`). D-67 dice que N=10 es provisional «hasta que lo
   confirme la batería de los 71 con la función elegida».
4. **Dos «vigentes» distintos**: el candidato vigente de la competición lee `datos/composicion/<t>.csv`
   (`generadores.py:279, 286`); la comprobación 2 de la aceptación lee `composicion_publicada` = `datos/composicion/runs/<t>_<run>.csv`
   del `canonical_m06` del visor si existe y, si no, el mismo `<t>.csv` (`bateria_motor.py:473-476`). Si difieren, la
   garantía «nunca peor que el vigente por construcción» (`competicion.py` 1.4.0) no cubre la vara de la aceptación.
5. **Vigente sin comparación**: `competir.py` 1.2.0 dice que el territorio «sin_comparacion_vigente … la aceptación no lo
   esconde ni lo bloquea»; `bateria_motor.criterio_aceptacion` (l. 1018, 1041) y `ACEPTACION_MOTOR2.md` (c2) dicen que
   `SIN_VIGENTE`/`NO_EVALUABLE` deja el territorio **sin aceptación**. Consecuencia: con vigente de otro seccionado
   (las 52 del Congreso con el par 2025/2025, D-65/D-80) la aceptación de la batería no puede salir SÍ.
6. **Excepción de D-66** («excepción explícita en su contrato con su motivo (máximo 2)»): el código solo tiene
   `max_mixed_districts_per_split_municipality` por contrato (todos los contratos versionados lo declaran = 1); no hay un
   campo de excepción por municipio con motivo ni tope de 2.
7. **Canónico distinto en batería y P30**: la batería usa M05 canónico 7.4.4 con semilla fija (`generadores.Canonico`);
   el P30 usa el M06 del run (la versión de M05 activa en el run). Las cifras de la batería no son por tanto las de la 00.
8. **«10 cadenas ReCom» (D-84)**: lo que corre son 10 cadenas «ponderado» (ReCom con árbol de expansión ponderado y
   restricción del núcleo), no el ReCom de producción `m05_gerrychain_strategy` (generador `GerryChain`, solo con la
   función A). D-84 no distingue.
