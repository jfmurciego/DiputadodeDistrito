# T-509 · A1 · Motor Deslinde: código, formulación y escalado

Fecha: 2026-11-28. Código leído: `main` 9e630d11 (Deslinde 1.2, `exacto.py` 1.1.0, `competicion.py` 1.6.0).
Solo lectura y experimentos sintéticos en local (`/tmp/t509_A1_motor/exp.py`, ortools 9.14.6206). No se ha lanzado ni
publicado nada. Datos para la máquina: `A1_motor.json` (10 hallazgos).

## 1. Veredicto

1. El núcleo de reglas es sólido: fracciones exactas, una sola definición de validez y todo candidato se vuelve a juzgar.
2. El exacto (CP-SAT) está bien planteado para instancias pequeñas: simetrías rotas, objetivo entero, tope determinista.
3. Pero su «óptimo demostrado» es el óptimo de **otra clave**: frontera en mm, y la oficial redondea a 1 m (A1-2, reproducido).
4. Dentro de su tamaño (átomos × K ≤ 2.000) **no devuelve nada en 5 de 17 territorios** con K ≥ 5 (T-507).
5. La causa más probable es una pista incompleta: el resolutor olvida un plan que ya tiene (A1-1, mecanismo reproducido).
6. 4 de los 9 mapas que gana el exacto son «el mejor hallado al llegar al tope», y entran en la huella (A1-4).
7. Por encima de 2.000 solo hay 10 cadenas de 300 pasos, sin cota: 7 de 27 provincias y autonomías con K ≥ 5 y Madrid.
8. El modelo monolítico no escala: la cota de la frontera queda al 56 % en Sevilla y al 98 % en mi instancia de 210 átomos.
9. Para ejecutar miles de veces estorban el tiempo del exacto (×2,3), que nada se reutiliza y la variable de entorno.
10. **Liga de hoy: segunda división seria.** Demuestra en K ≤ 4 y en 7 de 27 con K ≥ 5; los mejores demuestran en todo.

## 2. Estado objetivo «referente mundial»

