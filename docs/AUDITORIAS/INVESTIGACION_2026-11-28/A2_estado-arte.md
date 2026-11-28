# A2 · Algoritmo: estado del arte mundial y mejoras para Deslinde (T-509)

Fecha: 2026-11-28. Agente local, solo lectura. Código de `main` en 9e630d11. No se ha ejecutado el motor ni ningún
experimento: todo lo propuesto lleva su prueba, sin hacer. Hallazgos en `A2_estado-arte.json` (11, con evidencia).

**Verificación independiente (28-11, contra `origin/main` 548968c4).** Revisados A2-1 a A2-10: 0 confirmados sin
cambios, 10 corregidos, 0 refutados; A2-11 sin revisar. Las cifras internas salen iguales; se corrigen propuestas,
criterios de aceptación, impactos y tres afirmaciones (sección 10). Detalle en el campo `verificacion` del JSON.

## 1. Veredicto

1. Deslinde juega hoy en **segunda alta**. Tiene algo que GerryChain y `redist` no dan: un óptimo demostrado y
   reproducible bit a bit, con un resolutor abierto, en los territorios pequeños.
2. Pero el exacto es **todo o nada**: territorio entero, una circunscripción, sin exenciones y átomos × K ≤ 2.000.
3. Medido en los 71 territorios: K va de 1 a **135**, no de 1 a 37. Hay 24 con K ≤ 4 (8 de ellos con K = 1, sin
   nada que trazar), 20 entre 5 y 10, 11 entre 11 y 37 y **16 con K > 37**. En esos 16, y en las autonómicas con varias circunscripciones, el exacto no entra nunca.
4. Fuera del exacto la búsqueda es ReCom básico (2019): N cadenas independientes de 300 pasos. Ya perdió en
   Burgos, Valladolid y Sevilla (8 demarcaciones partidas frente a 6 demostradas; desde T-503 ahí gana el exacto).
5. Más pasos ayudan poco: GerryChain puro con 100.000 pasos y 6,9 h de CPU tampoco llegó (T-466).
6. No hay ninguna cota donde el exacto no cierra: en esos territorios no se sabe a cuánto está el mapa del mejor.
7. No se publica nada con lo que otros puedan medirse: ni instancias, ni cotas, ni conjuntos de mapas.
8. La literatura de 2021 a 2026 tiene publicado, con código, casi todo lo que falta. Son cinco técnicas; la de
   cotas no se traslada tal cual (A2-2).
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
| Contigüidad por cortes y flujos (7); lineal en grafos planos (12) | Modelos enteros fuertes de contigüidad | Óptimo en 21 estados a nivel de tramo censal | GPL-3.0 y exige Gurobi: se reimplementa la idea | `exacto.py` (modelo 2.0). Hipótesis sin medir: podría subir el techo de 2.000 |
| Mínimo de condados partidos (8) | Cota por agrupaciones más plan que la alcanza | Todas las cámaras de EE. UU. salvo Hawái; p. ej. 95 condados, K = 33 | Repositorio público, licencia no visible | `cotas.py` nuevo, con modelo propio: la cota k − q acota particiones y D8 cuenta demarcaciones partidas |
| Generación de columnas (9) y reoptimización local (10) | Muchos distritos candidatos y un problema maestro; mejora por fragmentos | Estados enteros; en (10) la generación de columnas supera a las ráfagas | Sin comprobar | `exacto_local.py` y candidato «maestro». La vía para K > 37 |
| Diagramas de potencia equilibrados (11) | Distritos compactos de población exacta | Seis estados más poblados, por manzana | Académico | Encaje bajo: ignora municipios y núcleos. Solo semilla de reserva |
| Multiobjetivo multinivel (13) | Frente de Pareto con restricción ε tras contraer el grafo | Wisconsin | Datos y código públicos | Estudio con el exacto actual; contenido para T-470 y T-471 |
| Validación por enumeración (15) | Comprobar un muestreador contra todos los planes | 70 recintos (número de planes sin confirmar) | GPL (`redist`) | `exhaustivo.py` ya enumera: ventaja propia para validar T-469 |

Comisiones de límites (18, 19, 20): no usan optimizador como árbitro. Inglaterra fija ±5 % (69.724 a 77.062
electores) y trabaja por barrios, con propuestas iniciales, revisadas e informe final. Australia exige ±10 % hoy y
±3,5 % sobre la población proyectada, con datos por la unidad mínima (SA1). Canadá admite ±25 % con motivos
escritos, una comisión independiente por provincia y audiencias públicas.

