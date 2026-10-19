<!--
Nombre: Integración local de acreditaciones Cataluña pre-M04
Versión: 1.0.0
Fecha: 2026-10-19
Alcance: trasladar la puerta genérica de discontinuidades municipales acreditadas y su persistencia
Estado: candidato de integración local; no habilita M04 ni generación
Cambios/motivo: comprobar fuente/edición, contadores estrictos y recuperación durable sobre evidencia histórica auténtica
Anterior: no aplica; primera edición del expediente de integración
-->

# Cataluña pre-M04 — integración selectiva

## Identidad y alcance

La integración parte de la candidata OPT-01 local sobre `main` `51c797a89b15d324364ec578f0b76417f7de0b6b` (árbol `00190bc7749adf2e5bf6f97d3984f4cf3eb6321a`), que incluye AUTO-01 como dependencia y el M02 v7.3.3 exhaustivo. No se ejecutó M04 ni generación. El cambio CAT se limita al core de la puerta pre-M04, al materializador, sus regresiones, metadatos de versión y esta evidencia.

## Identidad de inputs y comparación de M02

- Run auténtico: `37453376100`.
- Artefactos M03/M03U/unidades internas: `11409125228`, `11409445285`, `11409600198`.
- SHA-256 exterior de los ZIP: M03 `1a60164eeba923794a69873ed7fc9238e04e9816e2ca1b1f4ea0b2feedc617f4`; M03U `27a4353d55c3464856ae2ed98e3064bc9a63c38284e6f13e7b83f18f425feaee`; job unidades `cbc9943db4bd256d57a2923c3f457aadbf12cd8d454f42dcc0b660d9543933e3`.
- Fuente: paquete SHA-256 `e904289f179ee4fe552f0bb7dae11b8822d2deecf918eb036bf52a0614e97ee0`, edición 2025, año de secciones 2024; identidad de compatibilidad `58c715a51035474378a2b8986da25d2b54fa5c714d736c1d3bf2e4e51c85ab6a`.
- El log original de M03 registra M02 v7.3.2, 14.316 aristas totales: 14.315 geométricas más el puente contractual de Llívia. La reconstrucción M02 v7.3.3 sobre M01 auténtico devuelve exactamente 14.315 pares geométricos, sin omisiones, extras ni duplicados; SHA-256 del conjunto canónico `0dc494dad59c9621d63db47a4fd36b03834840dcaf35a91e5d6ca537cdcb6576`. El archivo JSONL M02 del M03 auténtico tiene SHA-256 `ea3781a26a52e91e6780a1420edda3f527d9158926f6158524f2b116383c7c8c`; contiene 14.315 pares geométricos con ese SHA y conserva el mismo puente Llívia `1709401001—1714101003`. Esto demuestra igualdad del producto de aristas, no que el run histórico ejecutara el nuevo blob.
- Código M02 ensayado: SHA-256 `7e588c5454620bbca18d27ed49c670f6740a20aa40031bae128716c40bc6a42f`. El benchmark auténtico correspondiente está en `../OPT01_M02_733_INTEGRACION_20261019/results/real-m02-results.json`.

Los certificados/handoffs previos continúan ligados a su identidad original. La prueba de planificación en `tests/test_pre_m04_evidence_pipeline.py` confirma que el cambio M02 exige reacreditación antes de volver a consumir esas evidencias para generación; este ensayo durable solo demuestra que la puerta y persistencia admiten el caso auténtico de Tremp tras materializar la nueva evidencia.

## Reproducción durable

Comando desde la raíz del checkout de integración:

```bash
PYTHONPATH=. DDD_CAT_PRE_M04_EVIDENCE_ROOT=/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/artefactos/continuidad-autonomica-20261019/evidencias/opt01-cat-prem04-20261019/github_actions/extracted python3 docs/AUDITORIAS/CAT_PRE_M04_INTEGRACION_20261019/scripts/run_durable_pre_m04_roundtrip.py
```

