## 2026-11-08 — T-98 — Cádiz en el ensemble con la exención de suelo de San Fernando

Causa: T-92 dejó Cádiz fuera del ensemble porque `ddd_core/m05_gerrychain_engine.py` (1.2.0) no conocía
`validation.population_floor_exempt_municipalities`: el distrito de San Fernando (11031), exento del suelo desde el
2026-11-01 (#380), hacía inválida la partición inicial (`population_floor` y límite inferior de `population_tolerance`).

Cambio:
- `ddd_core/m05_gerrychain_engine.py` 1.3.0: `Contract.population_floor_exempt_municipalities`; el distrito que
  contiene un municipio exento no tiene suelo ni límite inferior de tolerancia, como M05 7.8.5 / M06 7.2.3. Techo,
  límite superior, K, atomicidad, disciplina municipal y provincia no cambian. Sin exentos, el comportamiento es idéntico.
- `herramientas/generar_config_ensemble.py` 1.1.0: `APROBADOS_PROPIETARIO` admite por territorio límites distintos del
  molde y la exención municipal si el contrato trae su decisión gobernada; la config copia los valores del contrato y
  deja `decisions` (decided_at/decided_by/reason/evidence). El resto de exenciones (Barcelona) sigue fuera.
- `configuracion/ensemble/congreso_cadiz.json` (K=11, techo 1,16, tolerancia 0,16, exento 11031) con la aprobación del
  techo del propietario (08-11) y la decisión de San Fernando copiada del contrato. El contrato de producción no cambia.

Pruebas: `tests/test_ensemble_exencion_suelo.py` (nuevo, caso sintético San Fernando + cadena ReCom real),
`test_generar_config_ensemble`, `test_ensemble_configs_territorios`, `test_m05_gerrychain_engine` y el resto de
`test_ensemble_*`, gobernanza R015 y guardián (registro, marcas) en verde en local (127 tests).

Corrida local con el motor real (fuentes INE 2023 de Cádiz: 926 secciones, 1.254.866 hab., como el contrato):
M01–M05 OK (M05 hard=1, San Fernando exento). Sobre esa partición, el motor 1.2.0 daba `population_floor:7` y
`population_tolerance:7`; el 1.3.0, ninguna. Ensemble corto (`balanced`, 150 pasos): 150 estados, 60 únicos, todas las
puertas duras en verde; el distrito de San Fernando queda en 0,825 del objetivo y el resto entre 0,95 y 1,159.

Efectos: el motor del ensemble no está en la huella M05 (`huella_checkpoint_m05.ENGINE_FILES`) ni en la evidencia
pre-M04: no invalida checkpoints ni M06; no hace falta ninguna 00.
