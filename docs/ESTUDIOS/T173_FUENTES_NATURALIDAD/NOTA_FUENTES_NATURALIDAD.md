# T-173 · Fuentes para la naturalidad de distritos (nota documental)

Fecha de consulta: 2026-11-10. Sin código, sin lanzamientos, sin tocar el motor.

## Estado de la verificación (léase primero)
- Desde la nube solo responden `boe.es` e `ine.es` (HTTP 200). El resto da `403` en el túnel del proxy
  (`CONNECT` denegado): `centrodedescargas.cnig.es`, `www.ign.es`, `www.mapa.gob.es`, `download.geofabrik.de`,
  `overpass-api.de`, `www.icgc.cat`, `opendata.aragon.es`, `datos.gob.es`, `www.idee.es`, `www.openstreetmap.org`.
- Por tanto **no hay muestra descargada ni sha256** de ninguna fuente de (a)–(c). Lo que sigue sale de resultados
  de búsqueda web (títulos y extractos), no de los ficheros. Todo está marcado «a comprobar» hasta que el
  propietario baje la muestra y se anote su sha256. No se ha usado la memoria para ningún dato oficial.
- Sugerencia técnica: pedir al administrador del entorno que permita (solo esos hosts) `centrodedescargas.cnig.es`
  y `www.mapa.gob.es` evitaría la descarga manual; si no, plan manual en la sección (d).

## (a) Comarcas con cobertura nacional
| Opción | Fuente (consultada 2026-11-10) | Estado |
|---|---|---|
| Comarcas agrarias, MAPA | Página de descarga <https://www.mapa.gob.es/es/cartografia-y-sig/ide/descargas/agricultura/comarcas_agrarias> y servicio WFS en <https://www.mapa.gob.es/ca/cartografia-y-sig/ide/directorio_datos_servicios/servicio_wfs> | La página existe (la devolvió la búsqueda); formato, nº de comarcas y licencia **a comprobar** en la ficha. El MAPA publica licencias de reutilización de geodatos que remiten a INSPIRE (Directiva 2007/2/CE); no se ha podido confirmar que cubra esta capa. |
| Comarcas oficiales por comunidad | Cada comunidad tiene la suya (algunas no existen como división oficial: p. ej. no hay comarcas oficiales homogéneas en todas). Hoy el repositorio solo tiene Aragón, Castilla y León y Galicia. | Sin cobertura nacional homogénea; **a comprobar** comunidad por comunidad. |

Recomendación: usar las **comarcas agrarias del MAPA** como capa nacional homogénea (una sola fuente, un solo
criterio) y las oficiales autonómicas solo donde el propietario prefiera el criterio administrativo.
Limitación esperable (a comprobar): las comarcas agrarias son agrícolas, no siempre coinciden con las
administrativas; las provincias insulares y Ceuta/Melilla pueden tener un tratamiento propio.

Cruce con municipios INE: el código `ddd_core/comarcas.py` ya espera un CSV con columnas
`Municipio código` (5 dígitos, se normaliza a `[:5].zfill(5)`), `Comarca código` y `Comarca nombre`, exige que
cada municipio tenga una sola comarca y, con `require_full_coverage`, cobertura total. Si la fuente MAPA viene
como polígonos (no como tabla municipio→comarca), hay que generar esa tabla con un cruce espacial de los
polígonos con el límite municipal oficial (centroide en polígono o mayor solape; registrar los municipios
partidos entre comarcas y decidir una regla fija). Si viene como tabla con códigos INE, el cruce es directo
(vigilar códigos obsoletos tras fusiones municipales: validar contra el nomenclátor INE vigente, que sí es
alcanzable en `ine.es`).

