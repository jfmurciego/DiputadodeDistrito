# NAT-G-002 — Minimalidad municipal: alcance local y contraejemplo global

## Hallazgo

El certificado `_topological_municipal_minimum` de M05 prueba si una división municipal puede reducirse manteniendo fijas las asignaciones de todas las demás CUSEC. No demuestra un óptimo global. El resultado ahora lo declara con `proof_scope=OTHER_CUSEC_ASSIGNMENTS_FIXED` y `global_minimality_proven=false`.

## Fixture mínimo reproducible

Grafo lineal de cuatro CUSEC y cuatro habitantes, con cotas por distrito `[1, 3]` y `K=2`:

```text
u0 — u1 — u2 — u3
M      X    M      Y
```

`u0` y `u2` pertenecen al mismo municipio M. La asignación inicial `A={u0}`, `B={u1,u2,u3}` produce poblaciones `(1,3)`, mantiene ambos distritos conectados y divide M en dos. Con las otras asignaciones fijas, colocar ambos CUSEC de M en A deja B desconectado; colocarlos en B vacía A. El certificado local puede, por tanto, justificar dos distritos **solo bajo ese estado fijo**.

Existe una reasignación simultánea válida: `A={u0,u1,u2}`, `B={u3}`. Las poblaciones siguen dentro de cotas (`3,1`), ambos distritos están conectados y M queda íntegro. La división no es globalmente necesaria.

## Corrección y pruebas

El reparador ahora considera una mejora del término principal de fragmentación municipal aun cuando el objetivo poblacional blando no cambie. Antes de aceptar un estado final, valida de forma independiente todos los invariantes y rechaza candidatos que todavía contengan una división municipal reducible. La búsqueda puede conservar estados intermedios y continuar hasta una reasignación válida.

`tests/test_m05_population_repair.py::test_fixed_assignment_minimum_is_not_claimed_as_global_minimum` comprueba el alcance del certificado, la alternativa global, y que `repair()` la encuentra con `max_transfer_set=2`. El ensayo real devuelve `IMPROVED_NOT_REPAIRED` porque mantiene outliers del objetivo blando; la partición final es estructuralmente válida, satisface cotas, y no divide M. Esto no es un producto territorial ni una certificación.

La búsqueda M05 sigue siendo acotada y heurística. No se afirma `PROVEN_MINIMAL` global ni imposibilidad fuera del fixture exhaustivo. Si no encuentra alternativa dentro de presupuesto, el estado es de búsqueda limitada, no una prueba de minimalidad global.

## Reproducción

```bash
python -m pytest -q tests/test_m05_population_repair.py
```

El incremento no cambia K, cotas, política municipal, identidad CUSEC ni la política autonómica predeterminada.
