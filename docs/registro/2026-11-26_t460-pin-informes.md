## 2026-11-26 — T-460 — Pin de los dos informes de la doble vuelta tras renombrar «Derecha nacional»

- Causa: tras #1015 (T-460) se relanzaron las dos P75; P40 solo publica lo fijado en `configuracion/doble_vuelta_publicada.json` (sha256 del informe, `INFORME_SHA256_DISTINTO` si no coincide).
- Cambio: nacional, run P75 45871996553-1 (52/52), `interno/doble-vuelta/nacionales/congreso-2023/informe-doble-vuelta.json`, sha256 `650ba13c…60cc`. Autonómicas, run P75 45872763812-1 (16 OK; aut11, aut18 y aut19 `NO_APLICA`), `interno/doble-vuelta/autonomicas/informe-doble-vuelta.json`, sha256 `2a77a8f1…ffb9`. Datos de la entrega del Coordinador (ejecuciones success, intento 1); el sha256 de los informes no se ha podido leer desde la nube.
- Pruebas: tests de T-419/T-443 y gobernanza en local.
- Riesgos: la P40 45873075949 se lanzó antes del pin y puede fallar con `INFORME_SHA256_DISTINTO`; con esta PR fusionada, hay que relanzarla (permiso del propietario en el Operador). Sin cambio en M04/M05/huellas.
