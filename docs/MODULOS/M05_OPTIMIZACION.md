# M05 — Optimizar distritos

**Versión documental:** 1.4.1
**Nombre de versión:** Contrato de informe con motor y wrapper separados
**Fecha:** 2026-09-11
**Código activo:** M05 v7.5.2
**Lógica optimizadora validada:** M05 v7.4.0 — GitHub Run #9 `34599224954`
**Baseline anterior:** M05 v7.3.0 — GitHub Run #8 `34592470470`
**Anterior:** `legacy/docs/MODULOS/M05_OPTIMIZACION_v1.4.0.md`
**Cambio:** mantiene la fase C opt-in de v7.5.1, pero formaliza la semántica del informe: `version` identifica el motor optimizador que produjo el informe y `wrapper_version` identifica la interfaz/orquestador activo.
**Motivo:** R015 Run `34642133611` confirmó que la integridad de la evidencia publicada y el determinismo pasan, pero detectó que v7.5.1 sobrescribía `version=7.4.0` con la versión del wrapper. El test R016 usa correctamente ese campo para identificar la lógica optimizadora validada.

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional sin violar ninguna regla estructural. M04 construye una solución válida; M05 explora mejores soluciones dentro del espacio duro válido.

## Separación wrapper / motor
- `modulos/05_optimizar_distritos.py` v7.5.2 es la interfaz activa.
- `ddd_core/m05_opt_engine_v740.py` sigue siendo la copia exacta del optimizador v7.4.0 validado.
- `ddd_core/m05_swap_polish.py` v1.0.1 añade exclusivamente la fase C determinista y está desacoplado del motor base.
- Si OGR puede leer `ddd_unit_id`, el wrapper delega primero al motor v7.4.0 sin transformar la entrada.
- Si OGR pierde el campo, lee las propiedades GeoJSON crudas, asigna códigos enteros estables a las unidades y ejecuta exactamente el motor v7.4.0.
- La configuración se resuelve siempre con `ddd_core.config.load_params_yaml`.

## Semántica del informe
- `version`: versión del **motor optimizador** que genera el cuerpo del informe. En el wrapper actual permanece `7.4.0`.
- `wrapper_version`: versión de la **interfaz/orquestador** activo. En esta versión es `7.5.2`.
- `swap_polish.version`: versión del componente de fase C cuando se ejecuta; actualmente `1.0.1`.
- `unit_id_normalization`: se registra cuando el fallback de identidad es necesario.

Esta separación evita presentar una evolución de orquestación como si fuera una nueva versión de la lógica base validada y mantiene estable el contrato consumido por R016.

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

EXT-05 Run `34641298906` encontró 8 swaps 1×1 estrictamente mejores sobre ese estado.

EXT-06 Run `34642098588` validó operativamente la fase C sobre c020: acepta 2 swaps, reduce los outliers de 4 a 2 y el error cuadrático de `0.137478882166` a `0.131455334058`, sin modificar el máximo desvío de 13,30 %, sin violaciones duras y sin aumentar splits municipales. Por tanto, la fase C es útil pero todavía no resuelve por sí sola el contrato ±10 % de Extremadura.

## Estado de validación
- La lógica base v7.4.0 permanece validada/promocionada por Run #9.
- El wrapper v7.5.2 es **candidato**. Con `swap_polish_max: 0` debe reproducir los baselines anteriores.
- La fase C está **validada operativamente en EXT-06 pero sigue opt-in** porque quedan dos outliers en Extremadura.
- La promoción general exige R015 PASS completo y diagnóstico/resolución explícita de los dos outliers restantes; no se ocultan mediante relajación de tolerancias.

## Productos auditables
- GeoJSON ZIP de asignación completa optimizada.
- Informe M05 con objetivos, movimientos, primera factibilidad, parámetros, versión del motor, versión del wrapper, mapeo de normalización cuando proceda y metadatos de swaps cuando la fase C esté activa.

## Baseline vigente
**Aragón Run #9 `34599224954` / `gh-34599224954-1`.** Toda evolución debe mantener sus PASS. Las regresiones reales reejecutan M01–M06 en GitHub Actions para Aragón y Castilla y León. M05 v7.3.0 y Run #8 permanecen registrados como baseline histórico previo.
