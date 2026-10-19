# CNIG histórico — recepción segura de un paquete independiente

**Ámbito:** `NAT-C-056` de la campaña nacional de Congreso. La solicitud oficial al CNIG se envió y confirmó el 18-10-2026; todavía no es un recibo de geometría. Este procedimiento es independiente de la revisión de PR #268 y no desbloquea ninguna generación.

## Cuando el organismo facilite una URL o un paquete

1. Comprobar que procede del CNIG/IGN y no es una exportación del mismo seccionado INE. Conservar la comunicación oficial, URL, licencias, fecha efectiva y detalles del Registro Central de Cartografía.
2. Descargar el fichero original a una ubicación **local fuera del repositorio** y conservar sus bytes. No admitir compromisos de pago sin autorización.
3. Preparar un JSON separado, por ejemplo:

```json
{
  "authority": "CNIG/IGN",
  "product": "LILIM",
  "source_url": "https://centrodedescargas.cnig.es/CentroDescargas/limites-municipales-provinciales-autonomicos",
  "edition_issued_on": "2025-01-20",
  "intended_valid_at": "2025-01-01",
  "license": "compatible con CC BY 4.0, con atribución",
  "acquired_at": "2026-10-19T12:00:00+02:00"
}
```

**Ejemplo únicamente:** ninguna edición o fecha anterior está acreditada aquí, ni debe falsificarse una descarga no efectuada.

4. Ejecutar `python -m ddd_core.congreso_cnig_receipt --archive /ruta/local/fuente.zip --metadata /ruta/local/metadatos.json --output /ruta/local/receipt_candidate.json`.

La herramienta no accede a la red, no extrae los archivos y calcula hashes de los bytes, examina los miembros del ZIP y sus CRC, rechaza rutas peligrosas y sólo emite el estado **PENDING_INDEPENDENT_HISTORICAL_ACREDITATION**.

## Puerta que NO se abre por un hash correcto

El recibo candidato no demuestra que las fronteras municipales y provinciales coincidan con el estado efectivo al **01-01-2025**. Hará falta una comprobación independiente de vigencia temporal y títulos RCC, correspondencia con CPRO/CUMUN, capas, CRS, cobertura de 52 provincias y ciudades, y comparación con INE sin modificar las fuentes originales. Hasta entonces `NAT-C-003..054` y `NAT-C-002` continúan bloqueadas; `generation_authorized=false` y K=407.

La respuesta de CNIG puede exigir un procedimiento de descarga diferente o indicar que ninguna versión publicada corresponde al estado solicitado. Documentar esa respuesta antes de cambiar el contrato.


## Fuente complementaria oficial verificada el 19-10-2026: `LimitesTime`

El IGN anuncia en su boletín de marzo de 2026 una capa de consulta histórica de límites con parámetro TIME desde 2009. En `https://www.ign.es/wms-inspire/unidades-administrativas?SERVICE=WMS&REQUEST=GetCapabilities` figura `LimitesTime`, y el WMS responde **GeoJSON de líneas**, no sólo imágenes, cuando se solicita `FORMAT=application/json;type=geojson`, `TIME=2025-01-01` y `CRS=CRS:84`. Una prueba acotada en rectángulo -4.05,42.4,-3.95,42.5 devolvió 13 líneas con identificador y atributos `date_boundary`, `endlifespanversion`, `nationalcode`. No corresponde al territorio nacional completo.

Herramienta reproducible opcional (sin descarga automática desde CI):
`python -m ddd_core.congreso_ign_historical_wms --bbox -4.05 42.4 -3.95 42.5 --raw-output /tmp/ign_view_2025.geojson --receipt-output /tmp/ign_view_2025.receipt.json`.

**Límite crucial:** un WMS `GetMap` puede limitar elementos, generalizar para visualización, devolver datos recortados, o no acreditar exhaustividad administrativa. La consulta y sus atributos no sustituyen por sí solos un snapshot vectorial legal histórico, cotejo RCC ni receipt CNIG. No está autorizado pasar NAT-C-056 a VALIDATED, ni lanzar las 52 comparaciones por esta evidencia parcial. La prueba solo identifica una vía oficial a evaluar con la autoridad y extrae muestras verificables para investigación.


## Recepción de archivos individuales GML o GeoPackage (sin ZIP)

También se admiten candidatos de cartografía `BDLJE` además de `LILIM`, con cualquiera de estos contenedores: ZIP de Shapefiles/GML/GPKG; GML individual; GeoPackage individual. La comprobación de un GML o GeoPackage suelto verifica el SHA-256 de los bytes y una firma básica de formato, **no** su esquema interno, su CRS ni la vigencia de los límites.

Se utiliza el mismo comando `python -m ddd_core.congreso_cnig_receipt`, pasando el archivo recibido en `--archive` aunque no sea ZIP. El recibo incluye `container_format` y mantiene a `False` todas las puertas de acreditación y producción. No se admite un Shapefile `.shp` aislado sin sus archivos asociados; debe entregarse completo en ZIP. Una respuesta GeoJSON parcial del WMS tampoco es un paquete nacional acreditado.
