# N06 — Primacía de la mónada electoral: expediente corregido

**Versión:** 1.1.0. **Fecha:** 2026-10-12. **Alcance:** recomendación institucional Congreso DDD, población y seccionado 2025; sin generación. **Estado:** `WAIT_OWNER`. **Cambios:** retira la recomendación legal de 350, propone redondeo provincial y excepciones declarativas. **Motivo:** orden expresa del propietario, canalizada por Work. **Anterior:** [expediente 1.0.0](../../../legacy/docs/ESTUDIOS/N06_DECISION_K_20261012_v1.0.0/EXPEDIENTE.md).

## Recomendación única

Recomendar **407 diputados para la población 2025**, como suma de asignaciones independientes `K_i=max(1, floor(P_i/120000+1/2))` en las 52 circunscripciones. El total es un resultado, no una restricción nacional. Recomendar conjuntamente las excepciones poblacionales de circunscripción completa y la política previa de singularidades físicas descritas abajo. Su aplicación cartográfica permanece bloqueada hasta acreditar el registro de componentes y su factibilidad; 407 es una referencia de planificación reproducible, no un mapa certificado ni una aprobación automática.

N06 sigue vinculada al Plan `ddd-maestro-20261008`, tarea N06, copia viva `ddd-maestro-vivo-20261011`; [vínculo preservado](vinculo_plan.json). No se cambia el Plan ni el contrato candidato, que conserva total nulo y generación no autorizada. Work dirige y registra la futura decisión.

## Principios institucionales ya establecidos por el propietario

DDD se inspira en la teoría de representación política de Antonio García-Trevijano y persigue la representación directa del elector mediante distritos uninominales. La mónada electoral y la igualdad de representación fundamentan el modelo. Esta declaración recoge el mandato del propietario; no atribuye una fórmula operacional concreta al autor sin evidencia histórica.

1. La dimensión ordinaria está en el orden de 100.000–120.000 habitantes, con referencia histórica de cálculo de 120.000.
2. K deriva de población y territorio; no se prefija nacionalmente.
3. Las provincias son fronteras duras; ninguna unidad puede cruzarlas.
4. Todas las provincias conservan representación propia; Ceuta y Melilla separadamente.
5. Las provincias pequeñas, especialmente Soria, y ambas ciudades requieren excepciones expresas suficientemente amplias.
6. Una excepción territorial no crea una tolerancia general que vacíe la igualdad ordinaria.
7. Se preservan en lo posible identidad territorial, municipal y comarcal; el mapa histórico de 2022 es referencia preferente de continuidad, condicionada a acreditación, integridad y compatibilidad con secciones 2025.
8. Los 350 escaños, el reparto LOREG y el intervalo constitucional actual son contraste externo; no son fundamento, objetivo ni criterio de optimización de DDD.

Están pendientes de aprobación **la fórmula, el desempate y las reglas operacionales de excepción**, no estos principios.

## Rectificación y conservación del antecedente

Se retira íntegramente la recomendación institucional de K=350 y los textos A/B del expediente anterior. Reproducir dos mínimos provinciales y repartir un residual para alcanzar un total legal invierte la causalidad DDD: fija primero el tamaño y después ajusta la representación. En 2025 implica media nacional 140.366,56 y una razón Madrid/Soria de 4,15, incompatible con usar la mónada de 120.000 como fundamento. La conformidad con legislación vigente no subsana esa contradicción institucional.

El original se conserva literalmente en `legacy/`, con su manifiesto original y SHA de commit **d8fb5ada561d02669b25adfb349f469aa2db4619**. Su dictamen recibido fue **GO_ACOTADO**, revisión independiente, y sus pruebas 11+42 PASS. Ese dictamen no valida la recomendación institucional de 350. No se dispone en este directorio del texto íntegro del dictamen anterior: se conserva su identificación como estado recibido, sin inventar acta. Todos los scripts, logs, datos y 15 escenarios originales permanecen intactos. K350 es exclusivamente comparativo no seleccionado.

