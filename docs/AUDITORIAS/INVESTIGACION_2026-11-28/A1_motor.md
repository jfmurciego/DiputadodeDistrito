# T-509 · A1 · Motor Deslinde: código, formulación y escalado

Fecha: 2026-11-28. Código leído: `main` 9e630d11 (Deslinde 1.2, `exacto.py` 1.1.0, `competicion.py` 1.6.0).
Solo lectura y experimentos sintéticos en local (`/tmp/t509_A1_motor/exp.py`, ortools 9.14.6206). No se ha lanzado ni
publicado nada. Datos para la máquina: `A1_motor.json` (10 hallazgos).

**Verificado por un escéptico independiente el 28-11** (sección 11): 9 hallazgos revisados, 1 confirmado, 8 corregidos, ninguno refutado.
Este texto ya lleva las correcciones.

## 1. Veredicto

1. El núcleo de reglas es sólido: fracciones exactas, una sola definición de validez y todo candidato se vuelve a juzgar.
2. El exacto (CP-SAT) está bien planteado para instancias pequeñas: simetrías rotas, objetivo entero, tope determinista.
3. Pero su «óptimo demostrado» es el óptimo de **otra clave**: frontera en mm, y la oficial redondea a 1 m (A1-2, reproducido).
   Solo cambia el resultado entre planes a menos de 1 m; no hay caso real conocido.
4. Dentro de su tamaño (átomos × K ≤ 2.000) **no devuelve nada en 5 de 17 territorios** con K ≥ 5 (T-507).
5. La causa **no está probada**. La pista incompleta es una candidata (A1-1), pero en la prueba sintética no basta para
   explicarlo y los tiempos de T-507 apuntan a que el exacto acaba antes del tope. Primero, diagnóstico.
6. 4 de los 9 mapas que gana el exacto son «el mejor hallado al llegar al tope», y entran en la huella (A1-4). Nadie ha
   visto cambiar el plan, pero solo Sevilla se ha repetido.
7. Por encima de 2.000 solo hay 10 cadenas de 300 pasos, sin cota: 7 de 27 provincias y autonomías con K ≥ 5 y Madrid.
8. El modelo monolítico no escala: la cota de la frontera queda al 56 % en Sevilla y al 98 % en mi instancia de 210 átomos.
9. Para ejecutar miles de veces estorban el tiempo del exacto (×2,3), que nada se reutiliza y la variable de entorno.
10. **Liga de hoy: segunda división seria.** Demuestra en K ≤ 4 y en 7 de 27 con K ≥ 5; los mejores demuestran en todo.

## 2. Estado objetivo «referente mundial»

