# Cartografía histórica y consecuencias de las cinco alternativas nacionales

**Versión:** 1.0.0
**Nombre:** Incorporación histórica, comparación acreditada y evaluación provincial
**Fecha:** 2026-10-08
**Alcance:** incremento analítico local del frente Distritos nacionales
**Estado:** candidato para conservación local; CI_PENDIENTE; sin alternativa institucional aprobada
**Cambios:** inventario físico, bytes históricos conservados, instrumento cartográfico, métricas y sensibilidad
**Motivo:** concretar la decisión del Director sin atribuir ediciones ni causas por inferencia
**Origen:** incremento nuevo sobre `effa34f80d9c5c8cb7ac5c39216524aa95eba66d`; complementa el expediente previo, no sustituye el modelo

## Base y versiones conservadas

Se han comprobado esquema y versión 1.0.0 del modelo y los hashes de sus archivos contra su manifiesto y cierre. La fuente INE 2025, la tabla provincial y las cinco asignaciones originales permanecen intactas. Este incremento lee sus resultados; únicamente recalcula cuotas para **escenarios de sensibilidad nuevos**, necesarios para evaluar estabilidad. No vuelve a adquirir población ni a generar cartografía.

Las métricas siguientes proceden de [evaluación exacta](cartografia_nacional_20261008/evaluacion_alternativas.json), su [tabla resumida](cartografia_nacional_20261008/evaluacion_alternativas.csv) y los hashes del manifiesto de este incremento. Ninguna alternativa de K está aprobada. La conservación local con CI aplazada está autorizada por el Director; integración y producción continúan bloqueadas.

## Inventario físico y acreditación

La búsqueda exacta y de otros nombres cartográficos que incluyeran 2022 recorrió la raíz de usuario del equipo de búsqueda original, excluyendo directorios técnicos, credenciales, papelera y `Library`; no produjo errores de acceso en ese recorrido. Spotlight no devolvió resultados. No se afirma una búsqueda exhaustiva de volúmenes externos o de los directorios excluidos. [Inventario](cartografia_nacional_20261008/inventario.json) registra alcance, IDs relativos, tamaños, hashes e inspecciones. No se encontraron otros mapas 2022 acreditados en ese alcance.

| Material físicamente inspeccionado | Identidad y contenido | Edición y compatibilidad |
| --- | --- | --- |
| `Documents/Politics/Demos/Estudio del Diputado de Distrito/Final/spain-districts-selected.json` | GeoJSON, SHA `2a0a4cf5…`; 391 IDs de distrito únicos, códigos provinciales 01–52, población `pob_t_total`, objetivo 120000, `map_iteration`. CRS84 declarado. | Ediciones cartográfica y demográfica desconocidas; origen local del proyecto, fuente primaria y método no acreditados. Una geometría inválida. |
| `Final/map.geojson`, en el mismo directorio | SHA `a2c8f630…`; mismos 391 IDs, geometrías y atributos normalizados. Sin miembro CRS: el instrumento aplica la convención GeoJSON RFC 7946 de longitud/latitud CRS84 y la deja registrada. | No es un mapa 2025 acreditado. La equivalencia con el JSON demuestra una variante del mismo material histórico. |
| `Final/assembled_districts_spain.xlsm` | SHA `aeae36e7…`; 391 filas de distrito, sin geometrías ni CRS; tabla de población/provincia/iteración. XML interno creado/modificado 2021-05-04; sin miembros VBA. | Fecha de creación del contenedor, no edición del mapa o población. No se ejecutó Excel ni macros. |
| `Downloads/My Drive/assembled_districts_spain.xlsm` | SHA `125112c4…`; mismos miembros ZIP y tabla XML. Sólo difiere `docProps/core.xml`, con fecha 2022-01-27. | No acredita un mapa distinto de 2022 ni cambios distritales. |
| `Downloads/Estudio DDD Aragon 2026/spain-districts-selected.json` | SHA idéntico al JSON de `Final`. | Copia binaria, no otra edición. |

Se conservaron **cuatro inputs únicos**, comprimidos sin modificar sus bytes, bajo `cartografia_nacional_20261008/inputs/`. El inventario relaciona cada una de las cinco ubicaciones con su archivo conservado y el SHA del contenido original. Los nuevos inputs son materiales históricos no acreditados, no fuentes productivas. La unidad geográfica representada es el distrito agregado; su unidad mínima de construcción y correspondencia con municipios/secciones no quedan acreditadas por estos archivos. La presencia de los 52 códigos provinciales prueba cobertura de etiquetas, no integridad geográfica nacional.