No se reabre investigación jurídica ni se adquieren fuentes de 2026. Las referencias BOE del antecedente quedan allí como contraste externo.

## Fórmula y correspondencia histórica

`q_i=P_i/120000`; `K_i=max(1,(P_i+60000)//120000)` para población entera positiva. Es redondeo al entero más próximo, con empate exacto de cuota terminada en 0,5 **hacia arriba**; no se usa `round()` bancario ni coma flotante. Ejemplos: 179.999 →1; 180.000 →2; 180.001 →2. El mínimo uno preserva cada circunscripción incluso por debajo de 60.000. Las ciudades aplican la misma fórmula sobre 2025 y tienen una plaza cada una; su separación no depende del resultado aritmético.

La semántica coincide con `half_up` y `nearest_half_up_independiente` del estudio N05 integrado; el mínimo no cambia ninguna asignación de esa alternativa en 2025. No hay empates exactos en las 52 cuotas actuales. El redondeo minimiza por provincia el error absoluto en número de mónadas `|K_i-q_i|` sujeto a mínimo uno; no se afirma que minimice toda medida de desigualdad poblacional por diputado.

La reconstrucción histórica propuesta es **compatible conceptualmente** con 120.000 y continuidad provincial, pero **no está acreditada como fórmula ejecutada en 2022**. La evidencia ya integrada conserva 391 IDs/geometrías, incidencia documental 392/391, una geometría inválida y ediciones no acreditadas. El recuento contrafactual 391 con población 2025 no equivale al redondeo actual. No se reparan geometrías ni se reconstruyen las 15 alternativas. La continuidad histórica se evalúa después de acreditar sus entradas, subordinada a igualdad e integridad.

## Tabla de las 52 circunscripciones

Población: INE 65034 conservado, 1 de enero de 2025, total 49.128.297. SHA fuente `6a5f16d1bf354bebb1d05ad0f9afc350d8dc1c7ea251aac3ce6002e392b16a7c`. Cuota frente a 120.000, media provincial P/K, desviación respecto del objetivo, no de la media nacional. Fracciones exactas en [CSV](resultados/reparto_ddd_52.csv) y [JSON](resultados/correccion_ddd.json). N07 conserva 36.554 secciones y 52 circunscripciones; ese crosswalk no acredita población por sección ni conectividad física.

