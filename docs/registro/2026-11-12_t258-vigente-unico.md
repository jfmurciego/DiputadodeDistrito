## 2026-11-12 — T-258 — Un único vigente: el publicado en el visor (competición, P30 y aceptación)

- `ddd_motor2/vigente.py` 1.0.0 (nuevo): `vigente_publicado(t)` = canonical_m06 de mayor run de
  `orchestracion/publicaciones_visor.json` (2023-07-23) → `datos/composicion/runs/<t>_<run>.csv`, o `<t>.csv` solo si
  MANIFEST dice que es ese run; si no, sin vigente comparable con el motivo (nunca otro mapa).
- Antes: la competición (generadores.Vigente, P30, `--reanudar`) leía `datos/composicion/<t>.csv` y la aceptación el run del
  visor: 31 territorios con mapas distintos (Castilla y León y 30 del Congreso); Canarias medía un `<t>.csv` de otro run.
- `generadores` 1.2.2, `competir` 1.2.1, `produccion` 1.1.2 (huella motor2 + `runs/*.csv`, MANIFEST y
  `publicaciones_visor.json`; P30.json guarda run y origen del vigente), `bateria_motor` 1.2.5: indicadores exige que el
  vigente de COMPETICION.json sea el publicado (sha256; si no, NO_EVALUABLE); otro seccionado → SIN_VIGENTE; la aceptación
  lista SIN_VIGENTE en «vigente_no_comparable» y no bloquea (T-224). Canónico de referencia: el del run (sin cambios).
- Semilla D-90 y generadores Canonico/GerryChain/Ponderado intactos: HUELLAS_FIJAS sin cambios. Cambia el vigente que compite
  (y con él el resultado) solo donde el publicado ≠ `<t>.csv`. Tests: `tests/test_t258_vigente_unico.py` y T-258 en
  `test_bateria_motor`.
