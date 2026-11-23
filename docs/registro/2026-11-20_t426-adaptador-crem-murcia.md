## 2026-11-20 — T-426 — Adaptador CREM de Murcia 2023 (votos por sección, aut14)

**Causa.** aut14 no tenía votos por partido de su elección vigente (ficha T-421). La ficha suponía datos municipales; el CREM (PU2077) publica mayo de 2023 por distrito y sección (`excel/sec54.xls` y `sec55.xls`) y por mesa (`sec56/57`). No hace falta repartir nada.

**Cambio.** `herramientas/adaptador_crem_murcia_2023.py` (nuevo, 1.0.0): xls → `secciones.csv` (CUSEC, partido, votos) + `MANIFEST.json`; sha256 fijados (sec54 `62eb0b7b…`, sec55 `dc910666…`); fuentes en `fuentes/crem_murcia_2023/`. 1.223 secciones = composición M06. El voto C.E.R.A. (2.558) queda fuera de las secciones y declarado; 7 candidaturas desglosadas, el resto en `otros_votos`.

**Pruebas.** `tests/test_adaptador_crem_murcia_2023.py`: secciones = composición; votos a candidaturas + C.E.R.A. = 676.554 (fila oficial «Región de Murcia»); sha256 erróneo falla.

**Riesgos.** No toca huellas M04/M05. Pendiente: enchufar a la doble vuelta y a `bloques_autonomicas.py`. Pendientes aut03, aut08 (fuente no localizada) y aut11 (decisión D-183: fuera).
