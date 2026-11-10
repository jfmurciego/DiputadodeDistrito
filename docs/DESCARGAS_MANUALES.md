# Descargas manuales (T-177)

Desde la nube solo responden `boe.es` e `ine.es`. Bájalo en un ordenador con acceso normal. Tras cada descarga:
`shasum -a 256 <fichero>` y anota nombre, tamaño y sha256 en `huellas.json` (se sube con los ficheros).
**Destino común:** un release de GitHub por grupo (como `fuente-infoelectoral-02202307`); la nube lo baja con
`gh api repos/<r>/releases/assets/<id> -H "Accept: application/octet-stream"`. Ninguna URL se ha comprobado: las notas
(T173, T158) son de búsqueda web, sin ficheros. Guarda también la ficha de licencia de cada fuente.

## Prioridad 1 · Naturalidad (release `fuente-naturalidad`)
| Fichero | URL | Tamaño | Formato | Licencia |
|---|---|---|---|---|
| Comarcas agrarias (MAPA) | https://www.mapa.gob.es/es/cartografia-y-sig/ide/descargas/agricultura/comarcas_agrarias | MB | a comprobar (SHP/GPKG/tabla) | a comprobar (INSPIRE) |
| BTN100/BCN200: hidrografía y carreteras, por provincia del piloto | https://centrodedescargas.cnig.es/CentroDescargas/ | cientos de MB en total (a comprobar) | SHP/GPKG (a comprobar) | CC BY 4.0 ign.es (a comprobar) |
| MDT de malla gruesa (25 m o 200 m) del piloto; MDT05 solo si hace falta | mismo Centro de Descargas (ficha MDT05: https://datos.gob.es/es/catalogo/e0dat0002-wmts-del-modelo-digital-de-terreno-de-espana1) | MDT05 nacional: decenas de GB | ráster por hoja MTN50 | CC BY 4.0 |
| `spain-latest.osm.pbf` (opcional, tiempos de viaje) | https://download.geofabrik.de/europe/spain.html | ~1 GB (a comprobar) | PBF | ODbL 1.0 (atribución y compartir igual) |

## Prioridad 2 · Otros ámbitos
Municipales 2023-05 y europeas 2024-06 comparten seccionado con el Congreso (ya en el repositorio).
| Fichero | URL | Tamaño | Formato | Licencia | Destino |
|---|---|---|---|---|---|
| Municipales 2023-05, resultados por mesa (nacional) | URL a confirmar: Infoelectoral, Ministerio del Interior (descarga de ficheros por mesa) | no consta | ZIP | no verificada (cita obligada) | release `fuente-infoelectoral-02202305` |
| Europeas 2024-06, resultados por mesa (nacional) | URL a confirmar: Infoelectoral, Ministerio del Interior | no consta | ZIP | no verificada | release `fuente-infoelectoral-02202406` |
| Cartografía municipal más fina que la sección (manzana/portal) | URL a confirmar: CNIG, Catastro | no consta | no consta | no verificada (CNIG suele ser CC BY 4.0) | release `fuente-municipales-cartografia` |
| Ecuador: resultados por junta receptora/recinto (CNE; 2021 y 2023) | URL a confirmar: portal de datos abiertos del CNE | no consta | no consta | no consta | release `fuente-ecuador` |
| Ecuador: límites político-administrativos y sectores/zonas censales, Censo 2022 (INEC) | URL a confirmar: INEC | no consta | no consta | no consta | `fuente-ecuador` |
| Ecuador: cartografía base (IGM) | URL a confirmar: Instituto Geográfico Militar | no consta | no consta | no consta | `fuente-ecuador` |
| Ecuador: población (Censo 2022, proyecciones) y normativa vigente (Código de la Democracia; Asamblea Nacional) | URL a confirmar: INEC; Registro Oficial/CNE; sitio de la Asamblea | no consta | no consta | no consta | `fuente-ecuador` |

Europeas: los agregados de results.elections.europa.eu no traen sección; no hace falta bajarlos.

## Alternativa
Si el administrador del entorno permite los hosts `centrodedescargas.cnig.es` y `www.mapa.gob.es`, la prioridad 1
(salvo OSM) se descarga desde la nube sin pasos manuales.
