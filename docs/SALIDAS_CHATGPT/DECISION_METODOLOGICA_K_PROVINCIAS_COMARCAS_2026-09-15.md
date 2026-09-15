# Decisión metodológica sobre K, provincias y comarcas

**Fecha:** 2026-09-15  
**Estado:** PROPUESTA ARQUITECTÓNICA — NO IMPLEMENTADA  
**Ámbito:** definición del problema territorial, semántica de restricciones y diseño de experimento posterior a Aragón-10  
**Base de lectura de `main`:** `273d8c49c354dd4be65cf1686c83dd6a0417a3be`  
**Ejecuciones territoriales realizadas para este documento:** ninguna  
**Cambios de código/configuración/workflows/resultados:** ninguno  
**Google Drive:** consultado exclusivamente en lectura

Este documento no cambia el contrato vigente de Aragón. Su función es separar decisiones que hoy aparecen acopladas —K, reparto provincial, frontera provincial y comarcas— y dejar una decisión metodológica preparada para que un chat integrador la convierta posteriormente en ADR y documentación canónica.

## 0. Criterio de evidencia

Se usan tres etiquetas de forma estricta:

- **[HECHO REPOSITORIO]**: está expresado por el `main` vigente o se deriva directamente de datos/evidencia versionada del repositorio.
- **[CONCLUSIÓN CLAUDE]**: procede de la auditoría externa de Claude de 15-09-2026 o, cuando se indica, de su informe consolidado de 14-09-2026. No sustituye por sí sola a la fuente de verdad del repositorio.
- **[DECISIÓN PROPUESTA]**: interpretación arquitectónica de este documento. No está implementada y no debe tratarse como comportamiento vigente.

Cuando hay tensión entre una reconstrucción histórica y el contrato canónico actual, prevalece el repositorio. En particular, una coincidencia numérica o una interpretación retrospectiva no se convierte en procedencia documentada.

## 1. Decisión ejecutiva

1. **K=67 se conserva, por ahora, como baseline heredado de Aragón, no como fórmula universal ni como decisión histórica cuya causa conozcamos.** El repositorio declara expresamente `k_source: historico_no_registrado`. La relación entre 67 y el tamaño de las Cortes de Aragón es una pista institucional señalada por Claude, pero no prueba que esa fuera la regla que originó la decisión.
2. **11/7/49 es una consecuencia aritmética de tres premisas previas: K=67, poblaciones provinciales y método Hamilton.** Hamilton explica cómo se llega a esos enteros; no justifica por qué la provincia debe ser unidad de reparto ni por qué debe ser una frontera infranqueable.
3. **La provincia no debe elevarse a restricción dura universal del producto DDD.** En Aragón sigue siendo una restricción dura durante la recuperación actual y el piloto Aragón-10 para no cambiar simultáneamente la definición del problema. Después del piloto debe ejecutarse, en un trabajo separado, un experimento controlado `provincia dura` frente a `provincia no dura`.
4. **La comarca debe tener una única semántica primaria: `SOFT OBJECTIVE` (objetivo blando de optimización), nunca restricción dura.** Su preservación debe influir en la preferencia entre soluciones válidas, pero no decidir por sí misma la factibilidad. Las métricas comarcales son la observación de ese objetivo y P07 es su puerta de publicabilidad; esos dos usos son capas de medición y aceptación, no semánticas competidoras.
5. **La fuente de verdad de K, barreras administrativas y comunidades de interés debe ser el contrato territorial.** El subsistema GerryChain no debe poder activar una comarca o una barrera que el contrato canónico declara inactiva mediante un segundo booleano independiente.
6. **La recuperación topológica/M04 actual y esta reforma metodológica deben permanecer separadas.** No deben cambiarse K, reparto provincial, frontera provincial ni semántica comarcal antes de cerrar el nuevo baseline de Aragón y el piloto Aragón-10.

---

# A. K

## A.1 Qué sabemos realmente del origen de K=67

### Hechos del repositorio

**[HECHO REPOSITORIO]** `territorios/aragon/config/aragon_2025.yaml` declara:

- `k_districts: 67`;
- `k_source: historico_no_registrado`;
- `k_rationale`: K=67 es el baseline canónico certificado, su criterio original no quedó registrado y no se reconstruye retrospectivamente.

**[HECHO REPOSITORIO]** `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md` refuerza la misma regla: `historico_no_registrado` es una declaración honesta de deuda y **no una fórmula reutilizable**. Para nuevos territorios la decisión de K debe existir antes de M04 y ser independiente del resultado del mapa.

**[HECHO REPOSITORIO]** La arquitectura multi-territorio obliga a definir K y, si aplica, el método de reparto por provincias/estados/departamentos como parte del contrato territorial antes de M04. No existe en la documentación consultada una regla universal que calcule K automáticamente.

### Qué dice Claude

**[CONCLUSIÓN CLAUDE — informe consolidado 14-09-2026]** Claude identifica que los K utilizados coinciden con el número de escaños de los parlamentos autonómicos analizados y formula esa relación como explicación: Aragón 67, Castilla y León 82, Extremadura 65. En el mismo informe pide justificar por escrito por qué K debe igualar el tamaño del parlamento autonómico.

