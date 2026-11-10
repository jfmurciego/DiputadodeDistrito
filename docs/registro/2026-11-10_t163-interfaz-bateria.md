## 2026-11-10 — T-163 — Motor 2: interfaz de la competición para la batería T-132 (paso 4)

- Causa: D-48: la batería T-132 corre la competición en los 71 y comprueba la aceptación (71/71 válidos, ninguno peor que
  el canónico, tiempos medidos).
- Cambio: `ddd_motor2/competir.py`: `PYTHONHASHSEED=0 python -m ddd_motor2.competir --out bateria --cadenas 5 --todos`
  (o territorios sueltos); API `competir_territorio(t, out, n_cadenas)`. Por territorio `COMPETICION.{json,md}`; agregado
  `<out>/competicion/RESUMEN.{json,md}` (ganador, mejora/empata/empeora frente al canónico, huella, tiempos, veredicto de
  aceptación; salida 1 si no se cumple). Un territorio sin entradas o sin ancla queda como ERROR en el resumen.
- Pruebas: `python -m unittest tests.test_motor2_competir`.
- Siguiente: la batería de los 71 (T-132).