| CPRO | Provincia/ciudad | Población 2025 | Cuota | K | Media | Desviación hab. | Desviación % |
|---|---|---:|---:|---:|---:|---:|---:|
| 01 | Araba/Álava | 341,961 | 2.85 | 3 | 113,987.00 | -6,013.00 | -5.01 |
| 02 | Albacete | 390,751 | 3.26 | 3 | 130,250.33 | 10,250.33 | 8.54 |
| 03 | Alicante/Alacant | 2,033,566 | 16.95 | 17 | 119,621.53 | -378.47 | -0.32 |
| 04 | Almería | 770,554 | 6.42 | 6 | 128,425.67 | 8,425.67 | 7.02 |
| 05 | Ávila | 160,738 | 1.34 | 1 | 160,738.00 | 40,738.00 | 33.95 |
| 06 | Badajoz | 665,155 | 5.54 | 6 | 110,859.17 | -9,140.83 | -7.62 |
| 07 | Islas Baleares | 1,249,844 | 10.42 | 10 | 124,984.40 | 4,984.40 | 4.15 |
| 08 | Barcelona | 5,959,941 | 49.67 | 50 | 119,198.82 | -801.18 | -0.67 |
| 09 | Burgos | 362,663 | 3.02 | 3 | 120,887.67 | 887.67 | 0.74 |
| 10 | Cáceres | 388,190 | 3.23 | 3 | 129,396.67 | 9,396.67 | 7.83 |
| 11 | Cádiz | 1,261,420 | 10.51 | 11 | 114,674.55 | -5,325.45 | -4.44 |
| 12 | Castellón/Castelló | 627,620 | 5.23 | 5 | 125,524.00 | 5,524.00 | 4.60 |
| 13 | Ciudad Real | 494,848 | 4.12 | 4 | 123,712.00 | 3,712.00 | 3.09 |
| 14 | Córdoba | 773,163 | 6.44 | 6 | 128,860.50 | 8,860.50 | 7.38 |
| 15 | Coruña, A | 1,135,623 | 9.46 | 9 | 126,180.33 | 6,180.33 | 5.15 |
| 16 | Cuenca | 199,859 | 1.67 | 2 | 99,929.50 | -20,070.50 | -16.73 |
| 17 | Girona | 830,429 | 6.92 | 7 | 118,632.71 | -1,367.29 | -1.14 |
| 18 | Granada | 945,797 | 7.88 | 8 | 118,224.62 | -1,775.38 | -1.48 |
| 19 | Guadalajara | 285,839 | 2.38 | 2 | 142,919.50 | 22,919.50 | 19.10 |
| 20 | Gipuzkoa | 733,149 | 6.11 | 6 | 122,191.50 | 2,191.50 | 1.83 |
| 21 | Huelva | 538,789 | 4.49 | 4 | 134,697.25 | 14,697.25 | 12.25 |
| 22 | Huesca | 230,087 | 1.92 | 2 | 115,043.50 | -4,956.50 | -4.13 |
| 23 | Jaén | 618,143 | 5.15 | 5 | 123,628.60 | 3,628.60 | 3.02 |
| 24 | León | 448,030 | 3.73 | 4 | 112,007.50 | -7,992.50 | -6.66 |
| 25 | Lleida | 458,226 | 3.82 | 4 | 114,556.50 | -5,443.50 | -4.54 |
| 26 | Rioja, La | 326,803 | 2.72 | 3 | 108,934.33 | -11,065.67 | -9.22 |
| 27 | Lugo | 326,022 | 2.72 | 3 | 108,674.00 | -11,326.00 | -9.44 |
| 28 | Madrid | 7,113,886 | 59.28 | 59 | 120,574.34 | 574.34 | 0.48 |
| 29 | Málaga | 1,791,183 | 14.93 | 15 | 119,412.20 | -587.80 | -0.49 |
| 30 | Murcia | 1,586,989 | 13.22 | 13 | 122,076.08 | 2,076.08 | 1.73 |
| 31 | Navarra | 683,854 | 5.70 | 6 | 113,975.67 | -6,024.33 | -5.02 |
| 32 | Ourense | 305,278 | 2.54 | 3 | 101,759.33 | -18,240.67 | -15.20 |
| 33 | Asturias | 1,015,128 | 8.46 | 8 | 126,891.00 | 6,891.00 | 5.74 |
| 34 | Palencia | 158,702 | 1.32 | 1 | 158,702.00 | 38,702.00 | 32.25 |
| 35 | Palmas, Las | 1,171,547 | 9.76 | 10 | 117,154.70 | -2,845.30 | -2.37 |
| 36 | Pontevedra | 947,818 | 7.90 | 8 | 118,477.25 | -1,522.75 | -1.27 |
| 37 | Salamanca | 328,446 | 2.74 | 3 | 109,482.00 | -10,518.00 | -8.77 |
| 38 | Santa Cruz de Tenerife | 1,087,319 | 9.06 | 9 | 120,813.22 | 813.22 | 0.68 |
| 39 | Cantabria | 593,623 | 4.95 | 5 | 118,724.60 | -1,275.40 | -1.06 |
| 40 | Segovia | 158,251 | 1.32 | 1 | 158,251.00 | 38,251.00 | 31.88 |
| 41 | Sevilla | 1,977,664 | 16.48 | 16 | 123,604.00 | 3,604.00 | 3.00 |
| 42 | Soria | 90,183 | 0.75 | 1 | 90,183.00 | -29,817.00 | -24.85 |
| 43 | Tarragona | 875,530 | 7.30 | 7 | 125,075.71 | 5,075.71 | 4.23 |
| 44 | Teruel | 136,091 | 1.13 | 1 | 136,091.00 | 16,091.00 | 13.41 |
| 45 | Toledo | 755,081 | 6.29 | 6 | 125,846.83 | 5,846.83 | 4.87 |
| 46 | Valencia/València | 2,763,996 | 23.03 | 23 | 120,173.74 | 173.74 | 0.14 |
| 47 | Valladolid | 528,644 | 4.41 | 4 | 132,161.00 | 12,161.00 | 10.13 |
| 48 | Bizkaia | 1,167,233 | 9.73 | 10 | 116,723.30 | -3,276.70 | -2.73 |
| 49 | Zamora | 165,564 | 1.38 | 1 | 165,564.00 | 45,564.00 | 37.97 |
| 50 | Zaragoza | 998,443 | 8.32 | 8 | 124,805.38 | 4,805.38 | 4.00 |
| 51 | Ceuta | 83,567 | 0.70 | 1 | 83,567.00 | -36,433.00 | -30.36 |
| 52 | Melilla | 87,067 | 0.73 | 1 | 87,067.00 | -32,933.00 | -27.44 |

