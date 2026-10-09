# Paquete A — Integridad electoral C-05/C-09

**Versión:** 1.0.0
**Fecha:** 2026-09-13
**Estado:** implementado; pendiente de certificación CI
**Anterior:** ninguno — documento nuevo

M07 ya no puede perder votos silenciosamente. Cada ejecución escribe `m07_reconciliacion.json` con votos de entrada, asignados y no asignables. Los descuadres deben declararse por sección; si cambian o aparece uno nuevo, M07 falla.

Aragón reconoce los dos casos demostrados por la auditoría: `5002501003`, con 608 votos no asignables al universo 2025, y `2221301003`, presente en el mapa pero sin resultados RTVE 2026. La excepción no inventa una asignación geográfica.

La reconciliación contra la composición M06 certificada `gh-34599224954-1` y la fuente RTVE materializada da `PASS_WITH_DECLARED_EXCEPTIONS`: 648.799 votos de entrada, 648.191 asignados y 608 no asignables. Ambos universos contienen 1.463 secciones; difieren exactamente en las dos claves anteriores. La evidencia queda materializada en `EVIDENCIAS/PAQUETE_A_RECONCILIACION_ARAGON.json`.

El módulo pasa de 66 líneas con una sentencia de 2.180 caracteres a 222 líneas estructuradas; su línea más larga tiene 97 caracteres. No cambia M01–M06 ni la geometría distrital.