El seccionado local de 2025 tiene SHA `55c9da7e…`, idéntico al baseline INE protegido por `inputs/MANIFEST.sha256`. La [inspección de atributos y CRS](cartografia_nacional_20261008/referencia_seccionado_2025.json) acredita 36.554 registros, 36.554 claves CUSEC únicas, 52 códigos provinciales y CRS ETRS89/UTM 30N (`EPSG:25830`). Se han leído DBF y PRJ, **no** validado sus geometrías ni ejecutado un overlay nacional. Es seccionado censal, no un mapa nacional de distritos de 2025; su edición se vincula al baseline conservado, no únicamente al nombre del fichero.

## Resultado real y límites de comparación

[Equivalencia de archivos](cartografia_nacional_20261008/equivalencia_archivos.json): **391 pares de IDs con coordenadas exactamente idénticas y 391 pares con atributos normalizados idénticos**. Se normalizan únicamente tipos de los códigos e iteración; no se modifican límites. No hay evidencia de dos mapas temporales distintos.

En ambos GeoJSON, el distrito **44**, provincia **07 — Islas Baleares**, falla validez: `Hole lies outside shell[3.23111263179678 39.7349979107275]`. Hay 313 Polygon y 78 MultiPolygon. Las multipartes quedan diagnosticadas como componentes separados; no se declaran automáticamente excepciones ni se exige una contigüidad nacional aún no aprobada. No se reparó, simplificó ni descartó el distrito inválido para conseguir PASS.

La [puerta de comparabilidad](cartografia_nacional_20261008/comparabilidad_temporal.json) devuelve **NOT_COMPARABLE**: ediciones 2022/2025 y procedencia primaria no acreditadas, geometría inválida, y ausencia de mapa distrital nacional 2025. Las métricas temporales de solapamiento, cobertura, correspondencia y diferencias poblacionales por distrito permanecen `null`. Las 390 geometrías válidas no se presentan como comparación nacional completa.

Los atributos históricos suman aproximadamente **46.883.062** habitantes; sus residuos decimales de serialización se conservan. La [diferencia numérica provincial frente a INE 2025](cartografia_nacional_20261008/diferencias_poblacion.json) es aproximadamente **2.245.235**, con 52 filas comparables por etiqueta provincial. **No se interpreta como crecimiento 2022–2025**, pues falta acreditar el año, universo y fuente de la cifra histórica. Tampoco se distribuye población de 2025 entre distritos históricos por proporción de área.

## Instrumento de comparación y fórmulas

`herramientas/comparar_cartografia_nacional.py` acepta dos GeoJSON (también comprimidos) y sus descriptores. Exige hashes del contenido, ediciones cartográfica y demográfica 2022/2025, procedencia explícitamente acreditada con evidencia, ámbito y tipo de unidad compatibles, identidades no vacías/duplicadas y geometrías poligonales válidas. La conectividad puede exigirse expresamente; en su ausencia sólo se diagnostica y no se concede una excepción productiva. No modifica geometrías inválidas.

