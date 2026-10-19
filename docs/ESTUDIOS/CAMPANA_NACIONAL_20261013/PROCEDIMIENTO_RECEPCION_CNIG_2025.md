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
