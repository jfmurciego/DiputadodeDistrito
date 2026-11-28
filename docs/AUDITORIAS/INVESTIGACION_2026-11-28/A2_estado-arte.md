# A2 · Algoritmo: estado del arte mundial y mejoras para Deslinde (T-509)

Fecha: 2026-11-28. Agente local, solo lectura. Código de `main` en 9e630d11. No se ha ejecutado el motor ni ningún
experimento: todo lo propuesto lleva su prueba, sin hacer. Hallazgos en `A2_estado-arte.json` (11, con evidencia).

## 1. Veredicto

1. Deslinde juega hoy en **segunda alta**. Tiene algo que GerryChain y `redist` no dan: un óptimo demostrado y
   reproducible bit a bit, con un resolutor abierto, en los territorios pequeños.
2. Pero el exacto es **todo o nada**: territorio entero, una circunscripción, sin exenciones y átomos × K ≤ 2.000.
3. Medido en los 71 territorios: K va de 1 a **135**, no de 1 a 37. Hay 24 con K ≤ 4, 20 entre 5 y 10, 11 entre 11
   y 37 y **16 con K > 37**. En esos 16, y en las autonómicas con varias circunscripciones, el exacto no entra nunca.
4. Fuera del exacto la búsqueda es ReCom básico (2019): N cadenas independientes de 300 pasos. Ya perdió en
   Burgos, Valladolid y Sevilla (8 demarcaciones partidas frente a 6 demostradas).
5. Más pasos no lo arreglan: GerryChain puro con 100.000 pasos y 6,9 h de CPU tampoco llegó (T-466).
6. No hay ninguna cota donde el exacto no cierra: en esos territorios no se sabe a cuánto está el mapa del mejor.
7. No se publica nada con lo que otros puedan medirse: ni instancias, ni cotas, ni conjuntos de mapas.
8. La literatura de 2021 a 2026 tiene resuelto, con código, casi todo lo que falta. Son cinco técnicas.
9. Tres de ellas son baratas (una sesión o dos) y se prueban en local con los cuatro territorios del piloto.
10. Con ellas y con un banco público de instancias, el proyecto puede jugar en **primera**.

## 2. Estado objetivo: cómo se ve un referente mundial

- **Exactitud (Buchanan y coautores, Oklahoma State).** Óptimo demostrado de «condados partidos» para todas las
  cámaras de Estados Unidos, con código y con el mapa óptimo de cada estado enlazado. Aquí: por cada uno de los 71
  territorios, «óptimo demostrado» o «como mucho a N del mejor», con certificado que un tercero pueda comprobar.
- **Conjuntos (ALARM, Harvard).** Simulaciones de los 50 estados con muestreador de distribución conocida,
  diagnósticos y datos en abierto. Aquí: 10.000 mapas por provincia con la prueba de validación al lado.
