## 2026-11-08 — T-102 — Nombres de distrito de Alicante, Barcelona y Málaga (main en rojo)

- **Causa:** `main` en rojo (`test_nombres_comunidades_nacional.Datos49Provincias`: 52 != 49). No lo causan los gemelos
  `congreso350_*` (no empiezan por `congreso_` ni publican): entre las 17:11 y las 17:29 del 08-11 los registros del visor
  añadieron el M06 publicado de Alicante, Barcelona y Málaga, que no tenían nombres de distrito (C12/C13).
- **Cambio:** nombres e informes de las 3 provincias con `herramientas/generar_nombres_comunidades_nacional.py --descargar`
  (M06 publicados con sha256); los 49 anteriores salen idénticos. Seis topónimos en español en `toponimos_es.csv`
  (Alicante, Alcoy, Elche, San Vicente del Raspeig, Villajoyosa, Hospitalet de Llobregat). El test exige nombres para
  todas las provincias publicadas (al menos 49) en lugar de un número fijo.
- **Pruebas:** `tests.test_nombres_comunidades_nacional`, `test_nombres_distrito`, `test_nombres_visibles_nacional`,
  `test_partidos_judiciales` en verde.
- **PR/run:** PR de arreglo de `main` (cb4c4d3 en rojo).
