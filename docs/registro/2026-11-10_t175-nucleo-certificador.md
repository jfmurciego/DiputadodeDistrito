## 2026-11-10 — T-175 — R-NUCLEO en el certificador exacto

- Causa: el certificador 1.2.0 no aplicaba R-NUCLEO (núcleos urbanos cerrados). Solo existía el adaptador que deduce los
  núcleos de una composición M06; faltaba uno desde las unidades de partición.
- Cambio: `ddd_motor2/adaptadores.py` 1.1.0 añade `nucleos_desde_unidades` y `con_nucleos`, que `problema_y_plan` también
  usa. `herramientas/certificador_exacto.py` 1.3.0 lee `district_id` y `ddd_closed_urban` del M04 y marca
  `Unidad.nucleo_cerrado` por unidad M04. Cada núcleo forma un solo grupo y su distrito no admite otros átomos (también
  con superátomos). Añade `--sin-nucleos`. Sin cambios en producción, huellas ni workflows.
- Resultados (`docs/ESTUDIOS/T136_CERTIFICADOR_EXACTO.md`): el publicado cumple R-NUCLEO en Álava, Albacete, Burgos y
  Huesca. Burgos: con la regla, óptimo certificado 9 hab. en 7 s (sin ella, cota [9, 11] en 61 s).
- Pruebas: `python -m unittest tests.test_certificador_nucleos tests.test_certificador_exacto tests.test_certificador_ligero tests.test_motor2_adaptadores`.
