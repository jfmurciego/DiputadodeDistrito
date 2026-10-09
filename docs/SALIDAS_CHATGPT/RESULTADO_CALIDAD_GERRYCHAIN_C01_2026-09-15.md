# Resultado — calidad metodológica GerryChain / C-01

**Fecha:** 2026-09-15  
**Ámbito:** exclusivamente `ddd_ensemble/**`, pruebas GerryChain nuevas, legacy y este documento.  
**Estado:** IMPLEMENTADO Y CI VERDE.  
**No ejecutado:** Aragón, Aragón-10, Aragón-50 ni ningún territorio real.  

## 1. Problema resuelto

La instrumentación previa de GerryChain registraba `unique_states` y `self_loops`, pero no los convertía en una puerta de calidad. Además, cada cadena se utilizaba principalmente para seleccionar su mejor estado, de modo que el producto visible era una **galería de alternativas optimizadas** y no una distribución estadística de los estados visitados.

La continuidad de M04 del 15-09-2026 ya dejaba C-01 abierto precisamente por esta razón: no debe confundirse la galería de mejores candidatos con una distribución estadística de referencia y deben conservarse métricas de los estados visitados. La auditoría C-01 anterior, basada en 50 semillas M05, sigue siendo evidencia válida sobre **robustez entre ejecuciones** y mantiene su resultado `FAIL_ROBUSTNESS`; este cambio añade el eje complementario de **exploración y distribución dentro de cada cadena**. No reinterpreta ni recalcula aquella evidencia.

## 2. Decisión sobre la puerta de degeneración

Se adopta como umbral mínimo:

- `unique_states / steps_requested >= 0.10`;
- `self_loops / (states_observed - 1) <= 0.90`;
- la cadena debe completar todos los pasos solicitados.

Una infracción produce explícitamente `FAIL_DEGENERATE_CHAIN` y la cadena no puede convertirse en candidato válido del lote.

### Por qué 0,10

El 10 % propuesto por la auditoría es técnicamente defendible **como suelo de patología**, no como criterio de convergencia. Exige, como mínimo, del orden de un estado distinto por cada diez pasos pedidos. Es suficientemente conservador para detectar cadenas prácticamente inmóviles sin pretender demostrar independencia, estacionariedad ni mezcla adecuada.

Por esa misma razón no se usa solo el cociente de estados únicos. Una cadena puede revisitar un conjunto pequeño de estados sin producir self-loops consecutivos; otra puede alcanzar el 10 % de estados únicos y después quedar casi inmóvil. La tasa de self-loop añade una segunda señal explícita de movilidad local. El umbral 0,90 es coherente con el mismo orden de magnitud: más de nueve transiciones inmóviles de cada diez se considera degeneración.

**Importante:** superar esta puerta significa únicamente “no degeneración evidente”. No demuestra mixing, tamaño muestral efectivo ni convergencia MCMC. Esa distinción queda codificada en el informe como `interpretation = sanity_floor_not_mixing_proof`.

## 3. Separación entre optimización y muestreo estadístico

Se crea `ddd_ensemble/statistical_quality.py` y se modifica únicamente el runner del subsistema ensemble.

Cada cadena produce ahora dos productos conceptualmente distintos:

1. **Galería de alternativas:** se sigue seleccionando el mejor estado de la cadena según la función de score vigente. Solo ese estado necesita GeoJSON completo.
2. **Ensemble estadístico:** se conservan observaciones compactas de estados visitados, independientes de la selección del mejor candidato.

Para cada observación estadística se almacena:

- paso;
- SHA-256 de la asignación;
- desviación poblacional máxima absoluta;
- Polsby–Popper mínimo, medio y mediano cuando está disponible;
- retención poblacional de comarca;
- número de comarcas fragmentadas;
- churn de asignación;
- cut edges;
- score de optimización.

No se conserva geometría completa para esos estados.

## 4. Memoria controlada

El almacenamiento estadístico usa un **reservoir sampling uniforme, Algorithm R**, con RNG local determinista derivado de la semilla de la cadena.

El valor por defecto es `max_samples = 5000`. Con la configuración ensemble actual de 1.000 pasos se conservan, por tanto, las métricas compactas de todos los estados observados. Si en el futuro se amplía mucho la longitud de las cadenas, la memoria queda acotada y la muestra retenida sigue siendo uniforme sobre la secuencia de estados visitados.

El artefacto por cadena es `statistical-states.jsonl`. El informe declara expresamente `stores_full_geometry = false`.

## 5. Distribuciones y posición del mapa de referencia

Se añaden funciones para calcular, por métrica:

- mínimo y máximo;
- percentiles 5, 25, 50, 75 y 95;
- percentil empírico del mapa de referencia;
- percentil de favorabilidad, teniendo en cuenta si para esa métrica es mejor un valor alto o bajo.

Los empates se resuelven mediante **mid-rank**. El mapa de referencia es la asignación inicial válida desde la que parte la cadena y queda identificado también por su SHA-256.

El agregado distingue explícitamente:

