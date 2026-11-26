## 2026-11-26 — T-503 — Deslinde 1.2: exacto por tamaño y huella sin cotas abiertas

- **Causa:** T-502 (#1029): en Sevilla (nac41, K = 16) el exacto no se aplicaba por `K_MAX = 4` y Deslinde partía 8
  demarcaciones frente al óptimo de 6; y la cota de CP-SAT de una etapa que no cierra cambia entre ejecuciones.
- **Cambio:** `exacto.py` 1.1.0: aplica con K ≥ 2 y átomos × K ≤ 2.000 (`TAMANO_MAX`), sin tope de K; `info` lleva
  `tamano`; la versión que entra en la huella es la del modelo CP-SAT (1.0.0, sin cambios). `competicion.py` 1.6.0: en
  `huella_resultado` las etapas no OPTIMAL entran sin su cota. Deslinde 1.2.0. `DESLINDE_1_0.md` 1.2.0.
  `tests/test_t502_sevilla_exacto.py` activado; test nuevo `tests/test_t503_exacto_tamano.py`.
- **Pruebas (local, motor real, entradas `bateria_motor.py entradas --desde-fuente --seccionado shapefile`):** Sevilla
  pasa de 8 a 6 (gana `exacto`, 785,968 km); Burgos, Valladolid y La Rioja con el mismo ganador y la misma
  `huella_resultado` que `main`; dos ejecuciones dan la misma huella en los cuatro (cotas de la etapa 4: 361,7 M y
  384,5 M). Sevilla tarda 113-149 s frente a 27 s.
- **Efectos:** cambia `huella_resultado` de los territorios con K ≥ 5 (aplique o no el exacto, cambia su decisión) y la
  huella `motor2` de todos (código del motor); `HUELLAS_FIJAS` no cambian.
