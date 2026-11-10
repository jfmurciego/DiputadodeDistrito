## 2026-11-09 — T-132 — Batería del motor: 71 territorios desde fuente, M04-M06 en local y matriz territorio × regla

**Causa.** Decisión del propietario (opción B, batería primero): saber en minutos y sin lanzar nada si el motor vigente
produce distritos válidos en los 71 territorios (52 circunscripciones del Congreso + 19 comunidades) y qué cambia entre
versiones del motor. Los M01/M03 de los runs caducan a los 14 días.

**Cambio.** `herramientas/bateria_motor.py` 1.0.0 (nuevo): `nacionales` (copias INE con sha256), `entradas` (adquisición
oficial por la ruta de producción, OGC del INE y 65034 servida desde `inputs/partes`, y M01-M03), `motor` (unidades
internas, M04, M05 canónico vigente o motor base legacy 7.4.3/7.4.2, M06 y `herramientas/validar_ejecucion.py`, la misma
validación de producción), `matriz` y `archivar` (R2: solo la entrada mínima, M01 + grafo M03 + ENTRADAS.json, por orden
del propietario; `entradas --desde-r2` reutiliza los estados M03 ya archivados si llevan la identidad del contrato
vigente). `herramientas/banco_generadores.py` 1.0.0 (nuevo, T-132 A): canónico, GerryChain de producción y semilla por
árboles (`recursive_tree_part`) + ReCom con las mismas reglas. Workflow manual `bateria-motor.yml` 1.0.0 («Auxiliar — Batería del Motor»,
solo `workflow_dispatch`, sin programación ni escritura en `main`). No toca motor, contratos ni huellas.

**Resultado (M04 7.6.7).** M05 7.4.4: 71/71 PASS en K, atomicidad, población, contigüidad, provincia y disciplina
municipal; 58/69 particiones idénticas al M06 vigente del visor. 7.4.3: 71/71 PASS, 61/69 iguales. 7.4.2: 70/71 (Castilla
y León falla R012: Ávila 05019 con 2 distritos mixtos, el error que corrigió la 7.4.3). Cambian de resultado 7.4.3→7.4.4: 6
territorios (Alicante y Las Palmas del Congreso, Navarra, C. Valenciana, Cantabria, Andalucía); 7.4.2→7.4.3: 1 (CyL).
Entradas 32 min, motor 40 min por versión. Matriz en `docs/ESTUDIOS/T132_BATERIA_MOTOR/` y nota de reglas (C).

**Hallazgos.** La declaración de fuentes de la Comunidad Valenciana (esquema 1.1) no fija años y declara
`seccionado_2025` frente al 2023 del contrato; 13 composiciones canónicas de `datos/composicion/` son de un run anterior
al M06 vigente del visor (la de CyL es la de 7.4.2, que incumple R012; la batería compara con `datos/composicion/runs/`); la descarga en vivo de la 65034 no termina desde la nube; con el shapefile
nacional del INE Madrid queda bloqueada por solapes > 1 m² (el OGC pasa); la 65034 coincide con el contrato en 61/71.

**Pruebas.** `tests/test_bateria_motor.py`; listas de workflows manuales en `test_design_a_matriz_sintetica` y
`test_codauto_preparation_contract`.
