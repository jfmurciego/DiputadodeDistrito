# Datos abiertos y licencia

Los datos publicados viven en [`../datos/`](../datos/INDEX.json) (paquete por provincia):

- `distritos.geojson`: distritos del producto territorial M06 (CRS84).
- `resultados.csv`: ganador por distrito en las generales de 2023. Solo consta el ganador, no los votos de cada partido.
- `distrito-<n>.html`: ficha estática del distrito.
- `INDEX.json`: run de origen, `blob_sha` y sha256 de cada fichero.

## Licencia

Creative Commons Atribución 4.0 Internacional ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es)): se puede copiar, redistribuir y adaptar, también con fines comerciales, citando «Diputado de Distrito» y el run de procedencia. Las fuentes oficiales subyacentes (INE, Ministerio del Interior, BOE) conservan sus condiciones de reutilización.

## Verificación

El `sha256sum` de cada fichero debe coincidir con `INDEX.json`.
