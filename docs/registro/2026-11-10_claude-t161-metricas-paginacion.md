## 2026-11-10 — T-161 — Métricas del proceso: paginación completa y minutos reales de jobs

Causa: `herramientas/metricas_proceso.py` hacía una sola consulta `created>=fecha` y la API de runs corta a 1.000 resultados; con `--dias 14` daba 5.920 min y 4 territorios frente a 46.284 min y 74 del estudio T-155 (#615).
Cambio: `metricas_proceso.py` 1.1.0. Runs por ventanas de fechas de 6 h (`--ventana-horas`), con bisección si una ventana llega al tope; reintentos con espera exponencial (403/429/5xx y reseteos de conexión), también con `gh`; minutos = suma real de `completed_at − started_at` de los jobs de cada run, con caché por run (reloj del run solo si no hay jobs o se agota `--max-detalle`, ahora 1.500; se informa en `runs_con_reloj_en_vez_de_jobs`). Copia anterior en `legacy/herramientas/`.
Pruebas: `tests.test_metricas_proceso` con API simulada que topa a 1.000 y tiene 2.600 runs (1.300 en una hora): total exacto 26.000 min; reintento tras reseteo de conexión.
Riesgos: la primera pasada hace una consulta de jobs por run (miles; luego, caché). Sin cambios de motor, huellas ni workflows; no requiere 00.