Para entradas admitidas, reproyecta a `EPSG:3035`, con orden x/y y sin transformación ballpark, comprueba geometrías proyectadas y ausencia de solapamientos interiores superiores a epsilon. El epsilon analítico es **0,01 m²**, explícito en el resultado; no es una tolerancia nacional aprobada. [Shapely](https://shapely.readthedocs.io/en/2.1.1/reference/shapely.is_valid.html) valida geometrías; [pyproj](https://pyproj4.github.io/pyproj/stable/api/transformer.html) realiza las transformaciones.

- Para cada pareja con intersección positiva: `I = área(A ∩ B)`, `Jaccard = I / (área(A)+área(B)-I)`, cobertura de A por B `I/área(A)` y de B por A `I/área(B)`.
- Cambio de geometría: área de diferencia simétrica `A △ B`; equivalencia dentro del epsilon declarado. Contactos puntuales o de frontera sin área no constituyen correspondencia positiva.
- La matriz incluye divisiones/fusiones; no fuerza parejas uno a uno. La intersección de identificadores no se llama identidad conservada sin namespace común y acreditación explícita de estabilidad.
- Cobertura: unión de cada mapa e intersección/diferencia simétrica entre esas uniones. No se afirma completitud territorial nacional sin una referencia territorial externa acreditada.
- Población: totales declarados y diferencias por identidad estable cuando se acredita. Si cambiaron sus límites, la diferencia mezcla universos; no se atribuye automáticamente a evolución demográfica.

| Clase de cambio | Evidencia necesaria | Estado de este incremento |
| --- | --- | --- |
| Administrativo real | Acto o fuente oficial y correspondencia de unidades/fechas que sustente el cambio. | No acreditado; ninguna atribución automática. |
| Cartográfico | Misma unidad y edición/procedencia conocidas; geometrías comparables y cambio medido. | Dos representaciones históricas con coordenadas idénticas; hay diferencias de formato y metadatos, no límites distintos entre ellas. |
| Derivado del algoritmo | Mismo universo/base y parámetros/versiones o recibos de ejecuciones que expliquen la diferencia. | Los cambios de K y cuotas de los escenarios son resultados del modelado. El método histórico no se reconstruye desde K=391 o `map_iteration=7`. |

## Comparativa cuantitativa común

Para cada provincia: media `m_i=P_i/K_i`, desvío `d_i=m_i−120000`, desvío relativo `d_i/120000`. Para K_i=0, media y desvío son `null` y la población se registra aparte como no representada. MAE ponderado por plazas: `Σ K_i·|d_i| / Σ K_i`; también se conserva `Σ K_i·d_i² / Σ K_i`. El MAE excluye K_i=0 y **no compensa** su falta de representación; ambas métricas deben leerse juntas.

Los mínimos/máximos siguientes son **medias provinciales**, no poblaciones observadas de distritos generados ni garantías de equilibrio dentro de una provincia. Los extremos reales de los nuevos distritos permanecen pendientes.

| Alternativa | K | MAE provincial ponderado (hab.) | Media provincial mínima–máxima (hab.) | Población con K_i=0 | Distancia L1 de cuotas al material histórico de 391 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Inferior independiente | 383 | 7.591,33 | 120.173,74 (Valencia)–230.087 (Huesca) | 260.817 | 30 |
| Más próximo independiente | 407 | 4.064,14 | 83.567 (Ceuta)–165.564 (Zamora) | 0 | 20 |
| Superior independiente | 435 | 7.061,39 | 68.045,50 (Teruel)–119.621,53 (Alicante) | 0 | 44 |
| Hamilton con K derivado | 409 | 4.061,62 | 83.567 (Ceuta)–165.564 (Zamora) | 0 | 22 |
| Mínimos de referencia con K derivado | 409 | 22.345,40 | 30.061 (Soria)–152.819 (Barcelona) | 0 | 66 |

La distancia L1 es `Σ |K_i−K_histórico_i|`; el delta total frente a 391 es −8/+16/+44/+18/+18. Mide diferencia de **cuotas**, no distritos conservados, cambios administrativos o proximidad geométrica. Las barreras provinciales quedan respetadas únicamente en la definición de la tabla de cuotas: sin mapas nuevos no se verifica que distritos geométricos las cumplan.

Entre 407 independiente y Hamilton 409 sólo cambian Huelva **4→5** y Sevilla **16→17**. Su MAE difiere unos **2,53 habitantes**; eso no convierte 409 en una decisión institucional. Los mínimos contrafactuales garantizan dos iniciales por provincia y uno por ciudad, pero redistribuyen el residual y perjudican las medias de provincias pequeñas. Las restricciones normativas y del perfil común se contrastan en el expediente anterior; no se reinterpretan como autorización nacional.

### Sensibilidad explícita, no evolución real

Se ejecutaron **1.060 escenarios**: shocks uniformes −5%, −1%, +1%, +5%; y esos cuatro shocks sobre una provincia cada vez, para las cinco reglas. La población perturbada se redondea al entero más próximo con empate hacia arriba. Se informa K, delta total, vector de provincias cambiadas y distancia L1 frente a la asignación conservada. No se sustituye la población oficial ni se infiere una trayectoria demográfica.

| Alternativa | K con shocks uniformes −5/−1/+1/+5% | Casos locales ±1% sin cambio de cuotas (de 104) | L1 máximo local ±1% / ±5% |
| --- | --- | ---: | ---: |
| Inferior | 362 / 379 / 386 / 402 | 97 | 1 / 3 |
| Más próximo | 391 / 404 / 414 / 429 | 94 | 1 / 3 |
| Superior | 414 / 431 / 438 / 454 | 97 | 1 / 3 |
| Hamilton | 389 / 405 / 413 / 430 | 86 | 2 / 4 |
| Mínimos de referencia | 389 / 405 / 413 / 430 | 90 | 3 / 3 |

El redondeo independiente localiza sus cambios en la provincia perturbada; Hamilton y el reparto residual pueden cambiar otras provincias por K total o ranking de restos. Coincidir con K histórico en algún shock no acredita el algoritmo ni la fecha histórica.

## Opciones y consecuencias para decisión institucional

| Opción todavía no aprobada | Ventaja del modelo | Coste o incompatibilidad que exige decisión explícita |
| --- | --- | --- |
| Inferior provincial, 383 | Recuento menor y dentro del intervalo constitucional de referencia 300–400. | Deja sin plazas a Soria, Ceuta y Melilla; Huesca supera el techo hipotético. No reproduce los 350 escaños legales. |
| Más próximo provincial, 407 | Independencia provincial; baja desviación y sensibilidad local acotada. | Excede 400 y no preserva todos los mínimos provinciales de referencia. |
| Hamilton global derivado, 409 | Conserva el entero derivado de la cuota nacional y el reparto por restos; MAE similar a 407. | Excede 400 y puede redistribuir cuotas entre provincias ante un shock local. No preserva todos los mínimos de referencia. |
| Superior provincial, 435 | Evita K_i=0; medias provinciales inferiores al objetivo. | Mayor número total, fuera del intervalo constitucional; más provincias bajo el suelo hipotético. |
| Mínimos de referencia con 409 | Mantiene dos iniciales por provincia y ciudades fijas, como contrafactual. | Excede 400; mayor desigualdad provincial; Soria recibe tres plazas con media 30.061. No reproduce el reparto legal con K=350. |

Consecuencias aritméticas que Work debe resolver si decide convertir el perfil en contrato: para un total máximo de 400, la media nacional sería al menos **122.820,7425**; con 350, sería **140.366,562857…**. Mantener la hipótesis de 120.000 no autoriza aumentar el tamaño legal. Mantener barreras provinciales y el suelo hipotético de 96.000 es incompatible con al menos un distrito en Soria, Ceuta y Melilla con estas poblaciones; exigir dos iniciales en Soria aumenta la incompatibilidad. No se propone ni se concede una excepción para resolverla.

Pendientes concretos: acreditar la edición y fuente de las 391 geometrías y sus atributos, y aportar/identificar un mapa nacional 2025 o el universo de unidades/crosswalk común; resolver la geometría inválida mediante fuente o transformación acreditada conservando el original; elegir qué referencia institucional y restricciones prevalecen entre las opciones anteriores. Ninguna de esas decisiones se deduce de estas métricas.

## Reproducción, pruebas y gobierno

Dependencias analíticas fijadas en `requirements-cartografia-nacional.lock`, en entorno temporal aislado. No se cambiaron requisitos del motor autonómico. La instalación fue autorizada mediante la aprobación de acceso fuera del sandbox; no se descargó cartografía. Los inputs históricos originales se recuperan descomprimiendo los archivos del inventario y comprobando sus SHA.

```sh
python3 -m venv .venv-cierre
.venv-cierre/bin/python -m pip install -r requirements-cartografia-nacional.lock
.venv-cierre/bin/python receta_cierre.py ../reproduccion-nueva
```

Corrección C3 (versión 1.0.1, 2026-10-09; revisión pendiente): receta_cierre.py reconstruye busqueda.json desde inventario.json y los inputs comprimidos verificados. La búsqueda original se conserva en el expediente como busqueda-original.json; sus rutas personales son evidencia histórica. Se reconstruye el seccionado desde inputs/partes y se exige su hash protegido. Predecesor: legacy/docs/ESTUDIOS/CARTOGRAFIA_Y_ALTERNATIVAS_NACIONALES_2026-10-08.md.

Los destinos deben ser nuevos. Si las rutas originales no existen en otra máquina, el inventario y las cuatro copias comprimidas permiten recuperar los mismos bytes; la referencia 2025 también puede reconstruirse desde las partes protegidas de `inputs/`, sin nueva descarga. La diferencia poblacional se reproduce con `population_diagnostic` sobre `atributos_historicos.json` y la fuente poblacional conservada. Para un futuro par 2022/2025 acreditado, el comparador se invoca con `--old`, `--new`, `--old-descriptor`, `--new-descriptor`, `--output`; los descriptores históricos actuales mantienen los años desconocidos y deben fallar la puerta temporal.

Las pruebas dirigidas cubren identidad ausente/duplicada, edición incompatible/desconocida, procedencia no acreditada, hash contradictorio, CRS contradictorio y reproyección, discontinuidad, geometría inválida, cobertura, contactos sin área, solapamiento interno, división/renumeración, determinismo, métricas exactas, ceros, conservación y sensibilidad. Se verifica además el corpus real archivado y sus límites de acreditación. Comandos, resultados y dictamen se conservan con este incremento.

Política de versiones: componentes nuevos versión 1.0.0, metadatos y origen explícitos; ningún fichero funcional previo se sustituye, por lo que no hay predecesor que mover a `legacy/`. Los inputs históricos preservan bytes y formato; su trazabilidad está en inventario/manifiesto. Este expediente registra el incremento. CI_PENDIENTE se conserva por autorización expresa del Director para cierre local; bloquea integración, no este commit. No cambia comportamiento territorial ni se ejecuta un run territorial. Dependencias: sólo lectura del modelo y fuente oficial ya conservados, más materiales locales no acreditados del proyecto. No se incorporan cambios de otros frentes, fuentes productivas o catálogos.