**[CONCLUSIÓN CLAUDE — auditoría GerryChain 15-09-2026]** Sigue considerando pendiente una justificación escrita de K y del reparto provincial.

### Decisión metodológica

**[DECISIÓN PROPUESTA]** No debe reescribirse la historia de Aragón diciendo que “K=67 se eligió porque las Cortes tienen 67 escaños” mientras no aparezca una fuente contemporánea a la decisión original que lo pruebe. La igualdad numérica puede ser una explicación plausible y quizá sea la política que el proyecto quiera adoptar en el futuro, pero hoy es **hipótesis de racionalización**, no procedencia demostrada.

La formulación correcta para Aragón sigue siendo:

> **K=67 es un baseline heredado y certificado cuya motivación original no está documentada.**

Si posteriormente el proyecto adopta explícitamente el principio “un distrito por cada escaño de la cámara que se pretende sustituir o reinterpretar”, esa será una **nueva decisión normativa**, fechada y versionada. No debe presentarse como recuperación de una decisión histórica que el repositorio afirma no conocer.

## A.2 Procedimiento universal para K en nuevos territorios

**[DECISIÓN PROPUESTA]** El producto DDD debe universalizar **el procedimiento de decisión de K**, no un número ni una fórmula única sin fundamento. Todo territorio nuevo debe tener un `K Decision Record` previo a M04 con esta jerarquía de procedencia:

1. **Norma aplicable o mandato institucional explícito.** Ejemplo conceptual: si el ejercicio consiste formalmente en sustituir una cámara existente por distritos uninominales conservando su tamaño, K se deriva del número de escaños vigente en la fecha de referencia.
2. **Fórmula pública y preexistente.** Si una jurisdicción o metodología externa define el número de representantes a partir de población u otra magnitud, se registra la fórmula, versión, fuente y fecha.
3. **Fórmula propia del proyecto, motivada ex ante.** Solo si no existe una regla superior. Sus parámetros deben aprobarse antes de ver mapas o resultados electorales y ser reutilizables en territorios equivalentes.
4. **Baseline histórico sin procedencia.** Permitido únicamente para preservar una implantación heredada ya existente, como Aragón. No puede utilizarse para dar de alta un territorio nuevo ni como precedente metodológico.

El registro debe separar, como mínimo, cinco conceptos: propósito institucional del ejercicio, K total, fuente/versión de la regla, población y fecha de referencia cuando la regla la use, y justificación. Después se decide de forma independiente si K se reparte previamente entre subterritorios administrativos.

La regla universal de gobierno es, por tanto:

> **K se fija ex ante por una regla institucional o metodológica declarada y auditable; nunca se elige comparando qué K produce el mapa más cómodo, compacto o favorable.**

Esto es coherente con R036 y evita que una decisión política de diseño quede disfrazada de parámetro técnico.

---

# B. Reparto provincial

## B.1 Qué garantiza Hamilton en Aragón

**[HECHO REPOSITORIO]** C-04 mide el reparto provincial de K y publica estas cuotas para la población de referencia de Aragón:

| Provincia | Población | Cuota exacta sobre K=67 | Distritos Hamilton | Error de cuota | Sesgo de carga poblacional |
|---|---:|---:|---:|---:|---:|
| Huesca (22) | 230.087 | 11,296784235 | 11 | −0,296784235 | +2,6980 % |
| Teruel (44) | 136.091 | 6,681779776 | 7 | +0,318220224 | −4,5460 % |
| Zaragoza (50) | 998.443 | 49,021435988 | 49 | −0,021435988 | +0,0437 % |
| **Total** | **1.364.621** | **67** | **67** | — | — |

La aritmética es inequívoca. Los suelos son 11, 6 y 49, que suman 66. El mayor resto es el de Teruel (0,681779776), por lo que el distrito restante se asigna a Teruel y el resultado es **11/7/49**.

**[HECHO REPOSITORIO]** El método Hamilton garantiza aquí una asignación entera que suma exactamente K y respeta la regla de mayores restos respecto de las cuotas poblacionales exactas. C-04 identifica explícitamente el sesgo restante como efecto estructural previo a M04: nace al convertir cuotas fraccionarias en distritos enteros.

### Lo que Hamilton no garantiza

**[DECISIÓN PROPUESTA]** Debe quedar escrito que Hamilton no demuestra ninguna de estas afirmaciones:

- que la provincia deba ser la unidad de reparto;
- que los distritos no deban cruzar una provincia;
- que el reparto resultante coincida con un reparto legal o estatutario;
- que produzca la mejor geometría;
- que maximice comunidades de interés;
- que elimine diferencias de carga representativa;
- que sea superior políticamente a una circunscripción regional única.

Hamilton resuelve un problema aritmético **después** de haber decidido que K se preasigna por provincias. No justifica esa decisión previa.

## B.2 Qué sesgo introduce el 11/7/49 cuando la provincia es dura

**[HECHO REPOSITORIO]** C-04 mide en Aragón un máximo absoluto de sesgo de carga del 4,546 %, en Teruel. Huesca queda con aproximadamente un 2,70 % más de habitantes por distrito que la media regional; Teruel, con aproximadamente un 4,55 % menos; Zaragoza queda prácticamente en la media.

