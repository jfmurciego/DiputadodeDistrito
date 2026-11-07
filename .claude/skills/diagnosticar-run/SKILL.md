---
name: diagnosticar-run
description: Da la causa de un run fallido o bloqueado de DDD en cinco líneas, con el catálogo de causas raíz. Úsala cuando el propietario o el planificador pasen un run id, una 00 en PARADA o un error de CI.
---

# Diagnosticar un run

Salida: cinco líneas — territorio y run · paso que falla · mensaje · causa (del catálogo o nueva) · siguiente acción.

1. Territorio: `TERRITORY:` en el log del job «Planificar» (nunca por el orden).
2. Error sin descargar logs: `gh api repos/jfmurciego/DiputadodeDistrito/check-runs/<job_id>/annotations`.
   Si hace falta el log: `get_job_logs` guardado en fichero y filtrado (`::error|Traceback|Error`).
3. Los artefactos dan 403 desde la nube y caducan a los 14 días: para el motor usa los volcados de `diagnostico/*`
   (M01 + grafo M03) y reproduce en local (`.claude/rules/diagnostico-local.md`). Si faltan, pídelos al Mac del propietario.
4. Mira `CHECKPOINT_RUN_ID` en el paso M04: «Reutilizar» puede haber restaurado un checkpoint anterior a los arreglos.

Catálogo de causas raíz (FRAMEWORK §9):
| Síntoma | Causa | Arreglo |
|---|---|---|
| Falla igual con el código nuevo | «Reutilizar» restauró un M06 viejo | 00 «Ejecutar desde el principio» |
| Exento no visto (`bajo límite=1`) | Validador sin campo municipal | `CUMUN` / CUSEC[:5] (#398) |
| Otro distrito pierde la exención | M05 movió el municipio exento | anclaje (#399) |
| Techo 1,15 en vez del de la política | Contrato completo sin reaplicar política | `apply_policy_population_limits` (#403) |
| Distrito exento contado como duro | Exención por formato de id | M05 7.8.7 (#404) |
| `DURABLE_LINEAGE_INCOMPATIBLE`, digest vacío | Puerta 04 sin M08 | `electoral_product_available=false` + «Reutilizar» (#407) |
| Residuo municipal sobre el techo | M05 no redibuja piezas internas | M04 7.6.6 (#419) |
| `GEOMETRY_INVALID_AUDITED` / conectividad pre-M04 | CRS 3035 en vez de 25830 | CRS del autonómico (#374 #383) |
| «grafo no supera conectividad administrativa» | Faltan puentes de enclaves | `generar_provincias_congreso.py` (#371) |
| `TERRITORIAL_REPLAN_BLOCK` | Catálogo con receipt antiguo | alinear con `preparation_evidence` (#338 #352) |
| `GH013` / `Duplicate header: "Authorization"` | Ruleset o credencial de registro | `.claude/rules/workflows.md` (#386) |
| `main` roto tras una fusión | Marcas de conflicto | hotfix #422; guardián de CI |

Bloqueo de población: comprueba antes si es estructural (vecinos municipales en el grafo M03); más presupuesto de
reparación no ayuda. Causa nueva: añádela a esta tabla en la PR del arreglo.
