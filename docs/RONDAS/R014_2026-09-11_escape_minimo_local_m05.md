# R014 — Escape de mínimo local en M05

**Fecha:** 2026-09-11  
**Estado:** candidato pendiente de ratificación por GitHub Actions  
**Módulo afectado:** M05  
**Código:** `modulos/05_optimizar_distritos.py` v7.3.0  
**Configuración:** `configuracion/aragon_2025.yaml` v7.5.0  
**Auditoría de origen:** `docs/AUDITORIAS/AUDITORIA_M05_RUN7_2026-09-11.md`

## 1. Problema que resuelve
El Run #7 `34588834266` demostró que M04 v7.3.0 satisface las reglas estructurales R012, pero M05 v7.2.0 dejó un distrito fuera de la banda fina ±12 % y aceptó cero movimientos.

El distrito afectado es el 56 de Zaragoza, con 31.563 habitantes frente a un target de 20.367,48. No viola el techo duro 1,75×target, pero presenta una desviación de +54,97 %.

La auditoría sobre los artefactos exactos M03 y M04 del Run #7 demuestra que no faltan relaciones candidatas: existen 642 movimientos dirigidos únicos en el estado inicial. El bloqueo aparece después, al aplicar contigüidad y aceptación lexicográfica estrictamente monótona.

## 2. Causa raíz
Los movimientos salientes del distrito 56 que conservan contigüidad —por ejemplo Gallur, Mallén o Pinseque— reducen su exceso, pero hacen que el distrito receptor quede temporalmente fuera de ±12 %. La función objetivo de M05 v7.2.0 prioriza el número de distritos fuera de tolerancia; por ello rechaza el paso intermedio 1→2 aunque una secuencia posterior permita llegar a 0.

Los movimientos pequeños que sí mejorarían inmediatamente el vector poblacional rompen la contigüidad del distrito 56 y son rechazados correctamente.

El defecto es, por tanto, un **mínimo local del método de búsqueda greedy**, no un fallo de M03, M04, las adyacencias o las reglas provinciales/municipales.

## 3. Decisión de diseño
M04 no se modifica. M05 v7.3.0 separa dos conceptos que v7.2.0 confundía:

1. **objetivo canónico de selección del producto**: sigue siendo lexicográfico y no se rebaja;
2. **función de exploración**: puede atravesar estados poblacionalmente peores para escapar de un mínimo local, siempre dentro del espacio territorial duro válido.

La optimización queda dividida en dos fases:

- **Fase A — greedy determinista:** examina movimientos válidos y aplica el mejor que mejore estrictamente el objetivo canónico;
- **Fase B — escape por recocido simulado reproducible:** solo se activa si todavía existen distritos fuera de ±12 %, y solo dentro de las provincias afectadas.

Durante el recocido se conserva permanentemente una copia de la mejor solución encontrada según el objetivo canónico. La salida de M05 es esa mejor solución, nunca el último estado explorado.

## 4. Restricciones que jamás se relajan
Ni el greedy ni el recocido pueden aceptar una transición que produzca:

- población por debajo de 0,80×target o por encima de 1,75×target;
- cruce provincial;
- pérdida de contigüidad del donante o receptor;
- movimiento parcial de una `ddd_unit_id`;
- cesión o recepción por un distrito `ddd_closed_urban`;
- cambio del número de distritos.

La disciplina municipal final sigue siendo validada por la puerta de calidad global R012.

## 5. Función de exploración
La energía del recocido combina:

- error cuadrático poblacional de los distritos de la provincia activa;
- penalización por número de distritos fuera de ±12 %;
- penalización por máximo desvío;
- penalización de `churn`, es decir, número de unidades que se separan de la asignación M04 original.

Parámetros canónicos Aragón v7.5.0:

- `greedy_moves_limit: 1000`
- `anneal_iters: 20000`
- `seed: 12345`
- `anneal_seed_offset: 0`
- `anneal_outside_penalty: 0.01`
- `anneal_maxdev_weight: 0.05`
- `anneal_churn_weight: 0.0016`
- `anneal_temp_start: 0.02`
- `anneal_temp_end: 0.0005`

Estos parámetros son reproducibles y forman parte de la configuración, no constantes ocultas del procedimiento.

## 6. Prueba diagnóstica previa
Se ejecutó M05 v7.3.0 contra los artefactos exactos M03 y M04 del Run #7. Resultado diagnóstico:

- 67 distritos;
- 1.463 secciones;
- 1.364.621 habitantes conservados;
- Huesca 11 / Teruel 7 / Zaragoza 49;
- `hard=0`;
- `fuera_12=0`;
- máximo desvío relativo ≈ 0,11943;
- población mínima 18.345;
- población máxima 22.800;
- 0 distritos desconectados;
- 0 cruces provinciales;
- 0 infracciones de disciplina municipal según el validador R012;
- 75 unidades con asignación final distinta de M04.

La fase de escape aceptó múltiples transiciones exploratorias y encontró una solución con todos los distritos dentro de ±12 %. Esta prueba sirve para justificar técnicamente el cambio, pero **no constituye aceptación del procedimiento**.

## 7. Criterio de aceptación de R014
R014 solo se promueve cuando una nueva ejecución de GitHub Actions, lanzada desde el `main` que contiene M05 v7.3.0 y configuración v7.5.0, confirme simultáneamente:

- workflow completo SUCCESS;
- `hard=0`;
- `fuera_12=0`;
- provincia PASS;
- disciplina municipal PASS;
- contigüidad PASS;
- conservación exacta de secciones y población;
- outputs M01–M08 publicados y auditables.

Hasta entonces, Run #7 sigue siendo la última referencia GitHub aceptada estructuralmente y R014 permanece candidato.

## 8. Siguiente acción
Lanzar `Procedimiento DDD — Aragón` en modo `iterativo` desde GitHub Actions. Inspeccionar el nuevo run y, solo si pasa la puerta completa, registrar el expediente de ejecución y actualizar README, bitácora, Estado Maestro y continuidad con la nueva referencia.
