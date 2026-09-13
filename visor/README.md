# Visor público MapLibre

Versión: 1.1.0
Anterior: legacy/visor/README_v1.0.0.md

El visor consume un registro declarativo en orchestracion/productos_publicos.json. Cada producto indica fuente canónica, cardinalidad y ruta pública. El navegador transforma EPSG:25830 a WGS84 sólo para dibujar. No recalcula M01–M06 ni modifica geometrías.

Añadir un territorio certificado exige incorporarlo al registro y superar el contrato del manifiesto; no exige reescribir el visor.
