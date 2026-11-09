# Datos abiertos de Diputado de Distrito

Paquete por provincia (52 provincias nacionales completas) con:

- `<territorio>/distritos.geojson`: distritos del producto territorial M06 publicado (EPSG:4326 / CRS84), con la propiedad `distrito` (1..K) en lugar
  del `district_id` interno del motor; `INDEX.json` lleva su sha256 (`geojson.sha256`) y el del GeoJSON M06 de origen (`sha256_origen`).
- `<territorio>/resultados.csv`: ganador por distrito en las elecciones generales de 2023 (congreso) (columnas: distrito, poblacion,
  votos_totales, ganador, votos_ganador, porcentaje_ganador). Solo consta el ganador, no los votos de cada partido.
- `<territorio>/distrito-<n>.html`: ficha estática del distrito. Los distritos se numeran de 1 a K en cada provincia
  (no existe el distrito 0); hasta la versión 1.0 del paquete se numeraban desde 0 (`distrito-0.html` pasa a ser `distrito-1.html`, etc.).
- `INDEX.json`: por territorio, run de origen, `blob_sha` del producto en git, sha256 del ZIP de origen, del GeoJSON y del CSV.

## Licencia

**Creative Commons Atribución 4.0 Internacional (CC-BY-4.0)**, <https://creativecommons.org/licenses/by/4.0/deed.es>. Puede copiar, redistribuir, adaptar y usar los datos,
también con fines comerciales, citando la fuente: «Diputado de Distrito (https://github.com/jfmurciego/DiputadodeDistrito)», y el run de procedencia. Se propone CC BY 4.0 por ser
la licencia abierta más usada para datos públicos y exigir solo atribución. Las fuentes oficiales subyacentes (INE,
Ministerio del Interior, BOE) conservan sus propias condiciones de reutilización.

## Verificación

`sha256sum` de cada fichero debe coincidir con `INDEX.json`. El GeoJSON procede del blob `blob_sha` del repositorio
`jfmurciego/DiputadodeDistrito` (ZIP con huella `sha256_origen`).