- **Óptimo o cota en todos los territorios**, con el hueco publicado. Validi, Buchanan y Lykhovyd (Operations
  Research 70(2), 2022, <https://pubsonline.informs.org/doi/10.1287/opre.2021.2141>) resuelven al óptimo con contigüidad
  hasta Indiana (1.511 secciones censales): ramificación y corte, contigüidad añadida en callback y fijación de variables
  por Lagrange. Deslinde llega a 372 átomos con K = 3 o 111 con K = 16.
- **Mínimo exacto de demarcaciones partidas**, que es el tercer término de D8: Shahmizad y Buchanan (Operations
  Research 73(2), 2025, <https://pubsonline.informs.org/doi/10.1287/opre.2023.0094>) lo calculan para los estados de
  EE. UU. con programación entera y descomposición, con código y resultados públicos.
- **Certificado verificable por terceros**: instancia canónica, plan y cota sobre la misma función que se publica.
- **Repetición sin condiciones de entorno**: basta la semilla pública; hoy hace falta además `PYTHONHASHSEED=0`.

## 3. La formulación exacta, con precisión

Fichero: `paquetes/deslinde/src/deslinde/exacto.py`. Se aplica con D8, una circunscripción, sin exenciones y
2 ≤ K ≤ 4 o átomos × K ≤ 2.000 (líneas 61-79).

- **Átomos** (105-158): unidades unidas cuando el municipio no se puede partir (⌈población/objetivo⌉ ≤ 1) o comparten
  núcleo cerrado; cada grupo se separa en componentes conexas y las componentes de un grupo van al mismo distrito.
- **Asignación**: `x[i,k]` booleana, una por átomo y distrito (n·K, el «tamaño»); exactamente un distrito por átomo.
- **Población**: `p[k] = Σ pob·x` entre ⌈suelo⌉ y ⌊techo⌋; `dev[k] = den·|p − objetivo|`, entero exacto (188-201).
- **Simetría** (202-213): una raíz `r[i,k]` por distrito, obligada a ser su átomo de menor índice, y `pos[k] < pos[k+1]`.
  Los K! etiquetados equivalentes quedan en uno. Está bien hecho; no es por aquí por donde se gana.
- **Contigüidad** (218-234): árbol padre/nivel. Cada átomo es raíz o elige un vecino padre `pa[i,j]`, que obliga a
  «mismo distrito» (`dd[i] == dd[j]`, igualdad entera semirreificada) y a `nivel[i] ≥ nivel[j] + 1`, con nivel en 0..n−1.
  No hay flujos ni cortes.
- **Disciplina municipal y núcleos** (182-187, 235-269): `y[c,k]` (la clave c toca el distrito k), `mixto[k]`, número
  de distritos por clave entre ⌈P/techo⌉ y ⌈P/objetivo⌉, y como mucho `max_mixtos` distritos mixtos si se parte.
- **Clave D8** (270-308), cinco términos enteros: `fuera` (distritos con dev > tolerancia); `exceso_8`
  (25·den·máx(8 % del objetivo, desvío de los que están dentro)); `partidas` (partidos judiciales y comarcas en más de un
  distrito); `frontera_mm` (suma de mm de las aristas cortadas); `desvio` (dev máximo).
- **Lexicográfica** (327-360): cinco resoluciones seguidas. Tras cada óptimo se añade `término == valor` y se da como
  pista la `x` anterior. Si una etapa no demuestra el óptimo, **se para** y devuelve el mejor plan hallado.
- **Límites**: 60 unidades deterministas por etapa (no segundos), 4 hilos con `interleave_search`, semilla 0. No hay
  tope de reloj. Medido en T-507: de 0 a +131 s por territorio.
- **Tamaño medido**: 210 átomos y K = 7 dan 6.450 variables y 8.112 restricciones.

**Por qué no escala más allá de 2.000:**
1. El árbol padre/nivel casi no propaga ni da relajación lineal útil: **sin pista, el modelo no encuentra ningún plan**
   en 8,5 unidades con tamaño 1.470 (medido). El exacto vive de la pista de las cadenas.
2. La cota de la frontera es muy floja: 98,5 % de hueco tras 10 unidades (medido, 210 átomos); en Sevilla, 56 % a
   60 unidades y entre 9 % y 41 % a 300 (T-502).
3. Cinco resoluciones desde cero: cada una repite el presolve (3,5 unidades de 60 con 210 átomos) y rehace la pista.
4. El 2.000 es «el mínimo que cubre lo medido» (T-502), no una ley de escalado: dentro de él fallan 5 de 17.

## 4. Hallazgos, de mayor a menor impacto

### A1-3 · Escalar con mejora local exacta y descomposición (impacto 5, esfuerzo L; amplía T-468)
- **Hoy:** de 120 contratos, 14 tienen varias circunscripciones y 11 exenciones: NO_APLICA. De los 27 con K ≥ 5 de
  T-507, 7 no caben y Madrid da 10.502. Subir el límite no sirve (sección 3).
- **Propongo**, por orden: (a) **descomposición exacta por circunscripción** (con provincia única y cuotas, un modelo por
  provincia; `fuera`, `partidas` y `frontera` suman; `exceso` y `desvio` son máximos que se coordinan etapa a etapa);
  (b) candidato nuevo de **mejora local exacta**: desde el mejor plan, liberar 2 o 3 distritos vecinos, fijar el resto y
  resolver ese trozo con el mismo `_Modelo`, en orden fijo de vecindarios, hasta que ninguno mejore;
  (c) contigüidad por cortes de separadores solo si (a) y (b) no bastan.
- **Criterio:** con las entradas de T-507, la mejora local alcanza la clave del óptimo demostrado en ≥ 6 de 7 (nac04,
  nac14, nac23, nac33, nac39, aut18, aut19) partiendo del mejor candidato no exacto; mejora al ganador en ≥ 3 de los 7 que
  no caben (nac03, nac46, nac50, aut03, aut06, aut15, aut17); ≤ 120 s por territorio; misma huella en dos ejecuciones.
- **Riesgo:** un óptimo local no es un óptimo demostrado; necesita otro nombre de estado.

### A1-1 · El exacto olvida la solución que ya tiene (impacto 4, esfuerzo S)
- **Hoy:** la pista solo fija `x` (`exacto.py:329-332` y `350-353`). En T-507, nac06, nac17, nac18, nac31 y nac45
  salen SIN_SOLUCION con un plan válido disponible: +215 s y ningún resultado.
- **Medido** (210 átomos, K = 7): sin pista, UNKNOWN; pista de `x`, 7,5 s y 12.676 ramas para recuperar el plan; pista de
  todas las variables (factibilidad con `x` fija, 0,05 s), 1,4 s y 0 ramas. Con el bucle de etapas actual, la etapa
  `partidas` acaba UNKNOWN y pierde el plan de la etapa anterior; con pista completa conserva el valor.
- **Propongo:** completar la pista antes de la etapa 1 y pasar la solución entera entre etapas. Sube `MODELO` a 1.1.0.
- **Criterio:** en los 5 territorios, `exacto.estado != SIN_SOLUCION` y clave del exacto ≤ la del mejor previo; en los 17
  aplicables ningún ganador empeora; misma `huella_resultado` en dos ejecuciones.
- **Riesgo:** cambia huellas y quizá ganadores (P30 y republicación). La reproducción es sintética (sección 8).

### A1-2 · El «óptimo demostrado» es de otra clave (impacto 4, esfuerzo S)
- **Hoy:** el modelo suma mm enteros (`exacto.py:298`); la clave oficial hace `round(suma/1000, 3)` en coma flotante
  (`naturalidad_clave.py:66`), es decir, 1 m, y luego desempata por desvío. El exceso oficial resta el float 0.08 (línea 83).
- **Reproducido:** camino a-b-c-d (47, 3, 3, 47 hab.), K = 2. El exacto devuelve `OPTIMO` con a|bcd, clave oficial
  (0, 0.0, 0, 1.0, 3/50). El plan ab|cd es válido y su clave es (0, 0.0, 0, 1.0, 0): **estrictamente mejor**.
- **Propongo:** frontera en una sola unidad entera (mm o m) en la clave y en el modelo; exceso con `Fraction(2, 25)`.
- **Criterio:** en 200 instancias aleatorias de ≤ 12 unidades, la clave oficial del plan OPTIMO es igual al mínimo por
  enumeración; el caso de arriba devuelve ab|cd.
- **Riesgo:** cambia el último decimal de D8 y todas las huellas del motor.

### A1-4 · 4 de los 9 mapas del exacto dependen de un tope y entran en la huella (impacto 4, esfuerzo M)
- **Hoy:** nac12, nac15, nac41 y nac43 ganan con `MEJOR_VALIDO`. T-502 vio la cota cambiar entre dos ejecuciones
  idénticas (345 M y 355 M); T-503 sacó la cota de la huella, pero el plan sigue dentro y su repetición está probada
  con 2 ejecuciones en una máquina. Entre planes empatados, el que sale depende de la pista y de la versión de ortools.
- **Medido:** en mi instancia, 3 ejecuciones dan valor, cota y conflictos idénticos; la variación no se reproduce ahí.
- **Propongo:** prueba de repetición (5 territorios × 5 veces en local y 1 en runner); etapa final canónica (función
  lineal fija de `x`) para que un OPTIMO dependa solo de la instancia.
- **Criterio:** una sola `huella_plan` por territorio en las 30 ejecuciones; dos pistas distintas, mismo plan OPTIMO.

### A1-6 · Miles de ejecuciones: el exacto multiplica por 2,3 el tiempo y nada se reutiliza (impacto 4, esfuerzo M)
- **Hoy:** en los 17 aplicables con K ≥ 5, de 859 s a 1.956 s (suma de T-507). `produccion.py:264` borra y recalcula.
  El resultado del exacto es función pura de la instancia. Las 10 cadenas van en serie en un núcleo.
- **Propongo:** instancia canónica con sha256; almacén de certificados por esa huella (se verifica en milisegundos con
  `evaluar` y la clave, no se resuelve); cadenas en procesos paralelos.
- **Criterio:** segunda competición de nac41 con certificado: mismo ganador y huella, ≤ 40 s (hoy 113-149 s); un
  certificado alterado se rechaza y se resuelve de nuevo.

### A1-5 · Al primer tope se para (impacto 3, esfuerzo S)
- **Hoy:** `exacto.py:357-359`. Si no cierra `partidas`, frontera y desvío no se optimizan. Dato compatible: nac43
  baja de 7 a 6 demarcaciones y la frontera sube de 302,5 a 467,2 km.
- **Propongo:** tras una etapa sin prueba, añadir `término ≤ valor` y seguir.
- **Criterio:** en los 5 `MEJOR_VALIDO`, clave ≤ la actual término a término y al menos uno mejora; tiempo ≤ 1,2 ×.

### A1-7 · El «exhaustivo» optimiza la clave A en una competición D8 (impacto 3, esfuerzo S)
- **Hoy:** `exhaustivo.py:73-74` ordena con `calidad.metricas` (función A); producción elige con D8.
- **Propongo:** pasar la clave de la competición. **Criterio:** con D8 y ≤ 40 unidades, el exhaustivo tiene clave ≤ la
  de todos los candidatos y coincide con el exacto donde ambos aplican.

### A1-8 · `PYTHONHASHSEED=0` obligatorio y sin guarda en la CLI de la batería (impacto 3, esfuerzo S)
- **Hoy:** `ddd_motor2/competir.py` no lo comprueba (solo aparece en el docstring); `produccion.py` y `deslinde` sí.
- **Propongo:** guarda en `competir_publico`; después, quitar la causa (enteros y `sorted` en el grafo de la cadena).
- **Criterio:** con `PYTHONHASHSEED=1` sale con 6 o, tras quitar la causa, da la misma huella con 0, 1 y sin fijar.

### A1-10 · El lock del exacto no basta solo y Sevilla nunca corre en la CI (impacto 3, esfuerzo S)
- **Medido:** venv limpio + `requirements-exacto.lock --no-deps`: `ModuleNotFoundError: numpy`. El test de Sevilla
  necesita entradas que no están en git: «en la CI siempre sale saltado» (registro de T-503).
- **Propongo:** versionar 3 instancias canónicas pequeñas con su clave óptima y un test que las resuelva.
- **Criterio:** `pruebas` ejecuta (no salta) el test de nac41 y exige 6 demarcaciones y 785.968.300 mm.

### A1-9 · Unas 50 lecturas del mismo grafo y una cota 3 veces más lenta (impacto 2, esfuerzo M)
- **Hoy:** `adaptadores.py:296` y `naturalidad_clave.py:186` parsean el grafo M03 en cada juicio y en cada cadena
  (28 + 24 llamadas contadas en el código). `cota.py:90` llama a `evaluar` completo hasta 20.000 veces.
- **Medido** (210 unidades): `evaluar` 0,833 ms frente a `valido(ctx)` 0,266 ms; 16,7 s frente a 5,3 s por 20.000.
- **Criterio:** `json.loads` del grafo ≤ 2 veces por competición; misma huella; `cota_nodos` ≤ 40 % del tiempo.

## 5. Mejoras de formulación y de búsqueda, por beneficio esperado

| # | Mejora | Fichero | Experimento barato | Criterio |
|---|---|---|---|---|
| 1 | Pista completa (A1-1) | `exacto.py` | 5 territorios SIN_SOLUCION, 10 min de CPU | ninguno SIN_SOLUCION |
| 2 | No parar al primer tope (A1-5) | `exacto.py` | 5 territorios MEJOR_VALIDO | clave ≤ actual, uno mejora |
| 3 | Mejora local exacta, 2-3 distritos (A1-3 b) | candidato nuevo en `deslinde/` | 14 territorios, 60 min | ≥ 6 de 7 óptimos; ≥ 3 de 7 mejoran |
| 4 | Descomposición por circunscripción (A1-3 a) | `exacto.py` | 3 autonómicas con K por provincia ≤ 12 | misma clave que el modelo entero donde este cabe |
| 5 | Certificados por huella de instancia (A1-6) | `competicion.py` | nac41 dos veces | ≤ 40 s la segunda |
| 6 | Etapa canónica de desempate (A1-4) | `exacto.py` | 3 instancias, 2 pistas | mismo plan |
| 7 | Cortes lineales de frontera `c ≥ x_ik − x_jk` | `exacto.py` | Sevilla, etapa 4 a 60 y 300 unidades | hueco ≤ 25 % a 60 |
| 8 | Contigüidad por flujos o por cortes de separadores | `exacto.py` | La Rioja autonómica (E1 no cierra, T-296) | encuentra plan sin pista |
| 9 | Rotura de simetrías adicional | — | — | no la propongo: ya está resuelta |

La 7 la probé en pequeño: con 10 unidades el hueco pasa de 98,5 % a 98,4 %. **No concluyente**; hay que medirla en
Sevilla con el tope real antes de darle prioridad.

## 6. Qué estorba hoy para ejecutar el motor miles de veces

- **El exacto**: +1.097 s en 17 territorios; 215 s de ellos sin resultado. Sin certificados reutilizables.
- **Entradas y salidas**: composición y grafo releídos por candidato; cada candidato escribe su CSV y se relee para
  juzgarlo; `P30` borra la carpeta al empezar.
- **Un núcleo para las cadenas** y 4 hilos fijos para CP-SAT: dos competiciones a la vez se pisan (T-507 lo anota).
- **Dependencias y entorno**: `PYTHONHASHSEED=0`, ortools con numpy y pandas de otro lock, gerrychain fijado; la huella
  incluye la versión de ortools, así que actualizarla cambia todas las huellas con exacto.
- **Sin prueba automática con instancia real** de K ≥ 5: cada cambio del exacto exige una medición manual en local.

## 7. Camino en tres pasos

1. **Esta semana:** A1-1, A1-5 y A1-2 en una PR de motor, y la prueba de repetición de A1-4. Prueba: los 5 SIN_SOLUCION
   devuelven plan, el test de propiedad de la clave pasa y hay una sola `huella_plan` por territorio en 30 ejecuciones.
2. **Este mes:** instancias canónicas en la CI (A1-10), certificados reutilizables (A1-6), exhaustivo con D8 (A1-7) y
   guarda de entorno (A1-8). Prueba: segunda competición de nac41 en ≤ 40 s con la misma huella.
3. **Este trimestre:** descomposición por circunscripción y mejora local exacta (A1-3), con cota publicada donde no
   haya óptimo (T-468). Prueba: una línea por territorio, «óptimo demostrado», «óptimo local» o «a tanto como mucho»,
   en los 120 contratos.

## 8. Lo que no pude comprobar

- **Que la pista parcial sea la causa en los 5 territorios reales.** No tenía las entradas de la batería (sin R2 ni
  seccionados). Mi instancia es una rejilla con un municipio por unidad, sin núcleos. Se comprueba con el experimento 1.
- **Que la variación de la cota de T-502 afecte al plan.** En mi instancia no hay variación. Se comprueba con A1-4.
- **El tiempo real de las relecturas del grafo** (A1-9): contado en el código, no cronometrado. Hace falta un `cProfile`.
- **Que quitar `PYTHONHASHSEED` baste con enteros y `sorted`** (A1-8): hipótesis; no instalé gerrychain.
- **Madrid** y **Vizcaya** (nac48, FALLO_M04 en la nube): no medidos por nadie con el exacto.
- Las lecturas externas son de resumen y ficha de revista; no abrí los artículos completos.

## 9. Objeciones (D-216)

- **El criterio de #1037** («ninguno pasa de 10 min, luego `TAMANO_MAX` = 2.000 se mantiene») mide tiempo, no
  utilidad: 5 de 17 no devuelven nada. Propongo añadir «todo territorio aplicable devuelve plan».
- **La republicación del 29-11** incluye 4 mapas `MEJOR_VALIDO` (nac12, nac15, nac41, nac43). La prueba de repetición
  cuesta unos 30 min de CPU y debería ir antes.
- **«Óptimo demostrado»** en textos públicos: mientras la clave del modelo y la oficial difieran (A1-2), la frase
  exacta es «óptimo demostrado con la frontera medida en milímetros».

## 10. Reproducir los experimentos

```
python3 -m venv V && V/bin/pip install --no-deps --require-hashes -r requirements-exacto.lock
V/bin/pip install numpy pandas==2.3.2        # el lock del exacto no los trae (A1-10)
PYTHONHASHSEED=0 V/bin/python exp.py redondeo                     # A1-2
PYTHONHASHSEED=0 V/bin/python exp.py pista 15 14 7 8 sin|x|completa   # A1-1
PYTHONHASHSEED=0 V/bin/python exp.py etapas 15 14 7 5 x|full         # A1-1 y A1-5
PYTHONHASHSEED=0 V/bin/python exp.py corte 15 14 7 10 actual|lineal  # sección 5, fila 7
PYTHONHASHSEED=0 V/bin/python exp.py evaluar 15 14 7                 # A1-9
```
`exp.py` está en `/tmp/t509_A1_motor/` (temporal, 243 líneas): construye el `Problema`, las `Reglas` y el `Natural`
sintéticos y llama a `deslinde.exacto._Modelo` sin tocar el repositorio. Si se quiere conservar, va a
`docs/ESTUDIOS/T509_A1_MOTOR/`.
