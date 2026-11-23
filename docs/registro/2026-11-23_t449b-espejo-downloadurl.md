## 2026-11-23 — T-449 — Espejo oficial: probar `downloadURL` y todas las candidatas del año

- Causa: el espejo de aut08 (run 45158272014, main@c54a2a0) salió con `ESPEJO_ES_HTML`. La API de datos.gob.es respondió, pero la URL
  elegida devolvió una página web, y el log no decía cuál. La herramienta tomaba `accessURL`, que en DCAT suele ser la página de
  aterrizaje, antes que `downloadURL`, y solo probaba una candidata.
- Cambio: `herramientas/espejo_fuente_oficial.py` 1.0.1. Cada distribución aporta `downloadURL` antes que `accessURL`. Se prueban en
  orden todas las candidatas del año (xlsx > csv > xls > zip > json) hasta la primera que sea un fichero de datos. El log lleva
  `ESPEJO_CANDIDATAS`, `ESPEJO_INTENTO` (URL y motivo) y `ESPEJO_ELEGIDA`. Si ninguna vale: el código común o `ESPEJO_SIN_FICHERO`,
  con lo probado. El workflow no cambia.
- Pruebas: `tests/test_t449_espejo_fuente_oficial.py` 1.0.1 (orden de candidatas, salto de la portada a la siguiente, motivo y URL
  cuando ninguna vale).
- Riesgo: si datos.gob.es solo enlaza la portada autonómica en obras, el siguiente run vuelve a fallar, pero con la lista exacta de URL.
  Entonces queda el recurso declarado por el propietario (medio, marcado como fuente NO oficial).
