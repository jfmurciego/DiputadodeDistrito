## 2026-11-10 — T-166 — La 00 no encadena la hija «Reutilizar» si no puede planificar

**Causa.** El job «Encadenar par de fuentes y 04» (00 1.6.1) lanza, tras activar el par, una 00 «Reutilizar» como
github-actions[bot]. Si el catálogo conserva un M08 de una 04 fallida (manifiesto con la fase 04 sin digest, p. ej. runs
41037133327 Cantabria y 41042675119 Extremadura), la hija falla siempre en «Planificar ejecución completa» con
`CONTINUE_DURABLE_BLOCK … DURABLE_LINEAGE_INCOMPATIBLE: electoral_product` (`build_plan`, validación de activos
durables). Runs 42651881625 y 42720255020 (Cantabria) y 42737598841 (Extremadura); las 00 madre quedaron en success.

**Cambio.** `resolver_ejecucion_completa.py` 1.2.0: `chain_block_reason` y `--check-chain` (solo detecta ese linaje; otros
errores los sigue informando la hija). 00 1.6.2: el job de encadenado hace checkout de `main`, ejecuta la guarda y, si no
puede planificar, no activa el par ni lanza la hija (estado `CHAIN_SKIPPED_M08_LINEAGE` en el artefacto de cadena y el
resumen). Sin cambio en motor, huellas ni `ddd_core`. No degrada `build_plan` (red de seguridad no necesaria: la guarda
usa la misma función que la hija).

**Pruebas.** `tests/test_t166_cadena_m08_linaje.py` con fixtures congeladas de los tres runs (catálogo y evidencias del
commit de cada hija, `tests/fixtures/t166_encadenado_m08/`): `build_plan` falla y la guarda lo detecta; sin M08 se sigue
encadenando; orden de pasos en el workflow. `test_00_encadenado_par` 1.0.3.

**Riesgos.** El M08 viejo sigue en el catálogo: para completar la 04 de esos territorios hace falta
«Generar desde fuente territorial acreditada» (o decidir cómo retirar el receipt M08 inválido); esta PR solo evita el run
inútil. No se ha lanzado ninguna ejecución.
