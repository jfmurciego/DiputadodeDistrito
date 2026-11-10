## 2026-11-10 — T-163 — Motor 2: interfaz de la competición para la batería T-132 y sustituto de M05 para el banco

- Causa: D-48: la batería T-132 corre la competición en los 71 y comprueba la aceptación (71/71 válidos, ninguno peor que
  el canónico, tiempos medidos).
- Cambio: `ddd_motor2/competir.py`: `PYTHONHASHSEED=0 python -m ddd_motor2.competir --out bateria --cadenas 5 --todos`
  (o territorios sueltos; `--reanudar` salta los COMPETICION.json ya escritos); API `competir_territorio(t, out, n_cadenas)`. Por territorio `COMPETICION.{json,md}`; agregado
  `<out>/competicion/RESUMEN.{json,md}` (ganador, mejora/empata/empeora frente al canónico, huella, tiempos, veredicto de
  aceptación, reescrito tras cada territorio; salida 1 si no se cumple). Un territorio sin entradas o sin ancla queda como ERROR en el resumen.
- Pruebas: `python -m unittest tests.test_motor2_competir`.
- Cambio: `ddd_motor2/competidor.py`: `python -m ddd_motor2.competidor --params <contrato> --run-id <id> [--semilla n]`
  (lee in_graph_json/in_geojson de modulo_05; deja el M05 y el informe del ganador en out_geojson/out_report). Por
  candidato: M05 (canónico `modulos/05`; GerryChain `m05_gerrychain_strategy --seed-count 1 --seed-base <semilla
  pública>`, desde la semilla canónica si la Formación M04 no es admisible) + M06 para juzgar con el núcleo. `--semilla`
  se ignora (semillas públicas). Informe en `<carpeta M05>/competicion/`. rc 0 con salida / 2 sin candidato
  evaluable (borra out_geojson y out_report) / 3 sin ancla.
- Pruebas: `python -m unittest tests.test_motor2_competidor` (semilla inicial de GerryChain y main(): rc 3, rc 2, copia del ganador). La ejecución real (M05, M06,
  GerryChain) la mide la batería T-132: esta sesión no tiene geopandas ni GerryChain.
- Siguiente: la batería de los 71 (T-132).
