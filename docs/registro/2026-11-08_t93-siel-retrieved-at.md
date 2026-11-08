## 2026-11-08 — T-93 — Contrato electoral SIEL sin `retrieved_at`

Causa: `adaptador_siel_andalucia_2026.build` escribía `sources[0]` sin `retrieved_at`; la preparación electoral (42425793937) dio success y M07 falló en la 00 (42430164925) con `contrato.sources[0]: falta retrieved_at`.
Cambio: el extractor SIEL graba `retrieved_at` (fecha UTC de la descarga) en el manifiesto del snapshot; el adaptador lo exige y lo copia a `sources[0]`; `preparar_snapshot_electoral_oficial` falla si el contrato embebido no valida con `load_election_contract`. Tests en `test_adaptador_siel_andalucia_2026` y `test_adquisicion_electoral_especial`.
Efectos: cambia el contrato embebido (`contract_sha256`) y el sha del artefacto del paquete; la identidad electoral (elección/fecha) no cambia. El paquete 42425793937 es inválido: repetir `preparacion-resultados-electorales` con reutilizar=false (volverá a descargar SIEL) y luego `prepare_one` antes de la 00. No toca M04/M05 ni checkpoints.
Pruebas: `unittest` de los dos ficheros anteriores y `test_adquirir_siel_andalucia_2026`, `test_preparacion_electoral_industrial` (OK). `test_r039` no corre en local (sin geopandas).
Riesgos: bajos; `retrieved_at` es la fecha de finalización del snapshot (con reanudación, puede ser posterior al primer tramo).
