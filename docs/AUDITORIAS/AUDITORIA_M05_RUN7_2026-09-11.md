# Auditoría M05 — Run #7 `34588834266`

**Fecha:** 2026-09-11  
**Objeto:** explicar por qué M05 v7.2.0 aceptó 0 movimientos aunque M04 v7.3.0 dejó un distrito fuera del objetivo fino ±12 %.  
**Fuentes:** artefactos M03 y M04 del Run #7, `resultados/ejecuciones/gh-34588834266-1/M05/`, código `modulos/05_optimizar_distritos.py` v7.2.0.

## 1. Hallazgo principal
M05 **no carece de candidatos**. Reproduciendo exactamente la construcción de `uadj` y `candidates()` sobre los artefactos del Run #7 aparecen 1.276 relaciones candidatas globales; 74 implican al distrito 56.

El distrito problemático es el **56 (Zaragoza)**: 31.563 habitantes, frente a target 20.367,48 y banda fina [17.923,38; 22.811,57]. Está dentro del techo duro 1,75×target, por lo que R012 es PASS, pero excede el +12 %.

## 2. Composición del distrito 56
El distrito está formado por 10 unidades municipales completas:

- Alagón: 7.520
- Alcalá de Ebro: 245
- Figueruelas: 1.310
- Gallur: 2.648
- Mallén: 3.059
- Novillas: 508
- Pedrola: 3.843
- Pinseque: 4.597
- Remolinos: 1.021
- Tauste: 6.812

Total: 31.563.

## 3. Por qué el greedy queda bloqueado
M05 v7.2.0 solo acepta un movimiento si la nueva tupla lexicográfica es estrictamente mejor:

`(violaciones_duras, magnitud_dura, distritos_fuera_12, max_desvio, error_cuadratico)`.

Los movimientos salientes del distrito 56 que sí mantienen conectado al donante son, entre los observados directamente:

- Gallur (2.648) → distrito 55;
- Mallén (3.059) → distrito 55;
- Pinseque (4.597) → distrito 63.

Todos reducen con fuerza el exceso del distrito 56, pero hacen que el receptor pase temporalmente fuera del ±12 %. Por tanto `distritos_fuera_12` pasa de 1 a 2 y el movimiento se rechaza antes de considerar la mejora de `max_desvio` o del error cuadrático.

Existen movimientos pequeños que mejorarían la tupla poblacional manteniendo `fuera_12=1` —por ejemplo Alcalá de Ebro, Figueruelas o Remolinos hacia determinados vecinos—, pero al retirar esas unidades el distrito 56 queda desconectado, por lo que la guarda de contigüidad los rechaza correctamente.

**Conclusión:** M05 está atrapado en un mínimo local generado por la combinación de (a) movimientos atómicos de una sola unidad y (b) aceptación estrictamente monótona de la función lexicográfica. No es un defecto de M03, M04 ni de las adyacencias.

## 4. Implicación algorítmica
Para llegar a `fuera_12=0` es necesario permitir una secuencia temporal de redistribución: el excedente del distrito 56 debe entrar primero en un vecino y después propagarse hacia otros distritos. La solución intermedia puede tener 2 o más distritos fuera del ±12 %, aunque el resultado final mejore la función objetivo canónica.

No deben relajarse:
- provincia;
- suelo/techo duro;
- contigüidad;
- unidades `ddd_unit_id`;
- distritos urbanos cerrados;
- disciplina municipal final.

## 5. Propuesta para M05 v7.3.0
Mantener la función lexicográfica como criterio de **mejor solución** y de aceptación final, pero separar de ella la función de **exploración**. Cuando el greedy queda bloqueado, ejecutar una fase determinista de recocido simulado dentro de las provincias que todavía contienen distritos fuera de ±12 %:

1. nunca aceptar un estado que viole suelo/techo, provincia o contigüidad;
2. explorar con una energía continua basada en error cuadrático, número de distritos fuera de tolerancia y máximo desvío;
3. usar semilla fija y enfriamiento parametrizado;
4. conservar durante toda la búsqueda la mejor solución según la función lexicográfica original;
5. finalizar devolviendo esa mejor solución, nunca el último estado explorado;
6. detener la fase de escape cuando se alcance `fuera_12=0`.

Una simulación diagnóstica sobre los artefactos exactos del Run #7 demuestra que este mecanismo puede alcanzar `hard=0` y `fuera_12=0` sin romper contigüidad, provincia ni disciplina municipal. Esta simulación **no sustituye una ejecución GitHub** y no constituye todavía referencia arbitral.

## 6. Veredicto
**Causa raíz confirmada en M05 v7.2.0: estrategia de búsqueda greedy atrapada en mínimo local.**

El siguiente cambio debe hacerse en M05, no en M04.
