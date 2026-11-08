## 2026-11-08 — T-91b — La recuperación electoral no registra receipts de una 04 fallida

- Causa: la recuperación de la 00 «Reutilizar» (`detectar_producto_electoral_huerfano.py`) solo toma runs con la fase 04 en `failure` y M08 existente, y registra el receipt (manifiestos 42428211067, 42428208611, 42428213222; commit f26d062 en Barcelona). `resolver_activos_durables.py` exige la 04 de origen en success con run/artefacto/digest, así que toda recuperación válida acaba en DURABLE_LINEAGE_INCOMPATIBLE.
- Cambio: `validate_candidate` devuelve NO_RECOVERY (`ORIGIN_PHASE04_NOT_SUCCESS`) si la 04 del manifiesto de origen no es success con run/artefacto/digest. Los bloqueos por M08 expirado/ambiguo/identidad siguen antes.
- Pruebas: `tests/test_reanudacion_m08_huerfano.py` (los casos VALID pasan a NO_RECOVERY); fallaban antes del cambio.
- Riesgos: la recuperación queda inoperante para 04 fallidas. Receipts existentes con origen no-success: congreso_alicante, congreso_barcelona, congreso_malaga, cantabria (41037133327), extremadura (41042675119); NO retirados aquí (segundo commit cuando el Coordinador avise, tras las 00 «Generar»). Sin tocar workflows ni motor.