**[HECHO REPOSITORIO]** El contrato actual y el contrato GerryChain exigen simultáneamente que ningún distrito cruce provincia y que el recuento sea exactamente Huesca 11, Teruel 7 y Zaragoza 49. En `ddd_core/m05_gerrychain_engine.py` la comprobación de los recuentos provinciales está ligada a `require_single_province`.

**[CONCLUSIÓN CLAUDE]** La auditoría de 15-09-2026 señala que este diseño confina la cadena dentro de cada provincia. Su observación metodológica es correcta: si ninguna propuesta puede cruzar la frontera, la búsqueda no dispone del espacio regional completo. Claude destaca especialmente que Teruel, con solo siete distritos, ofrece un espacio de recombinación menor que Zaragoza.

**[DECISIÓN PROPUESTA]** El sesgo debe describirse con precisión. Si la provincia deja de ser dura, desaparece **el sesgo obligatorio derivado de fijar previamente 11/7/49**, porque ya no existe una cuota entera provincial que la geometría tenga que conservar. No es correcto afirmar sin más que “desaparece todo sesgo provincial”: la distribución territorial de representación pasa a ser endógena y puede seguir produciendo asimetrías. Lo que desaparece es el sesgo mecánico impuesto por la preasignación Hamilton.

## B.3 Qué se gana y qué se pierde si la provincia deja de ser frontera dura

### Ganancias potenciales

**[DECISIÓN PROPUESTA]** Al abrir la frontera provincial se amplía el espacio factible a todos los distritos regionales contiguos que cumplen las demás reglas. Eso puede:

- permitir compensar población a ambos lados de una frontera administrativa;
- aumentar el número de recombinaciones posibles y reducir autociclos/rechazos;
- permitir formas más compactas cuando una frontera provincial obliga a rodeos;
- permitir que una comunidad de interés supra-provincial tenga peso real si existe una fuente que la justifique;
- dejar de importar como condición fija el error de redondeo 11/7/49.

### Costes y pérdidas potenciales

Abrir provincias también sacrifica propiedades reales que deben medirse, no minimizarse retóricamente:

- la provincia deja de ser una unidad representativa cerrada y fácilmente explicable;
- pueden aparecer distritos que mezclen dos o más provincias;
- la cifra “distritos de Huesca/Teruel/Zaragoza” deja de ser un atributo exacto salvo que se use una convención artificial para asignar distritos mixtos;
- P03, tal como está redactado, tendría que declararse no aplicable o reformularse si la provincia ya no es unidad de reparto de K;
- nombres, comunicación institucional y gobernanza del mapa pueden hacerse menos intuitivos;
- un mayor espacio de soluciones no implica por sí mismo mejor representación: puede facilitar también soluciones geográficamente extrañas si forma, municipio y comunidades no están bien gobernados.

Por tanto, **provincia dura frente a provincia abierta es una decisión de modelo territorial, no un ajuste de rendimiento del optimizador**.

## B.4 Desacoplar dos decisiones hoy unidas

**[DECISIÓN PROPUESTA]** La arquitectura futura debe considerar por separado:

1. **política de reparto de K**: si existen o no cuotas previas por provincia y con qué método;
2. **política de frontera administrativa**: si un distrito puede o no cruzar provincia.

El contrato actual de Aragón las acopla: Hamilton 11/7/49 + frontera dura. El experimento propuesto en C compara deliberadamente ese paquete vigente con una circunscripción regional sin cuotas provinciales previas. Otros modelos son conceptualmente posibles, pero no deben introducirse en el primer A/B porque añadirían un tercer tratamiento y harían más difícil interpretar la causa de los cambios.

---

# C. Experimento futuro: provincia dura vs provincia no dura

**Este experimento queda diseñado, no autorizado ni ejecutado.** Debe hacerse después del piloto Aragón-10 y en un expediente separado.

## C.1 Pregunta causal

> Manteniendo K=67, los datos, la topología y todas las demás reglas constantes, ¿qué efecto tiene convertir la provincia de barrera dura con cuotas 11/7/49 en una división administrativa no vinculante para la geometría?

La variable experimental debe ser solo la política provincial.

## C.2 Precondiciones antes de ejecutarlo

**[DECISIÓN PROPUESTA]** El A/B no debe empezar hasta que se cumplan estas precondiciones:

- Aragón tenga un baseline nuevo certificado con la topología de frontera compartida mínima de 1 metro;
- la recuperación M04 y el trinquete correspondiente estén cerrados;
- exista auditoría independiente de componentes geométricos;
- Aragón-10 haya demostrado que la cadena GerryChain no está degenerada;
- la telemetría `unique_states`, `self_loops` y estados válidos sea suficiente para interpretar la exploración;
- la semántica comarcal esté congelada de forma idéntica en ambos brazos; no se permite cambiar a la vez provincia y comarca;
- se confirme que el grafo M03 contiene adyacencias geométricas reales que cruzan fronteras provinciales. Si no existen, poner `require_single_province=false` no crea un tratamiento distinto y el experimento sería inválido.

