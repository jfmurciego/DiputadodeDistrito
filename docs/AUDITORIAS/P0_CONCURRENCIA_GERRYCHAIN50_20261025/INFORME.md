# P0 — colas durables, GerryChain 50 y preparación nocturna

Base local usada: `origin/main@ebe12094740fd0ea6827671032c396a5ac54524b` (snapshot 20-10-2026). La rama local `main` está 415 commits por detrás de la última referencia local. No se ejecutó ningún territorio ni se modificó el producto certificado.

## Dictamen

**BLOCKED para creación de PR y GO técnico.** Work autorizó una PR draft, pero no puedo publicarla mientras la autenticación GitHub siga inválida y DNS no resuelva `github.com`. Además, no se instaló ni ejecutó `actionlint`; tres pruebas del runtime real GerryChain se omiten porque el paquete no está instalado. No quedan verificados los runs concretos del 24-10 ni la vigencia/descargabilidad de artefactos para la noche.

El cambio añade `queue: max` a los 24 bloques de concurrencia con `cancel-in-progress: false` observados. Se mantiene serialización para cada recurso compartido y para cada territorio/edición; no se cambian grupos de cancelación intencionada de CI. GitHub admite hasta 100 pendientes por grupo con `queue: max`; ejecuciones que excedan ese máximo pueden cancelarse.

`02` deriva `gerrychain_50` y `require_unique_hashes=true` del selector manual. `00` los deriva del mismo selector y conserva el rechazo fail-closed de contratos de campaña contradictorios. `procedimiento.sh` valida M04 como baseline, exige el runtime GerryChain y no permite fallback a Canónico para GerryChain 50. El portfolio debe incluir exactamente 50 candidatos, hashes de asignación distintos y artefactos cuyos SHA coincidan. M05 registra `M05_SUCCESS` con certificación `PENDING_M06`; el artefacto de auditoría M06 registra el dictamen de certificación aparte. Los fallos M05 generan diagnóstico conservado.


## Informe de los 24 grupos modificados

Cada grupo conserva su clave de exclusión. `queue: max` cambia el tratamiento de pendientes a FIFO (hasta 100); no amplía el solapamiento entre escritores del mismo grupo. La auditoría encontró 24 bloques preexistentes con `cancel-in-progress: false`: 24 ahora tienen `queue: max`; cero combinaciones `queue: max` + `cancel-in-progress: true`; cero bloques no cancelables sin cola. El smoke no productivo preparado más abajo es un grupo nuevo aparte y no se incluye en estos 24.

