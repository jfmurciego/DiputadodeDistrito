## 2026-11-10 — T-202 — Naturalidad: C y D8 en Castilla y León, Extremadura y Principado de Asturias

**Causa:** el laboratorio no corría en estas tres (municipios mixtos en el mapa vigente; unidades internas R012 del M06); requisito del relevo.
**Cambio:** `ddd_motor2/naturalidad_competicion.py` 1.4.0: contratos con `connected_internal_units` → municipio atómico hasta `atomicity_ratio` × objetivo y, por encima, la sección como unidad y clave R012 (aproximación más fina que los trozos de producción, irreproducibles sin el grafo M03 original); mapa vigente que incumple el núcleo (D-66) → A sigue siendo el vigente, marcado no válido, y C/D8 parten de un vigente reparado y solo eligen entre mapas válidos. `ddd_motor2/naturalidad_informe.py` 1.3.0: columna «valido» y marca en la tabla. Entregable en `docs/ESTUDIOS/T179_naturalidad_nacional/t202/`. Castilla y León: la reparación es factible (una sección de Ávila de un distrito mixto a otro); no se propone excepción. Producción no lo importa; sin huellas, workflows ni contratos.
**Pruebas:** `tests.test_motor2_naturalidad` (+ `test_reparar_vigente_con_dos_mixtos`), `GovernanceHeaders`.
**Riesgos:** ninguno en producción.
