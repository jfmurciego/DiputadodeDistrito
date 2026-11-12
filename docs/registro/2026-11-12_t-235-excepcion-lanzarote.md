## 2026-11-12 — T-235 — Exención de techo de Lanzarote y La Graciosa en el contrato 2026 de Las Palmas (D-83)

**Causa.** Con el padrón INE 2025, Lanzarote y La Graciosa (partición 35-G01, un solo distrito) suman 166.878 hab., es
decir, 1,424 veces la media (117.154,7). El techo es 1,40. El distrito es la isla entera, así que no hay otra
partición posible: M04 paraba con `INCOMPATIBLE_ATOMIC_POPULATION` (T-225). Solo existían exenciones de suelo.

**Cambio.**
- `ddd_core/population_cap_exemptions.py` 1.0.0 (nuevo): es la única regla que leen M04, M05, M06 y el validador.
  `validation.population_cap_exempt_partitions` solo se admite para una partición con K=1 en `province_districts` y
  con decisión en `population_cap_exempt_partition_decisions` (decided_at, decided_by=propietario, decision, reason,
  evidence). Cualquier otro uso es un error. Sin la clave, el techo es el general.
- Contrato `congreso_las_palmas_2026.yaml` 1.0.1: exención solo de 35-G01 (decisión D-83). El techo general sigue en 1,40.
- M04 7.6.8 (`ddd_core/m04_seed_engine.py`, `configuracion/m04_engine.json`): el preflight aplica el techo efectivo
  de cada partición.
- M05: wrapper `modulos/05` 7.8.8 y motor base 7.4.5 (`m05_opt_engine_v741.py`). Techo por distrito en el objetivo, en
  los estados y en el informe (`cap_exempt`). El distrito exento queda fuera de la reparación, porque es fijo.
- M06 7.2.4: `within_hard_bounds` y `population_status` con el techo efectivo (columna `population_cap_exempt`).
- `validar_ejecucion.py` 1.3.6: `above_cap` recalcula sobre las secciones qué distritos están exentos.
- `comprobar_exenciones_gobernadas.py` 1.1.0: aplica la misma regla a todos los contratos.
- motor2 (`ddd_motor2/reglas`): `modelo` 1.1.0 añade `Reglas.exentas_techo`, leída con la misma función. Si el
  contrato no es admisible, da `ErrorContrato`; sin exención, la forma canónica y la huella de las reglas no cambian.
  `evaluar` 1.2.0 añade `exento_de_techo`: el distrito exento no da R-POB-TECHO ni R-TOL por exceso. `enumerar` 1.3.0
  aplica la misma regla en la poda.

**Pruebas.**
- `tests/test_exencion_techo_particion.py` (14, tres de ellos de motor2). Casos: sin la clave no cambia nada; K>1 se rechaza; también una
  partición desconocida o una decisión que falta, está incompleta o no es del propietario; la exención vale solo para
  el distrito de la partición; en el contrato de Las Palmas 2026 solo está exenta 35-G01, con el techo en 1,40; el
  validador y el comprobador de exenciones.
- En local, ejecución real de M04-M06 y del validador con la batería, con entradas desde la fuente versionada:
  - Las Palmas 2026 pasa de `FALLO_M04` a `PASS`. El distrito 9 (35-G01) queda en PASS con `cap_exempt` y la
    reparación en `NOT_NEEDED`.
  - Composición M06 idéntica bit a bit (sha256) antes y después del cambio en `congreso_huesca`,
    `congreso_la_rioja`, `la_rioja`, `congreso_santa_cruz_de_tenerife` (2025 y 2026) y `congreso_las_palmas` 2025.
- motor2: competición D8 con `--cadenas 1` y las mismas entradas en `main` y en la rama. `huella_resultado` es idéntica
  en los cinco territorios anteriores. Las Palmas 2026 queda VÁLIDO.
- Tests de gobernanza, motor2, huellas, N08, exenciones, M04/M05/M06, validador y T-225: OK.

**Efectos.** Cambian las huellas M04, M05, M06 y motor2 (`ddd_core/config` no cambia). La huella de reglas de motor2
solo cambia con exención declarada. Los checkpoints M04/M05 previos quedan invalidados. Las Palmas 2026 se genera con la 00 «Generar desde
fuente territorial acreditada». Los demás territorios no cambian de mapa.
