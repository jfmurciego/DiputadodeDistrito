# PR #268 — Expediente de aceptación técnica, 2026-10-17

**Ámbito:** integración A–J de la Rama Nacional, 52 unidades administrativas de origen, K=407. **Referencia verificada previamente a la conciliación:** `main@21a4a150eb14f1abecd5d798b159d84a71df1f4a`, `PR #268@115947fb548682d784e2e8350aca4c3c5446c8f7` (OPEN/DRAFT, mergeable), CI `38895708383=SUCCESS`. Este documento no se auto-certifica como revisión de su propio HEAD: tras cualquier commit posterior, **consultar GitHub por SHA y ejecutar CI correspondiente**.

## 1. Incremento N06 — código e invariantes auditadas

- `ddd_core/congreso_contract.py`: `_approved_k_errors()` protege decisión `N06-OWNER-20261012-K`, total exacto **407**, método de cuotas aprobado y lista exacta de 52 cuotas. Diferencias compensadas entre provincias también deben rechazarse.
- Protección activada al **afirmar aprobación** en `k_decision.status` o `institutional_decision.status`, aunque se falsifiquen a la vez ambos `decision_id`; la admisión meramente **estructural** de contratos históricos/candidatos sin aprobación no implica habilitación productiva.
- `tests/test_congreso_politica_aprobada.py`: pruebas negativas de total 406, bool, `decision_id` falsificado, cuotas individuales/compensadas, procedencia, combinación de cambios y generación inactiva.
- `production_blockers()` conserva diagnósticos estructurales antiguos y rechaza contratos N06 falsificados; `validate_production_admission()` y `national_readiness()` no pueden declarar la generación autorizada por este guard.

**CI examinada:** `38895708383`: 1.711 pruebas, 27 omitidas, cero fallos; 23 pruebas de GerryChain correctas. Es evidencia de regresión para ese SHA, **no sustituto de revisión independiente sobre el HEAD posterior a esta conciliación**.

## 2. PR completa: alcance y aceptación condicionada

El diff tiene aproximadamente 360 archivos (expediente, manifiestos, fixtures, motores y herramientas). La evidencia conocida acredita integración en **rama candidata**, no `main`; los tests CI no convierten preflights 52/52 en factibilidad, ni 407 distritos en productos existentes. El inventario topológico sigue esperando límite administrativo independiente efectivo a `2025-01-01`; los nueve casos físicos no están resueltos en lo administrativo.

**Criterios para revisor independiente, otra sesión:**
1. Inspeccionar HEAD actual de PR #268 y base de `main`; comprobar diffs funcionales frente a políticas N06/N08.
2. Verificar negativa dual de aprobación, alteración compensada de cuotas, `generation_authorized=false`, no mezcla con autonomías.
3. Revisar consistencia TASK_REGISTRY / MATRIZ / BLOCKER / CHECKPOINT / EVENT_LOG / READY_SELECTION y SHA de artefactos; contraste con GitHub, no sólo informes estáticos.
4. Verificar autenticidad de 52 preflights diagnósticos y límites de los testimonios constructivos, sin reinterpretarlos como producción.
5. Corroborar la CI **del HEAD exacto revisado**, evitando reutilizar el run anterior cuando cambie código.
6. Dictaminar `REVIEW_PASS`, `REVIEW_PASS_WITH_SCOPE_LIMITS` o `REVIEW_NO_GO`, con hallazgos que puedan reproducirse.

**Salida:** preparada para revisión independiente de alcance integral; **no emitir aquí un REVIEW_PASS independiente ni GO de fusión**. `merge=false`, `generation_authorized=false`.
