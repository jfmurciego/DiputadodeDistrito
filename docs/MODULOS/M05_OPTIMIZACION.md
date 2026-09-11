# M05 — Optimizar distritos

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

## Estrategia v7.3.0
**Fase A — greedy determinista:** solo movimientos individuales que mantienen restricciones y mejoran estrictamente el objetivo.

**Fase B — escape de mínimo local:** si queda desequilibrio ±12 %, recocido simulado reproducible limitado a la provincia afectada. Puede atravesar estados temporalmente peores en el objetivo fino, pero jamás una restricción dura. Conserva continuamente la mejor solución canónica y exporta esa mejor solución, no el último estado explorado.

La energía de exploración y el churn son mecanismos de búsqueda, no sustituyen el objetivo canónico ni las validaciones.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- `M05/asignacion_optimizada.csv` con las 1.463 secciones.
- `aragon_2025_m05_informe.json` con objetivos, métricas, movimientos, unidades finales cambiadas, provincia activa, semilla y parámetros.

## Aceptación
Toda transición preserva restricciones duras; el producto final debe superar la puerta global. Una ejecución local es diagnóstico. La aceptación corresponde a GitHub Actions reproducible.

## Estado validado
**Run #8 `34592470470` valida M05 v7.3.0 / R014.**

Partiendo del mismo estado problemático de Run #7:
- objetivo inicial: `fuera_12=1`, `max_rel_dev=0.549676430306`;
- objetivo final: **`fuera_12=0`, `max_rel_dev=0.119431695687`**;
- `hard=0`;
- 1.030 movimientos de recocido aceptados;
- 75 unidades finalmente modificadas;
- 9.038 iteraciones ejecutadas;
- 0 cruces provinciales, 0 desconectados y 0 violaciones municipales en validación final.

R014 queda cerrado. Cualquier modificación posterior de M05 abre una nueva versión/ronda y debe mantener como regresión obligatoria todos los PASS de Run #8.
