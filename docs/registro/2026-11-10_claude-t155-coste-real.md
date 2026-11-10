## 2026-11-10 — T-155 — Cuadro de coste real de las dos últimas semanas

Causa: el propietario pidió coste real por territorio y campaña, éxito a la primera, causas de gasto y propuesta de tope.
Cambio: estudio documental `docs/ESTUDIOS/T155_COSTE/` (informe + 5 CSV), solo lectura de la API de Actions; sin código ni workflows.
Hallazgo: `metricas_proceso.py` pagina una sola consulta (tope de 1.000 resultados) y subestima 8 veces los minutos; queda como tarea aparte.
Pruebas: cifras recalculadas desde 4.639 runs y 3.417 jobs; sin tests (no hay código).
Riesgos: ninguno; los umbrales son una propuesta.
