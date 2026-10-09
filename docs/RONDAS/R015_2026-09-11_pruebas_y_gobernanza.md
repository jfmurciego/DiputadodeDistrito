# R015 — Pruebas automáticas y gobernanza verificable

**Fecha:** 2026-09-11  
**Tipo:** ingeniería y gobernanza; sin cambio de algoritmo territorial  
**Baseline territorial protegido:** GitHub Run #8 `34592470470` / R014

## Objetivo
Cerrar dos deudas detectadas por auditoría sin modificar la solución territorial aceptada: (1) cabeceras y referencias `legacy/` inconsistentes; (2) ausencia de una suite automática independiente que detecte regresiones en las invariantes R012/R014 y en el determinismo de M05.

## Separación respecto del algoritmo
R015 no redefine provincia, contigüidad, disciplina municipal, suelo/techo, tolerancia ni función objetivo. M04/M05 conservan su lógica validada por Run #8. Los cambios de versión sobre componentes activos son PATCH de metadatos/trazabilidad salvo la incorporación de pruebas y workflows de CI.

## Trabajo de gobernanza
- archivar la versión activa de cada componente afectado antes de sustituirla;
- normalizar `VERSIÓN`, `NOMBRE DE VERSIÓN`, `FECHA`, `ESTADO`, `CAMBIOS`, `MOTIVO` y `ANTERIOR`;
- hacer que `ANTERIOR` apunte siempre a un fichero real e inmediato en `legacy/`;
- no fabricar antecedentes no recuperados: se mantienen catalogados como deuda histórica;
- conservar byte a byte el antecedente archivado, incluso si contiene defectos cosméticos como espacios finales.

## Suite automática
`tests/test_r015_invariantes.py` incorpora:
1. regresión contra los productos navegables del Run #8;
2. conservación exacta del universo de 1.463 secciones y 1.364.621 habitantes;
3. 67 distritos y reparto provincial 11/7/49;
4. provincia única por distrito;
5. contigüidad por el grafo M03;
6. suelo 0,80×target y techo 1,75×target;
7. disciplina municipal, incluida indivisibilidad de municipios que caben bajo techo;
8. M04 con el único outlier fino histórico y M05 con `fuera_12=0`;
9. máximo desvío R014 ≈ 0,119431695687;
10. determinismo de M05 ejecutándolo dos veces sobre un fixture sintético con la misma semilla y exigiendo informe/asignación idénticos;
11. atomicidad de una `ddd_unit_id` multisección;
12. auditoría de cabeceras activas y existencia física de sus predecesores `legacy/`.

## CI
`.github/workflows/pruebas-ddd.yml` ejecuta la auditoría de `legacy/` sobre el checkout completo y las pruebas territoriales/deterministas dentro del contenedor reproducible del proyecto. No depende de `pytest`; utiliza `unittest` de la librería estándar.

## Criterio de aceptación
R015 se considera cerrada cuando la migración de gobernanza se materializa en `main` y la puerta `Pruebas DDD — R015` termina SUCCESS sobre ese estado. Un fallo de pruebas debe corregirse en la causa que corresponda; no se rebajan las invariantes R012/R014 para conseguir verde.
