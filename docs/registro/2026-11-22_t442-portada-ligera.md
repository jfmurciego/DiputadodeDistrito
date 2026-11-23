## 2026-11-22 — T-442 — Portada ligera en el móvil: fotos a la medida y vídeo solo al pulsar

- **Causa:** D-192 (propietario, 22-11; diseño T-441, #971 §2.1): la portada baja en el móvil las mismas fotos que en el ordenador (89 % de su peso) y pide los datos del vídeo al abrir.
- **Cambio (`visor/v4/`):**
  - Copias reducidas de las dos imágenes del encabezado, generadas del original (Pillow, LANCZOS, WebP calidad 80): `assets/congreso-760.webp` (760×447, 68,9 KB frente a 156,3 KB) y `assets/mapa_espana-320.webp` (320×336, 15,6 KB frente a 65,4 KB). Los originales de la autora no cambian (sha256 igual).
  - `index.html`: `<picture>`: la foto reducida hasta 600 px de ancho de pantalla y el mapa reducido hasta 1000 px; el resto de pantallas, el original.
  - `assets-manifest.json`: dos entradas `derived` con `derived_from` y el sha256 del original; mismos derechos y alcance.
  - `app.js`: el vídeo con `preload = 'none'`: no se descarga nada hasta pulsar play (antes, sus metadatos al abrir).
  - La carga diferida del mapa de la portada (§2.1.2 del diseño) no se aplica: está en el encabezado, a la vista nada más abrir, y diferirlo no ahorra nada.
- **Pruebas:** `test_visor_v4_base` (5 recursos; copias reducidas declaradas, más ligeras y servidas solo en pantallas pequeñas; original intacto), `test_visor_v4_video.js` (`preload` «none»), suites V4/T-428/T-419/sin terceros (87 OK) y Node. Comprobado con Chromium: a 390 px usa las dos copias; a 800 px la foto original y el mapa reducido; a 1400 px los originales.
- **Ahorro en el móvil al abrir la portada:** ≈ 137 KB de imágenes (≈ 234 KB → ≈ 97 KB comprimidos) más los metadatos del vídeo.
- **Riesgos:** la foto reducida se ve algo menos nítida en móviles de alta densidad (ya lo era con el original, que tiene 598 px de alto para un hueco de 355). Entra en la próxima P40; no lanza ni publica.