## 4. Hallazgos, de mayor a menor impacto

### A2-1 · El exacto es todo o nada: falta el exacto por vecindarios (impacto 4, esfuerzo L)
- **Hoy.** `exacto.py:54,61-79`: solo territorio entero, D8, una circunscripción, sin exenciones, 2 ≤ K ≤ 4 o
  tamaño ≤ 2.000. 16 de 71 territorios tienen K > 37 (todos K ≥ 45: no caben nunca, átomos × K ≥ 2.025). La Rioja
  autonómica (K = 33) no cierra ni la primera etapa (`T296_OPTIMO_D8/README.md:69`).
- **Propongo.** Candidato «exacto local» (`exacto_local.py`, reutiliza `_Modelo`): desde el mejor candidato, tomar
  en orden fijo grupos de 2 a 4 distritos contiguos, fijar el resto, resolver D8 exacto en el fragmento y aceptar
  solo si mejora la clave oficial completa. Certificado nuevo: «ningún grupo de hasta 4 distritos vecinos que quepa
  en 2.000 mejora» (óptimo local, no global).
- **Aceptación.** En Sevilla, desde el plan de 8 partidas y sin exacto global, llega a 6 · 785,968 km en menos de
  5 min de CPU con la misma huella dos veces. En La Rioja autonómica acaba en menos de 30 min de CPU, con la misma
  huella dos veces y plan válido, y el informe dice si mejora y en qué término.
- **Riesgo.** Cambio de motor (solo en regeneración). Los términos globales de D8 hay que modelarlos con cuidado.
  El modelo excluye hoy varias circunscripciones y exenciones, que es el caso de casi todas las autonómicas grandes.
- **Ya previsto.** T-468 solo como propuesta de la auditoría; no está en `docs/PLAN.md` ni nombra la técnica.
- **Verificación: corregido.** Impacto 5 → 4: da un óptimo local, no demostración ni cota, y no hay experimento. En
  la fuente (10) lo que supera a las ráfagas es la generación de columnas, no la reoptimización local.

### A2-2 · Sin cota fuera del exacto: hace falta una cota propia (impacto 3, esfuerzo M, confianza baja)
- **Hoy.** La cota sale solo de CP-SAT y solo donde el modelo entero aplica (`exacto.py:354-358`). El término que
  decide es «demarcaciones partidas» (`T465…/INFORME.md:8-10`). Se parece a «condados partidos», pero D8 cuenta las
  demarcaciones repartidas en más de un distrito (`naturalidad_clave.py:52-53`) y la técnica de (8) acota las
  particiones (partes − 1): en Sevilla, tres comarcas partidas en 4, 6 y 13 son 3 para D8 y 20 particiones.
- **Propongo.** `cotas.py` con modelo propio: programa entero sobre las piezas partido judicial ∩ comarca que
  maximiza las demarcaciones enteras (cada una en un solo distrito, sin pasar del techo). Demarcaciones menos ese
  máximo acota el tercer término de D8. Va a `COMPETICION.json` como dato.
- **Aceptación.** En los cuatro del piloto la cota es ≤ el óptimo (2, 2, 2, 6) y ≥ la cota trivial (demarcaciones
  mayores que el techo; en Sevilla, 3), con su hueco, en menos de 30 s; en un territorio con K > 37 da cota y hueco
  en menos de 5 min. Si no mejora la trivial en ninguno, se descarta y se deja escrito.
- **Riesgo.** Ignora contigüidad y R012: válida siempre, ajustada quizá no. El repositorio de (8) no muestra licencia.
- **Verificación: corregido.** La cota «K menos el máximo de agrupaciones» no vale para D8 (sección 10). Impacto 4 → 3.

### A2-3 · La contigüidad del exacto es la formulación padre y nivel (impacto 3, esfuerzo M)
- **Hoy.** Árbol padre/nivel con un entero 0..n−1 por átomo (`exacto.py:218-234`). En el estudio de Sevilla la etapa
  de frontera se lleva 42,8 de 60,2 s y cierra (`resultados/exacto/nac41.json`); en producción no cierra ni con tope
  60 ni con 300 (`T502…/INFORME.md:49-61`). Que la causa sea la contigüidad es una hipótesis: CP-SAT no depende de
  la relajación lineal como un resolutor entero clásico, y la configuración del estudio no se ha comparado.