| Workflow / job | Grupo exacto | Motivo para conservar la exclusión |
|---|---|---|
| `_reutilizable-generacion-territorial.yml` · `workflow` | `ddd-territorial-engine-${{ inputs.params }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `_reutilizable-generacion-territorial.yml` · `jobs/pre_m04_evidence` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `_reutilizable-generacion-territorial.yml` · `jobs/pre_m04_diagnostic` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `_reutilizable-generacion-territorial.yml` · `jobs/registrar` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `_reutilizable-incorporacion-electoral.yml` · `jobs/registrar` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `_reutilizable-operacion-territorial.yml` · `jobs/promover_catalogo_operacional` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `_reutilizable-publicar-sitio.yml` · `workflow` | `ddd-pages-prod` | Serializa la promoción y despliegue sobre el único destino Pages. |
| `desplegar-visor-publico.yml` · `jobs/preparar_publicacion` | `ddd-shared-operational-state` | Serializa cambios al estado operativo compartido; otros territorios quedan en cola. |
| `ejecucion-completa-proyecto.yml` · `workflow` | `ddd-full-prod-${{ inputs.territory_id }}-${{ inputs.data_edition }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `ejecucion-completa-proyecto.yml` · `jobs/actualizar_estado` | `ddd-shared-operational-state` | Serializa cambios al estado operativo compartido; otros territorios quedan en cola. |
| `ejecucion-completa-proyecto.yml` · `jobs/manifestar` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `generar-alternativas-territoriales.yml` · `workflow` | `ddd-ensemble-${{ inputs.territory_id }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `incorporacion-resultados-electorales.yml` · `workflow` | `ddd-electoral-prod-${{ inputs.territory_id }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `orquestacion-durable.yml` · `workflow` | `orquestacion-durable` | Serializa el estado durable común de la orquestación. |
| `preparacion-fuentes.yml` · `workflow` | `ddd-territorial-prod-${{ inputs.territory_id }}-${{ inputs.data_edition || 'vigente' }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `preparacion-fuentes.yml` · `jobs/registrar` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `preparacion-legislatura-vigente.yml` · `workflow` | `ddd-current-legislature-preparation-${{ inputs.territory }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `preparacion-legislatura-vigente.yml` · `jobs/registrar_par` | `ddd-prepared-source-pair` | Serializa el par durable de fuentes de la misma jurisdicción. |
| `preparacion-resultados-electorales.yml` · `workflow` | `ddd-electoral-prod-${{ inputs.territory_id }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `preparacion-resultados-electorales.yml` · `jobs/registrar` | `ddd-catalog-promotion` | Serializa las escrituras del catálogo durable; conserva FIFO en vez de sustituir la siguiente promoción. |
| `produccion-distritos.yml` · `workflow` | `ddd-territorial-prod-${{ inputs.territory_id }}-${{ inputs.data_edition }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `producir-territorio-por-contrato.yml` · `workflow` | `ddd-production-${{ inputs.params }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `recuperar-producto-electoral-durable.yml` · `jobs/registrar` | `ddd-electoral-product-recovery-${{ inputs.territory_id }}-${{ inputs.data_edition }}` | Mantiene el cerrojo para la misma identidad territorial/recurso; claves distintas avanzan simultáneamente. |
| `smoke-gerrychain-galicia.yml` · `workflow` | `ddd-smoke-gerrychain-galicia` | Evita duplicar el smoke que consume el mismo checkpoint de Galicia y conservar trazas ambiguas. |

## Evidencia local de preparación territorial

`MATRIZ_TERRITORIOS_2025.csv` contiene los 19 CODAUTO, estado de catálogo, autorización, evidencia fuente local, checkpoint y run de referencia. El preflight local de `resolver_ejecucion_completa` clasifica 17 registros como GO contractual y bloquea:

- Aragón (02): `DURABLE_LINEAGE_INCOMPATIBLE`, vínculo `territorial_product→electoral_product` ausente.
- Castilla y León (07): `DURABLE_ASSET_INVALID`, receipt durable `electoral_product` ilegible.

Asturias (03) es GO local para GerryChain 50 y está reservada a la Operación 1 para evitar duplicar su lanzamiento en la Operación 2. Otros 16 territorios aparecen como GO contractual para `00` Canónico y `territorial_only`. **Ninguno está habilitado para lanzamiento aún**: la matriz marca la comprobación API de artefactos remotos `UNVERIFIED_GITHUB_AUTH_UNAVAILABLE`; el preflight de Actions debe ejecutarse y congelar el conjunto elegible antes de cualquier despacho.

El umbral nocturno será `success / elegibles congelados >= 0,70`. `skipped` no es éxito. Un territorio que falle después de clasificarse elegible permanece en el denominador; no hay reintentos automáticos. Hoy hay cero runs de esta operación, así que no existe una tasa de éxito que reportar.

## Operaciones previstas, no ejecutadas

Operación 1 (Asturias):

```sh
gh workflow run "02 Generación de Distritos Autonómicos" \
  --repo jfmurciego/DiputadodeDistrito --ref main \
  -f territory_id="03 Principado de Asturias" \
  -f data_edition=2025 \
  -f execution_mode="Reutilizar progreso existente" \
  -f optimization_algorithm="GerryChain 50"
```

Operación 2, repetir individualmente **solo para los 16 CODAUTO con preflight remoto GO**, después de congelar el conjunto:

```sh
gh workflow run "00 Ejecución Completa del Proyecto" \
  --repo jfmurciego/DiputadodeDistrito --ref main \
  -f territory_id="<opción exacta del catálogo>" \
  -f data_edition=2025 \
  -f execution_mode="Reutilizar progreso existente" \
  -f optimization_algorithm=Canónico \
  -f publication_mode=territorial_only \
  -f publish_result=false
```

No ejecutar esas órdenes hasta revalidar runs/artefactos y autorizar expresamente el despacho.

## Pruebas y límites

Resultado final de la batería dirigida renovada con el entorno DDD: 157 tests, 151 aprobados y 6 omitidos. Los seis skips son: tres pruebas end-to-end de Galicia (`test_output_is_m06_consumable`, `test_reproducible_assignment_and_bytes`, `test_runtime_refuses_unpinned_hash_seed`) por falta del checkpoint M03/M04 de Galicia; y tres pruebas de ejecución real GerryChain (`test_declared_water_bridge_does_not_block_gerrychain_start`, `test_recoverable_recom_failure_becomes_self_loop`, `test_real_gerrychain_recom_smoke`) porque el paquete `gerrychain` no está instalado. Los skips por dependencia ausente sí incluyen runtime real; el wiring manual, el rechazo de contrato, los 50 hashes/artefactos y el fallo cerrado están cubiertos por tests ejecutados. Por tanto, queda pendiente una validación de runtime ReCom real antes de GO. Cubre concurrency/colas, flujo 00, perfiles M05, contrato de campañas y portfolio, reutilización M04, M06 y regresiones de workflows. `bash -n procedimiento.sh`, parseo YAML de todos los workflows y `git diff --check` pasan. El smoke no productivo conserva cinco pendientes en el mismo modelo de grupo y representa el patrón comunicado del 24-10 sin inventar run IDs. Una batería adicional de 184 tests incluyó una prueba heredada (`test_generation_gate_real_territories_and_both_entry_paths`) con 12 subcasos incompatibles con el catálogo/evidencias actuales de `origin/main`; el test y los módulos de esos errores no forman parte del diff. Dos fallos de esa pasada en encadenamiento por Bash 3.2 se corrigieron en este candidato y los casos pasan en la batería final. Los tres fallos de ruta temporal se eliminaron al usar `TMPDIR=/private/tmp`.

No ejecutados: `actionlint` (no instalado: Go 1.7 no admite `go install pkg@version`, DNS no resuelve `github.com`; Homebrew no pudo escribir caché fuera del candidato), runs remotos 24-10, GerryChain 50 territorial, workflows 00/02, cálculo de tasa nocturna. No se pudo descartar el falso positivo de `concurrency.queue` de actionlint 1.7.12 ni completar el resto de sus diagnósticos; no se excluyó ni silenció ningún diagnóstico. No hubo push, PR, merge, publicación, preparación de fuentes, ni ejecución territorial. El smoke remoto no productivo está preparado en `.github/workflows/smoke-concurrencia-cola.yml`: cinco despachos manuales con tickets distintos comparten un grupo, duermen 45 s y no hacen checkout ni escrituras. Runbook (ejecutar solo tras integrar el workflow y recibir autorización):

```sh
for ticket in 1 2 3 4 5; do
  gh workflow run smoke-concurrencia-cola.yml --repo jfmurciego/DiputadodeDistrito --ref main -f ticket="$ticket"
done
gh run list --repo jfmurciego/DiputadodeDistrito --workflow smoke-concurrencia-cola.yml --limit 10
```

Conservar las cinco URLs/IDs y observar un job activo y al menos tres pendientes del grupo `ddd-p0-concurrency-smoke`, sin estado `cancelled`; después verificar que los cinco terminan `success`. No se ejecutó. La rama local de entrega es `codex/p0-concurrency-gerrychain-20261025`; la autenticación GitHub sigue inválida, así que no hay número de PR ni revisión independiente. Se conservará un commit local y un patch exportable; `main` permanece intacta.

Cabezal de referencia de esta evidencia: `origin/main@ebe12094740fd0ea6827671032c396a5ac54524b`. Estado de entrega: commit local en la rama candidata, sin push; `main` intacta.


## Addendum de revisión y corrección

En el HEAD posterior se corrige la interpolación del input `ticket` del smoke remoto: ahora es una opción 1–5, se valida en Bash y viaja por `env`. Se conserva el predecesor 1.0.0 en `legacy/`.
