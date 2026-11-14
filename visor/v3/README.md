# Visor V3 · explorador cartográfico unificado

**VERSIÓN:** 1.0.0 · **FECHA:** 2026-11-12 · **ESTADO:** candidato · **ANTERIOR:** ninguna (fichero nuevo)

## Propósito
V3 integra en un único espacio cartográfico cuatro ejes de navegación:
Ámbito nacional/autonómico, sistema proporcional/mayoritario DDD, vista territorial/electoral y calendario de elecciones por ámbito. Mantiene una ficha contextual, búsqueda, navegación geográfica y leyenda con colores políticos oficiales del proyecto.

## Datos reales y límites verificables
- Provincias y comunidades: `/v2/datos/provincias.json` y `/v2/datos/comunidades.json` publicados (cartografía INE).
- Congreso proporcional 2023: el reparto y el partido más votado proceden del producto provincial oficial incorporado en V2.
- Congreso DDD 407: `/datos/INDEX.json`, geometría M06 y ganadores M08 materializados y acreditados por el publicador. No se sustituyen por polígonos de ejemplo.
- Secciones: `/v2/datos/secciones/INDEX.json` y fichero `<CODPRO>.geojson` generado del seccionado INE 2025 por provincia. Su color electoral, si se aplica, se **hereda del distrito ganador**; NO representa un recuento propio de sección.
- Ámbito autonómico: marco territorial, calendarios documentados y productos M06/M08 si la publicación los incluye. No confundir votos autonómicos con resultados nacionales. El proporcional autonómico no dispone aún de un mapa electoral certificado de detalle en el paquete actual: se señaliza ausencia.
- Históricos: el calendario expone únicamente carpetas de ediciones existentes en `datos/resultados/historico/autonomicas/`. No pinta resultados pasados a partir de colores de 2023.
- El filtro de población/desviación se calcula sobre atributos de población publicados; no se inventan densidad, renta, mesa ni participación.

## Compatibilidad
No modifica `visor/`, `visor/v2/`, registros electorales ni GeoJSON canónicos. P50 copia el frontend a `/v3/`, conserva V1 en `/v1/`, V2 en `/v2/`, y redirige `/` a `/v3/`. Cuando falle la precondición o la prueba, NO despliega.
No activar el nuevo despliegue hasta CI y revisor aprobados. La publicación P50 debe ejecutarse explícitamente en modo «solo sitio» y comprobando el dominio HTTPS.
