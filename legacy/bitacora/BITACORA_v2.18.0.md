# Bitácora de progreso

**Versión:** 2.18.0
**Fecha:** 2026-09-11
**Anterior:** `legacy/bitacora/BITACORA_v2.17.0.md`

## R001–R013
Se recuperó y profesionalizó el procedimiento; se formalizaron M01–M08, fuentes congeladas, caché territorial, validación, outputs completos, manifiestos, versionado y continuidad documental. Run #5 reveló defectos de validación territorial; Run #6 aisló una desconexión originada en M04; M04 v7.3.0 corrigió la construcción conexa. Run #7 consiguió los PASS estructurales R012, pero dejó un distrito fuera de ±12 %.

## R014 — Escape de mínimo local en M05
La auditoría de Run #7 demostró un mínimo local del greedy. M05 v7.3.0 añadió recocido reproducible dentro del espacio duro válido.

### Run #8 — 34592470470 — R014 VALIDADO
SUCCESS. M05 pasa de `fuera_12=1`, `max_rel_dev=0,549676` a **`fuera_12=0`, `max_rel_dev=0,119431695687`**, manteniendo `hard=0`. Validación final: 67 distritos, 1.463 secciones, 1.364.621 habitantes, 11/7/49, 0 desconectados, 0 cruces provinciales, 0 violaciones municipales y 0 violaciones de suelo/techo.

## R015 — Pruebas automáticas y gobernanza verificable

Se crea `tests/test_r015_invariantes.py` y `.github/workflows/pruebas-ddd.yml` para proteger cardinalidad, conservación, provincia, contigüidad, suelo/techo, disciplina municipal, objetivo ±12 %, atomicidad y determinismo. También se normalizan cabeceras y predecesores `legacy/`, conservando la deuda histórica no recuperada de forma explícita.

La puerta R015 queda aceptada y se mantiene obligatoria para cambios posteriores.

## R016 — Refinamiento canónico post-factibilidad

Se detecta que M05 v7.3.x se detenía en cuanto alcanzaba `fuera_12=0`, aunque su propia función objetivo todavía debía minimizar máximo desvío y error cuadrático. M05 v7.4.0 elimina esa parada prematura sin cambiar restricciones, semilla ni configuración.

### CI previa a ejecución territorial
La prueba específica R016 confirma que M05 continúa trabajando después de la primera factibilidad y que el resultado final no empeora el objetivo canónico. La puerta general R015 permanece verde.

### Run #9 — 34599224954 — R016 VALIDADO Y PROMOCIONADO
SUCCESS sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`.

M05 alcanza la misma primera solución válida que Run #8 en la iteración **9.038**:

`objective_first_feasible = [0, 0.0, 0, 0.119431695687, 0.182704485064]`

Después continúa **10.962 iteraciones** hasta completar las 20.000:

`objective_final = [0, 0.0, 0, 0.099299365905, 0.161271162560]`

Resultado:
- `fuera_12=0`;
- máximo desvío: **9,930 %** frente a 11,943 % de Run #8;
- error cuadrático global: **0,161271162560** frente a 0,182704485064;
- 67 distritos, 1.463 secciones y 1.364.621 habitantes;
- reparto provincial 11/7/49;
- 0 desconectados;
- 0 cruces provinciales;
- 0 violaciones municipales;
- 0 bajo suelo y 0 sobre techo.

Solo cambian 12 distritos frente a Run #8, todos en Zaragoza. El peor Zaragoza pasa de +11,943 % a +9,140 %. Huesca y Teruel permanecen intactos. R016 queda **CERRADO** y Run #9 pasa a ser el baseline territorial.

## Limpieza de ramas
Tras integrar la rama temporal de R016 y revisar las ramas históricas `infra/fuentes-reproducibles*`, se eliminan las cinco ramas sobrantes. El repositorio queda con **una sola rama: `main`**. Desde ahora `main` es la única rama permanente; cualquier rama técnica temporal debe eliminarse al acabar su integración.

## Reglas permanentes
Un informe nunca sustituye al producto. Una ejecución local/IA no sustituye a GitHub reproducible. Corregir el primer módulo que rompe contrato. Toda versión nueva preserva `legacy/` antes de sustituir el activo. Una copia histórica no se reescribe para satisfacer lint. Una referencia documental `Anterior` activa debe resolver a un fichero real. No relajar restricciones para obtener un PASS. No reescribir un ejecutable ya validado solo para cambiar una etiqueta de promoción: el estado canónico se registra en documentación y expediente de ejecución.
