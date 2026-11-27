## 2026-11-26 — T-503 — Deslinde 1.2: exacto por tamaño y huella sin cotas abiertas

- **Causa:** T-502 (#1029): en Sevilla (nac41, K = 16) el exacto no se aplicaba por `K_MAX = 4` y Deslinde partía 8
  demarcaciones frente al óptimo de 6; y la cota de CP-SAT de una etapa que no cierra cambia entre ejecuciones.
- **Cambio:** `exacto.py` 1.1.0: aplica con 2 ≤ K ≤ 4, como antes, o con K ≥ 5 si átomos × K ≤ 2.000 (`TAMANO_MAX`);
  lo que no aplica conserva el motivo literal de la 1.0.0 (con `TAMANO_MAX = 0`, exactamente la 1.0.0); `info` lleva
  `tamano`; la versión que entra en la huella es la del modelo CP-SAT (1.0.0, sin cambios). `competicion.py` 1.6.0: en
  `huella_resultado` las etapas no OPTIMAL entran sin su cota. Deslinde 1.2.0. `DESLINDE_1_0.md` 1.2.0.
  `tests/test_t502_sevilla_exacto.py` activado, pero necesita las entradas de la batería (no están en git): **en la CI
  siempre sale saltado**; la protección real es la medición de T-507. Test nuevo `tests/test_t503_exacto_tamano.py`.
- **Pruebas (local, motor real, entradas `bateria_motor.py entradas --desde-fuente --seccionado shapefile`):** Sevilla
  pasa de 8 a 6 (gana `exacto`, 785,968 km); Burgos, Valladolid y La Rioja con el mismo ganador y la misma
  `huella_resultado` que `main`; dos ejecuciones dan la misma huella en los cuatro (cotas de la etapa 4: 361,7 M y
  384,5 M). Sevilla tarda 113-149 s frente a 27 s.
- **Efectos:** `huella_resultado` cambia solo donde el exacto pasa a aplicar. Candidatos, sacados de los contratos
  (`Reglas.desde_contrato` de `territorios/*/config/*_2025.yaml`: K ≥ 5, una circunscripción, sin exenciones):
  aut03, aut06, aut13, aut15, aut17, aut18, aut19, nac03, nac04, nac06, nac12, nac14, nac15, nac17, nac18, nac20, nac23,
  nac28, nac31, nac33, nac39, nac41, nac43, nac45, nac46, nac48, nac50; de ellos, cambian los que quepan
  (átomos × K ≤ 2.000), que mide T-507. Confirmado: nac41 (Sevilla, tamaño 1.776). Los demás (K ≤ 4, varias
  circunscripciones o exenciones) conservan su `huella_resultado`, salvo una etapa del exacto que no cierre. La huella
  `motor2` cambia en todos (código del motor): la P30 no se reutiliza; modo de la 00 para los que cambian: P30 rehecha
  y republicar (con permiso del propietario). `HUELLAS_FIJAS` no cambian.