La sugerencia de Claude de una puerta `unique_states / steps_requested >= 0,10` debe tratarse como **propuesta de auditor**, no como umbral canónico actual. Si se adopta, tiene que aprobarse antes del A/B y aplicarse por igual a ambos brazos.

## C.3 Tratamientos

| Variable | Brazo A — PROVINCIA_DURA | Brazo B — PROVINCIA_ABIERTA |
|---|---|---|
| K total | 67 | 67 |
| Universo de secciones | idéntico | idéntico |
| Grafo/topología | idéntico | idéntico |
| Frontera provincial | ningún cruce | cruces permitidos si son contiguos |
| Cuotas provinciales | 11/7/49 obligatorias | ninguna cuota provincial obligatoria |
| Población | mismo contrato | mismo contrato |
| Contigüidad | dura | dura |
| Atomicidad/unidades | dura | dura |
| Disciplina municipal | dura | dura |
| Urbano cerrado | preservado | preservado |
| Comarca | misma semántica y peso en ambos | misma semántica y peso en ambos |
| Forma/cut edges/churn | mismos pesos | mismos pesos |
| Semillas y presupuesto | mismos | mismos |
| Estado inicial | mismo mapa válido cuando sea admisible | mismo mapa válido |

El uso de las mismas semillas permite comparaciones pareadas. Para una decisión metodológica seria, la unidad de análisis no debe ser “el mejor mapa” de cada brazo, sino la distribución de resultados de múltiples cadenas/semillas.

## C.4 Tamaño y estructura recomendados

**[DECISIÓN PROPUESTA]** Tras Aragón-10, el experimento confirmatorio debería usar **50 semillas emparejadas por brazo**. El número se alinea con el precedente C-01 y permite comparar distribuciones sin volver a seleccionar una única semilla favorable.

Si el coste obliga a una fase exploratoria, puede hacerse primero un lote de 10 pares únicamente para validar la instrumentación. Ese lote no debe usarse para decidir la política provincial. La decisión debe basarse en el lote predeclarado confirmatorio.

## C.5 Métricas obligatorias

| Familia | Métrica | Por qué importa |
|---|---|---|
| Factibilidad | tasa de soluciones sin infracciones duras | comprueba que abrir/cerrar provincia no oculta fallos contractuales |
| Robustez | distribución de `max_rel_dev`, distritos fuera de tolerancia y hashes únicos | evita elegir un caso favorable |
| Exploración | `unique_states/steps`, `self_loops/steps`, propuestas aceptadas/rechazadas | mide si la barrera provincial colapsa o no la cadena |
| Población | máximo, mediana y percentiles de desviación absoluta | mide igualdad de carga sin reducirla a un único extremo |
| Provincia | número de distritos que cruzan provincia; población incluida en distritos mixtos; número de provincias por distrito | cuantifica el precio visible de abrir la frontera |
| Representación provincial | “distritos equivalentes fraccionarios” por provincia frente a cuota poblacional exacta | permite medir carga provincial sin asignar artificialmente un distrito mixto a una sola provincia |
| Forma | Polsby–Popper mínimo, mediano y medio; proporción <0,15 | compara geometría bajo la política P05 existente |
| Topología real | número de componentes geométricos por distrito | evita confundir conectividad del grafo con continuidad física |
| Bordes | cut edges y longitud de frontera interna cuando esté disponible | mide fragmentación territorial |
| Municipio | municipios partidos, residual mixto y cumplimiento P04 | comprueba que la ganancia provincial no se paga rompiendo disciplina municipal |
| Comarca | comunidades partidas, retención, dominante por distrito, comunidades por distrito | comprueba interacción con P07 sin cambiar el tratamiento comarcal |
| Coste | tiempo, memoria, propuestas por estado único | informa la viabilidad operativa, no la calidad política |

### Métrica propuesta para representación provincial con distritos mixtos

**[DECISIÓN PROPUESTA]** En el brazo abierto no debe inventarse un “distrito de Teruel” por mayoría de superficie o por nombre. Para comparar con la cuota ideal puede usarse una atribución fraccionaria puramente diagnóstica:

`distritos_equivalentes(provincia p) = Σ_d población(p ∩ d) / población(d)`

La suma sobre provincias es exactamente K. Esta métrica permite comparar el peso efectivo de cada provincia con su cuota poblacional exacta sin reintroducir una frontera dura por la puerta de atrás. No es una asignación legal de escaños y no debe presentarse como tal.

## C.6 Hipótesis predeclaradas

**H1 — espacio de soluciones.** La provincia abierta producirá una mayor diversidad efectiva de estados y/o menor tasa de autociclos, especialmente en el entorno de Teruel.

**H2 — equilibrio poblacional.** La provincia abierta reducirá o no empeorará de forma sistemática la distribución de desviaciones poblacionales, al eliminar la cuota entera provincial como condición previa.

**H3 — forma.** La provincia abierta puede mejorar compacidad y cut edges al permitir fronteras de distrito distintas de la frontera provincial; no se da por hecho.

