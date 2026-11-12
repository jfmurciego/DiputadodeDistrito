## 2026-11-12 — T-116 — Explorador cartográfico V3 integrado

- **Causa:** evolución de la experiencia pública desde la V2 hacia un dashboard cartográfico integrado, solicitado por el propietario. Continuación funcional de la línea T-116 sin modificar su lógica de datos.
- **Cambio:** nuevo `visor/v3/` con selector nacional/autonómico, proporcional/mayoritario, territorial/electoral, capas, nivel hasta sección censal, búsqueda, colores de partidos inequívocos, ficha y calendario por ámbito. Reutiliza M06/M08, datos de V2 e índices de secciones con fallo cerrado.
- **Publicación:** `_reutilizable-publicar-sitio.yml` 3.14.2; archiva íntegro el 3.14.1 en `legacy/workflows/_reutilizable-publicar-sitio_v3.14.1_20261112.yml`. V1 y V2 permanecen en rutas propias y la portada pasa a V3 solo con precondiciones y validación.
- **Restricción de veracidad:** el color de una sección refleja el ganador de su distrito si se usa M08 (no resultados propios de esa sección); el proporcional autonómico y las elecciones sin producto electoral geolocalizado indican datos no disponibles.
- **Pruebas:** `tests/test_preparar_portada_v3.py`, contrato V2 preservado y validación JS con `node --check`; CI y revisor deben aprobar antes del lanzamiento de P50.
- **PR:** a completar al abrir; ejecución productiva pendiente de validación.