- **Propongo.** Estudio con tres variantes sobre las instancias neutras: la actual, flujo por distrito, y sin
  contigüidad más bucle de cortes separadores. Solo si una gana, se propone como modelo 2.0.
- **Aceptación.** Tabla de estado y tiempo por etapa en nac09, nac47, nac26, nac41 y aut17 con la configuración de
  producción; se adopta una variante solo si cierra la frontera de Sevilla dentro del tope 60 (hoy no cierra ni con
  300) o cierra la primera etapa de aut17, con el mismo plan dos veces.
- **Riesgo.** CP-SAT no admite cortes dentro de la búsqueda; el bucle puede no ganar.
- **Verificación: corregido.** Impacto 4 → 3 (estudio de resultado incierto). Necesita aprobación del propietario
  (D-18, D-216), no «nada». El criterio anterior («la mitad del tiempo actual») no se podía medir.

### A2-4 · Cadenas independientes de 300 pasos: probar ráfagas cortas (impacto 4, esfuerzo S)
- **Hoy.** `candidatos.py:301` (300 pasos), `competicion.py:450` (5 cadenas por defecto), `ponderado.py:101-115`.
  En el estudio de las 71 (cadena de entonces, función B) el N de saturación fue 15 o 20 en 26 territorios y 20,
  el tope probado, en 11; cuenta también cambios de ganador por desempate de huella.
- **Propongo.** Mismo total de pasos en ráfagas de b pasos desde el mejor plan según D8; registrar la tasa de
  rechazo del núcleo, que hoy no se guarda. Prueba con b = 5, 20 y 50, sin el candidato exacto.
- **Aceptación.** Arrancando solo del canónico (sin vigente ni exacto) y con línea base de las cadenas actuales:
  alcanza el óptimo demostrado en 2 de 3 (Burgos, Valladolid, Sevilla) y en más que la línea base, y nunca empeora
  su clave en los cuatro. Si no, se descarta y se deja escrito.
- **Ya previsto.** T-467 (propuesta: «cadenas más largas»). El piloto mide que más pasos ayudan poco.
- **Verificación: corregido.** En Burgos y Valladolid el candidato vigente ya es el óptimo: sin fijar el arranque
  y la línea base, el criterio se cumplía solo. Impacto sin cambio.

### A2-5 · Los mapas alternativos piden un muestreador validado (impacto 3, esfuerzo M)
- **Hoy.** La única cadena es ReCom con recargos y rechazo duro (`ponderado.py:46-66,81-102`): buena para buscar,
  sin distribución conocida. `exhaustivo.py:50` enumera todos los planes válidos en lo pequeño. Las alternativas
  se retiraron el 16-11 (D-138, D-141) y T-469 no está aprobada (D-214).
- **Propongo.** Antes de T-469: en 2 o 3 territorios enumerables, comparar cadena actual, ReCom reversible y
  `redist` (fuera del paquete) contra la enumeración. Elegir con esa tabla.
- **Aceptación.** Distancia de variación total menor que 0,05 en partidas (por valor), frontera y desvío (10 tramos
  fijados antes) con 10.000 planes, y R-hat menor que 1,05 entre 4 ejecuciones. Si nadie lo cumple, se deja escrito.
- **Verificación: corregido.** Depende de una tarea que no existe: impacto 4 → 3. Publicar la prueba choca con D-92.

### A2-6 · No se publica nada con lo que otros puedan medirse (impacto 3, esfuerzo M)
- **Hoy (verificado).** `datos_abiertos/INDEX.json` (52 territorios) no tiene ninguna clave de exacto, cota, huella,
  semilla ni competición. `paquetes/deslinde/MAPAS.json` tiene 0 mapas y dice versión 1.0.0 (el paquete va por
  1.2.0). Las instancias neutras de T-296 «no se versionan». Es así por decisión: D-92 declara secretos el código,
  la definición formal de D8 y los estudios y mediciones.
- **Propongo.** Primero, que el propietario decida si revisa D-92: un verificador que da la clave D8 publica la
  definición de D8, y la mejor clave y la cota son mediciones. Solo entonces, «Banco DDD» empezando por los cuatro
  del piloto: instancia neutra con sha256, mejor clave, cota, estado y verificador de un fichero.