**H4 — coste institucional.** La mejora, si existe, tendrá un coste medible en distritos transprovinciales. Ese coste puede ser metodológicamente inaceptable aunque las métricas geométricas mejoren.

**H5 — sesgo Hamilton.** El sesgo de carga derivado específicamente de 11/7/49 dejará de ser una condición fija. No se presupone que toda desigualdad territorial desaparezca.

## C.7 Criterio de comparación y decisión

El experimento no debe “coronar” el mapa con menor `score`. Debe comparar formulaciones del problema.

**[DECISIÓN PROPUESTA]** El brazo abierto solo debe convertirse en candidato a política canónica si se cumplen simultáneamente estas condiciones:

1. no introduce ninguna infracción en las restricciones duras comunes;
2. no degrada P01/P02/P04/P05 respecto del brazo duro y mejora de forma reproducible al menos una dimensión material entre robustez, equilibrio poblacional, forma o exploración;
3. la mejora aparece en la distribución de semillas, no solo en un óptimo local;
4. la carga de cruces provinciales se publica completa y no se oculta mediante una convención nominal;
5. antes de promoverlo se adopta una decisión de gobernanza explícita sobre el nivel admisible de mezcla provincial y se adapta P03 a esa decisión.

El repositorio actual no contiene un umbral defendible de “máximo de distritos transprovinciales”. Inventarlo después de ver el A/B repetiría exactamente el problema metodológico que C-13 prohíbe para comarcas. Por ello, si se quiere usar un límite cuantitativo como puerta, debe aprobarse **antes** del experimento confirmatorio.

---

# D. Comarcas

## D.1 Situación actual, sin reconstrucciones

### Pipeline canónico

**[HECHO REPOSITORIO]** `territorios/aragon/config/aragon_2025.yaml` declara una fuente `inputs/COMARCAS.csv`, pero `comarcas.enabled: false`.

**[HECHO REPOSITORIO]** `configuracion/comunidades_interes.json` y C-13 declaran Aragón `NOT_EVALUABLE` en P07 precisamente porque esa fuente no está incorporada al universo canónico ni existe evidencia M06 que permita medir las cuatro métricas exigidas.

**[HECHO REPOSITORIO]** La política de publicabilidad define P07 como criterio supra-municipal y exige fuente pública, cobertura completa, métricas y umbrales precomprometidos.

### GerryChain / alternativas

**[HECHO REPOSITORIO]** `configuracion/ensemble/aragon.json` declara la misma fuente como `comarca_lookup`, define campos comarcales y fija `"comarca": {"enabled": true}`.

**[HECHO REPOSITORIO]** El motor GerryChain exige cobertura comarcal completa cuando esa capa está activada, calcula fragmentación/retención y usa la retención como término de `score_metrics`. La integración también utiliza la región comarcal como preferencia de ReCom. La pertenencia a una comarca **no aparece entre las infracciones duras**.

**[HECHO DRIVE — HITOS_MANTENIMIENTO_DDD_BUSINESS]** El Hito 9 resume la intención operativa con claridad: “comarca continúa ponderada y publicada”, mientras población, provincia, reparto provincial, contigüidad, atomicidad y disciplina municipal continúan como restricciones duras.

### Auditoría externa

**[CONCLUSIÓN CLAUDE — 15-09-2026]** Claude identifica correctamente “dos caminos divergentes para la comarca”: `enabled: true` en el ensemble y `enabled: false` en el contrato territorial. Lo considera deriva de configuración que debe unificarse o justificarse.

**[CONCLUSIÓN CLAUDE — 14-09-2026]** La capacidad comarcal ya existía históricamente y fue desactivada al parametrizar el pipeline de febrero. Es decir, no hay base para decir que el pipeline canónico actual “siempre quiso” optimizar comarcas; la funcionalidad ha cambiado de estado a lo largo de la historia.

## D.2 Semántica única propuesta

**[DECISIÓN PROPUESTA]** La comarca debe ser **SOFT OBJECTIVE**.

No debe ser una restricción dura. Tampoco debe quedar reducida a una métrica pasiva si P07 pretende que las comunidades de interés tengan relevancia sustantiva.

La semántica exacta es:

> Una solución que rompe una comarca puede seguir siendo técnicamente factible, pero, a igualdad de restricciones duras, debe ser preferida una solución que conserve mejor comunidades de interés conforme a una fuente pública y una función predeclarada.

### Por qué no HARD CONSTRAINT

- Las comarcas no tienen el mismo carácter universal ni la misma granularidad en todos los territorios.
- Algunas pueden ser demasiado grandes, pequeñas o geométricamente complejas para conservarse íntegramente con K y población fijos.
- Convertirlas en barrera absoluta puede hacer el problema infactible o trasladar el defecto a población/forma.
- C-13 admite “comarca o equivalente funcional”, lo que confirma que se trata de comunidad de interés, no de una frontera administrativa universalmente obligatoria.

### Por qué no solo DIAGNOSTIC METRIC

Si la comarca se mide únicamente al final, el optimizador puede ignorarla durante toda la búsqueda y producir sistemáticamente soluciones que después fallen P07. Dado que el proyecto ha decidido que P07 es sustantivo para publicabilidad, es más coherente que el motor pueda orientar la búsqueda hacia mejor retención sin convertirla en prohibición absoluta.

