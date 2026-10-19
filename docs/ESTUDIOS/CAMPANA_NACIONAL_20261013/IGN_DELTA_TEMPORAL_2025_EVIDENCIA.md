# IGN 2025 — discrepancia de fecha documentada

**Fuente:** comparativa exploratoria entre dos servicios oficiales del IGN, consulta del 19-10-2026.

- GeoJSON de `https://api-features.ign.es/collections/administrativeboundary/items`, tramo `M34104646029M34104646197T0246715` (Algemesí / Polinyà de Xúquer): `date_boundary=2025-06-19`.
- GeoJSON de `https://www.ign.es/wms-inspire/unidades-administrativas`, capa `LimitesTime`, mismo `nationalcode`: `date_boundary=2025-06-18Z`, `endlifespanversion=2998-12-31Z`.
- Petición `TIME=2025-01-01`: el tramo no aparece; petición `TIME=2026-01-01`: aparece, en un mismo rectángulo delimitado a Algemesí / Polinyà de Xúquer.
- En consecuencia **se demuestra la diferencia temporal de inclusión del tramo**, no la identidad de la fecha jurídica (hay un día de diferencia entre API y WMS). Puede estar relacionada con la representación horaria, pero **no se supone equivalente sin explicación de la autoridad**.
- Estas 13 líneas por vista no acreditan completitud de datos administrativos nacionales 52/52, tampoco constituyen un recibo de geometría histórica inmutable.

**Automatización:** `herramientas/verificar_cambio_historico_ign.py`, con prueba de red acotada. Una respuesta HTTP que no llegue genera un registro `NETWORK_UNAVAILABLE_NO_TEMPORAL_EVIDENCE` y **no certifica nada**. Los SHA-256 se calculan sobre los bytes HTTP originales solo si el proveedor responde y las validaciones pasan.

**Estado:** ejemplo temporal compatible con referencia 2025-01-01, pero `NAT-C-056` permanece `READY`, pendiente de source receipt, evidencia legal, cobertura y comparación independiente.
