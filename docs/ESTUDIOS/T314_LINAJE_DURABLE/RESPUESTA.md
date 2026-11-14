# T-314 — ¿`CONTINUE_DURABLE_BLOCK … territorial_source→territorial_product` bloquea la P00 «Generar desde fuente»?

**Respuesta: TRANSITORIO. No bloquea «Generar desde fuente» ni «Ejecutar desde el principio»; solo bloquea «Reutilizar progreso existente»
(y, por tanto, la «Reutilizar» que encadena el bot). Lo resuelve el M06 nuevo.** Solo lectura; simulado en copia temporal de `origin/main` (c4e4206).

## 1. Dónde se lanza y qué comprueba
- Se lanza en `herramientas/resolver_activos_durables.py:495` (`validate_durable_assets`, def. :389). Compara el artefacto y SHA de la
  fuente vigente del catálogo (`preparation_evidence`: `artifact_name`, `artifact_sha256`) con la fase «01 ·» del **manifiesto productor del M06**
  (`_phase(manifest,"01 ·")`, :489-496); si el manifiesto es el M06 puro, con `inputs.source_package_artifact` (:476-484, mensaje «contradice las entradas M06»).
  `_same_phase_asset` (:354) añade run. Se envuelve como `CONTINUE_DURABLE_BLOCK` en `herramientas/resolver_ejecucion_completa.py:605` y `:621`.
- Único llamador de producción: `build_plan` (`resolver_ejecucion_completa.py:591-621`), **solo dentro de `if automatic_continue`**
  (def. :553: `execution_mode == "reuse"` y sin fuente explícita y algoritmo Canónico). El resto son tests.

## 2. Caminos
| Camino | ¿Llega a ese código? |
|---|---|
| «Reutilizar progreso existente» (`mode=reuse`, workflow 00 :449) | **Sí → se detiene** |
| «Generar desde fuente territorial acreditada» (`catalog_source`, :451) | **No**: `catalog_source_mode` toma `_catalog_territorial_source` (:562-563, def. `resolver_ejecucion_completa.py:271`), que solo valida run/artefacto/SHA del propio catálogo; `automatic_continue` es falso |
| «Ejecutar desde el principio» (`from_start`, :452) | No (mismo motivo) |
| Hija «Reutilizar» del bot / `chain` | Sí (es `reuse`) → se detendría, pero solo si la 00 padre dejó el M06 sin renovar |
| Gestor/legislatura vigente, panel | `legislatura_vigente.build_plan` y `gestor_campana_nacional.py:302` solo planifican; el dashboard no llama a `validate_durable_assets` |

## 3. Qué lo resuelve
La 00 «Generar desde fuente» regenera 02 y el M06 nuevo con su propio manifiesto, que acredita la fuente nueva (`inputs.source_package_artifact`);
al registrarse, el linaje vuelve a cuadrar. Tras eso, la cadena legislatura → electoral → P50 parte del par nuevo (el par viejo ya queda
incompatible, ver CLAUDE.md «Ejecución 00»). No hace falta arreglo de código → **sin diff mínimo** (punto 3 no aplica).

## 4. Efecto en tests/CI de main
Hoy en main CLM está en ese estado: `catalogo_preparacion.yaml` aut08 → `preparation_evidence.run_id 43633706440` (sha `59153d79…`), mientras el
M06 vigente (`generaciones_m06/43025652192.json`) consume la fuente `40690624792` (sha `bdd316c8…`). Reproducido en copia temporal:
`reuse` → `CONTINUE_DURABLE_BLOCK … artefacto o SHA contradice el manifiesto productor`; `catalog_source` y `from_start` → plan válido
(`run_prepare_territorial`, `run_generate`, `run_incorporate` = true).
Tests de estado vivo que leen el CLM real y fallan por esto (módulos del job «Estado vivo», `pruebas-plataforma.yml:599-607`):
`tests.test_continuar_ultimo_resultado_valido…test_castilla_la_mancha_m08_reuse_follows_m06_lineage` (:401) y
`tests.test_ejecucion_completa.CastillaLaManchaReuseCurrentDurableInputsTests` (:984). Ese job es `continue-on-error`
(`pruebas-plataforma.yml:634-639`): señal roja, no bloquea main, y la siguiente PR hereda el rojo hasta el M06 nuevo. En mi copia fallaron además
tests por `pyproj` ausente y 3 del Gestor nacional (Extremadura/Ceuta/14 rutas) cuya relación con CLM no he verificado.

## 5. Riesgo al rehacer los 71 P10
Cada territorio con M06 vigente repetirá el rojo (un par de tests de estado vivo por territorio que fije «reuse» en vivo) hasta su M06 nuevo. Si
se quiere evitar el ruido: rehacer P10 y 00 por territorio de seguido (no en lote P10 → 00 tardía), o que esos tests usen fixture congelada
(`tests/_raiz_congelada.py`, como pide `test_guardia_estado_vivo`). Decisión del Planificador; no implementado.