### Cómo conviven objetivo, métrica y publicabilidad sin “doble verdad”

No son tres significados distintos:

- **semántica de búsqueda:** `SOFT OBJECTIVE`;
- **observabilidad:** las cuatro métricas de C-13 miden el resultado del objetivo;
- **gobernanza:** P07 decide si el resultado medido alcanza umbrales definidos ex ante.

La frontera entre capas queda así nítida: el objetivo orienta, la métrica observa y la publicabilidad acepta o rechaza. La comarca nunca convierte por sí sola una propuesta en “imposible”.

## D.3 Una sola fuente de verdad

**[DECISIÓN PROPUESTA]** Después de Aragón-10 debe desaparecer conceptualmente la posibilidad de que el contrato territorial diga “comarca desactivada” y el ensemble diga “comarca activada” como dos verdades simultáneas.

El contrato territorial debe gobernar:

- fuente y versión de comunidades de interés;
- si la capa está disponible para el territorio;
- su semántica `SOFT OBJECTIVE`;
- la definición de las métricas;
- los umbrales de P07;
- la política cuando la fuente no existe o no tiene cobertura completa.

El runner GerryChain debe **consumir esa decisión**, no redefinirla. Un experimento puede tener un overlay explícitamente identificado como experimental, pero no debe presentarse como equivalente al pipeline canónico ni convertirse silenciosamente en un segundo contrato.

El peso/surcharge concreto es un parámetro de calibración del objetivo blando. Su eventual barrido —Claude sugiere explorar 0,3–0,8— debe ser un experimento propio. No debe mezclarse con el A/B de provincia, porque entonces no podría atribuirse la mejora a la apertura provincial o al cambio de fuerza comarcal.

---

# E. Taxonomía de restricciones, objetivos, métricas y publicabilidad

## E.1 Definiciones

| Categoría | Significado arquitectónico | Efecto sobre una propuesta |
|---|---|---|
| **HARD CONSTRAINT** | Invariante de factibilidad. Define el espacio de soluciones admitidas. | Una infracción rechaza la propuesta/plan. |
| **SOFT OBJECTIVE** | Preferencia optimizable dentro del espacio factible. | Empeora score/probabilidad/preferencia, pero no invalida por sí sola. |
| **DIAGNOSTIC METRIC** | Medida observacional para auditoría, comparación y explicación. | No cambia la factibilidad ni el score salvo que otra capa la consuma explícitamente. |
| **PUBLICABILITY CRITERION** | Puerta de gobernanza aplicada a un resultado técnico, con regla predeclarada. | Puede bloquear publicación aunque el plan sea técnicamente válido. |

Una misma dimensión puede tener una regla dura y una métrica de verificación sin existir contradicción. Por ejemplo, contigüidad es una restricción dura y P02 verifica para publicación que esa restricción se ha cumplido. Lo que debe evitarse es que dos configuraciones den **semánticas computacionales distintas** a la misma dimensión sin una decisión explícita.

## E.2 Clasificación propuesta

| Dimensión | HARD CONSTRAINT | SOFT OBJECTIVE | DIAGNOSTIC METRIC | PUBLICABILITY CRITERION | Decisión/nota |
|---|---|---|---|---|---|
| Universo de secciones y conservación | **Sí** | No | Sí, G03 | Garantía transversal | Nunca se optimiza perdiendo unidades/población. |
| K total | **Sí, como definición del problema** | No | Sí, trazabilidad | P09/G04 indirectamente | Debe fijarse ex ante con procedencia; no es una variable del optimizador. |
| Población: suelo/techo/tolerancia contractual | **Sí en el contrato vigente** | Puede minimizarse desviación dentro de la zona factible | maxdev, percentiles, fuera de tolerancia | **P01** | Umbral duro y objetivo fino son capas distintas. No relajar para ganar forma/comarca. |
| Contigüidad de grafo y continuidad física exigible | **Sí** | No | componentes, conectividad | **P02** | La continuidad geométrica independiente debe cerrar la laguna detectada por Claude. |
| Provincia — Aragón vigente | **Sí, condicional al modelo actual** | No | cruces, carga y cuotas | **P03 mientras sea unidad de reparto** | No elevar a regla universal; objeto del A/B posterior. |
| Recuento provincial 11/7/49 | **Sí solo en variante provincia dura** | No | error de cuota y `population_load_bias` | Parte de P03 en modelo actual | Hamilton es mecanismo de reparto, no justificación política. |
| Municipio / atomicidad | **Sí** | No | municipios partidos, mezclas | **P04** | Mantener como invariante actual. |
| Municipio sobredimensionado / residual mixto | **Sí** | No | nº de fragmentos y mixtos | **P04** | La excepción está reglada, no optimizada libremente. |
| Urbano cerrado | **Sí** | No | alteraciones del bloque | P04 / inteligibilidad | Preservación vigente; no mezclar con provincia A/B. |
| Comarca / comunidad de interés | **No** | **Sí — semántica primaria propuesta** | splits, retención, dominante, comunidades/distrito | **P07** | Objetivo blando con fuente gobernada; nunca hard barrier. |
| Forma/compacidad | No actualmente | **Sí** | Polsby–Popper, cut edges, longitudes | **P05** | Mantener blanda en búsqueda y dura solo como puerta de publicación predefinida. |
| Cut edges | No | **Sí** | Sí | No directo | Instrumento de forma/coherencia, no criterio político autónomo. |
| Churn respecto del mapa inicial | No | **Sí** | Sí | No | Regularizador técnico; no debe convertirse en argumento de publicabilidad. |
| Robustez entre semillas/cadenas | No | No | **Sí** | **G01** | Se evalúa sobre distribución, no sobre el mejor estado. |
| Degeneración de cadena | Puede ser puerta técnica si se predeclara | No | unique states, self-loops | G01/G02 | El umbral 0,10 es propuesta de Claude, aún no norma. |
| Neutralidad electoral de M01–M06 | **Sí como regla de separación de datos** | No | trazabilidad de inputs | **P06** | Ningún voto/partido debe influir en límites. |