- **Apertura (Dave's Redistricting, PlanScore).** Cualquiera sube un mapa y recibe su nota con la regla pública.
  Aquí: instancia neutra y verificador de un fichero; cualquiera calcula la clave D8 de su mapa.
- **Proceso (comisiones de Inglaterra, Australia, Canadá).** Tolerancia fija y publicada, pieza mínima declarada,
  propuestas con consulta y, en Australia, tolerancia también sobre la población proyectada.

## 3. Fichas de técnicas (2019–2026)

Fuentes numeradas en la sección 9. «Encaje» dice el fichero de `paquetes/deslinde/src/deslinde/`.

| Técnica (fuente) | Qué resuelve | Tamaño demostrado | Licencia | Encaje y balance para 71 territorios |
|---|---|---|---|---|
| ReCom (1) | Cadena con movimientos grandes: fusiona dos distritos y los corta por un árbol | Estados enteros, miles de recintos | BSD (GerryChain) | Ya es `ponderado.py`. Sin distribución conocida con 3 o más distritos |
| ReCom reversible (2) | Lo mismo, con equilibrio conocido (árboles de expansión) | Estados; más cálculo por paso | BSD (GerryChain la trae) | Muestreador para T-469. Coste bajo; el núcleo como rechazo puede frenarlo |
| Forest ReCom y multiescala (3) | Metropolis sobre bosques; respeta jerarquías (condados) | Carolina del Norte por recintos | Código de Duke, licencia sin comprobar | Encaja con municipio → sección. Coste alto; solo si (2) no mezcla |
| SMC, `redist` (4) y SMC generalizado (5) | Planes en paralelo, distrito a distrito; (5) añade distritos plurinominales y pasos de fusión | 50 estados (ALARM); validado contra enumeración | GPL | Solo comparación externa (D-73). No se puede enlazar al paquete |
| Ráfagas cortas (6) | Optimizar con una cadena neutra: ráfagas de b pasos desde el mejor visto | Luisiana, cámaras estatales | BSD (`SingleMetricOptimizer`) | `ponderado.py`, pocas líneas, mismo gasto. Lo más barato de probar |
| Contigüidad por cortes y flujos (7); lineal en grafos planos (12) | Modelos enteros fuertes de contigüidad | Óptimo en 21 estados a nivel de tramo censal | GPL-3.0 y exige Gurobi: se reimplementa la idea | `exacto.py` (modelo 2.0). Sube el techo de 2.000 |
| Mínimo de condados partidos (8) | Cota por agrupaciones más plan que la alcanza | Todas las cámaras de EE. UU. salvo Hawái; p. ej. 95 condados, K = 33 | Repositorio público, licencia no visible | `cotas.py` nuevo. Cota del tercer término de D8 en segundos, también en lo grande |
| Generación de columnas (9) y reoptimización local (10) | Muchos distritos candidatos y un problema maestro; mejora por fragmentos | Estados enteros; (10) supera a las ráfagas | Sin comprobar | `exacto_local.py` y candidato «maestro». La vía para K > 37 |
| Diagramas de potencia equilibrados (11) | Distritos compactos de población exacta | Seis estados más poblados, por manzana | Académico | Encaje bajo: ignora municipios y núcleos. Solo semilla de reserva |
| Multiobjetivo multinivel (13) | Frente de Pareto con restricción ε tras contraer el grafo | Wisconsin | Datos y código públicos | Estudio con el exacto actual; contenido para T-470 y T-471 |
| Validación por enumeración (15) | Comprobar un muestreador contra todos los planes | 70 recintos, 44 millones de planes | GPL (`redist`) | `exhaustivo.py` ya enumera: ventaja propia para validar T-469 |

Comisiones de límites (18, 19, 20): no usan optimizador como árbitro. Inglaterra fija ±5 % (69.724 a 77.062
electores) y trabaja por barrios, con propuestas iniciales, revisadas e informe final. Australia exige ±10 % hoy y
±3,5 % sobre la población proyectada, con datos por la unidad mínima (SA1). Canadá admite ±25 % con motivos
escritos, una comisión independiente por provincia y audiencias públicas.

## 4. Hallazgos, de mayor a menor impacto

### A2-1 · El exacto es todo o nada: falta el exacto por vecindarios (impacto 5, esfuerzo L)
- **Hoy.** `exacto.py:54,61-79`: solo territorio entero, D8, una circunscripción, sin exenciones, tamaño ≤ 2.000.
  16 de 71 territorios tienen K > 37 (medido en `T180_CADENAS/todos_71/TERRITORIOS.csv`). La Rioja autonómica
  (K = 33) no cierra ni la primera etapa (`T296_OPTIMO_D8/README.md:69`).
- **Propongo.** Candidato «exacto local» (`exacto_local.py`, reutiliza `_Modelo`): desde el mejor candidato, tomar
  en orden fijo grupos de 2 a 4 distritos contiguos, fijar el resto, resolver D8 exacto en el fragmento y aceptar
  solo si mejora la clave oficial completa. Certificado nuevo: «ningún grupo de hasta 3 distritos vecinos mejora».
- **Aceptación.** En Sevilla, desde el plan de 8 partidas y sin exacto global, llega a 6 · 785,968 km en menos de
  5 min de CPU con la misma huella dos veces; en La Rioja autonómica acaba con clave igual o mejor y plan válido.
- **Riesgo.** Cambio de motor (solo en regeneración). Los términos globales de D8 hay que modelarlos con cuidado.
- **Ya previsto.** T-468 solo como propuesta de la auditoría; no está en `docs/PLAN.md` ni nombra la técnica.

### A2-2 · Sin cota fuera del exacto: la da la técnica de agrupaciones (impacto 4, esfuerzo M)
- **Hoy.** La cota sale solo de CP-SAT y solo donde el modelo entero aplica (`exacto.py:354-358`). El término que
  decide es «demarcaciones partidas» (`T465…/INFORME.md:8-10`), el mismo problema que «condados partidos».
- **Propongo.** `cotas.py`: programa entero sobre el grafo de demarcaciones (decenas de piezas por provincia) que da
  el máximo de agrupaciones; K menos ese máximo acota las partidas, por familia. Va a `COMPETICION.json` como dato.
- **Aceptación.** En los cuatro del piloto la cota es ≤ el óptimo (2, 2, 2, 6) y lo iguala en al menos dos, en
  menos de 30 s; en un territorio con K > 37 da una cota mayor que 0 en menos de 5 min.
- **Riesgo.** Dos familias que se solapan: la suma puede quedar floja. Válida siempre, ajustada no siempre.

### A2-3 · La contigüidad del exacto es la formulación débil (impacto 4, esfuerzo M)
- **Hoy.** Árbol padre/nivel con un entero 0..n−1 por átomo (`exacto.py:218-234`). En Sevilla la etapa de frontera
  se lleva 42,8 de 60,2 s (`resultados/exacto/nac41.json`) y en producción no cierra (`T502…/INFORME.md:49-61`).
- **Propongo.** Estudio con tres variantes sobre las instancias neutras: la actual, flujo por distrito, y sin
  contigüidad más bucle de cortes separadores. Solo si una gana, se propone como modelo 2.0.
- **Aceptación.** Tabla de tiempo determinista por etapa en nac09, nac47, nac26, nac41 y aut17; se adopta una
  variante solo si cierra la frontera de Sevilla en menos de la mitad o cierra la primera etapa de aut17, con el
  mismo plan dos veces.
- **Riesgo.** CP-SAT no admite cortes dentro de la búsqueda; el bucle puede no ganar.

### A2-4 · Cadenas independientes de 300 pasos: probar ráfagas cortas (impacto 4, esfuerzo S)
- **Hoy.** `candidatos.py:301` (300 pasos), `competicion.py:450` (5 cadenas por defecto), `ponderado.py:101-115`.
  En el estudio de las 71, el ganador por naturalidad aún cambiaba con la cadena 15 o posterior en 26 territorios y
  con la 20 (tope probado) en 11.
- **Propongo.** Mismo total de pasos en ráfagas de b pasos desde el mejor plan según D8; registrar la tasa de
  rechazo del núcleo, que hoy no se guarda. Prueba con b = 5, 20 y 50, sin el candidato exacto.
- **Aceptación.** Alcanza el óptimo demostrado en 2 de 3 (Burgos, Valladolid, Sevilla) y nunca empeora la clave de
  las cadenas actuales en los cuatro. Si no, se descarta y se deja escrito.
- **Ya previsto.** T-467 (propuesta: «cadenas más largas»). El piloto ya mide que más pasos no basta.

### A2-5 · Los mapas alternativos piden un muestreador validado (impacto 4, esfuerzo M)
- **Hoy.** La única cadena es ReCom con recargos y rechazo duro (`ponderado.py:46-66,81-102`): buena para buscar,
  sin distribución conocida. `exhaustivo.py:50` enumera todos los planes válidos en lo pequeño.
- **Propongo.** Antes de T-469: en 2 o 3 territorios enumerables, comparar cadena actual, ReCom reversible y
  `redist` (fuera del paquete) contra la enumeración. Elegir con esa tabla y publicarla con el conjunto.
- **Aceptación.** Distancia de variación total menor que 0,05 en partidas, frontera y desvío con 10.000 planes, y
  R-hat menor que 1,05 entre 4 ejecuciones.

### A2-6 · No se publica nada con lo que otros puedan medirse (impacto 4, esfuerzo M)
- **Hoy (verificado).** `datos_abiertos/INDEX.json` no tiene ninguna clave de exacto, cota, huella, semilla ni
  competición. `paquetes/deslinde/MAPAS.json` tiene 0 mapas y dice versión 1.0.0 (el paquete va por 1.2.0). Las
  instancias neutras de T-296 «no se versionan». El README del paquete no menciona banco ni cota.
- **Propongo.** «Banco DDD»: 71 instancias neutras con sha256, mejor clave conocida, cota y estado, y un
  verificador de un fichero con solo biblioteca estándar. No abre el motor.
- **Aceptación.** `datos_abiertos/banco/INDEX.json` con 71 instancias; `verificar_plan.py` da en los cuatro del
  piloto la clave de `T465_BANCO_PILOTO/resultados/RESUMEN.json`; una prueba de CI lo comprueba.
- **Necesita.** Decisión del propietario: choca con D-92 y D-94 (privado) y con la licencia pendiente (T-473).

### A2-7 · Separar buscar de certificar (impacto 3, esfuerzo M)
- **Hoy.** La prueba depende del tope de 60 por etapa (`exacto.py:56,389-390`): Sevilla tiene el plan óptimo y
  sale «MEJOR_VALIDO». D-73 nombraba HiGHS o CBC; solo hay CP-SAT, nadie cruza la prueba.
- **Propongo.** Certificado fuera de línea por territorio (sin tope, con registro y versión) y segundo resolutor
  abierto para la etapa decisiva. La competición compara la huella del plan con la certificada.
- **Aceptación.** Certificado de Sevilla con cinco etapas OPTIMAL; un segundo resolutor confirma «partidas = 6».

### A2-8 · Recombinar los distritos que las cadenas tiran (impacto 3, esfuerzo M, confianza baja)
- **Hoy.** `ponderado.py:104-115` guarda el mejor plan y solo la huella del resto.
- **Propongo.** Guardar los distritos vistos y resolver con CP-SAT la selección de K que cubren el territorio.
- **Aceptación.** En el piloto, clave igual o mejor que la mejor cadena y estrictamente mejor en uno; menos de 60 s.

### A2-9 · Publicar lo que cuesta cada renuncia de D8 (impacto 3, esfuerzo S)
- **Hoy.** Burgos: de 3 a 2 partidas sube el desvío del 0,02 % al 4,23 %. Sevilla: de 8 a 6 cuesta 22 km.
- **Propongo.** Con el exacto actual, la tabla de puntos no dominados (partidas, frontera, desvío) por territorio.
- **Aceptación.** Tabla de los cuatro del piloto, cada punto con estado OPTIMAL y el elegido por D8 marcado.

### A2-10 · Medir la población futura, como Australia (impacto 3, esfuerzo S)
- **Hoy.** La tolerancia usa una sola fecha (`exacto.py:168,188-198`).
- **Propongo.** Estudio: los 71 mapas vigentes evaluados con el padrón de cuatro años antes.
- **Aceptación.** Tabla por territorio de distritos fuera de tolerancia en t − 4 y en t, con fuentes y sha256.

### A2-11 · Diagramas de potencia: encaje bajo (impacto 2)
- Ignoran municipios, partidos y núcleos; D8 no premia la compacidad geométrica. No implementar ahora.

## 5. Las cinco técnicas que más suben de liga, con su experimento barato

| # | Técnica | Experimento (local, sin lanzar nada) | Criterio de aceptación |
|---|---|---|---|
| 1 | Exacto por vecindarios (A2-1) | Sevilla y La Rioja autonómica desde el ganador de las cadenas | Sevilla llega a 6 · 785,968 km en < 5 min de CPU, huella repetida |
| 2 | Cotas por agrupaciones (A2-2) | Programa sobre demarcaciones en los cuatro del piloto y en uno con K > 37 | Cota ≤ óptimo en los cuatro, igual en dos, < 30 s |
| 3 | Ráfagas cortas (A2-4) | Mismas semillas y pasos, b = 5, 20, 50, sin exacto | Óptimo en 2 de 3; nunca peor que hoy |
| 4 | Contigüidad por cortes o flujos (A2-3) | Tres variantes del modelo en cinco instancias neutras | Frontera de Sevilla en la mitad de tiempo, o aut17 cierra la etapa 1 |
| 5 | Muestreador validado (A2-5) | Tres muestreadores contra `enumerar_exacto` en 2 o 3 territorios | Variación total < 0,05 y R-hat < 1,05 |

Orden por coste: 3 (una sesión), 2 y 4 (dos o tres), 5 (dos o tres), 1 (una semana).

## 6. Qué publican los mejores y este proyecto aún no

| Qué | Quién lo publica | Aquí hoy |
|---|---|---|
| Instancias de prueba descargables | Validi y otros (7); Shahmizad y Buchanan (8) | Existen (T-296) y no se versionan |
| Mapa óptimo y su prueba, por instancia | (8), enlazados en Dave's Redistricting | Solo en estudios internos |
| Cota y hueco donde no hay óptimo | Grupo de Aquisgrán (17); (8) | Ninguna cota publicada |
| Conjunto de mapas alternativos con diagnósticos | ALARM (14) | Retirados el 16-11; T-469 sin aprobar |
| Validación del muestreador contra enumeración | Fifield y otros (15); McCartan e Imai (4) | No hay muestreador validado |
| Código de reproducción de cada cifra | (7), (8), (13), (14) | Paquete privado (D-94) |
| Puntuar un mapa ajeno con la regla pública | Dave's Redistricting; PlanScore (21) | No hay verificador público |
| Tolerancia sobre población proyectada | Comisión Electoral de Australia (19) | Una sola fecha |

## 7. Camino en tres pasos

1. **Esta semana (sin tocar el motor).** Ráfagas cortas (A2-4) y tabla de renuncias (A2-9) como estudios en
   `docs/ESTUDIOS/`. Prueba: las dos tablas de aceptación, reproducibles con un comando.
2. **Este mes.** Cotas por agrupaciones (A2-2), variantes de contigüidad (A2-3) y validación del muestreador
   (A2-5). Prueba: una línea por territorio del piloto, «óptimo» o «a N como mucho», y la tabla de validación.
3. **Este trimestre.** Exacto por vecindarios (A2-1) como Deslinde 1.3 en la siguiente regeneración; banco público
   (A2-6) y certificados (A2-7). Prueba: los 71 territorios con estado «óptimo demostrado», «óptimo local
   certificado» o «a N como mucho», y `datos_abiertos/banco/` con verificador en CI.

## 8. Lo que no pude comprobar, y objeciones

**No comprobado**
- Tamaños exactos de las instancias de (7) y planes por estado de ALARM: `arxiv.org`, `par.nsf.gov` y
  `pmc.ncbi.nlm.nih.gov` no se resuelven desde esta sesión; habría que permitirlos en la red del entorno.
- Átomos × K de los 71 territorios: no hay tabla versionada. Se obtiene con `bateria_motor.py entradas` y
  `exacto.tamano`, sin lanzar el motor. Sin ella no se sabe cuántos territorios caben hoy en 2.000.
- Ningún experimento se ha ejecutado: `ortools` no está instalado aquí y las instancias neutras no se versionan.
- Licencias de `fairmandering` y de `frcw.rs`; autores del artículo de Polsby-Popper (doi 10.1287/opre.2024.1078).
- El estudio T-180 usó la cadena de producción de entonces y la función B a posteriori, no el «ponderado» actual:
  su dato de saturación es un indicio, no una medida de Deslinde 1.2.

**Objeciones (D-216)**
- El encargo habla de K de 1 a 37; lo medido llega a 135, con 16 territorios por encima de 37. La estrategia
  «subir el techo del exacto» no alcanza a esos: hace falta descomponer (A2-1).
- T-467 está condicionada a «si hace falta». El piloto ya dice que hace falta (Sevilla) y que la receta prevista,
  más pasos, no sirve. Conviene reescribirla como «ráfagas y exacto local», no como «cadenas más largas».
- El techo de 2.000 se fijó con tres puntos (Sevilla, Burgos, Valladolid; `T502…/INFORME.md:65-68`). Antes de
  recalibrarlo conviene decidir la formulación (A2-3): el techo depende de ella.
- D-92 y D-94 (privado) y «referente mundial» tiran en sentidos contrarios: nadie cita un banco que no puede bajar.

## 9. Fuentes

1. DeFord, Duchin, Solomon (2021). Recombination. *Harvard Data Science Review*. https://arxiv.org/abs/1911.05725
2. Cannon, Duchin, Randall, Rule (2022, rev. 2025). Spanning Trees and Redistricting. https://arxiv.org/abs/2210.01401
3. Autry, Carter, Herschlag, Hunter, Mattingly (2023). Metropolized Forest Recombination. *SIAM J. Appl. Math.*
   83(4). https://arxiv.org/abs/1911.01503
4. McCartan, Imai (2023). Sequential Monte Carlo for sampling balanced and compact redistricting plans. *Annals of
   Applied Statistics* 17(4). https://arxiv.org/abs/2008.06131
5. O'Sullivan, Imai, McCartan (2026). Generalized Sequential Monte Carlo Sampling. https://arxiv.org/abs/2603.22188
6. Cannon y otros (2023). Voting Rights, Markov Chains, and Optimization by Short Bursts. *Methodology and Computing
   in Applied Probability* 25:36. https://link.springer.com/article/10.1007/s11009-023-09994-1
7. Validi, Buchanan, Lykhovyd (2022). Imposing Contiguity Constraints in Political Districting Models. *Operations
   Research* 70(2). https://github.com/hamidrezavalidi/Political-Districting-to-Minimize-Cut-Edges
8. Shahmizad, Buchanan (2025). Political Districting to Minimize County Splits. *Operations Research* 73(2).
   https://github.com/maralshahmizad/Political-Districting-to-Minimize-County-Splits
9. Gurnee, Shmoys (2021). Fairmandering. https://arxiv.org/abs/2103.11469
10. Brous, Shmoys (2025). Optimizing Districting Plans… via IPs and Local Search. https://arxiv.org/abs/2508.07446
11. Cohen-Addad, Klein, Young (2018). Balanced centroidal power diagrams. https://arxiv.org/abs/1710.03358
12. Zhang, Validi, Buchanan, Hicks (2023). Linear-size formulations… https://doi.org/10.1007/s11590-023-02070-0
13. Swamy, King, Jacobson (2023). Multiobjective Optimization for Politically Fair Districting. *Operations
    Research* 71(2). https://doi.org/10.1287/opre.2022.2311
14. McCartan y otros (2022). Simulated redistricting plans… (ALARM). *Scientific Data* 9:689.
    https://doi.org/10.1038/s41597-022-01808-2
15. Fifield, Imai, Kawahara, Kenny (2020). The Essential Role of Empirical Validation… *Statistics and Public
    Policy* 7(1). https://arxiv.org/abs/2006.10148
16. GerryChain (MGGG), optimizadores. https://gerrychain.readthedocs.io/en/latest/user/optimizers/
17. Goderbauer, Winandy (2018). Political Districting Problem: Literature Review… RWTH Aachen.
    https://or.rwth-aachen.de/files/research/repORt/LitSurvey_PoliticalDistricting__Goderbauer_Winandy_20181024.pdf
18. Boundary Commission for England. Guide to the 2023 Review.
    https://boundarycommissionforengland.independent.gov.uk/2023-review/guide-to-the-2023-review-of-parliamentary-constituencies/
19. Australian Electoral Commission. Enrolment projections overview (2023).
    https://www.aec.gov.au/redistributions/2023/wa/enrolment-projections-overview.html
20. Biblioteca del Parlamento de Canadá (2022). https://lop.parl.ca/en/researchpublications/202227e
21. PlanScore. https://planscore.org/about/ · Dave's Redistricting. https://davesredistricting.org
