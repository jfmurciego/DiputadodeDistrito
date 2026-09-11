# M05 — Optimizar distritos

**Versión documental:** 1.2.0
**Nombre de versión:** R016 validado — refinamiento canónico post-factibilidad
**Fecha:** 2026-09-11
**Código ejecutado y validado:** M05 v7.4.0 — GitHub Run #9 `34599224954`
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.1.0.md`
**Cambio:** promociona la estrategia v7.4.0 tras demostrar mejora real sobre Run #8 sin regresiones territoriales.
**Motivo:** Run #9 confirma que continuar después de la primera factibilidad reduce el máximo desvío y el error cuadrático manteniendo todas las restricciones.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Restricciones duras
1. 67 distritos;
2. Huesca 11 / Teruel 7 / Zaragoza 49;
3. provincia infranqueable;
4. contigüidad estricta por M03;
5. población entre 0,80×target y 1,75×target;
6. movimientos de `ddd_unit_id` completas;
7. distritos `ddd_closed_urban` no reciben ni ceden unidades;
8. disciplina municipal final preservada.

## Objetivo canónico
Comparación lexicográfica: violaciones duras → magnitud dura → número fuera de ±12 % → máximo desvío → error cuadrático global.

## Estrategia validada v7.4.0
**Fase A — greedy determinista:** acepta únicamente movimientos individuales que mantienen restricciones duras y mejoran estrictamente el objetivo. No se detiene por el mero hecho de llegar a `fuera_12=0`.

**Fase B — recocido reproducible + refinamiento:** el ámbito se fija a las provincias que tenían distritos fuera de ±12 % al inicio de M05. El recocido puede atravesar estados peores en el objetivo fino, nunca restricciones duras, conserva continuamente la mejor solución canónica y agota el presupuesto configurado para intentar reducir el máximo desvío y el error cuadrático.

El reporte registra `first_feasible_iteration`, `objective_first_feasible` y `post_feasible_iterations`, permitiendo demostrar cuánto trabajo se realiza después de alcanzar por primera vez ±12 %.

## Evidencia Run #9

Primera factibilidad, iteración 9.038:

`[0, 0.0, 0, 0.119431695687, 0.182704485064]`

Resultado final tras 20.000 iteraciones:

`[0, 0.0, 0, 0.099299365905, 0.161271162560]`

Mejora:
- máximo desvío: 11,943 % → **9,930 %**;
- error cuadrático: 0,182704485064 → **0,161271162560**;
- `fuera_12=0` se conserva;
- todas las restricciones duras permanecen PASS.

Solo cambian 12 distritos respecto de Run #8, todos en Zaragoza. El peor Zaragoza termina en +9,140 %. El máximo global pasa a Huesca (-9,930 %), provincia que R016 no modifica.

## Estado de la cabecera del ejecutable
El fichero `modulos/05_optimizar_distritos.py` conserva la etiqueta de publicación `candidato R016`. No se reescribe después de haber sido probado únicamente para cambiar esa palabra, porque eso alteraría el blob validado. El estado canónico vigente de v7.4.0 es **VALIDADO / PROMOCIONADO por Run #9**.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- `M05/asignacion_optimizada.csv` con las 1.463 secciones.
- `aragon_2025_m05_informe.json` con objetivos, métricas, movimientos, primera factibilidad, unidades finales cambiadas, provincia activa, semilla y parámetros.

## Baseline vigente
**Run #9 `34599224954` / `gh-34599224954-1`.** Toda evolución de M05 debe demostrar que mantiene sus PASS y mejora un objetivo territorial explícitamente definido.
