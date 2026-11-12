## 2026-11-11 — T-254 — Medición de Deslinde 1.0: tiempo por fase, código muerto, duplicados y reparaciones

- Solo medición (D-85, D-89); no cambia código de producción. Nuevo `docs/ESTUDIOS/T254_MEDICION_DESLINDE/`: `README.md`
  (informe), `medir.py` (tiempo por fase con cronómetros en proceso, 3 repeticiones + P30 + auditoría geométrica),
  `experimento_memo.py` (caché de `rango_municipal` en su proceso, compara huellas), `codigo_muerto.py` (cierre de
  imports desde producción) y `resultados/` (JSON, perfiles cProfile, vulture).
- Cifras (congreso_huesca, congreso_la_rioja, la_rioja; entradas desde fuente): el exhaustivo se lleva el 60-87 % de la
  competición (51-127 s) y en los tres agota los 200 000 nodos sin candidato; cadenas 10-29 %; canónico M04+M05 3-10 %.
  La caché de `rango_municipal` baja el total un 8-25 % con mapas y `huella_resultado` idénticos.
- Código muerto: 5 849 de 23 451 líneas de `ddd_core`/`ddd_motor2` fuera de producción; M04 `v745`–`v754` (1 839)
  y M05 `v740` (444) se pueden retirar al archivo.