### Nota sobre “forma como hard constraint”

**[CONCLUSIÓN CLAUDE]** La auditoría sugiere estudiar una cota dura de aristas de corte. **[DECISIÓN PROPUESTA]** No debe incorporarse en esta decisión. La política vigente ya dispone de P05 y el GerryChain actual usa forma como objetivo blando. Convertir forma en restricción dura sería un cambio de espacio factible que necesita experimento y ADR propios; no debe mezclarse con provincia ni recuperación topológica.

---

# F. Recomendación de secuencia

## F.1 Qué NO debe mezclarse con la recuperación actual

**[DECISIÓN PROPUESTA]** Hasta cerrar el baseline topológico nuevo y Aragón-10 deben permanecer congelados:

- K=67;
- Hamilton 11/7/49;
- `require_single_province=true`;
- reglas municipales y urbano cerrado;
- ratios poblacionales vigentes;
- semántica/peso comarcal que ya esté cableada en el piloto pendiente;
- pesos de forma, cut edges y churn;
- cualquier nueva fórmula universal de K;
- cualquier A/B provincia dura/abierta;
- cualquier barrido de `comarca_surcharge`.

La razón no es que esos valores sean metodológicamente definitivos. Es exactamente la contraria: **se están cuestionando**, y por ello no deben alterarse mientras se intenta certificar que la nueva topología de un metro y la reparación M04 funcionan. Cambiar el modelo de representación en mitad de esa recuperación destruiría la atribución causal y haría imposible saber qué cambio corrigió o empeoró el resultado.

La secuencia inmediata sigue siendo la ya documentada en `HITOS_MANTENIMIENTO_DDD_BUSINESS`: certificar M01–M06 con el grafo depurado, fijar nuevo baseline/trinquete, medir componentes geométricos y solo después lanzar Aragón-10.

## F.2 Qué debe implementarse después de Aragón-10

**[DECISIÓN PROPUESTA]** Una vez revisado Aragón-10, el integrador debe separar cuatro trabajos, en este orden:

### 1. ADR de definición del problema

Convertir este documento en decisiones canónicas sobre:

- gobierno universal de K;
- separación conceptual entre reparto subterritorial y frontera administrativa;
- provincia como política configurable, no regla global del motor;
- comarca como `SOFT OBJECTIVE` gobernado desde el contrato territorial.

Este ADR no requiere recalcular por sí solo ningún territorio.

### 2. Fuente única de semántica comarcal

Eliminar la doble verdad entre YAML canónico y configuración del ensemble. El contrato territorial debe ser la única autoridad y GerryChain debe heredarla. En la misma fase deben quedar predeclarados los umbrales P07 si Aragón va a ser evaluable.

No debe aprovecharse este trabajo para recalibrar el peso comarcal. Primero se unifica la semántica; luego, si hace falta, se calibra en un experimento independiente.

### 3. Experimento provincia dura vs abierta

Ejecutar el protocolo C con K=67 y todos los demás factores congelados. El resultado debe ser un informe comparativo de distribuciones y costes de mezcla provincial, no una nueva galería de “mejores mapas”.

Solo tras ese experimento puede decidirse si el baseline futuro de Aragón conserva provincia dura, la abre o necesita una tercera política explícita.

### 4. Generalización a nuevos territorios

Aplicar el procedimiento de K a cada territorio antes de M04. `historico_no_registrado` no será admisible en nuevas altas. La existencia de provincias u otros niveles administrativos no los convierte automáticamente en barreras: cada contrato deberá declarar si actúan como barrera, preferencia o simple dimensión diagnóstica, conforme al principio ya presente en `ARQUITECTURA_MULTI_TERRITORIO.md`.

## F.3 Qué no debe decidirse todavía

Esta propuesta **no** recomienda cambiar K de Aragón, no recomienda un K alternativo, no determina que la provincia abierta sea superior y no fija un umbral de cruces provinciales. Hacer cualquiera de esas tres cosas sin el experimento o sin una decisión normativa previa sustituiría una deuda metodológica por otra.

