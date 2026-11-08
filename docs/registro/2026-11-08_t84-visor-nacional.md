## 2026-11-08 — T-84 — Visor Nacional con barra temporal y capas (D-16)

Causa: D-16 pide el visor en dos vistas, Nacional y Autonómica. Hoy solo hay el visor técnico por territorio.
Cambio: nueva página `visor/nacional/` (index.html, nacional.js, styles.css, todo 1.0.0, ficheros nuevos). Lee `datos/INDEX.json` (paquete `datos_abiertos`, 49 provincias, generales 2023), dibuja el ganador por distrito (325 distritos) con feature-state para hover y selección y ficha por distrito. Barra temporal 2011–2023: solo 2023 activa. Capas ganador por sección, rotación y participación desactivadas con motivo (sin datos publicados; histórico en T-83/T-85). Autonómica: botón desactivado. No se inventan datos.
Pendiente: PMTiles (hoy un GeoJSON por provincia, ~53 MB en total, cargados en paralelo); publicar `visor/nacional/` en el sitio exige tocar `_reutilizable-publicar-sitio.yml` (avisar al Coordinador, no tocado aquí); Canarias, Ceuta y Melilla no están en el paquete.
Efectos: ninguno en módulos, huellas ni workflows; sin publicación.
Pruebas: captura local con Playwright (325 distritos, 49 provincias, GeoJSON verificados con sha256 vía `generar_datos_abiertos.py --materializar`), `tests.test_visor_nacional`, `test_r015_invariantes.GovernanceHeaders`.
Riesgos: bajos; carpeta nueva sin enlace desde el visor actual.
