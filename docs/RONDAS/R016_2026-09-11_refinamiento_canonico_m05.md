# R016 — Refinamiento canónico post-factibilidad en M05

**Fecha:** 2026-09-11
**Tipo:** cambio funcional controlado en M05
**Baseline de entrada:** Run #8 `34592470470` / R014
**Estado final:** **VALIDADO Y PROMOCIONADO**
**Baseline de salida:** Run #9 `34599224954`

## Problema
M05 declara como objetivo canónico: restricciones duras → número fuera de ±12 % → máximo desvío → error cuadrático. Sin embargo, v7.3.x interrumpía greedy y recocido en cuanto aparecía una solución con `hard=0` y `fuera_12=0`. En Run #8 esa primera factibilidad llegó en la iteración 9.038 y se convirtió automáticamente en resultado final.

## Cambio aplicado
1. se preservó M05 v7.3.1 en `legacy/`;
2. se publicó M05 v7.4.0;
3. greedy dejó de detenerse únicamente por alcanzar ±12 %;
4. el ámbito de recocido se fija a las provincias problemáticas al inicio;
5. el recocido no se detiene al primer ±12 %, sino que agota `anneal_iters`;
6. se conserva siempre la mejor solución según el objetivo canónico;
7. se registran primera factibilidad y refinamiento posterior.

## Lo que NO cambió
K=67; reparto 11/7/49; provincia infranqueable; contigüidad; suelo 0,80; techo 1,75; tolerancia ±12 %; atomicidad `ddd_unit_id`; cierres urbanos; semilla 12345; parámetros de recocido; M04 y configuración Aragón.

## Evidencia de aceptación — Run #9
GitHub Run `34599224954` terminó SUCCESS sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`.

Primera solución factible, iteración 9.038:

`[0, 0.0, 0, 0.119431695687, 0.182704485064]`

Resultado final, iteración 20.000:

`[0, 0.0, 0, 0.099299365905, 0.161271162560]`

La mejora posterior a la primera factibilidad es real:
- máximo desvío: 11,943 % → **9,930 %**;
- reducción relativa del máximo desvío: **16,9 %**;
- error cuadrático: 0,182704485064 → **0,161271162560**;
- reducción del error cuadrático: **11,7 %**;
- `fuera_12=0` permanece en 0.

## Alcance territorial del cambio
Solo cambian 12 distritos respecto de Run #8 y todos están en Zaragoza. El peor Zaragoza pasa de +11,943 % a +9,140 %. Huesca y Teruel quedan exactamente iguales. El máximo global final pasa a ser Huesca distrito 0, con -9,930 %.

## Validación dura
PASS:
- 67 distritos;
- 1.463 secciones;
- 1.364.621 habitantes;
- Huesca 11 / Teruel 7 / Zaragoza 49;
- 0 cruces provinciales;
- 0 desconectados;
- 0 infracciones municipales;
- 0 bajo suelo;
- 0 sobre techo;
- 0 fuera de ±12 %.

## Veredicto
**R016 PROMOCIONADO.** Run #9 sustituye a Run #8 como referencia territorial. Cualquier R017 debe conservar estos PASS y demostrar una mejora territorial explícita; no se seguirá optimizando únicamente por reducir números sin definir antes qué calidad se pretende mejorar.
