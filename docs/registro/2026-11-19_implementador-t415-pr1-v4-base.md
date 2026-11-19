## 2026-11-19 — T-415 — PR 1: base de `visor/v4/` (portada final de la autora)

Causa: D-174 aprueba el diseño de T-415 (#909); orden de PR: metadatos, NOTICE y base de v4/.
Cambio: `visor/v4/` con la versión por ficheros de la autora (`index.html`, `comprender.html`, `auditoria-registro.html`, `styles.css`, `app.js`, `catalogo-mapas.js`, 3 WebP y `assets-manifest.json`) copiada sin modificar salvo el enlace «Explorar» / «Consultar el visor», que ahora abre `mapa/` (la V4) y no la V3; `visor/v4/NOTICE.md` (autoría y procedencia de las ilustraciones); `tests/test_visor_v4_base.py`.
Revisión de metadatos: los 3 WebP sin EXIF/XMP/ICC; HTML, CSS, JS y manifiesto sin rutas de usuario, correos ni URL privadas (la `source_url` privada solo estaba en `COMPROBACIONES.json`, que no se copia).
Pruebas: 7 tests nuevos (enlaces y anclas, Explorar→mapa/, sin M01–M08, catálogo DOI vacío, sin recursos externos ni rutas privadas, sha256 de los WebP, `lang` y una `h1`).
Riesgos: ninguno de ejecución; no se publica (P40 no copia `v4/`), no toca V3, workflows ni LICENSE. Aún sin «La doble vuelta», vídeo, tokens de bloques ni la revisión de contraste (PR siguientes). Los 3 menores de redacción del revisor sobre #909 se alinean en `DISENO.md` cuando #909 se fusione (no existe aún en `main`).
