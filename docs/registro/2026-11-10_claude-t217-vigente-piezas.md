## 2026-11-10 — T-217 + T-218 — El vigente compite y piezas finas con la atomicidad del contrato

**Causa:** en las autonómicas, el canónico M05 queda peor que el mapa publicado (Navarra: 24 fuera de tolerancia frente a 11) y las cadenas, sobre unidades M04 gruesas, no lo alcanzan (T-211). Decisiones: T-217 (opción c) y D-79 (atomicidad del contrato en la competición autonómica).
**Cambio:**
- `ddd_motor2/generadores.py` 1.2.0:
  - generador `Vigente`: `datos/composicion/<t>.csv` sobre las filas del canónico; no es representable si cambian las secciones o si parte un municipio atómico;
  - `piezas_finas`: una unidad por sección en los municipios de más de `municipality_atomicity_limit_ratio` × objetivo, fuera del Congreso y sin `connected_internal_units`; suelo, techo, K, tolerancia y regla de mixtos sin cambios;
  - el `Ponderado` usa piezas finas y parte del vigente con las semillas que le da la competición.
  - **vigente reparado (D-66)**: si el publicado incumple el núcleo, `reparar` hace una reparación mínima y determinista (R-NUCLEO: el núcleo cerrado al distrito con más población suya y las unidades ajenas a una vecina; R-MUN-MIXTOS: como el laboratorio), lo juzga de nuevo y, si vale, compite y da semilla. Lo publicado queda en `extra.publicado` (fuera de tolerancia, validez, infracciones).
  - Además, el `Ponderado` llama a `natural_desde_m06`, que desde naturalidad_clave 1.1.0 (#693) activa el recuento del contrato: con varias circunscripciones, sus cadenas eligen su mejor estado con otra clave y su recorrido cambia frente a r3.
- `ddd_motor2/competicion.py` 1.4.0: `competir(..., vigente=)`. El vigente se juzga tras el canónico; si es válido compite (orden 1) y la mitad final de las semillas parte de él. Si no, no compite y `Resultado.vigente` dice por qué.
- `ddd_motor2/competir.py` 1.2.0: con C/D5/D8, el vigente por defecto. La fila añade `vigente`, `vigente_compite` y `frente_al_vigente`; el resumen, `peor_que_el_vigente`, que entra en la aceptación y compara con el fuera de tolerancia del vigente **publicado** (no con el reparado).
- Copias en `legacy/`. Sin `vigente` (tests de aceptación) todo igual: las HUELLAS_FIJAS no cambian. Las huellas reales de la batería cambian en todos los territorios (nuevo candidato y semillas desde el vigente).

**Prueba en sesión (fuera de tolerancia del contrato; aceptación frente al vigente publicado):**
- Navarra: vigente 11 (válido), canónico 24, ganador **11**.
- Madrid: vigente 26 (válido), canónico 24, ganador **14** (r3: 21).
- Cataluña: el vigente (33) incumplía R-NUCLEO; reparado moviendo 3 secciones (6775 hab.) al distrito del núcleo, compite; ganador **31** (r3: 41).
- Castilla y León: el vigente (2) incumplía R-MUN-MIXTOS en Ávila; reparado con 1 unidad (1918 hab.); ganador **2**.

Ninguno queda peor que el vigente publicado.
Detalle en `docs/ESTUDIOS/T217_vigente_piezas_finas/`.
**Pruebas:** `tests.test_motor2_competicion_d8` (`VigenteCompite`, `VigenteReparado`, `PiezasFinas`, `PonderadoDesdeVigente`), `tests.test_motor2_competir.Resumen.test_peor_que_el_vigente`, suite `test_motor2_*` y `GovernanceHeaders`.
**Notas de #693 (Coordinador):**
- El «después» de T-211 (Aragón 0, Castilla-La Mancha 5, Castilla y León 2, Galicia 6) se generó en sesión. Su extracto (candidatos, fuera de tolerancia, clave y huella) está en `docs/ESTUDIOS/T211_ponderado_autonomicas/datos/despues_clave_contrato.json`; se reproduce con la batería nueva.
- La orden pedía contar «con las exenciones del contrato», pero el recuento las ignora a propósito, como `reglas.evaluar` y el M04 (`outside_target_tolerance`). En el contrato las exenciones solo relajan el suelo (R-SUELO; R-TOL asimétrica para el exento) y no sacan a ningún distrito del recuento de fuera de tolerancia. Descontarlas haría que la clave contara distinto que el núcleo y que el M04.

**Riesgos:** ninguno en producción (M04/M05/ddd_core sin cambios). Las cadenas de Madrid tardan más (3759 unidades). La reparación solo cubre R-NUCLEO y R-MUN-MIXTOS; ante otra infracción, el vigente no compite y se informa.
