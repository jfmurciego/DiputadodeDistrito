# R016 — Refinamiento canónico post-factibilidad en M05

**Fecha:** 2026-09-11
**Tipo:** cambio funcional controlado en M05
**Baseline protegido:** Run #8 `34592470470` / R014
**Estado inicial:** candidato, pendiente de CI y ejecución territorial

## Problema
M05 declara como objetivo canónico: restricciones duras → número fuera de ±12 % → máximo desvío → error cuadrático. Sin embargo, v7.3.x interrumpe tanto el greedy como el recocido en cuanto aparece una solución con `hard=0` y `fuera_12=0`. En Run #8 esa primera factibilidad llegó en la iteración 9.038 y se convirtió automáticamente en resultado final, por lo que nunca se comprobó si las iteraciones restantes podían reducir el 11,943 % máximo.

## Cambio mínimo
1. conservar M05 v7.3.1 en `legacy/`;
2. publicar M05 v7.4.0;
3. no detener greedy solo por alcanzar ±12 %;
4. fijar el ámbito de recocido a las provincias que eran problemáticas al inicio de M05;
5. no detener recocido al primer ±12 %, sino agotar `anneal_iters`;
6. conservar siempre la mejor solución según el objetivo canónico;
7. registrar primera factibilidad y refinamiento posterior.

## Lo que NO cambia
K=67; reparto 11/7/49; provincia infranqueable; contigüidad; suelo 0,80; techo 1,75; tolerancia ±12 %; atomicidad `ddd_unit_id`; cierres urbanos; semilla 12345; parámetros de recocido; M04 y configuración Aragón.

## Hipótesis
Con el mismo espacio de búsqueda y el mismo presupuesto de 20.000 iteraciones, permitir que M05 continúe después de la primera factibilidad puede encontrar una solución lexicográficamente mejor que Run #8 sin necesidad de relajar ninguna regla.

## Criterio de aceptación
- CI R015 PASS;
- prueba R016 PASS y determinista;
- nuevo procedimiento territorial PASS;
- `fuera_12=0`;
- `objective_final <= objective_first_feasible`;
- preferentemente `max_rel_dev < 0.119431695687` o, si empata, menor error cuadrático;
- cero regresiones en provincia, contigüidad, municipio, suelo/techo, secciones o población.

Si no existe mejora real o aparece degradación territorial, R016 se rechaza y M05 v7.3.1/Run #8 continúa como baseline.