El script usa los artefactos extraídos ya verificados fuera de este checkout, crea un snapshot temporal del código core/materializador y un bare Git local seedado desde el mismo checkout. El primer intento con `git init --bare` falló porque el checkout de integración era shallow y el bare vacío no contenía objetos ancestros. El harness se corrigió para clonar el bare desde el mismo checkout, conservando la frontera de objetos; el ensayo pasó después. No fue un fallo del materializador ni una operación GitHub.

Resultado durable reproducido sobre el main con AUTO-01 y OPT-01 ya fusionados: PASS. Base funcional `099b1441e70aecf0a3d37fdeec98ad617e77b08c`, árbol `d86d173f5ecb91aa9a9ac7e91d42ddb65ebeb222`; snapshot aislado de código CAT `dd8686c09c2a6810c8b3857610f95a9133ff01c0`, árbol `3901cd88f2d82da15d06d96b572b747a5052f91b`. SHA-256 código core `57da9d6f1077dd67df09ae615e5c2f98aa0386d0b1417c93467b726625140b0a`; materializador `a324f2d270545ab8f40f3422ad93e6d545dd3ee2a66a8edac8621ba83bdba87e`.

- La evidencia de Tremp se materializó desde M03/M03U auténticos: municipio `25234`, cinco secciones, componentes 4+1, fuente/edición correctas; puerta `allowed=true` por la ruta `validated_pre_m04_topology`.
- Persistencia: `REGISTERED`; segundo checkout independiente recuperó bytes e identidad; verificación de handoff: PASS.
- Reintento idéntico: `NO_OP`, mismo HEAD durable.
- Interrupción inyectada antes del push: el remoto local no avanzó; el reintento persistió correctamente.
- Candidata corrupta con año fuente alterado: rechazada (`INCOMPATIBLE_CURRENT_STATE`), el ref remoto no cambió.
- `m04_executed=false`, `territorial_generation_executed=false`.
- Limitación: remoto bare local; no ejercita GitHub Actions, API Contents, permisos hosted ni ejecución M03.

Resultados completos, candidatos, handoffs y outputs están en `results/durable-roundtrip.json` y archivos hermanos. En la reproducción sobre el nuevo main, SHA-256: `durable-roundtrip.json` `bc91732639254e826835a1d7e1dea301d70e1fc4a4e4e713629ec423315f786d`; candidata `50b9542615b8c5d9480caf1ec2604120c8488506f654fda8b4c661946ec01f9d`; metadata handoff `558e8c5f11044fef64209dfdc1aef7b015d16c7ab95c01b494af6e10ce3e4d30`. El commit usado como base del snapshot aislado es el main posterior a la fusión de OPT-01, no el viejo HEAD de la candidata. El script no contiene código territorial específico de Cataluña; el caso Tremp proviene del contrato real.

## Pruebas y límites

En el checkout limpio posterior a OPT-01, la regresión focal ejecutó `tests/test_pre_m04_evidence_pipeline.py`, `tests/test_temporal_source_preflight_contract.py`, `tests/test_r015_invariantes.py` y `tests/test_ejecucion_completa.py`: 88 passed, 51 subtests; log `results/focused-tests-after-m02.log`, SHA-256 `6ac520bedfbc7c9722d7704a43225e58d76349bbf491ea42cdeb086016127679`. La suite M02/consumidores ejecutada en la candidata OPT: 62 passed, 12 subtests; `tests/test_topology_preflight.py`: 33 passed, 4 subtests. OPT-01 quedó integrado por PR #274 (merge `099b1441e70aecf0a3d37fdeec98ad617e77b08c`); su CI y revisión independiente `INTEGRATION_GO` corresponden a HEAD `4887712344519d9a20cb9eb8691470d92033c23d`. Esta revisión CAT se limita al cambio de la puerta pre-M04 y persistencia durable, y debe superar sus propias CI y revisión antes de integración.

La aceptación de una evidencia pre-M04 no es certificación territorial ni permiso de generación. El M03/M03U histórico sigue identificado como producto del run original, y el cambio de código M02 mantiene la puerta de reacreditación antes de su uso productivo.
