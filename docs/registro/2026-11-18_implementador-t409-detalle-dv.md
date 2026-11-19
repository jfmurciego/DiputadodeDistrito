## 2026-11-18 — T-409 — Detalle por partido y bloque en la doble vuelta (dv_A)

Causa: el detalle de dv_A solo mostraba la candidatura-bloque; el propietario (vía Planificador) pide ver el bloque y los votos por
partido. Cambio: `herramientas/doble_vuelta.py` 1.1.0 (`detalle()` y `--detalle`: por distrito y escenario, partido, bloque,
candidatura y votos de primera vuelta; el manifiesto lleva el sha256 del detalle; `resolver` no cambia; copia 1.0.0 en `legacy/`)
y 4 tests nuevos con valores a mano. Sin tocar modulos/, workflows ni visor. Pruebas: 16 tests de `test_t409_doble_vuelta`,
guardian y GovernanceHeaders. PR con `no-automerge`.
