# M05 — Reparación poblacional genérica

## Inventario de la implementación previa

El motor base conserva tres fases. La fase A admite transferencias individuales de unidades indivisibles de frontera únicamente si preservan las restricciones duras y mejoran estrictamente el objetivo. La fase B usa búsqueda estocástica reproducible dentro del espacio duro válido y conserva el mejor estado encontrado. La fase C, opt-in, enumera intercambios 1×1 entre unidades frontera de dos distritos vecinos y acepta únicamente mejora lexicográfica estricta. No existía búsqueda 2×2 explícita; podía aparecer composición de movimientos en la fase estocástica, pero no como operador certificado independiente.

La contigüidad se comprueba sobre el grafo M03 para donante y receptor. Las unidades `ddd_unit_id` son indivisibles. La provincia es infranqueable y los distritos cerrados no ceden ni reciben. La disciplina municipal se audita sobre las unidades territoriales y el campo municipal configurado. El objetivo previo es lexicográfico: violaciones duras, magnitud de la violación dura, número de distritos fuera de tolerancia, máximo desvío y error cuadrático global. Las fases deterministas paran al no encontrar mejora o al agotar su máximo de operaciones; la fase estocástica agota su presupuesto configurado y conserva el mejor estado.

## Motor escalonado

`ddd_core/m05_population_repair.py` añade una búsqueda genérica posterior al motor base y al pulido existente. El espacio de estados está formado por asignaciones completas de unidades indivisibles a distritos. Los sucesores son transferencias de conjuntos fronterizos conectados. La exploración en anchura permite representar, con el mismo operador elemental, transferencias simples, intercambios de dos distritos y cadenas entre tres o más distritos vecinos. El tamaño de cada conjunto y la profundidad de la cadena están acotados.

La función objetivo del reparador es lexicográfica: (1) violaciones de límites duros; (2) número de distritos fuera de tolerancia; (3) desviación relativa máxima; (4) desviación relativa total; (5) penalización de cohesión. El baseline solo se sustituye si el vector completo mejora estrictamente. Por tanto, una solución peor nunca reemplaza el estado inicial y el número de outliers no aumenta en el resultado aceptado.

## Restricciones duras

Se preservan el número exacto de distritos, provincia de cada unidad, contigüidad de donantes y receptores, indivisibilidad de unidades, integridad de grupos municipales, suelo y techo poblacionales existentes y prohibición de transferencias entre provincias. El reparador no modifica tolerancias, cuotas, contratos ni geometría posterior.

## Configuración genérica

La integración es opt-in bajo `modulo_05_optimizar_distritos.population_repair`. Sus parámetros son `enabled`, `max_depth`, `max_transfer_set`, `max_candidates`, `max_seconds` y `seed`. Los valores por defecto del objeto de límites son profundidad 3, conjunto 2, 5000 candidatos, 5 segundos y semilla 0. Ninguno depende de un territorio.

## Evidencia

Cada ejecución devuelve `ddd.m05-population-repair/1.0`, situación poblacional y objetivo antes/después, asignación final, reparaciones aceptadas, unidades y distritos afectados, restricciones verificadas, rechazos muestreados con motivo, presupuesto efectivo y si se conservó el baseline. Los resultados son `REPAIRED`, `IMPROVED_NOT_REPAIRED` y `NO_FEASIBLE_REPAIR_FOUND`. El último significa exclusivamente que no se encontró reparación dentro del presupuesto de búsqueda; no afirma inexistencia matemática de solución.

## Complejidad y límites

Sea B el número de conjuntos fronterizos candidatos por estado y D la profundidad máxima. La exploración tiene cota combinatoria O(B^D), por lo que se corta adicionalmente por `max_candidates` y `max_seconds`. `max_transfer_set` limita la generación combinatoria de conjuntos conectados. La semilla fija el orden reproducible de pares de distritos; la aceptación sigue siendo determinista para la misma entrada y configuración.
