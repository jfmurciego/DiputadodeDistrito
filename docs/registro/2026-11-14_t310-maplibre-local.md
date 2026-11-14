## 2026-11-14 — T-310 — maplibre-gl servido desde el propio sitio (sin unpkg)

Causa: los visores (V1, nacional, congreso, V2, V3) y la galería técnica de `ddd_ensemble` cargaban maplibre-gl 5.7.0/5.6.0
desde unpkg.com; un tercero veía la IP del visitante.
Cambio: `visor/vendor/maplibre-gl/5.7.0/` (js 939 KB, css 69 KB, LICENSE BSD-3) bajado del tarball del registro npm
(sha512/sha1 verificados) con `PROCEDENCIA.json` (origen, sha256, SRI sha384); los cinco `index.html` apuntan a esa ruta
relativa con `integrity`; `ddd_ensemble/gallery.py` copia el vendor a su salida (5.6.0 → 5.7.0). Sin CSP por meta (no existía).
Pruebas: `tests/test_visor_sin_terceros.py` (HTML/CSS sin recursos externos, sin unpkg, sha256 y SRI contra la procedencia).
Pendiente de decisión del propietario: siguen cargándose en tiempo de ejecución (JS) las teselas raster de
`tile.openstreetmap.org` (mapa base) y el beacon opcional de `static.cloudflareinsights.com`; el test los declara como
excepciones dinámicas. Quitarlos exige otro mapa base/alojar teselas. Sin tocar workflows ni motor; se publica con la P50.