## (b) Hidrografía y relieve (IGN/CNIG)
| Capa | Fuente | Estado |
|---|---|---|
| Ríos y masas de agua | BTN100 (Base Topográfica Nacional 1:100.000, la base de la BCN200) y BCN200, en el Centro de Descargas del CNIG: <https://centrodedescargas.cnig.es/CentroDescargas/> | Existencia confirmada por documentación IGN (<https://www.ign.es/web/ign/portal/cbg-bd>, <https://idee.es/resources/presentaciones/JIIDE13/jueves/47_BTN_100.pdf>). Formato (SHP/GPKG), tamaño y troceado por hoja o por provincia: **a comprobar** en la ficha. |
| Relieve (divisorias) | MDT05 (malla de 5 m) y MDT25/MDT200 si basta menor resolución | MDT05 figura en datos.gob.es con licencia Creative Commons Atribución 4.0 (<https://datos.gob.es/es/catalogo/e0dat0002-wmts-del-modelo-digital-de-terreno-de-espana1>, ficha del WMTS). Se distribuye por hojas MTN50; el tamaño nacional a 5 m es de decenas de GB (**a comprobar**). Para divisorias a escala de distrito basta una malla gruesa (25 m o 200 m). |

Licencia general IGN/CNIG: productos de la Orden FOM/2807/2015 bajo CC BY 4.0 con atribución visible
(«CC-BY 4.0 ign.es» + año; obra derivada: «Obra derivada de …»); condiciones en
<https://www.ign.es/resources/licencia/Condiciones_licenciaUso_IGN.pdf> (**a comprobar** la versión vigente y que
la capa de hidrografía no tenga condiciones propias; la búsqueda no lo aclaró).
Por provincia: el Centro de Descargas suele ofrecer selección por hoja, provincia o comunidad (**a comprobar**);
si no, se recorta nacional con el límite provincial.

## (c) Red de carreteras para tiempos de viaje
- IGN/CNIG: red de transporte de la BTN100 / BCN200 (carreteras con jerarquía), misma licencia CC BY 4.0 y mismo
  Centro de Descargas. Sin velocidades; habría que asignarlas por categoría.
- OpenStreetMap: extractos de Geofabrik (<https://download.geofabrik.de/europe/spain.html>) u Overpass; licencia
  ODbL 1.0 (atribución «© OpenStreetMap contributors» y compartir igual de la base derivada). Tamaño del PBF
  de España: del orden de 1 GB (**a comprobar**). Trae categoría, velocidad máxima y sentidos: más adecuado
  para tiempos de viaje.
- Ambas **no alcanzables** desde la nube; verificación pendiente de la descarga manual.
- Aviso de licencia: ODbL exige compartir igual la base derivada que se publique; CC BY 4.0 solo atribución.
  Decisión del propietario si el producto se publica.

## (d) Accesibilidad y plan de descarga manual
Alcanzable: `boe.es`, `ine.es`, el repositorio de GitHub. No alcanzable: todo lo demás (lista arriba).
Plan para el propietario, en un ordenador con acceso normal, por este orden y cada fichero con
`shasum -a 256 <fichero>` anotado:
1. MAPA: comarcas agrarias (SHP/GPKG o tabla) + capturar la ficha de licencia. Pequeño (MB).
2. CNIG: BTN100/BCN200 hidrografía y carreteras, por provincia del piloto; guardar la ficha de licencia. Cientos de MB como mucho en total (a comprobar).
3. CNIG: MDT de malla gruesa (25 m o 200 m) del piloto; MDT05 solo si hace falta más detalle.
4. Geofabrik: `spain-latest.osm.pbf` (~1 GB) si se opta por OSM para tiempos de viaje.
5. Dejar los ficheros en un release del repositorio (como el espejo de Infoelectoral) con su sha256 en un JSON; la
   nube los baja con `gh api .../releases/assets/<id> -H "Accept: application/octet-stream"`.

## (e) Cómo ligar cada fuente a las unidades de distrito
Unidad base: municipio (5 dígitos INE) y sección censal (`CUSEC`, 10 dígitos; el municipio son los 5 primeros,
como ya hace `attach_comarcas`).
- Comarca: por tabla municipio→comarca (ambigüedad nula si la tabla es oficial). Con polígonos, regla fija
  documentada para municipios partidos. Las secciones heredan la comarca de su municipio.
- Ríos: capa lineal. Se liga a la **arista** entre secciones/municipios contiguos: una arista «cruza un río
  principal» si la línea compartida intersecta un río de orden alto. Ambigüedad principal: ríos que hacen de
  límite municipal (usar solo el criterio de intersección con la frontera compartida, con tolerancia fija en
  metros y CRS 25830, ya usado en el repositorio).
- Divisorias: del MDT se obtiene cota media/máxima por sección (estadística zonal); la naturalidad se mide como
  diferencia de cota o cresta entre secciones vecinas. Ambigüedad baja si se fija estadística y malla.
- Carreteras: grafo viario; el tiempo entre secciones se calcula entre centroides ponderados por población
  (o punto más cercano a la red). Ambigüedad: islas (Baleares, Canarias) sin conexión por carretera: tratarlas
  aparte o con un tiempo fijo.
- Todo cruce deja su informe de cobertura (como `coverage_ratio` en comarcas) y falla si queda un municipio sin asignar.
