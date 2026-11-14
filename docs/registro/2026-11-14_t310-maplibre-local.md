## 2026-11-14 — T-310 — maplibre-gl servido desde el propio sitio (sin unpkg)

Causa: los visores (V1, nacional, congreso, V2, V3) y la galería técnica de `ddd_ensemble` cargaban maplibre-gl 5.7.0/5.6.0
desde unpkg.com; un tercero veía la IP del visitante.
Cambio: `visor/v2/vendor/maplibre-gl/5.7.0/` (dentro de v2 porque el workflow de publicación copia `visor/v2/` entero con `cp -R` y el resto solo ficheros sueltos; sin tocar workflows) (js 939 KB, css 69 KB, LICENSE BSD-3) bajado del tarball del registro npm
(sha512/sha1 verificados) con `PROCEDENCIA.json` (origen, sha256, SRI sha384); los cinco `index.html` apuntan a esa ruta relativa con `integrity` (V1 1.4.3 y nacional 1.0.4, con copia de la anterior en `legacy/`);
`construir_vista_previa.py` incrusta ahora el vendor; se retira el enrutado muerto de unpkg en `tests/test_visor_v2_*`; `ddd_ensemble/gallery.py` copia el vendor a su salida (5.6.0 → 5.7.0). Sin CSP por meta (no existía).
Pruebas: `tests/test_visor_sin_terceros.py` (HTML/CSS/JS/galería, vendor dentro de v2 y copiado por el workflow; sin recursos externos, sin unpkg, sha256 y SRI contra la procedencia).
Pendiente de decisión del propietario: siguen cargándose en tiempo de ejecución (JS) las teselas raster de
`tile.openstreetmap.org` (mapa base) y el beacon opcional de `static.cloudflareinsights.com`; el test los declara como
excepciones dinámicas. Quitarlos exige otro mapa base/alojar teselas. Sin tocar workflows ni motor; se publica con la P50.
