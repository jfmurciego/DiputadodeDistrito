# N08 — alcance de LimitesTime a 01-01-2025

Versión: 1.0.0. Fecha: 2026-10-27. Estado: investigación acotada cerrada; acreditación BLOCKED_EXTERNAL.
Alcance: fuentes oficiales para N08; dependencia del frente nacional. Origen: expediente nuevo, sin predecesor; base 75fe65b6a0b9bea533b726792632dc6744a4d6fc.
Cambios y motivo: conservar originales y resolver si una consulta temporal WMS acredita una edición íntegra. No modifica contratos ni puertas.

**Decisión:** sí se puede consultar vectorialmente el estado histórico solicitado; no queda acreditada una edición original, exhaustiva y jurídicamente vigente a 01-01-2025 con esta salida WMS. No corresponde afirmar que WMS solo sirve imágenes ni que TIME es ignorado. Tampoco se demuestra que sea imposible obtener la fuente por otra vía.

Se reutiliza GetCapabilities ya presente en `/private/tmp/ign-wms-unidades-admin-getcapabilities-20261027.xml`, preservado aquí como `capabilities_reused.xml`. Anuncia LimitesTime desde 2009 y formato GeoJSON. Su procedencia HTTP no se ha vuelto a capturar: es evidencia local preexistente, no adquisición nueva de esta sesión. El antecedente `docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/EVIDENCIA_IGN_CAMBIO_2025_2026.json` ya acredita una transición temporal en Algemesí; no se repite esa adquisición.

Dos nuevas consultas oficiales GetMap en BBOX CRS84 `-3.75,42.3,-3.65,42.4`, TIME `2025-01-01`, GeoJSON, producen nueve líneas cada una. Solo se cambian WIDTH/HEIGHT de 600 a 1200: coinciden IDs y propiedades, pero cambian las nueve geometrías, incluidos sus vértices. `resolution_comparison.json` fija las URLs exactas; `manifest.json` fija hashes y tamaños de los originales. Es una demostración directa de dependencia de la representación, no una medida del error respecto a la geometría original. `totalFeatures=unknown` tampoco permite acreditar exhaustividad.

Herramientas usadas: constructor de URL y `inspect_historical_response` de `ddd_core.congreso_ign_historical_wms`; descarga mediante curl con TLS verificado. El módulo de adquisición falló primero por DNS en sandbox y luego por falta de CA en Python fuera del sandbox. Curl del sistema obtuvo las dos respuestas sin desactivar TLS. El receipt de la primera muestra es diagnóstico, no un receipt nacional. La fecha de su inspección es posterior a la descarga por segundos.

También se inventarían por SHA los bytes WFS previamente presentes para nueve provincias, sin nueva descarga, en `existing_wfs_inventory.json`. El manifiesto ajeno de ocho elementos no inventaría Burgos; se incluye ese fichero adicional expresamente. La regla temporal declarada allí usa begin/endLifespanVersion: no se presume equivalente a vigencia jurídica. Los datos voluminosos siguen en su ubicación original; el inventario no es un respaldo de sus bytes.

## Expediente preparado para IGN/CNIG

Destinatario competente: IGN/CNIG, unidad custodio BDLJE/RCC. Antecedente: solicitud ya confirmada el 18-10-2026 según el expediente nacional; no se envía otra comunicación.

Solicitar: acceso al vector original sin simplificación ni dependencia de WIDTH/HEIGHT, válido al 01-01-2025; versión inmutable y manifiesto íntegro con cobertura 50 provincias, Ceuta y Melilla; identificación municipal/provincial, CRS y precisión, licencia y trazabilidad RCC; semántica de fechas TIME, date_boundary y begin/endLifespanVersion; aclaración de la discrepancia WMS 18/06/2025 frente a API 19/06/2025 ya observada. Pedir confirmación de si WMS generaliza/recorta y qué descarga o consulta permite recuperar geometría original exhaustiva.

Aceptar únicamente con bytes, hashes, cobertura, semántica temporal y títulos legales contrastables. Si no existe una instantánea, pedir identificación del conjunto y procedimiento oficial que permitan reconstruirla. Hasta entonces NAT-C-056/N08 no se acreditan y no se generan distritos. El ensayo no justifica barrer España mediante teselas WMS.

Validación local: 22 pruebas dirigidas PASS, salida en `directed_tests.log`; incluye pruebas de rechazo y simulación deliberada de fallo de red. Ese aviso simulado no describe el resultado de las dos consultas reales. CI de este expediente no ejecutada. Revisión separada pendiente antes del commit.