Tampoco recomienda promover Aragón-50. La auditoría de Claude identifica primero problemas de distribución estadística, degeneración de cadena y semántica provincial/comarcal. El lote grande debe seguir separado hasta que Aragón-10 haya demostrado que la infraestructura produce información metodológicamente interpretable.

---

# G. Matriz de decisión para futura ADR

| ID propuesto | Decisión | Estado tras este documento | Evidencia necesaria antes de implementación |
|---|---|---|---|
| D-K-01 | K es definición ex ante con procedencia obligatoria | **PROPUESTA ACEPTABLE** | ADR; no requiere run |
| D-K-02 | `historico_no_registrado` solo para legacy, nunca territorio nuevo | **PROPUESTA ACEPTABLE** | ADR/contrato futuro |
| D-PROV-01 | Hamilton no justifica provincia como barrera | **CONCLUSIÓN METODOLÓGICA** | ya sustentada por C-04 |
| D-PROV-02 | Provincia no es hard constraint universal | **PROPUESTA** | ADR + A/B Aragón posterior a Aragón-10 |
| D-PROV-03 | Mantener 11/7/49 y provincia dura durante recuperación/piloto actual | **REGLA DE AISLAMIENTO DEL CAMBIO** | ninguna ejecución adicional para decidirla |
| D-COM-01 | Comarca = `SOFT OBJECTIVE` | **PROPUESTA** | ADR + unificación contractual post Aragón-10 |
| D-COM-02 | Métricas C-13 observan; P07 gobierna publicación | **COMPATIBLE CON CANON ACTUAL** | umbrales ex ante para Aragón |
| D-EXP-01 | A/B provincia dura vs abierta con 50 semillas emparejadas | **DISEÑADO, NO AUTORIZADO** | baseline nuevo + Aragón-10 + cadena no degenerada |

---

# H. Fuentes consultadas

## Repositorio GitHub

Base de lectura: `jfmurciego/DiputadodeDistrito@273d8c49c354dd4be65cf1686c83dd6a0417a3be`.

- `territorios/aragon/config/aragon_2025.yaml`
- `territorios/aragon/config/elecciones/aragon_cortes_2026.json`
- `territorios/aragon/config/elecciones/diccionario_partidos_aragon_2026.json`
- `configuracion/ensemble/aragon.json`
- `configuracion/comunidades_interes.json`
- `docs/AUDITORIA_C01_ROBUSTEZ_SEMILLA.md`
- `docs/AUDITORIA_C04_SESGO_REPARTO_K.md`
- `docs/SALIDAS_CHATGPT/EVIDENCIAS/C04_SESGO_REPARTO_K.json`
- `docs/AUDITORIA_C13_COMUNIDADES_INTERES.md`
- `docs/POLITICA_PUBLICABILIDAD.md`
- `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`
- `docs/ARQUITECTURA_MULTI_TERRITORIO.md`
- `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md`
- documentación histórica y de rondas localizada por K=67 / 11-7-49
- `ddd_core/m05_gerrychain_engine.py`, solo para verificar la semántica vigente de restricciones duras, métricas y score; no modificado.

Entre el primer corte consultado (`ea6b305...`) y la base final de lectura (`273d8c49...`) `main` avanzó nueve commits relacionados con interfaz/workflows/tests. La comparación no mostró cambios en las fuentes metodológicas enumeradas arriba.

## Google Drive — solo lectura

- `AUDITORIA_GERRYCHAIN_2026-09-15.md` — id `106Aa9gSc0xQUKbdTfPPBRXHSXroI9X8MKhJ66v3IyfA`.
- `HITOS_MANTENIMIENTO_DDD_BUSINESS` — id `1Bzze-PCp-qDD3DRr1EJc_mS9bAn-M5ZOutXd_szi3tM`.
- `INFORME_CONSOLIDADO_DDD_2026-09-14.md` — id `1pFaIyAvBI9u3fuiYcUPqgsOhOPwLX6NzZd4Et_PoV0Y`, utilizado únicamente para reconstruir el contexto histórico y contrastarlo con la procedencia canónica actual.

No se ha escrito ni modificado ningún documento de Drive.

---

# I. Conclusión para el integrador

La deuda metodológica no está en la aritmética de Hamilton; esa parte es reproducible. Está en haber dejado acopladas cuatro decisiones distintas: **cuántos distritos existen, si se reparten antes por provincia, si la provincia es una barrera geométrica y cómo se incorporan las comunidades de interés**.

La arquitectura propuesta las separa:

- K se gobierna ex ante y con procedencia;
- Hamilton, cuando se use, es únicamente un método de apportionment sobre una unidad previamente justificada;
- la provincia puede ser barrera o no según una decisión territorial explícita, no por supuesto universal del motor;
- la comarca orienta la optimización de forma blanda y se evalúa con C-13/P07;
- las métricas diagnostican y las puertas de publicabilidad deciden, sin confundirse con las restricciones que definen factibilidad.

Para Aragón, la recomendación inmediata es conservadora: **no cambiar nada de esto antes de cerrar la recuperación actual y Aragón-10**. La reforma empieza después, con ADR y experimentos controlados, no durante la reparación del baseline.