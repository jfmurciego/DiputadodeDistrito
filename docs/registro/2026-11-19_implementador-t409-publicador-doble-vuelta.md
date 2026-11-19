## 2026-11-19 — T-409 — Publicador de la doble vuelta de los 52 nac para la V4 (P40)

Causa: la V4 muestra la doble vuelta de los territorios del Congreso (D-172, D-178) y P75 ya la archivó en R2 (run 44556621000, 52/52 OK). Cambio:
`herramientas/publicar_doble_vuelta.py` (nuevo): lee `configuracion/doble_vuelta_publicada.json` (run de P75, clave y sha256 del INFORME.json FIJADOS en el repo; sin él no hace nada),
baja el INFORME de R2 y exige su sha256 y 52/52 OK, baja cada ZIP (`clave_r2`) y exige el `sha256_salida` del informe, exige distritos internos 0..K-1 sin huecos y los pasa a
públicos 1..K (`numeracion_publica`), añade el escenario `primero` (el de más votos en primera vuelta, derivado del detalle de dv_base, con empate alfabético marcado y comprobado
contra los votos de dv_base) y escribe `v4/mapa/datos/INDEX.json` (cabecera con run, sha256 del informe, bloques y alias; por territorio id, nombre en español, etiqueta, distritos y
sha256 de cada CSV) y `<nacNN>/resultados_doble_vuelta.csv` (14 columnas) y `detalle.csv` (7), las de `visor/v4/mapa/dv.js`. Todo se valida antes de escribir: o 52/52 o nada.
`p40-publicacion.yml` 1.2.0 (copia 1.1.0 en `legacy/`): paso «Doble vuelta de los territorios del Congreso para la V4 (D-172)» antes de validar el sitio, mismas credenciales R2 que el
resto, sin entradas nuevas, sin escribir en git; con fijado, un fallo detiene la publicación. Tests: `test_t419_publicar_doble_vuelta.py` (R2 simulado, valores a mano, controles
negativos: sha256 del informe o del ZIP distinto, clave ausente, id fuera de rango, informe incompleto, primero incoherente, escenario desconocido, zip-slip; paso de P40) y la
equivalencia de `test_t372_p40_equivalencia.py` (ignora el paso nuevo). Pendiente: el fichero fijado (`configuracion/doble_vuelta_publicada.json`: run_p75 `44556621000-1` y el
sha256 del INFORME.json, que desde la nube no se puede leer) y que `v4/mapa/dv.js` acepte `primero` (T-415/T-413). No publica ni lanza. `no-automerge`.

Geometría (decisión del Planificador, opción A): el publicador reutiliza el GeoJSON de distritos que el propio P40 ya materializa en `<sitio>/datos/<nacNN>/distritos.geojson` (derivado del M06 por
`generar_datos_abiertos.py`: EPSG:4326, propiedad `distrito` 1..K), comprueba su sha256 contra `<sitio>/datos/INDEX.json`, lo simplifica con Douglas-Peucker por anillo (tolerancia fija
0,0005° ≈ 55 m, coordenadas a 5 decimales, sin topología compartida: puede quedar un hueco o solape de hasta la tolerancia entre vecinos) y escribe `v4/mapa/datos/<nacNN>/distritos.geojson`
con solo `district_id` (entero público 1..K) y `geometria {ruta, sha256, sha256_origen}` en INDEX.json (más `simplificacion` en la cabecera). Falla (y no escribe nada) si algún distrito de los
52 queda sin geometría (`DATO_SIN_GEOMETRIA`) o con geometría y sin dato (`GEOMETRIA_SIN_DATO`), o la geometría falta o su sha256 no casa (tests con control negativo; un anillo de 200.000 puntos
baja a 65 en 0,6 s). Límite: sin datos reales en git no hay prueba con los M06 de verdad (se comprobará en la primera publicación en simulación).
