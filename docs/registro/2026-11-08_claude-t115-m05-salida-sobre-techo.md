## 2026-11-08 — T-115 — M05 canónico 7.4.4: un distrito sobre el techo puede ceder unidades

- **Causa:** congreso350_madrid K=37, run 00 42522378370 (Canónico), `POPULATION_HARD_BLOCK`: el distrito 33
  (Móstoles 210.592 + Boadilla del Monte 64.635 + Villaviciosa de Odón 28.714 = 303.941) quedó sobre el techo 213.586.
  No es estructural: una búsqueda simple con el mismo M03 halla 37 distritos en límites con Móstoles solo. Reproducido en
  local con el M01 del run (sha256 ff17a366…) y el motor real: idéntico resultado; la semilla M04 no influye y la 7.4.2
  (anterior a #546) da lo mismo. Defecto: voraz y recocido exigían que donante y receptor quedaran dentro de
  [suelo, techo] en un solo paso, así que un distrito ya fuera de límites no podía ceder nada; la reparación privada
  (profundidad 6) no compensa.
- **Cambio:** `ddd_core/m05_opt_engine_v741.py` 7.4.4 (copia 7.4.3 en `legacy/`): `bounds_move_ok` admite el movimiento que
  reduce estrictamente la violación de un distrito que ya está fuera; un distrito dentro de límites sigue sin poder salir
  (sin cambio para soluciones factibles). Suelo, techo, K y atomicidad intactos.
- **Pruebas:** `tests/test_m05_salida_sobre_techo.py` (falla con 7.4.3, pasa con 7.4.4); tests M05/R015/R016/huella/N08
  en verde. Local Madrid K=37: PASS, reparación REPAIRED, 159.082–212.419 (−14,3 / +14,4 %). Madrid K=38 (D-25, contrato
  temporal): 7.4.3 PASS_WITH_EXCEPTIONS → 7.4.4 PASS (159.082–207.164).
- **PR/run:** cambia la huella M05: la 00 de congreso350_madrid va con «Ejecutar desde el principio». Sin lanzamientos.