- **Aceptación.** Solo si se revisa D-92: `datos_abiertos/banco/INDEX.json` con las cuatro instancias del piloto;
  `verificar_plan.py` da la clave de `T465_BANCO_PILOTO/resultados/RESUMEN.json`; una prueba de CI lo comprueba.
- **Necesita.** Decisión del propietario: va contra D-92 y D-94 y depende de la licencia pendiente (T-473).
- **Verificación: corregido.** Hay decisión en contra en vigor (D-92): impacto 4 → 3. Las 71 instancias no existen
  (solo 9 de T-296 y 4 del piloto; Madrid falla en la nube). T-466 no es propuesta: está hecha (#1025).

### A2-7 · Separar buscar de certificar (impacto 3, esfuerzo M)
- **Hoy.** En producción la etapa de frontera de Sevilla no cierra ni con tope 60 ni con 300 (`exacto.py:56,389-390`;
  T-502): tiene el plan óptimo y sale «MEJOR_VALIDO». El estudio T-465 sí cierra las cinco etapas. D-73 nombraba
  HiGHS o CBC; solo hay CP-SAT, nadie cruza la prueba.
- **Propongo.** Certificado fuera de línea por territorio (con la configuración que cierra, registro y versión) y
  segundo resolutor abierto para la etapa decisiva. La competición compara la huella del plan con la certificada.
- **Aceptación.** Certificado de Sevilla atado a la huella de reglas y al sha256 de la instancia (las cinco etapas
  OPTIMAL ya están en `resultados/exacto/nac41.json`); un segundo resolutor confirma «partidas = 6»; la competición
  marca OPTIMO si la huella del plan coincide, con la misma `huella_resultado` dos veces.
- **Verificación: corregido.** Subir el tope no basta (T-502) y media aceptación ya se cumplía con el estudio.

### A2-8 · Recombinar los distritos que las cadenas tiran (impacto 3, esfuerzo M, confianza baja)
- **Hoy.** `ponderado.py:104-115` guarda el mejor plan y solo la huella del resto.
- **Propongo.** Guardar los distritos vistos y resolver con CP-SAT la selección de K que cubren el territorio.
- **Aceptación.** En el piloto, sin vigente ni exacto: clave igual o mejor que la mejor cadena y estrictamente mejor
  en uno; menos de 60 s.
- **Verificación: corregido.** Es un estudio: necesita aprobación del propietario (D-18, D-216), no «nada».

### A2-9 · Medir lo que cuesta cada renuncia de D8 (impacto 3, esfuerzo S)
- **Hoy.** Sevilla: de 8 a 6 partidas cuesta 22 km de frontera. La cifra de Burgos de T-296 (de 3 a 2 partidas, el
  desvío sube del 0,02 % al 4,23 %) es de cuando la frontera valía 0; hoy su óptimo es 2 · 315,8 km · 7,84 %.
- **Propongo.** Con el exacto actual, por territorio: partidas = óptimo, + 1 y + 2, con frontera y desvío mínimos.
- **Aceptación.** Tabla de tres filas por cada uno de los cuatro del piloto, cada fila con su estado (OPTIMAL o «no
  cierra») y la elegida por D8 marcada.
- **Verificación: corregido.** Cifra de Burgos no vigente; el criterio pedía «todos los puntos no dominados», que la
  propuesta no calcula. Publicar la tabla fuera exige revisar D-92.

### A2-10 · Medir la población futura, como Australia (impacto 3, esfuerzo S)
- **Hoy.** La tolerancia usa una sola fecha (`exacto.py:168,188-198`).
- **Propongo.** Estudio: los 71 mapas vigentes evaluados con la población de cuatro años antes.
- **Aceptación.** Tabla por territorio de distritos fuera de tolerancia en t − 4 (Atlas del INE, tabla 30832) y en
  t, con la población que no casa, fuentes y sha256.
- **Verificación: corregido.** No hay «padrón por sección de 2011 a 2025»: T-357 midió el Atlas 2015-2024 (lista
  única de 37.229 secciones) y el censo de 2011, sin versionar; no existe padrón por sección anterior a 2015.

### A2-11 · Diagramas de potencia: encaje bajo (impacto 2; sin revisar en la verificación)
- Ignoran municipios, partidos y núcleos; D8 no premia la compacidad geométrica. No implementar ahora.

## 5. Las cinco técnicas que más suben de liga, con su experimento barato

| # | Técnica | Experimento (local, sin lanzar nada) | Criterio de aceptación |
|---|---|---|---|
| 1 | Exacto por vecindarios (A2-1) | Sevilla y La Rioja autonómica desde el ganador de las cadenas | Sevilla llega a 6 · 785,968 km en < 5 min de CPU, huella repetida |
| 2 | Cota de demarcaciones partidas, modelo propio (A2-2) | Programa sobre demarcaciones en los cuatro del piloto y en uno con K > 37 | Cota ≤ óptimo y ≥ la trivial en los cuatro, con su hueco, < 30 s |
| 3 | Ráfagas cortas (A2-4) | Mismas semillas y pasos, b = 5, 20, 50, desde el canónico, sin vigente ni exacto | Óptimo en 2 de 3 y en más que la línea base; nunca peor |
| 4 | Contigüidad por cortes o flujos (A2-3) | Tres variantes del modelo en cinco instancias neutras | Frontera de Sevilla cierra dentro del tope 60, o aut17 cierra la etapa 1 |
| 5 | Muestreador validado (A2-5) | Tres muestreadores contra `enumerar_exacto` en 2 o 3 territorios | Variación total < 0,05 (tramos fijados antes) y R-hat < 1,05 |

Orden por coste: 3 (una sesión), 2 y 4 (dos o tres), 5 (dos o tres), 1 (una semana). Tras la verificación, solo
A2-1 y A2-4 quedan con impacto 4; las otras tres, con 3.

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

1. **Esta semana (sin tocar el motor), si el propietario los aprueba (D-216).** Ráfagas cortas (A2-4) y tabla de
   renuncias (A2-9) como estudios en `docs/ESTUDIOS/`. Prueba: las dos tablas de aceptación, reproducibles con un comando.
2. **Este mes.** Cota de demarcaciones partidas (A2-2), variantes de contigüidad (A2-3) y validación del muestreador
   (A2-5). Prueba: una línea por territorio del piloto, «óptimo» o «a N como mucho», y la tabla de validación.
3. **Este trimestre.** Exacto por vecindarios (A2-1) como Deslinde 1.3 en la siguiente regeneración; banco público
   (A2-6, solo si se revisa D-92) y certificados (A2-7). Prueba: los 71 territorios con estado «óptimo demostrado», «óptimo local
   certificado» o «a N como mucho», y `datos_abiertos/banco/` con verificador en CI.

## 8. Lo que no pude comprobar, y objeciones

**No comprobado**
- Verificación: los 44 millones de planes de (15); cuántos territorios con K ≥ 5 caben en 2.000 (T-503 da 27
  candidatos y confirma Sevilla); por qué la frontera de Sevilla cierra en el estudio y no en producción.
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

## 10. Descartados en la verificación

Ningún hallazgo queda refutado entero: los diez revisados siguen en pie, corregidos. Se descartan estas afirmaciones:

- **«K menos el máximo de agrupaciones acota el tercer término de D8» (A2-2).** Esa cota es de particiones (partes
  − 1 por demarcación) y D8 cuenta demarcaciones partidas. En Sevilla el plan óptimo tiene 20 particiones solo en
  tres comarcas y D8 cuenta 6 en total: con menos de 10 comarcas, esa cota ya pasaría del óptimo demostrado.
- **«Óptimo demostrado en 24 de 71 territorios (K ≤ 4)» (liga de hoy).** 8 de los 24 tienen K = 1 y el exacto no
  aplica; con 2 ≤ K ≤ 4 hay 16, y el óptimo está medido en 8 provincias (T-296) y en el piloto.
- **«El proyecto ya tiene padrón por sección de 2011 a 2025» (A2-10).** T-357: Atlas del INE 2015-2024 y censo de
  2011, sin versionar; no existe padrón por sección anterior a 2015.
- **«El banco no abre el motor» y «los datos ya existen» (A2-6).** El verificador publica la definición de D8, que
  D-92 declara secreta; instancias neutras solo hay de 9 territorios más los 4 del piloto.
- **«La reoptimización local supera a las ráfagas cortas» (A2-1, fuente 10).** Lo que las supera es la generación
  de columnas; la reoptimización local mejora cualquier plan de partida.
- **Burgos, «el desvío sube del 0,02 % al 4,23 %» (A2-9).** Medido en T-296 con la frontera a 0; ya no es vigente.
