## 2026-11-20 — T-426 — Adaptador SADEI de Asturias 2023 (votos por concejo, aut03)

**Causa.** aut03 no tenía votos por partido de su elección vigente (ficha T-421).

**Cambio.** `herramientas/adaptador_sadei_asturias_2023.py` (nuevo, 1.0.0): CSV exportado de la tabla PxWeb 190426 de SADEI (Juntas electorales, municipal y completos) → `municipios.csv` (INE 5 cifras, partido, votos) + `MANIFEST.json` (nivel municipio, `aproximado_en_distrito`). Fuente en `fuentes/sadei_asturias_2023/` con sha256 `197045e1…f248f06` fijado. 78 concejos; concejos + «Residentes ausentes» (voto exterior, declarado y no repartido) = fila ASTURIAS exacta. El reparto a sección/distrito (D-183) no se hace aquí: lo aplica M07 con la composición del run vigente.

**Pruebas.** `tests/test_adaptador_sadei_asturias_2023.py` (cuadre con los totales oficiales, sha256 erróneo falla).

**Riesgos.** No toca huellas M04/M05. Pendiente: formato `doble_vuelta_autonomicas` de T-427 y alias/bloques.
