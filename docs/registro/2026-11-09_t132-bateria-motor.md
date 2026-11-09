## 2026-11-09 — T-132 — Batería del motor: 71 territorios desde fuente, M04-M06 en local y matriz territorio × regla

**Causa.** Decisión del propietario (opción B, batería primero): saber en minutos y sin lanzar nada si el motor vigente
produce distritos válidos en los 71 territorios (52 circunscripciones del Congreso + 19 comunidades) y qué cambia entre
versiones del motor. Los M01/M03 de los runs caducan a los 14 días.

**Cambio.** `herramientas/bateria_motor.py` 1.0.0 (nuevo): `nacionales` (copias INE con sha256), `entradas` (adquisición
oficial por la ruta de producción, OGC del INE y 65034 servida desde `inputs/partes`, y M01-M03), `motor` (unidades
internas, M04, M05 canónico vigente o motor base legacy 7.4.3/7.4.2, M06 y `herramientas/validar_ejecucion.py`, la misma
validación de producción), `matriz` y `archivar` (R2). Workflow manual `bateria-motor.yml` 1.0.0 («- Batería del Motor»,
solo `workflow_dispatch`, sin programación ni escritura en `main`). No toca motor, contratos ni huellas.

**Resultado (M04 7.6.7 + M05 7.4.4).** 71/71 PASS en K, atomicidad, población, contigüidad, provincia y disciplina
municipal; 56/67 particiones idénticas a la publicada (las 11 distintas: 6 publicadas con GerryChain 50 y 5 con otra
versión del canónico). Entradas 32 min, motor 40 min. Matriz en `docs/ESTUDIOS/T132_BATERIA_MOTOR/`.

**Hallazgos.** La declaración de fuentes de la Comunidad Valenciana (esquema 1.1) no fija años y declara
`seccionado_2025` frente al 2023 del contrato; la descarga en vivo de la 65034 no termina desde la nube; con el shapefile
nacional del INE Madrid queda bloqueada por solapes > 1 m² (el OGC pasa); la 65034 coincide con el contrato en 61/71.

**Pruebas.** `tests/test_bateria_motor.py`; listas de workflows manuales en `test_design_a_matriz_sintetica` y
`test_codauto_preparation_contract`.
