## 2026-11-11 — T-264 — motor2: los puentes del contrato llegan al adaptador

- Causa: T-254 §3 (duplicado «puentes del contrato»). `adaptadores._puentes_contrato` solo miraba
  `cfg["modulo_02_construir_adyacencias"]` en la raíz, pero los contratos los declaran en `cfg["modulos"][…]`, y además
  los CUSEC de `topology_bridges` llegan como entero sin el cero inicial. Devolvía vacío; los puentes solo llegaban
  por el `edge_type` del grafo M03.
- Cambio: `ddd_motor2/adaptadores.py` 1.2.0 → 1.2.1 (la anterior está en `legacy/ddd_motor2/adaptadores_v1.2.0_20261110.py`).
  Lee `modulos.modulo_02_construir_adyacencias` y usa la raíz como respaldo; aplica `zfill(10)` a los ids numéricos.
  Es el parche de `diag/T264b-puentes` (915552b), con el `zfill` limitado a ids numéricos para no alterar ids
  sintéticos.
- Efecto en los contratos: ahora se leen 1 puente en congreso_cantabria, 3 en congreso_burgos, 1 en congreso_huelva y
  1 en cantabria; antes se leían 0.
- Pruebas:
  - Nuevo `test_puentes_del_contrato_bajo_modulos_y_cusec_entero` en `tests/test_motor2_adaptadores.py`: falla con la
    1.2.0 (no lee `modulos`) y pasa con la 1.2.1.
  - Pasan además `tests.test_motor2_adaptadores` y R015 `GovernanceHeaders` (unittest, local).
- Prueba local: `bateria_motor.py entradas … --seccionado shapefile` y `PYTHONHASHSEED=0 python3 -m ddd_motor2.competir`
  (D8, 10 cadenas). «Antes» es `main` 8e4e268 y «después», esta rama sobre la misma base. En congreso_cantabria,
  congreso_burgos, congreso_huelva y cantabria salen:
  - el mismo ganador y la misma `huella_resultado`;
  - las 59 composiciones CSV idénticas (sha256);
  - el contenido de los GeoJSON M06 idéntico.
  Los puentes ya estaban en el grafo M03 como aristas de puente; ahora también los ve el contrato.
- Huellas: cambia solo la huella `motor2`, sin cambio de resultados. No toca M04, M05, `ddd_core/`, `modulos/` ni N08.
  Modo de 00: el que corresponda al territorio; esta PR no obliga a «Ejecutar desde el principio». No se lanza nada.
