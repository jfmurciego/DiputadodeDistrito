## 2026-11-07 — T-90 — Paquete mínimo y archivo en origen leen los GeoJSON *.geojson.zip

- **Causa**: las 04 encadenadas de Barcelona (run 42416213698), Alicante (42418334746) y Málaga (42418628975)
  fallaron en «Archivo en origen — M08 a R2» con `el paquete mínimo no tendría ningún GeoJSON distrital`. M01-M08
  escriben el GeoJSON comprimido (`*_m08_distritos_resultados.geojson.zip`, `*_m06_distritos.geojson.zip`) y el
  selector de #478 solo aceptaba `*.geojson` sueltos (los tests usaban `.geojson` sueltos). No es la cadena
  electoral: la 00 de Huesca (42421655965) fue verde porque no ejecutó la 04.
- **Cambio**: `archivar_artefactos_r2.py` 1.1.1 (`es_geojson`/`leer_geojson`: el paquete incluye el `.geojson.zip`
  distrital tal cual y sigue descartando el de secciones); `archivo_origen.py` 1.0.2 (composición y partidos leen
  también `.geojson.zip`, que habría fallado justo después). Copias en `legacy/herramientas/`.
- **Sin degradar a aviso**: el producto electoral ya está registrado antes de este paso («Registrar disponibilidad
  del producto electoral» pasó en 42416213698); el fallo solo deja la 04 en rojo, y el «run no verde si no se archiva»
  es la decisión de T-72. Arreglada la causa, no hace falta tocar workflows.
- **Pruebas**: `test_geojson_zip_del_estado_real` y el caso `.geojson.zip` de `Partidos` fallan antes y pasan después;
  `tests.test_archivar_artefactos_r2`, `tests.test_archivo_origen`, gobernanza y guardián en verde.
- **Siguiente**: relanzar la cadena electoral de Barcelona, Alicante y Málaga (Operador, con permiso del propietario).
