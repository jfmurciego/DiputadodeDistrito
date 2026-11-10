## 2026-11-10 — T-166 — La 00 hija «Reutilizar» planifica con un M08 sin linaje y completa la 04

**Causa.** Tras activar el par, «Encadenar par de fuentes y 04» lanza una 00 «Reutilizar» como github-actions[bot]. El
catálogo conserva un M08 de una 04 fallida (runs 41037133327 Cantabria y 41042675119 Extremadura: fase 04 sin digest);
`validate_durable_assets` lo daba por bloqueo y la hija fallaba siempre en «Planificar ejecución completa» con
`CONTINUE_DURABLE_BLOCK … DURABLE_LINEAGE_INCOMPATIBLE: electoral_product` (runs 42651881625, 42720255020, 42737598841).
Las 00 madre quedaron TERRITORIAL_COMPLETE con el eslabón electoral sin hacer.

**Cambio.** `resolver_activos_durables.py` 1.2.0: si la fase 04 del manifiesto no enlaza el M08 del catálogo o no es una
fase productora válida, el M08 se rechaza (`rejected_electoral_product`, `reusable=false`, igual que otros desajustes de
linaje) y la 00 lo reincorpora; el receipt o manifiesto ilegible o ajeno sigue bloqueando. Sin cambios en el workflow, el
motor, las huellas ni `ddd_core`. Se descarta la guarda previa en el encadenado (habría dejado la 04 sin hacer).

**Pruebas.** `tests/test_t166_cadena_m08_linaje.py` con fixtures congeladas de los tres runs
(`tests/fixtures/t166_encadenado_m08/`): antes `build_plan` lanzaba el error; ahora planifica con `run_incorporate=true`,
`run_generate=false` y el M08 rechazado. Además: la captura está acotada (04 en success con digest ajeno o no
validada sigue bloqueando) y al registrarse un M08 nuevo sustituye al rechazado y no se reincorpora. Sin regresión en
`test_reanudacion_m08_huerfano` (T-91b), `test_huerfano_recibo_declarado`, `test_m06_durable_manifest`,
`test_continuar_ultimo_resultado_valido` y `test_ejecucion_completa`.

**Riesgos.** La 04 se vuelve a ejecutar para esos territorios (es el objetivo). El catálogo sigue apuntando al M08 viejo
hasta que la 04 registre el nuevo. No se ha lanzado ninguna ejecución.