**Total: 407**, provincias 405 y ciudades 2. Media nacional **120,708.35**; objetivo ordinario **120.000**. La diferencia nacional de +708,35 (+0,5903%) no redefine el objetivo. Las cifras decimales de presentación usan separadores ingleses; los archivos exactos evitan ambigüedad.

## Igualdad efectiva y distorsiones

Cada distrito tendría un representante único y cada elector pertenecería a una sola unidad exhaustiva, sin cruces provinciales. La igualdad se mide aquí por habitantes por diputado; no se confunde con número de electores censados ni se acredita ya la partición interna. La regla ofrece igualdad aproximada, no igualdad exacta garantizada por un cálculo agregado.

MAE provincial ponderado por plazas: **4,064.14 habitantes (3,3868% del objetivo)**. Extremos: 83,567.00 (Ceuta) y 165,564.00 (Zamora); razón máxima/mínima **1.981213**. Excluyendo las tres excepciones de población baja: medias entre 99,929.50 y 165,564.00; razón **1.656808**.

El redondeo deja `|P_i-120000*K_i|≤60000` cuando el mínimo no fuerza una cuota menor que 0,5. Por tanto `|P_i/K_i-120000|≤60000/K_i`; este es un residuo aritmético verificable, **no una tolerancia por distrito**. La concentración de desviaciones en provincias de K pequeño es efecto de indivisibilidad. Zamora, Ávila, Palencia, Segovia y Teruel tienen K=1; sus medias superiores a 120.000 no requieren una dispensa inventada: cambiar a dos representantes sustituiría el error de redondeo por otro. En provincias grandes la envolvente se estrecha automáticamente.

La banda 100.000–120.000 expresa el orden ordinario, no un techo estricto ya adoptado. Ni siquiera Madrid podría cumplir techo 120.000 con sus 59 plazas: necesitaría 60. No se oculta esa tensión: aprobar redondeo supone aceptar desviación provincial aritmética expresa, sin trasladarla como licencia uniforme al mapa. La igualdad interna aún depende de población por sección, topología y disciplina municipal.

Son necesarias la representación mínima, separación provincial y cobertura de singularidades acreditadas. Son evitables la sobrerrepresentación artificial por dos mínimos legales, un K nacional fijo, aristas ficticias y desequilibrios internos cuando existen particiones más iguales. Se propone minimizar primero la máxima desviación relativa de población por distrito respecto a P_i/K_i, después la suma de desviaciones absolutas; identidad municipal/comarcal y continuidad histórica actúan entre soluciones de igual calidad poblacional y topológicamente válidas. No se promete optimalidad sin prueba de factibilidad y evidencia de búsqueda.

## Excepciones propuestas antes de generar mapas

