# Bitácora de progreso

**Versión:** 2.16.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.15.0.md`

## R001–R013
Se recuperó y profesionalizó el procedimiento; se formalizaron M01–M08, fuentes congeladas, caché territorial, validación, outputs completos, manifiestos, versionado y continuidad documental. Run #5 reveló defectos de validación territorial; Run #6 aisló una desconexión originada en M04; M04 v7.3.0 corrigió la construcción conexa. Run #7 consiguió los PASS estructurales R012, pero dejó un distrito fuera de ±12 %.

## R014 — Escape de mínimo local en M05
La auditoría de Run #7 demostró un mínimo local del greedy. M05 v7.3.0 añadió recocido reproducible dentro del espacio duro válido.

### Run #8 — 34592470470 — R014 VALIDADO
SUCCESS sobre `d57dc9cd77af4fa09780794401381d9727d1c71b`. M05 pasa de `fuera_12=1`, `max_rel_dev=0,549676` a **`fuera_12=0`, `max_rel_dev=0,119431695687`**, manteniendo `hard=0`. Validación final: 67 distritos, 1.463 secciones, 1.364.621 habitantes, 11/7/49, 0 desconectados, 0 cruces provinciales, 0 violaciones municipales y 0 violaciones de suelo/techo.

## R015 — Pruebas automáticas y gobernanza verificable

Objetivo: cerrar la deuda de ingeniería sin modificar el algoritmo territorial aceptado.

Se crea `tests/test_r015_invariantes.py` con regresión sobre los productos del Run #8 y fixture sintético de determinismo M05. Se crea `.github/workflows/pruebas-ddd.yml`, usando `unittest` de la librería estándar y el mismo contenedor reproducible del proyecto.

La suite protege: universo de secciones/población; K=67; 11/7/49; provincia; contigüidad; suelo/techo; disciplina municipal; `fuera_12=0`; máximo desvío R014; conservación M04→M05; atomicidad `ddd_unit_id`; y reproducibilidad de M05 con misma semilla. Además audita metadatos activos y existencia física de predecesores `legacy/`.

La migración de cabeceras normaliza 16 componentes no-workflow y el workflow territorial por separado. Se preservan sus predecesores inmediatos y se inventaría en `docs/DEUDA_HISTORICA_LEGACY.md` la arqueología anterior que nunca fue recuperada. Las versiones PATCH de R015 no cambian lógica funcional.

Durante la migración se detectaron dos incidencias de infraestructura, ambas documentadas y resueltas sin rebajar controles: `git diff --check` rechazó whitespace preexistente en una copia histórica y GitHub Actions rechazó modificar un workflow por falta de permiso `workflows`. La primera se resolvió excluyendo `legacy/**` del lint para conservar antecedentes literalmente; la segunda, separando la migración de workflows y realizándola por el canal GitHub autorizado.

### Aceptación R015 — Pruebas DDD Run 34594827070
SUCCESS sobre el estado posterior a retirar el migrador temporal. `Auditar cabeceras y legacy en checkout`: PASS. `Ejecutar regresión territorial y determinismo`: PASS.

R015 queda **CERRADA**. Run #8 continúa como referencia territorial; la CI R015 pasa a ser puerta de regresión obligatoria para cambios posteriores.

## Reglas permanentes
Un informe nunca sustituye al producto. Una ejecución local/IA no sustituye a GitHub reproducible. Corregir el primer módulo que rompe contrato. Toda versión nueva preserva `legacy/` antes de sustituir el activo. Una copia histórica no se reescribe para satisfacer lint. No relajar R012 ni ±12 % para obtener un PASS.
