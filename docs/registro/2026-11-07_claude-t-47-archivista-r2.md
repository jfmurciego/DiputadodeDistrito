## 2026-11-07 — T-47 — Archivista R2 de artefactos de Actions

Causa: los artefactos de Actions caducan a los 14 días y con ellos productos registrados en el catálogo
(el M05 de Cantabria, run 41037133327, caduca el 13-11).
Cambio: `herramientas/archivar_artefactos_r2.py` 1.0.0 (copia a R2 lo referenciado por catálogo y visor,
primero lo que caduca antes, idempotente por id y sha256), workflow diario `archivar-artefactos-r2.yml`
(registra `orchestracion/archivo_r2.json` en main con la app de registro) y lista de workflows manuales de dos tests.
Pruebas: `tests/test_archivar_artefactos_r2.py` (7, catálogo sintético y R2 simulado), workflow_safety, design A,
R015 y guardián. PR: #438.