- **Óptimo o cota en todos los territorios**, con el hueco publicado. Validi, Buchanan y Lykhovyd (Operations
  Research 70(2), 2022, <https://pubsonline.informs.org/doi/10.1287/opre.2021.2141>) resuelven al óptimo con contigüidad
  hasta Indiana (1.511 secciones censales): ramificación y corte, contigüidad añadida en callback y fijación de variables
  por Lagrange. Deslinde demuestra hasta 372 átomos con K = 3 (Burgos) y, con K ≥ 5, hasta tamaño 640; Sevilla (111
  átomos, K = 16) queda en `MEJOR_VALIDO`, sin prueba.
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

Impactos y textos tras la verificación independiente (sección 11).

### A1-1 · El exacto no devuelve nada en 5 de 17 territorios; causa sin probar (impacto 4, esfuerzo S)
- **Hoy (hechos):** en T-507 (#1037, abierta), nac06, nac17, nac18, nac31 y nac45 salen SIN_SOLUCION con un plan válido
  disponible: +215 s y ningún resultado. La pista solo fija `x` (`exacto.py:329-332` y `350-353`).
- **Hipótesis, no probada:** que lo segundo cause lo primero. T-507 no guardó el estado de las etapas ni si la pista
  llegó a aplicarse (`etiquetas()` devuelve `None` si el plan parte un átomo; si las unidades del mejor candidato no
  coinciden, la pista es el canónico).
- **Medido** (210 átomos, K = 7; repetido por el escéptico): pista de `x`, 7,6 s y 12.676 ramas; pista completa, 1,5 s y
  0 ramas; **las dos consumen 3,5 de 60 unidades deterministas**, así que la pista de `x` no agota el tope. Con tope de
  5 unidades, la etapa `partidas` acaba UNKNOWN con pista de `x` y FEASIBLE con pista completa; en el código real eso
  daría `MEJOR_VALIDO`, no SIN_SOLUCION.
- **Indicio en contra:** cuatro de los cinco añaden solo +18 a +43 s; los `MEJOR_VALIDO`, que sí agotan un tope,
  +119 a +131 s. No se descarta que la primera etapa salga INFEASIBLE o que no hubiera pista.
- **Propongo:** (0) diagnóstico: repetir los 5 guardando etapas y «pista aplicada: sí/no»; (1) solo si es UNKNOWN con
  pista aplicada, completar la pista antes de la etapa 1 y (2) pasar la solución entera entre etapas.
- **Criterio:** paso 0 (unos 8 min de CPU): tabla con el estado de la primera etapa de los 5. Pasos 1-2, donde toque:
  `exacto.estado != SIN_SOLUCION` y clave del exacto ≤ la del mejor previo; en los 17 aplicables ningún ganador empeora;
  misma `huella_resultado` en dos ejecuciones.
- **Riesgo:** el arreglo de la pista puede no cambiar nada. Si funciona, cambia huellas y quizá ganadores.

### A1-4 · 4 de los 9 mapas del exacto son `MEJOR_VALIDO` y entran en la huella (impacto 4, esfuerzo M)
- **Hoy:** nac12, nac15, nac41 y nac43 ganan con `MEJOR_VALIDO` (tope de 60 unidades deterministas, no de tiempo). T-502
  y T-503 vieron la cota cambiar entre ejecuciones idénticas (345 M y 355 M; 361,7 M y 384,5 M); T-503 sacó la cota de
  la huella, pero el plan sigue dentro. **Nadie ha visto cambiar el plan**: Sevilla se ha repetido dos veces en T-502 y
  dos en T-503; nac12, nac15, nac20 y nac43 solo se han ejecutado una vez.
- **Medido:** en la rejilla, 4 ejecuciones (3 del autor y 1 del escéptico) dan valor, cota y conflictos idénticos.
- **Hipótesis sin probar:** que entre planes empatados el que sale dependa de la pista. En un ciclo simétrico de 4
  unidades, tres pistas distintas devuelven el mismo plan.
- **Propongo:** prueba de repetición **antes de la republicación del 29-11** (5 territorios × 5 veces en local; una más
  en runner cuando el propietario autorice lanzarla); etapa final canónica para que un OPTIMO dependa solo de la instancia.
- **Criterio:** una sola `huella_plan` del exacto por territorio en las 25 ejecuciones locales (unos 60 min de CPU); un
  test con empate exacto devuelve el mismo plan con cualquier orden de unidades y cualquier pista válida.
- **Riesgo:** si falla, los 4 territorios que se van a publicar con el exacto el 29-11 necesitan otra regla antes.

### A1-3 · Escalar con mejora local exacta y descomposición (impacto 4, esfuerzo L; amplía T-468 y T-467)
- **Hoy:** de 120 contratos, 14 tienen varias circunscripciones y 11 solo exenciones: NO_APLICA. De los 27 con K ≥ 5 de
  T-507, 7 no caben y Madrid da 10.502. Subir el límite no sirve (sección 3). De los 14, 5 tienen además exenciones
  (aut01, aut04, aut05, nac07, nac35): la descomposición sola desbloquea 9 como mucho, y nadie ha medido si sus trozos caben.
- **Propongo**, por orden: (a) **descomposición exacta por circunscripción** (un modelo por provincia; `fuera`,
  `partidas` y `frontera` suman; `exceso` y `desvio` son máximos que se coordinan etapa a etapa);
  (b) candidato nuevo de **mejora local exacta**: desde el mejor plan, liberar 2 o 3 distritos vecinos, fijar el resto y
  resolver ese trozo con el mismo `_Modelo`, en orden fijo de vecindarios, hasta que ninguno mejore;
  (c) contigüidad por cortes de separadores solo si (a) y (b) no bastan.
- **Criterio:** (b) con las entradas de T-507, la mejora local alcanza la clave del óptimo demostrado en ≥ 6 de 7 (nac04,
  nac14, nac23, nac33, nac39, aut18, aut19) partiendo del mejor candidato no exacto; mejora al ganador en ≥ 3 de los 7 que
  no caben; ≤ 120 s por territorio; misma huella en dos ejecuciones. (a) Tabla previa con el tamaño de cada
  circunscripción de los 9 contratos sin exenciones; nac38 deja de dar NO_APLICA; en una instancia sintética de dos
  circunscripciones, misma clave que el modelo entero.
- **Riesgo:** un óptimo local no es un óptimo demostrado; necesita otro nombre de estado. No sustituye a la cota de T-468.
- **Ya previsto:** T-468 (cotas) y T-467 (búsqueda, «solo si hace falta») son propuestas del plan de mejora del 25-11, sin
  aprobar (D-214) y sin fila en `docs/PLAN.md`.

### A1-2 · El «óptimo demostrado» es de otra clave (impacto 3, esfuerzo S)
- **Hoy:** el modelo suma mm enteros (`exacto.py:298`); la clave oficial hace `round(suma/1000, 3)` en coma flotante
  (`naturalidad_clave.py:66`), es decir, 1 m, y luego desempata por desvío. El exceso oficial resta el float 0.08 (línea 83).
- **Reproducido** (autor y escéptico): camino a-b-c-d (47, 3, 3, 47 hab.), K = 2. El exacto devuelve `OPTIMO` con a|bcd,
  clave oficial (0, 0.0, 0, 1.0, 3/50). El plan ab|cd es válido y su clave es (0, 0.0, 0, 1.0, 0): **estrictamente mejor**.
- **Alcance:** solo entre planes cuya frontera difiere en menos de 1 m. Sin caso real conocido.
- **Propongo:** frontera en una sola unidad entera (mm o m) en la clave y en el modelo; exceso con `Fraction(2, 25)`.
- **Criterio:** test que hoy falla: 200 instancias de ≤ 12 unidades, al menos 50 con fronteras a menos de 1 m entre
  planes válidos; la clave oficial del plan OPTIMO es igual al mínimo por enumeración; el caso de arriba devuelve ab|cd.
- **Riesgo:** cambia el último decimal de D8 y todas las huellas del motor.

### A1-6 · El exacto multiplica por 2,3 el tiempo y nada se reutiliza (impacto 3, esfuerzo M)
- **Hoy:** en los 17 aplicables con K ≥ 5, de 859 s a 1.956 s (suma de T-507). `produccion.py:264` borra y recalcula.
  El resultado del exacto depende de la instancia **y de la pista** (el mejor candidato previo). Las 10 cadenas van en
  serie en un núcleo.
- **Propongo:** instancia canónica con sha256; almacén de certificados cuya clave incluye esa huella, `MODELO`, ortools y
  la huella de la pista (se verifica en milisegundos con `evaluar` y la clave, no se resuelve); cadenas en paralelo.
- **Criterio:** segunda competición de nac41 con certificado: mismo ganador y huella que sin él, ≤ 40 s (hoy 113-149 s);
  un certificado alterado, o con otra pista, no se usa y se resuelve de nuevo.
- **Riesgo:** ahorra unos 18 min por pasada de 17 territorios y añade un almacén que invalidar. Roza la regla del
  propietario del 08-11 («no conservar resultados antiguos»): lo decide él.

### A1-5 · Al primer tope se para (impacto 3, esfuerzo S)
- **Hoy:** `exacto.py:357-359`. Si no cierra `partidas`, frontera y desvío no se optimizan. Dato compatible: nac43
  baja de 7 a 6 demarcaciones y la frontera sube de 302,5 a 467,2 km.
- **Propongo:** tras una etapa sin prueba, añadir `término ≤ valor` y seguir.
- **Criterio:** en los 5 `MEJOR_VALIDO`, clave lexicográficamente ≤ la actual y al menos uno baja frontera o desvío;
  cada etapa añadida, ≤ 60 unidades; tiempo ≤ 2 × el actual; misma `huella_plan` en dos ejecuciones.

### A1-8 · `PYTHONHASHSEED=0` obligatorio y sin guarda en la CLI de la batería (impacto 3, esfuerzo S)
- **Hoy:** `ddd_motor2/competir.py` no lo comprueba (solo aparece en el docstring); `produccion.py` y `deslinde` sí, y
  los flujos P20 y P80 lo fijan: producción está protegida, el hueco es la CLI de medición.
- **Propongo:** guarda en `competir_publico`; después, quitar la causa (enteros y `sorted` en el grafo de la cadena).
- **Criterio:** con `PYTHONHASHSEED=1` sale con 6 o, tras quitar la causa, da la misma huella con 0, 1 y sin fijar.

### A1-10 · El lock del exacto no basta solo y Sevilla nunca corre en la CI (impacto 3, esfuerzo S)
- **Medido:** venv limpio + `requirements-exacto.lock --no-deps`: `ModuleNotFoundError: numpy`. El test de Sevilla
  necesita entradas que no están en git: «en la CI siempre sale saltado» (registro de T-503).
- **Propongo:** versionar 3 instancias canónicas pequeñas que cierren OPTIMO (p. ej. nac39, nac14, nac04) y un test.
- **Criterio:** `pruebas` ejecuta (no salta) el test de una instancia OPTIMO (p. ej. nac39) y exige estado y los cinco
  valores de etapa; ≤ 2 min más de CI. No se exige el valor de nac41: es `MEJOR_VALIDO` (A1-4).

### A1-7 · El «exhaustivo» optimiza la clave A en una competición D8 (impacto 2, esfuerzo S)
- **Hoy:** `exhaustivo.py:73-74` ordena con `calidad.metricas` (función A); producción elige con D8. Sin caso real
  conocido: donde el exacto no aplica por circunscripciones o exenciones, K ≥ 7 y la enumeración no consta completa.
- **Propongo:** pasar la clave de la competición. **Criterio:** con D8 y ≤ 40 unidades, el exhaustivo tiene clave ≤ la
  de todos los candidatos y coincide con el exacto donde ambos aplican.

### A1-9 · Unas 50 lecturas del mismo grafo y una cota 3 veces más lenta (impacto 2, esfuerzo M; sin verificar)
- **Hoy:** `adaptadores.py:296` y `naturalidad_clave.py:186` parsean el grafo M03 en cada juicio y en cada cadena
  (28 + 24 llamadas contadas en el código). `cota.py:90` llama a `evaluar` completo hasta 20.000 veces.
- **Medido** (210 unidades): `evaluar` 0,833 ms frente a `valido(ctx)` 0,266 ms; 16,7 s frente a 5,3 s por 20.000.
- **Criterio:** `json.loads` del grafo ≤ 2 veces por competición; misma huella; `cota_nodos` ≤ 40 % del tiempo.

## 5. Mejoras de formulación y de búsqueda, por beneficio esperado

| # | Mejora | Fichero | Experimento barato | Criterio |
|---|---|---|---|---|
| 1 | Diagnóstico de los 5 SIN_SOLUCION y, si procede, pista completa (A1-1) | `exacto.py` | 5 territorios, 10 min de CPU | causa identificada; ninguno SIN_SOLUCION |
| 2 | No parar al primer tope (A1-5) | `exacto.py` | 5 territorios MEJOR_VALIDO | clave lexicográfica ≤ actual, uno mejora |
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

1. **Esta semana:** antes del 29-11, la prueba de repetición de A1-4 y el diagnóstico de los 5 SIN_SOLUCION (A1-1);
   después, A1-1 (si procede), A1-5 y A1-2 en una PR de motor. Prueba: una sola `huella_plan` por territorio en 25
   ejecuciones, causa de los SIN_SOLUCION identificada y el test de propiedad de la clave pasa.
2. **Este mes:** instancias canónicas en la CI (A1-10), certificados reutilizables (A1-6), exhaustivo con D8 (A1-7) y
   guarda de entorno (A1-8). Prueba: segunda competición de nac41 en ≤ 40 s con la misma huella.
3. **Este trimestre:** descomposición por circunscripción y mejora local exacta (A1-3), con cota publicada donde no
   haya óptimo (T-468). Prueba: una línea por territorio, «óptimo demostrado», «óptimo local» o «a tanto como mucho»,
   en los 120 contratos.

## 8. Lo que no pude comprobar

- **Que la pista parcial sea la causa en los 5 territorios reales.** No tenía las entradas de la batería (sin R2 ni
  seccionados). Mi instancia es una rejilla con un municipio por unidad, sin núcleos. El escéptico añade que la prueba
  sintética no lo respalda (mismo consumo determinista con las dos pistas). Se comprueba con el paso 0 de A1-1.
- **Que el plan de un OPTIMO dependa de la pista en los empates** (A1-4): hipótesis; no se reproduce en un caso simétrico.
- **Que la variación de la cota de T-502 afecte al plan.** En mi instancia no hay variación. Se comprueba con A1-4.
- **El tiempo real de las relecturas del grafo** (A1-9): contado en el código, no cronometrado. Hace falta un `cProfile`.
- **Que quitar `PYTHONHASHSEED` baste con enteros y `sorted`** (A1-8): hipótesis; no instalé gerrychain.
- **Madrid** y **Vizcaya** (nac48, FALLO_M04 en la nube): no medidos por nadie con el exacto.
- Las lecturas externas son de resumen y ficha de revista; no abrí los artículos completos.

## 9. Objeciones (D-216)

- **El criterio de #1037** («ninguno pasa de 10 min, luego `TAMANO_MAX` = 2.000 se mantiene») mide tiempo, no
  utilidad: 5 de 17 no devuelven nada. Propongo añadir «todo territorio aplicable devuelve plan».
- **La republicación del 29-11** incluye 4 mapas `MEJOR_VALIDO` (nac12, nac15, nac41, nac43). La prueba de repetición
  cuesta unos 60 min de CPU (25 competiciones de 2 a 3 min) y debería ir antes.
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

## 11. Verificación independiente (escéptico, 28-11)

Quien construye no certifica. Otro agente ha reproducido la evidencia de los hallazgos de impacto 5, 4 y 3 (9 de 10; A1-9
queda sin revisar) contra `origin/main` 548968c4. El motor no ha cambiado desde #1035 y #1037 (T-507) sigue abierta.
Guiones del escéptico: recuento de contratos con `Reglas.desde_contrato`, enumeración a mano del caso de A1-2, ciclo
simétrico de A1-4 y repetición de `exp.py` (`pista`, `etapas`, `corte`).

| Hallazgo | Veredicto | Qué cambia |
|---|---|---|
| A1-1 | CORREGIDO | Cifras confirmadas; la causa pasa a hipótesis; paso 0 de diagnóstico; confianza baja |
| A1-2 | CORREGIDO | Reproducido; impacto 4 → 3 (solo empates a menos de 1 m); el test debe fallar hoy |
| A1-3 | CORREGIDO | Impacto 5 → 4; 5 de los 14 con varias circunscripciones tienen exenciones; criterio para (a); T-468 y T-467 son propuestas |
| A1-4 | CORREGIDO | Aún no publicados (29-11); dependencia de la pista sin probar; 25 ejecuciones locales y runner con permiso |
| A1-5 | CORREGIDO | Criterio: orden lexicográfico y tope de tiempo coherente con el riesgo |
| A1-6 | CORREGIDO | Impacto 4 → 3; el resultado depende también de la pista; regla del 08-11 |
| A1-7 | CORREGIDO | Impacto 3 → 2; sin caso real afectado |
| A1-8 | CONFIRMADO | — |
| A1-10 | CORREGIDO | El test de CI usa una instancia OPTIMO, no nac41 |

### Descartados en la verificación

Ningún hallazgo queda refutado entero. Se retiran estas afirmaciones:
- «La causa más probable de los 5 SIN_SOLUCION es la pista incompleta, mecanismo reproducido» (A1-1): la prueba
  sintética reproduce la pérdida del plan entre etapas con tope de 5 unidades, no un SIN_SOLUCION.
- «Entre planes empatados, el que sale depende de la pista» (A1-4): no reproducido; queda como hipótesis.
- «El resultado del exacto es función pura de la instancia» (A1-6): depende también de la pista.
- «Deslinde llega [al óptimo] con 111 átomos y K = 16» (sección 2): Sevilla es `MEJOR_VALIDO`.
- «Los 4 territorios publicados con el exacto» (A1-4): aún no se han publicado.
- «El exhaustivo afecta sobre todo a territorios pequeños donde el exacto no aplica» (A1-7): no hay ninguno.
