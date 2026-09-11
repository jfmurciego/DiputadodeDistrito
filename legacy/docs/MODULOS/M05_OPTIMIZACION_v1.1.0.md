# M05 — Optimizar distritos

**Versión documental:** 1.1.0
**Nombre de versión:** Candidato R016 — refinamiento canónico post-factibilidad
**Fecha:** 2026-09-11
**Código activo:** M05 v7.4.0 — candidato
**Última lógica territorial validada:** M05 v7.3.0 — GitHub Run #8 `34592470470`
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.0.0.md`
**Cambio:** elimina la parada al primer `fuera_12=0` y permite continuar optimizando los siguientes términos de la función canónica.
**Motivo:** v7.3.x declaraba una función lexicográfica completa pero interrumpía la búsqueda en cuanto satisfacía el tercer término.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Restricciones duras R012
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

## Estrategia candidata v7.4.0
**Fase A — greedy determinista:** sigue aceptando únicamente movimientos individuales que mantienen restricciones duras y mejoran estrictamente el objetivo. Ya no se detiene por el mero hecho de llegar a `fuera_12=0`; continúa mientras exista una mejora canónica individual.

**Fase B — recocido reproducible + refinamiento:** el ámbito se fija a las provincias que tenían distritos fuera de ±12 % al inicio de M05. El recocido puede atravesar estados peores en el objetivo fino, nunca restricciones duras, conserva continuamente la mejor solución canónica y ya no se detiene en la primera solución factible. Agota el presupuesto configurado para intentar reducir después el máximo desvío y el error cuadrático.

El reporte añade `first_feasible_iteration`, `objective_first_feasible` y `post_feasible_iterations`, de modo que se pueda demostrar cuánto trabajo se realizó después de alcanzar por primera vez ±12 %.

## Principio de prudencia
R016 **no reduce el umbral ±12 %**, no modifica suelo/techo, no cambia provincia, atomicidad municipal ni contigüidad, y no introduce compactness como objetivo. El candidato solo corrige la incoherencia entre función objetivo declarada y criterio de parada.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- `M05/asignacion_optimizada.csv` con las 1.463 secciones.
- `aragon_2025_m05_informe.json` con objetivos, métricas, movimientos, primera factibilidad, unidades finales cambiadas, provincia activa, semilla y parámetros.

## Aceptación R016
1. `Pruebas DDD — R015` debe permanecer verde.
2. La prueba específica R016 debe demostrar búsqueda posterior a primera factibilidad y determinismo.
3. Un nuevo run territorial debe conservar todos los PASS del Run #8.
4. `fuera_12` debe seguir en 0.
5. `objective_final` debe ser lexicográficamente igual o mejor que `objective_first_feasible`; para justificar promoción se espera mejora real en `max_rel_dev` o error cuadrático sin regresión territorial.

Hasta ese run, **Run #8 sigue siendo la referencia territorial** y M05 v7.4.0 es candidato, no baseline.
