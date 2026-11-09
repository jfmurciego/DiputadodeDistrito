# T-132 (C) · Dónde está escrita cada regla y en qué difieren

Fecha: 2026-11-09. Estado del código: `origin/main` c430791. Solo lectura; no se toca el motor.

## Inventario

| Regla | Validador de producción (`herramientas/validar_ejecucion.py` 1.3.5) | M04 (`modulos/04` + `ddd_core/m04_seed_engine*`) | M05 canónico (`ddd_core/m05_opt_engine_v741.py` 7.4.4 + `modulos/05` 7.8.7) | Reparadores M05 (`m05_population_repair`, `m05_swap_polish`, `m05_private_annealing`) | GerryChain producción (`ddd_core/m05_gerrychain_strategy.py` 2.2.0) | GerryChain ensemble (`ddd_core/m05_gerrychain_engine.py` + `ddd_ensemble/`) |
|---|---|---|---|---|---|---|
| Suelo/techo | `ddd_core.config.hard_limits` (falla si el contrato no declara las razones) | `hard_limits` | `hard_limits` | `hard_limits` | razones propias: `step5.population_*_ratio` ▸ `validation.*` ▸ **0,80/1,75 por defecto** | **0,80/1,75 por defecto** en el dataclass; las pasa el adaptador |
| Exención de suelo | municipio y partición (`population_floor_exemptions`) | municipio | municipio y partición (`population_floor_exemptions`) | municipio (anclaje, 7.8.6) | municipio y partición, código propio | municipio y partición, código propio |
| K y cuotas por provincia | `expected_districts` + `province_districts` | sí | sí | — | `--expected-k`, `--province-quotas` | adaptador |
| Contigüidad | componentes sobre el grafo M03 | crecimiento conexo propio | movimientos que conservan conexión | sí (copias propias) | sí, propia | sí, propia |
| Disciplina municipal (R012) | mín ⌈P/techo⌉, máx ⌈P/objetivo⌉, **mixtos ≤ 1 fijo** | atomicidad por límite (`municipality_atomicity_limit_ratio`) | **solo mixtos** ≤ `max_mixed_districts_per_split_municipality`; no comprueba mín/máx | `private_annealing`: **mixtos ≤ 1 fijo**, sin mín/máx; el resto, nada | mín/máx/mixtos con `max_mixed…` del contrato | igual que producción, copia propia |
| Provincia | `require_single_province_per_district` | sí | sí | sí | campo de partición (`DDD_PARTITION` en islas) | adaptador |
| Atomicidad (`ddd_unit_id`) | unicidad de sección y conservación de población | crea las unidades | mueve unidades | unidades | opera sobre unidades colapsadas | ídem |
| Núcleos urbanos cerrados | — (no lo valida) | sí (`m04_closed_target_cores`) | sí | `swap_polish` | sí | sí |

## Diferencias que pueden dar resultados distintos

1. **Mixtos por municipio**: el validador fija 1; M05 canónico y GerryChain leen `max_mixed_districts_per_split_municipality`.
   Hoy los 120 contratos declaran 1, así que no diverge; si alguno declarase 2, los motores aceptarían soluciones que
   el validador rechaza.
2. **Mín/máx de distritos por municipio**: solo lo comprueban el validador y GerryChain; el canónico y sus reparadores
   no lo optimizan (lo confían a M04). Un FAIL por `min=`/`max=` saldría solo en la validación final.
3. **Razones por defecto**: GerryChain (las dos copias) usa 0,80/1,75 si falta la razón; `hard_limits` aborta
   (CONTRATO_TERRITORIO §5). Además GerryChain da prioridad a `step5` sobre `validation`: si difieren, optimiza contra
   un suelo/techo distinto del validado.
4. **Exenciones**: cuatro implementaciones (validador, canónico, GerryChain producción y ensemble) de la misma regla
   (municipio y partición); solo el validador, M04 y el canónico comparten `ddd_core/population_floor_exemptions`.
5. **Núcleos urbanos cerrados**: los respetan los motores, pero el validador no los comprueba.
6. **Dos GerryChain**: `m05_gerrychain_strategy` (producción, 1371 l.) y `m05_gerrychain_engine` (ensemble, 781 l.)
   duplican contrato, contigüidad y R012.

Propuesta técnica (para decidir): un único módulo de reglas (`ddd_core/reglas_contrato.py`) usado por el validador, M05
y los dos GerryChain, que lea del contrato `max_mixed…`, las razones y las exenciones. La batería (`bateria_motor.py`)
mediría el efecto antes de cambiar nada.
