# M05 — Optimizar distritos

**Versión documental:** 1.3.0
**Nombre de versión:** Wrapper robusto multi-territorio sobre optimizador validado
**Fecha:** 2026-09-11
**Código activo:** M05 v7.4.1
**Lógica optimizadora validada:** M05 v7.4.0 — GitHub Run #9 `34599224954`
**Baseline anterior:** M05 v7.3.0 — GitHub Run #8 `34592470470`
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.2.1.md`
**Cambio:** el ejecutable activo pasa a wrapper v7.4.1, que delega la optimización sin cambios en el motor congelado v7.4.0 y solo normaliza `ddd_unit_id` cuando OGR lo descarta por tipado GeoJSON StringList.
**Motivo:** permitir entradas multi-territorio robustas sin modificar el algoritmo ya validado en Aragón y Castilla y León.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Separación wrapper / motor
- `modulos/05_optimizar_distritos.py` v7.4.1 es la interfaz activa.
- `ddd_core/m05_opt_engine_v740.py` es una copia exacta del optimizador v7.4.0 validado.
- Si OGR puede leer `ddd_unit_id`, v7.4.1 delega directamente y no transforma la entrada.
- Si OGR pierde ese campo, el wrapper lee las propiedades GeoJSON crudas, asigna códigos enteros estables a las unidades y ejecuta exactamente el mismo motor.
- El informe registra `unit_id_normalization` cuando se activa el fallback.

## Restricciones duras
1. K y cuotas definidos por el territorio;
2. provincia infranqueable;
3. contigüidad estricta por M03;
4. suelo/techo poblacional configurado;
5. movimientos de `ddd_unit_id` completas;
6. distritos `ddd_closed_urban` no reciben ni ceden unidades;
7. disciplina municipal final auditada contra `municipality_field` real.

## Objetivo canónico
Comparación lexicográfica: violaciones duras → magnitud dura → número fuera de tolerancia → máximo desvío → error cuadrático global.

## Estrategia validada v7.4.0
**Fase A — greedy determinista:** acepta únicamente movimientos individuales que mantienen restricciones duras y mejoran estrictamente el objetivo.

**Fase B — recocido reproducible + refinamiento:** el ámbito se fija a las provincias que tenían distritos fuera de tolerancia al inicio de M05. Puede atravesar estados peores en el objetivo fino, nunca restricciones duras, conserva la mejor solución canónica y agota el presupuesto configurado.

## Evidencia Aragón Run #9
Primera factibilidad, iteración 9.038:
`[0, 0.0, 0, 0.119431695687, 0.182704485064]`

Resultado final tras 20.000 iteraciones:
`[0, 0.0, 0, 0.099299365905, 0.161271162560]`

Máximo desvío: 11,943 % → **9,930 %**; `fuera_12=0`; restricciones duras PASS.

## Estado de validación
- La lógica v7.4.0 permanece validada/promocionada por Run #9.
- El wrapper v7.4.1 es candidato multi-territorio hasta que R015 confirme regresión idéntica y EXT-03 demuestre el fallback sobre una entrada que OGR no puede leer directamente.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- Informe M05 con objetivos, movimientos, primera factibilidad, parámetros y, cuando proceda, mapeo de normalización de unidades.

## Baseline vigente
**Aragón Run #9 `34599224954` / `gh-34599224954-1`.** Toda evolución debe mantener sus PASS. Castilla y León añade una segunda regresión territorial válida.