**E1, circunscripción completa de población inferior a 100.000:** regla general declarativa de ámbito estrecho: si P_i<100000 y K_i=1, un único distrito cubre toda la circunscripción; se dispensa únicamente el suelo ordinario poblacional. No se permite dividirla para multiplicar representación, cruzar fronteras ni aplicar este suelo reducido a otros distritos. Si en otra edición la fórmula diera más de uno, E1 dejaría de aplicarse; cualquier cambio debe registrarse.

| Ámbito 2025 | Fundamento | Población | K | Desviación de 120.000 | % |
|---|---|---:|---:|---:|---:|
| Soria (42) | representación provincial propia | 90.183 | 1 | −29.817 | −24,8475 |
| Ceuta (51) | representación separada de la ciudad | 83.567 | 1 | −36.433 | −30,3608 |
| Melilla (52) | representación separada de la ciudad | 87.067 | 1 | −32.933 | −27,4442 |

Estas tres excepciones abarcan 260.817 habitantes, 0,5309% de población nacional y 3/407 plazas (0,7371%). No se fija suelo universal 96.000 ni se adoptan 0,80/1,75 autonómicos. En 2025 no hay otra provincia bajo 100.000; las demás pequeñas conservan la regla ordinaria con su residuo explícito, sin privilegio adicional.

**E2, archipiélagos y componentes físicos separados:** ámbitos provinciales Islas Baleares (07: P=1.249.844, K=10, media=124.984,40, +4,1537%), Las Palmas (35: P=1.171.547, K=10, media=117.154,70, −2,3711%) y Santa Cruz de Tenerife (38: P=1.087.319, K=9, media=120.813,22, +0,6777%). Los totales provinciales son conocidos; población, K por isla y desviación por componente **no acreditados todavía**. No se concede una excepción numérica por isla sin esos datos.

Política propuesta: inventariar componentes habitados sobre geometría acreditada de 2025 **antes** de cualquier generación; no crear adyacencia marítima. Evaluar primero distritos conectados dentro de cada componente con K provincial conservado, distribuyendo plazas enteras positivas entre componentes para minimizar máxima desviación respecto a 120.000, luego error absoluto total y desempate por vector de K en orden lexicográfico ascendente de identificadores estables. Formalmente, para componentes habitados j con población acreditada P_j, enumerar vectores enteros k_j≥1 con Σk_j=K_i y minimizar lexicográficamente `(max_j |P_j/k_j−120000|/120000, Σ_j k_j|P_j/k_j−120000|, (k_j)_orden_ID)`. Es una comparación aritmética previa, no generación ni prueba suficiente de partición interna. Un mínimo por componente se evalúa como condición de factibilidad, no como nueva plaza automática. Si los componentes superan K o la cobertura topológica no es posible, falla la puerta: no aumenta K ni se fusionan islas automáticamente.

**E3, discontinuidades administrativas acreditadas:** una unidad administrativa legalmente discontinua puede proponerse como unidad compuesta solo mediante registro previo que identifique sus polígonos, municipio, provincia, fundamento administrativo, población 2025 por parte, K, desviación y justificación de que no existe alternativa conectada compatible más igualitaria. La dispensa afecta contigüidad de esa unidad, nunca límites provinciales ni igualdad por defecto. El inventario no está acreditado: no se afirma un listado de enclaves ni poblaciones inexistentes en la evidencia.

Para E2/E3, si la solución conectada no existe, se podrá presentar a Work **una excepción nominal de distrito compuesto sin arista ficticia**, con sus datos y prueba de necesidad, para aprobación específica previa a generar. El registro obligatorio tiene campos `exception_id, ámbito, tipo, fundamento, geometría/hash, población_2025/hash, K, desviación_hab, desviación_relativa, alternativa_conectada, prueba_necesidad, aprobación`. Campos ausentes → BLOCKED. No hay excepción automática descubierta después de observar un mapa. La política se recomienda ahora; su registro territorial concreto pendiente no se inventa ni se considera aprobado por este expediente.

