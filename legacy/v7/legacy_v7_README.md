# legacy/v7 — motor de distritación v7 (marzo 2026)

**Estado:** archivado. No ejecutar.
**Motivo de conservación:** contiene dos capacidades que el motor actual **no tiene** y
que hay que trasplantar: la restricción de comarca y la nomenclatura de distritos.

---

## Qué es esto

La implementación completa del procedimiento en ocho pasos, anterior a la reescritura
modular a `modulos/` + `ddd_core/`. Se dio por perdida durante meses; los ficheros se
recuperaron en septiembre de 2026 desde el equipo local del autor.

| Fichero | Paso |
|---|---|
| `ddd_step1_build_sections_v7_params.py` | base territorial y unión de comarcas |
| `ddd_step2_export_edges_v7_params.py` | adyacencias |
| `ddd_step3_build_graph_v7_params.py` | grafo, con `comarca_id` como atributo de nodo |
| `ddd_step4_seed_districts_v7_params.py` | semillas con crecimiento consciente de comarca |
| `ddd_step5_optimize_swaps_v7_params.py` | **recocido simulado multiobjetivo** |
| `ddd_step6_export_final_v7_params.py` | consolidación y **nomenclatura de distritos** |
| `ddd_step7_aggregate_elections_v7_params.py` | agregación electoral |
| `ddd_step8_join_results_v7_params.py` | integración de resultados |

**No es el motor de referencia.** Su ejecución de marzo de 2026 produjo un distrito de
134 habitantes formado por una sola sección. El motor actual resolvió ese defecto y es
mejor en equilibrio poblacional y en disciplina municipal. Este código se conserva por
lo que sabe hacer y el actual no, no como alternativa.

---

## Capacidad 1 — restricción de comarca

El motor actual optimiza **solo población**. El v7 optimizaba dos cosas:

```
score = α · desviación_cuadrática_media_relativa  +  γ · fracción_de_violación_comarcal
```

Valores por defecto: `alpha_pop: 0.70`, `gamma_comarca: 0.10`.

**Definición de la violación** (`ddd_step5_optimize_swaps_v7_params.py`, función `score`):
para cada distrito se determina su comarca dominante por número de secciones, y cuenta
como violación toda sección que pertenezca a otra comarca. El término es la fracción de
secciones en violación sobre el total.

**Delta incremental por movimiento** (mismo fichero, bloque «Comarca delta»): al mover
una sección de un distrito a otro se compara si era violación en origen (`was_bad`) y si
lo será en destino (`will_bad`), y se aplica `γ · (will_bad − was_bad) / total_secciones`.
No encarece la iteración, que es la razón de que 300.000 iteraciones fueran viables.

**Salvaguarda:** si ninguna sección trae `comarca_id`, el paso fija `gamma = 0` e informa
`[Step5] Sin comarca → gamma=0`. Un territorio sin dato comarcal degrada a monoobjetivo
en lugar de romperse.

**El paso 4 también la usaba**, con un mecanismo distinto: `comarca_priority_weight: 1.5`
penaliza el cruce de comarca durante el crecimiento de las semillas, de modo que el mapa
ya nace respetándolas en lugar de tener que corregirse después.

**Cadena del dato:** el paso 1 une un CSV municipio→comarca al seccionado por clave de
municipio y reporta cuántos municipios quedan sin casar; el paso 3 lo propaga al grafo
como `comarca_id` por nodo, con autodetección de columnas si el YAML no las declara.

### Por qué hay que recuperarla

El mapa actual de Castilla y León contiene el **distrito 31**: 29 municipios, 36
secciones, 28.736 habitantes, y una extensión de 72 km que va desde Molinaseca y Torre
del Bierzo hasta Pozuelo del Páramo, en la raya de Zamora. Une El Bierzo con La
Valduerna. Su Polsby-Popper es 0,086 y su desviación poblacional **−1,87 %**: es casi
perfecto en lo único que el sistema mide, y por eso nadie lo detectó.

Con la restricción comarcal activa, ese salto tiene coste y el optimizador lo evita.

---

## Capacidad 2 — nomenclatura de distritos

El motor actual produce distritos identificados por un entero. El v7 generaba
`district_name` en el paso 6 y lo propagaba a las secciones para que los pasos 7 y 8 lo
heredaran.

El criterio era doble: **comarca dominante** para los distritos rurales, calculada por
votación de secciones sobre los atributos comarcales; y **posición cardinal respecto a
la capital** para los urbanos, transformando las coordenadas de la capital a EPSG:25830
y comparando con el centroide métrico del distrito disuelto.

Un mapa de 82 polígonos numerados del 0 al 81 no es una propuesta publicable. Esta
capacidad es condición para publicar, y se perdió sin sustituto.

---

## Cómo trasplantarlo

**No portar el motor.** Portar los dos mecanismos al motor actual, que comparte
estructura —recorrido de frontera y aceptación por recocido— y donde esto es añadir un
término al score y un campo al nodo, no reescribir nada.

Secuencia recomendada:

1. **Solo Aragón primero.** Es el único territorio con dato comarcal limpio: 33 comarcas
   con entidad legal y correspondencia municipio→comarca inequívoca.
2. **En rama, con barrido de `gamma`.** Medir para cada valor el `maxdev` resultante y la
   distribución de compacidad. Esa tabla es la decisión que hasta ahora se ha tomado sola.
3. **Refijar los trinquetes después, con justificación escrita.** Con `gamma > 0`, Aragón
   dejará de dar 0,099299365905 y Castilla y León 0,119836116709, y ambas regresiones
   saltarán. Es el comportamiento correcto. Lo que no se admite es relajar un umbral para
   que pase: se mide, se decide y se documenta el nuevo valor.

### Advertencias

- **`gamma: 0.10` frente a `alpha: 0.70` es un peso bajo.** Con esa proporción la comarca
  solo desempata entre movimientos poblacionalmente equivalentes. Para eliminar casos como
  el distrito 31 probablemente haga falta subirlo, y eso empeorará el equilibrio
  poblacional. Ese intercambio hay que ponerle un número, no dejarlo implícito.
- **El dato comarcal solo existe limpio para Aragón.** En Castilla y León solo El Bierzo
  tiene estatuto propio; La Valduerna, la Maragatería o Tierra de Campos son comarcas
  tradicionales sin delimitación oficial única. Extremadura está en situación parecida.
  Elegir una delimitación es una decisión del proyecto, no un problema técnico, y debe
  quedar escrita antes de ejecutar.
- **El paso 4 y el paso 5 usan la comarca de forma distinta** —prioridad en el crecimiento
  frente a penalización en el intercambio— y conviene portar ambos. Corregir después lo que
  el sembrado hizo mal es más caro que sembrar bien.

---

## Procedencia

Ficheros recuperados del equipo local del autor en septiembre de 2026 y archivados sin
modificación. No se ha verificado que ejecuten con las versiones de librerías actuales
ni se ha reproducido su ejecución de marzo de 2026.
