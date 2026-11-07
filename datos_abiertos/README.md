# Datos abiertos de Diputado de Distrito

Paquete por provincia (49 provincias nacionales completas) con:

- `<territorio>/distritos.geojson`: distritos del producto territorial M06 publicado (EPSG:4326 / CRS84).
- `<territorio>/resultados.csv`: ganador por distrito en las elecciones generales de 2023 (congreso) (columnas: distrito, poblacion,
  votos_totales, ganador, votos_ganador, porcentaje_ganador). Solo consta el ganador, no los votos de cada partido.
- `<territorio>/distrito-<n>.html`: ficha estática del distrito.
- `INDEX.json`: por territorio, run de origen, `blob_sha` del producto en git, sha256 del ZIP de origen, del GeoJSON y del CSV.

## Licencia

**Creative Commons Atribución 4.0 Internacional (CC-BY-4.0)**, <https://creativecommons.org/licenses/by/4.0/deed.es>. Puede copiar, redistribuir, adaptar y usar los datos,
también con fines comerciales, citando la fuente: «Diputado de Distrito (https://github.com/jfmurciego/DiputadodeDistrito)», y el run de procedencia. Se propone CC BY 4.0 por ser
la licencia abierta más usada para datos públicos y exigir solo atribución. Las fuentes oficiales subyacentes (INE,
Ministerio del Interior, BOE) conservan sus propias condiciones de reutilización.

## Verificación

`sha256sum` de cada fichero debe coincidir con `INDEX.json`. El GeoJSON procede del blob `blob_sha` del repositorio
`jfmurciego/DiputadodeDistrito` (ZIP con huella `sha256_origen`).
