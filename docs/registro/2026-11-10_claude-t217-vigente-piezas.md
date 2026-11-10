## 2026-11-10 — T-217 + T-218 — El vigente compite y piezas finas con la atomicidad del contrato

**Causa:** en las autonómicas, el canónico M05 queda peor que el mapa publicado (Navarra: 24 fuera de tolerancia frente a 11) y las cadenas, sobre unidades M04 gruesas, no lo alcanzan (T-211). Decisiones: T-217 (opción c) y D-79 (atomicidad del contrato en la competición autonómica).
**Cambio:**
- `ddd_motor2/generadores.py` 1.2.0:
  - generador `Vigente`: `datos/composicion/<t>.csv` sobre las filas del canónico; no es representable si cambian las secciones o si parte un municipio atómico;
  - `piezas_finas`: una unidad por sección en los municipios de más de `municipality_atomicity_limit_ratio` × objetivo, fuera del Congreso y sin `connected_internal_units`; suelo, techo, K, tolerancia y regla de mixtos sin cambios;
  - el `Ponderado` usa piezas finas y parte del vigente con las semillas que le da la competición.
- `ddd_motor2/competicion.py` 1.4.0: `competir(..., vigente=)`. El vigente se juzga tras el canónico; si es válido compite (orden 1) y la mitad final de las semillas parte de él. Si no, no compite y `Resultado.vigente` dice por qué.
- `ddd_motor2/competir.py` 1.2.0: con C/D5/D8, el vigente por defecto. La fila añade `vigente`, `vigente_compite` y `frente_al_vigente`; el resumen, `peor_que_el_vigente` (cuenta en la aceptación).
- Copias en `legacy/`. Sin `vigente` (tests de aceptación) todo igual: las HUELLAS_FIJAS no cambian. Las huellas reales de la batería cambian en todos los territorios (nuevo candidato y semillas desde el vigente).

**Prueba en sesión (fuera de tolerancia del contrato):**
- Navarra: vigente 11, canónico 24, ganador 11; nunca peor que el vigente.
- Madrid: vigente 26, canónico 24, ganador 14 (r3: 21); nunca peor que el vigente.
- **Cataluña: el vigente (33) no cumple el núcleo** (R-NUCLEO: reparte el núcleo cerrado 41 del canónico, 6775 hab. fuera) y no compite; el ganador da 38, **5 más que el vigente**.
- Castilla y León: el vigente no cumple el núcleo (R-MUN-MIXTOS en Ávila), no compite y se informa; el ganador da 2, igual que el canónico.

Detalle en `docs/ESTUDIOS/T217_vigente_piezas_finas/`.
**Pruebas:** `tests.test_motor2_competicion_d8` (`VigenteCompite`, `PiezasFinas`, `PonderadoDesdeVigente`), `tests.test_motor2_competir.Resumen.test_peor_que_el_vigente`, suite `test_motor2_*` y `GovernanceHeaders`.
**Riesgos:** ninguno en producción (M04/M05/ddd_core sin cambios). Las cadenas de Madrid tardan más (3759 unidades). Cataluña queda pendiente de decisión (opciones en el estudio).