- `candidate_gallery_count`: número de alternativas optimizadas;
- `statistical_chain_count`: cadenas válidas que aportan evidencia estadística;
- `states_observed_total`: estados realmente recorridos;
- `statistical_state_count`: observaciones compactas retenidas.

Por tanto `candidate_count` deja de poder interpretarse accidentalmente como tamaño de la distribución estadística.

## 6. Comportamiento del runner

`ddd_ensemble/runner.py` usa ahora la capa estadística solo dentro del subsistema GerryChain. El motor canónico M01–M06 y `ddd_core/m05_gerrychain_engine.py` no se han modificado.

Una cadena válida genera:

- `candidate.geojson`: únicamente el mejor estado;
- `engine-report.json`: telemetría, puerta de degeneración y configuración;
- `statistical-states.jsonl`: métricas compactas visitadas;
- `report.json`: informe del candidato seleccionado.

Una cadena degenerada conserva `engine-report.json`, la muestra compacta disponible y `failure.json`, pero **no** se admite como candidato válido. La reanudación tampoco reutiliza outputs antiguos que carezcan de `chain_quality` aprobada y de evidencia estadística.

Al ensamblar el lote se crea además `analysis/statistical-summary.json`. La completitud del lote exige ahora tanto la galería válida como la evidencia estadística completa.

## 7. Terminología fijada

Dentro del subsistema se usan dos conceptos diferentes:

- **candidate gallery / galería de alternativas**: mejores estados seleccionados para comparación y revisión;
- **statistical ensemble / ensemble estadístico**: métricas de los estados visitados por las cadenas.

No se ha realizado ningún renombrado masivo de interfaz ni se han tocado workflows.

## 8. Pruebas añadidas

Se añade exclusivamente el fichero nuevo `tests/test_gerrychain_statistical_quality.py`, sin modificar `tests/test_ensemble_integration.py` ni los tests existentes.

Cubre:

1. cadena degenerada con 9 % de estados únicos -> FAIL;
2. cadena suficientemente exploratoria -> PASS;
3. cadena excesivamente pegajosa -> FAIL por self-loop rate;
4. percentiles y mid-rank correctos;
5. separación entre `candidate_gallery_count` y `statistical_state_count`;
6. reproducibilidad del reservoir con semilla fija.

La suite general `test_*.py` se ejecutó automáticamente en GitHub Actions con el commit de integración y terminó **SUCCESS**:

- workflow: `Pruebas DDD — R015`;
- run: `34961540379`;
- commit probado: `f324388a33b15b258e27fa8c965d5cb4073bc1fc`.

Este workflow ejecuta pruebas sintéticas y de regresión; no se lanzó ninguna operación territorial.

## 9. Commits de esta intervención

- `3d09430a6ce8e032fb8032dd0221d5fae4ed9c12` — capa estadística y puerta de degeneración;
- `d76b641b9d426a89820ec977ed0ce4cf34e63962` — pruebas sintéticas nuevas;
- `6e9858542e9f7be6a686257a4aafb4f381e4c2a7` — preservación legacy del runner anterior;
- `f324388a33b15b258e27fa8c965d5cb4073bc1fc` — integración en el runner ensemble.

## 10. Ficheros modificados o creados

- nuevo: `ddd_ensemble/statistical_quality.py`;
- modificado: `ddd_ensemble/runner.py`;
- nuevo: `tests/test_gerrychain_statistical_quality.py`;
- nuevo: `legacy/ddd_ensemble/runner_pre_calidad_c01_2026-09-15.py`;
- nuevo: este documento.

No se ha modificado `configuracion/ensemble/aragon.json`: los nuevos parámetros tienen defaults explícitos en el subsistema para evitar colisionar con la tarea metodológica concurrente sobre Aragón.

## 11. Límites y tareas restantes

La tarea de ingeniería queda cerrada, pero hay cuatro límites metodológicos que deben mantenerse visibles:

1. **0,10 / 0,90 no es una prueba de mixing.** Si C-01 evoluciona a inferencia MCMC formal, deberán añadirse autocorrelación, ESS y diagnósticos entre cadenas apropiados.
2. Los perfiles del ensemble pueden utilizar distintos `comarca_surcharge`; por ello, una distribución agregada entre perfiles debe interpretarse como **mezcla descriptiva de regímenes de exploración**, no como la distribución estacionaria de una única cadena homogénea. Para análisis inferencial futuro conviene estratificar por perfil/cadena además del agregado global.
3. La prueba definitiva de comportamiento sobre Aragón debe hacerse únicamente cuando se autorice expresamente el piloto territorial; esta intervención no lo ha ejecutado.
4. La auditoría C-01 previa ya demostró inestabilidad entre semillas de M05. Esta capa evita perder la distribución interna de cada cadena, pero no convierte por sí sola aquel `FAIL_ROBUSTNESS` en PASS.

## 12. Conclusión

El subsistema ya no puede presentar como “ensemble estadístico” una colección formada únicamente por los mejores estados de cada cadena. La selección optimizada permanece disponible para la galería, mientras la trayectoria aporta evidencia compacta, reproducible y percentilizable. Una cadena que no explore el mínimo exigido falla explícitamente y no puede ocultar su degeneración detrás de un buen estado seleccionado.
