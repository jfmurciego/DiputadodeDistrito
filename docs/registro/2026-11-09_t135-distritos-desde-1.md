## 2026-11-09 — T-135 — Distritos numerados de 1 a K en lo público (zona datos abiertos y visor)

Causa: regla del propietario (09-11), no existe el distrito 0. Datos abiertos, fichas y visor mezclaban 0..K-1 y d+1.
Cambio: `herramientas/numeracion_publica.py` (`numero_publico`, `csv_publico`); `generar_datos_abiertos` 1.1.0 (CSV, fichas
`distrito-1..K.html`, INDEX.json esquema 1.1 con `numeracion: 1..K`; migra el paquete 1.0 sin red y borra `distrito-0.html`);
generadores de rotación, territorial y secciones del v2 emiten 1..K y `v2.js`/`nacional.js` 1.0.3 dejan de sumar 1.
El id interno del motor (M04-M06, huellas, GeoJSON M06) no cambia: queda para el rediseño del motor.
GeoJSON público de `datos_abiertos/<t>/distritos.geojson` derivado del blob M06 (propiedad `distrito` 1..K, sin `district_id`),
con su sha256 en `INDEX.json` (`geojson.sha256`) y el de origen en `geojson.sha256_origen`; `materializar` verifica ambos.
Frontera: `datos/composicion`, `datos/resultados`, `datos/distritos` y el M06 quedan INTERNOS (0..K-1; ningún fichero mixto);
la conversión se hace solo al publicar. `visor/app.js` 1.4.1 muestra 1..K.
Pruebas: `tests.test_numeracion_publica`, `tests.test_datos_abiertos` (numeración, regeneración desde 1.0, GeoJSON público), Playwright `test_numero_mostrado_igual_al_csv_publico` (Álava y Madrid).
Efectos: cambian los sha256 de los 52 `resultados.csv` y de `INDEX.json`; enlaces `distrito-0.html` dejan de existir (nota en
`datos_abiertos/README.md`). Sin cambio de huellas ni de modo de 00. Sin segunda PR de `datos/`: se mantienen internos.
