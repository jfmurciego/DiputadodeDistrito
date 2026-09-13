# Visor público MapLibre

**Versión:** 1.0.0  
**Estado:** publicación estática de resultados certificados.

El visor consume exclusivamente:

- `resultados/finales/aragon/distritos.geojson`
- `resultados/finales/castilla_y_leon/distritos.geojson`

La transformación EPSG:25830 → WGS84 ocurre sólo en el navegador para dibujar. No recalcula M01–M06, no modifica geometrías ni promueve Extremadura.

El workflow `Desplegar visor público` publica un artefacto efímero de Pages que empaqueta el visor y una copia de lectura de dichos GeoJSON.
