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

## 4. Estado en main y caso futuro (rehecho sobre origin/main be94b20)
- **Hoy en main el estado ya no se da**: #786 (revert tanda 1 de r3) devolvió aut08 a run 40690624792 (sha `bdd316c8…`), coherente con el M06
  `43025652192`. Simulado en copia temporal: `reuse` OK (plan sin trabajo), `catalog_source` OK, `resolve-territorial` READY; los 2 tests de CLM
  (`test_continuar_ultimo_resultado_valido.py:401`, `test_ejecucion_completa.py:984`) **pasan**. Mi primera versión describía c4e4206, ya superado.
- **Caso futuro (P10 nuevo de CLM con M06 viejo)**, reproducido con la copia de c4e4206 (catálogo con run 43633706440 + su receipt, M06 viejo):
  - `reuse` → `CONTINUE_DURABLE_BLOCK … contradice el manifiesto productor` (bloquea «Reutilizar» y la hija del bot).
  - `catalog_source` («Generar desde fuente») → plan válido: `run_prepare_territorial=true`, `run_generate=true`, `run_incorporate=true`.
    Corrección: `build_plan` fija primero `run_prepare_territorial=False` para `catalog_source` (`resolver_ejecucion_completa.py:687-688`), pero
    `pre_m04_accreditation_planned` (ruta `planned_pre_m04_accreditation`, :731-732) lo vuelve `true` en CLM, antes y después del P10 nuevo.
  - Puerta «Planificar» (`ejecucion-completa-proyecto.yml:480-490`): `resolve-territorial` solo corre si `run_prepare_territorial != true`; con el valor
    `true` se omite. Si fuese `false` (territorio con evidencia pre-M04 válida), `consumir_par_fuentes_legislatura.py:93-117` comprueba que el receipt
    coincida con `preparation_evidence` y daría `PREPARED_TERRITORIAL_BLOCK` solo si un P10 dejase catálogo y receipt contradictorios; con P10 coherente
    (caso simulado) devuelve READY. Ese camino no usa `validate_durable_assets`.
  - Conclusión: tras un P10 nuevo, «Generar desde fuente» pasa Planificar; el M06 que genera acredita la fuente nueva y el linaje cuadra.
- Sin simular: P50/05 y la legislatura tras el M06 nuevo (no se ejecutó la 00).

## 5. Riesgo al rehacer los 71 P10 (solo si el catálogo cambia sin M06 nuevo)
Cada territorio con M06 vigente repetirá el rojo (un par de tests de estado vivo por territorio que fije «reuse» en vivo) hasta su M06 nuevo. Si
se quiere evitar el ruido: rehacer P10 y 00 por territorio de seguido (no en lote P10 → 00 tardía), o que esos tests usen fixture congelada
(`tests/_raiz_congelada.py`, como pide `test_guardia_estado_vivo`). Decisión del Planificador; no implementado.