## Comparación reutilizada

Las 15 alternativas originales y sus fracciones permanecen en [resumen.csv](resultados/resumen.csv), [comparaciones.json](resultados/comparaciones.json) y [repartos_52.csv](resultados/repartos_52.csv). Sus columnas de límites 96.000/210.000 son hipótesis antiguas; no participan en la selección corregida.

| Regla ya calculada | K | Media nacional | MAE frente a 120.000 | Lectura institucional |
|---|---:|---:|---:|---|
| n05_floor_independiente | 383 | 128,272.32 | 7,591.33 | Excluye Soria y ciudades; incompatible |
| n05_nearest_half_up_independiente | 407 | 120,708.35 | 4,064.14 | Seleccionada con mínimo uno explícito; idéntico reparto 2025 |
| n05_ceil_independiente | 435 | 112,938.61 | 7,061.39 | Sesgo de redondeo superior |
| n05_hamilton_k_derivado | 409 | 120,118.09 | 4,061.62 | Comparable; redistribuye por total nacional |
| n05_minimos_referencia_k_derivado | 409 | 120,118.09 | 22,345.40 | Comparativo no seleccionado; no prevalece sobre mónada |
| k300_minimos | 300 | 163,760.99 | 57,163.29 | Comparativo no seleccionado; no prevalece sobre mónada |
| k350_minimos | 350 | 140,366.56 | 36,747.28 | No seleccionada; total legal prefijado |
| k383_minimos | 383 | 128,272.32 | 27,210.05 | Comparativo no seleccionado; no prevalece sobre mónada |
| k391_minimos | 391 | 125,647.82 | 25,030.15 | Comparativo no seleccionado; no prevalece sobre mónada |
| k392_minimos | 392 | 125,327.29 | 25,272.42 | Comparativo no seleccionado; no prevalece sobre mónada |
| k400_minimos | 400 | 122,820.74 | 22,791.56 | Comparativo no seleccionado; no prevalece sobre mónada |
| k350_hamilton_puro | 350 | 140,366.56 | 20,989.97 | Comparativo no seleccionado; no prevalece sobre mónada |
| k391_hamilton_puro | 391 | 125,647.82 | 7,364.94 | Comparativo no seleccionado; no prevalece sobre mónada |
| k400_hamilton_puro | 400 | 122,820.74 | 5,030.40 | Comparativo no seleccionado; no prevalece sobre mónada |
| antecedente_391_reponderado_2025 | 391 | 125,647.82 | 8,852.70 | Continuidad histórica no acreditada como mapa 2025 |

407 frente a Hamilton 409: Huelva: 4→5; Sevilla: 16→17. Hamilton reduce el MAE solo de 4.064,14 a 4.061,62 (2,52 habitantes por plaza) y aproxima la media nacional a 120.000. Esa mejora marginal no justifica sustituir la asignación independiente provincial por conservación de un total nacional. No se impone 409 para obtener una media cómoda.

## Matriz pendiente para habilitar N08

| Requisito | Estado | Evidencia / puerta |
|---|---|---|
| Principios de mónada, provincias, ciudades e igualdad | ESTABLECIDOS | mandato expreso del propietario |
| Fórmula half-up, mínimo uno, referencia 407 y E1 | WAIT_OWNER | aprobación operacional específica |
| Política E2/E3 | WAIT_OWNER | aprobación del procedimiento; registro nominal posterior previo a generación |
| Población provincial 2025 | VERIFICADA analíticamente | INE 65034 y hashes; no certificación por sección |
| Secciones 2025 y cobertura administrativa | VERIFICADA parcialmente | N07 36.554/52; falta overlay provincial independiente |
| Pareja población/geometría por unidad mínima | PENDIENTE | fuente, cobertura, hashes y alineación 2025 acreditados |
| Componentes/islas/discontinuidades | BLOCKED para generación | registro E2/E3 con población y K; prueba previa de factibilidad |
| Contigüidad y grafo | PENDIENTE | fronteras compartidas válidas; ninguna arista provincial ni marítima ficticia |
| Disciplina municipal/comarcal | PENDIENTE | aprobación de unidad mínima y cuándo subdividir municipios |
| Igualdad interna y límites nacionales | PENDIENTE | aprobar criterio minimax y umbral de aceptación operativo; ningún suelo/techo autonómico heredado |
| Continuidad histórica 2022 | CONDICIONADA | acreditar ediciones, corregir integridad por expediente separado y overlay 2025 |
| Contrato candidato y registro de decisión | PENDIENTE | Work registra aprobación expresa; total actual nulo |
| Autorización N08 / ejecución | NO AUTORIZADA | puerta separada; este expediente no habilita producción |

