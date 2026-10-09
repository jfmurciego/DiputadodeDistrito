# M05 — Optimizar distritos

**Versión documental:** 1.4.0
**Nombre de versión:** Wrapper 7.5.1 con fase C determinista opt-in
**Fecha:** 2026-09-11
**Código activo:** M05 v7.5.1
**Lógica optimizadora validada:** M05 v7.4.0 — GitHub Run #9 `34599224954`
**Baseline anterior:** M05 v7.3.0 — GitHub Run #8 `34592470470`
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.3.1.md`
**Cambio:** el wrapper activo incorpora una fase C opcional de swaps 1×1 deterministas después del motor v7.4.0, conservando el fallback robusto de identidad de v7.4.2. El operador permanece desactivado por defecto mediante `swap_polish_max: 0`.
**Motivo:** EXT-05 Run `34641298906` demostró que el candidato c020 de Extremadura queda en un mínimo local de movimientos simples pero dispone de 8 swaps 1×1 válidos que mejoran estrictamente el objetivo. R015 exige que esta evolución se documente sin confundir código activo con lógica ya promocionada.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Separación wrapper / motor
- `modulos/05_optimizar_distritos.py` v7.5.1 es la interfaz activa.
- `ddd_core/m05_opt_engine_v740.py` sigue siendo la copia exacta del optimizador v7.4.0 validado.
- `ddd_core/m05_swap_polish.py` añade exclusivamente la fase C determinista y está desacoplado del motor base.
- Si OGR puede leer `ddd_unit_id`, el wrapper delega primero al motor v7.4.0 sin transformar la entrada.
- Si OGR pierde el campo, lee las propiedades GeoJSON crudas, asigna códigos enteros estables a las unidades y ejecuta exactamente el motor v7.4.0.
- La configuración se resuelve siempre con `ddd_core.config.load_params_yaml`.
- El informe registra `unit_id_normalization` cuando se activa el fallback y `swap_polish` cuando la fase C está configurada.

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

No debe interpretarse el número de outliers de manera aislada. Un estado con cuatro distritos apenas fuera de tolerancia puede ser estructuralmente mejor que otro con dos outliers si uno de ellos tiene una desviación extrema. La comparación canónica completa es la referencia.

## Estrategia
**Fase A — greedy determinista:** acepta únicamente movimientos individuales que mantienen restricciones duras y mejoran estrictamente el objetivo.

**Fase B — recocido reproducible + refinamiento:** el ámbito se fija a las provincias que tenían distritos fuera de tolerancia al inicio de M05. Puede atravesar estados peores en el objetivo fino, nunca restricciones duras, conserva la mejor solución canónica y agota el presupuesto configurado.

**Fase C — swap-polish determinista, opt-in:** si `swap_polish_max > 0`, enumera swaps 1×1 entre unidades frontera de distritos vecinos, descarta los que violan provincia, suelo/techo, cierre urbano o contigüidad, elige el mejor que reduzca lexicográficamente el objetivo y repite hasta mínimo local o hasta el límite configurado. No acepta pasos neutrales ni peores.

## Evidencia validada previa — Aragón Run #9
Primera factibilidad, iteración 9.038: `[0, 0.0, 0, 0.119431695687, 0.182704485064]`.

Resultado final: `[0, 0.0, 0, 0.099299365905, 0.161271162560]`.

Máximo desvío: 11,943 % → **9,930 %**; `fuera_12=0`; restricciones duras PASS.

## Evidencia experimental — Extremadura
EXT-04 estableció `chunk_ratio=0.20` como primer tamaño de macro-unidad interna probado que permite a M04 construir K=65 con cuotas 41/24 y `hard=0`. Después de M05 sin fase C, el máximo desvío baja de 36,79 % del enfoque por sección a aproximadamente 13,30 %, con cuatro outliers leves y menor churn.

EXT-05 Run `34641298906` encontró 8 swaps 1×1 estrictamente mejores sobre ese estado, varios de ellos internos al municipio real de Plasencia (`10148`). Esa evidencia justifica probar una fase C, pero no constituye todavía promoción multi-territorio.

## Estado de validación
- La lógica base v7.4.0 permanece validada/promocionada por Run #9.
- El wrapper v7.5.1 es **candidato**. Con `swap_polish_max: 0` debe reproducir los baselines anteriores.
- La fase C permanece **opt-in y experimental** hasta que EXT-06 cierre correctamente y R015 vuelva a PASS completo.
- No se promueve el swap-polish por defecto mientras esas dos condiciones no se cumplan.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- Informe M05 con objetivos, movimientos, primera factibilidad, parámetros, mapeo de normalización cuando proceda y metadatos de swaps cuando la fase C esté activa.

## Baseline vigente
**Aragón Run #9 `34599224954` / `gh-34599224954-1`.** Toda evolución debe mantener sus PASS. Castilla y León añade una segunda regresión territorial válida. M05 v7.3.0 y Run #8 permanecen registrados como baseline histórico previo.
