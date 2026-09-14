# Visor público MapLibre

Versión: 1.2.0
Anterior: legacy/visor/README_v1.1.0.md

El visor consume un registro declarativo en orchestracion/productos_publicos.json. Cada producto indica fuente canónica, cardinalidad, ruta y estado de publicabilidad. El navegador transforma EPSG:25830 a WGS84 sólo para dibujar. No recalcula M01–M06 ni modifica geometrías.

Los mapas visibles son vistas técnicas auditables. `PASS` acredita geometría y empaquetado; no equivale a autorización de publicación política. La decisión se rige por `docs/POLITICA_PUBLICABILIDAD.md`.

Añadir un territorio certificado exige incorporarlo al registro y superar el contrato del manifiesto; no exige reescribir el visor.
