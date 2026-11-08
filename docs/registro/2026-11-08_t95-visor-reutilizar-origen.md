## 2026-11-08 — T-95 — La 05 nombra el run origen al publicar una 00 «Reutilizar»

Causa: las 05 42430167433/42430169432/42430171257 pedían publicar las 00 «Reutilizar» 42428208611 (Barcelona), 42428211067 (Alicante) y 42428213222 (Málaga). Esas 00 no ejecutan 02 ni 04: reutilizan el M08 durable de otro run y no suben `ddd-audit*`, así que no hay `production_status.json` y el paso «Acreditar identidad» bloquea con `EXECUCION_SOLICITADA_SIN_EVIDENCIA_GENERADA`. Los exit 51/52 del materializador no se dan: solo aparecen como texto del script en el log.
Cambio: `evaluar_publicacion_visor.py` lee el `manifest.json` de la 00 descargada; si es `reuse` con `resumption.origin_run_id`, añade la razón `EJECUCION_REUTILIZADA_PUBLICAR_CON_PRODUCTION_RUN_ID=<origen>`. Sin cambios en workflows. Test `test_reused_run_without_audit_names_origin_run`.
Efectos: ninguno en módulos ni huellas. Orígenes con `ddd-audit-electoral` y M08 vigentes: Barcelona 42416213698, Alicante 42418334746, Málaga 42418628975 (su 04 falló solo en el archivo R2, con el M08 ya registrado).
Pruebas: `tests.test_publicacion_visor_identidad`, `test_r015_invariantes`, `test_workflow_safety`.
Riesgos: bajos; solo añade una razón al bloqueo.