## Texto exacto preparado para aprobación

> Para N06 del Plan Maestro ddd-maestro-20261008, apruebo como regla operacional de planificación del Congreso DDD la asignación independiente por cada una de las 52 circunscripciones K_i=max(1,floor(P_i/120000+1/2)), con población entera de referencia 2025 y empate exacto hacia arriba. Apruebo la tabla reparto_ddd_52.csv identificada por el manifiesto corregido, cuya suma es 407: este total es consecuencia de la regla, no un K nacional prefijado. La referencia ordinaria de cálculo es 120.000 habitantes, dentro del orden institucional de 100.000–120.000; acepto las desviaciones provinciales de redondeo documentadas, sin convertirlas en tolerancia general por distrito. Retiro K=350 y el reparto legal vigente como recomendación institucional DDD.
>
> Apruebo E1: circunscripción completa con P_i<100000 y K_i=1 queda expresamente dispensada del suelo ordinario poblacional; en 2025 se aplica únicamente a Soria, Ceuta y Melilla, una plaza separada para cada una. Mantengo infranqueables las fronteras provinciales y la representación propia de las 52 circunscripciones.
>
> Apruebo la política previa E2/E3 del expediente: registro acreditado de componentes físicos y discontinuidades administrativas antes de generar, búsqueda prioritaria de soluciones conectadas y más iguales dentro del K provincial, sin aristas ficticias ni cambios automáticos de K. Cada excepción nominal de contigüidad requerirá población, K, desviación, fundamento territorial, prueba de necesidad y aprobación específica previa; esta aprobación del procedimiento no concede excepciones nominales aún no acreditadas.
>
> Esta decisión aprueba la regla de K, E1 y el procedimiento E2/E3 para planificación. No acredita factibilidad cartográfica ni aprueba límites operativos por distrito todavía pendientes, no promueve fuentes ni autoriza N08 productivo, M01–M08, 00, generación, integración, certificación o publicación. Work registrará mi identidad, fecha, texto y decision_id, y actualizará por separado las puertas que correspondan. Hasta ese registro N06 permanece WAIT_OWNER.

## Validación y conservación

Se reutilizan y ejecutan las 11 pruebas N06 y las 42 regresiones originales, sin modificarlas. Se añaden únicamente regresiones de fórmula provincial, mínimos, 52 identidades, empate, determinismo, K derivado y excepciones explícitas. [validacion_correccion.log](validacion_correccion.log) conserva comandos y salidas. Revisión en sesión separada con habilidad ddd-revisor sobre el incremento completo; su dictamen final se ancla al commit entregado en evidencia externa para evitar circularidad de SHA.

Política de versiones: copia literal previa de expediente y manifiesto en legacy; incremento compatible 1.1.0, metadatos y motivo explícitos. Nuevos scripts y artefactos analíticos con origen. No cambia motor, contrato, mapas ni fuentes; no procede run territorial. CI remota no ejecutada por límite expreso de no push/PR; las pruebas locales no se presentan como CI.

N06 **WAIT_OWNER**. No se ha registrado aprobación ni firma del propietario. Push / PR / merge / fuentes nuevas / promoción / 00 / M01–M08 / generación / publicación: **NO**.
