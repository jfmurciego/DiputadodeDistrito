## 2026-11-09 — T-125 — CLAUDE.md: la 05 con production_run_id vacío es «solo sitio»

Causa: T-125 (#574) cambió el comportamiento de la 05; `CLAUDE.md` aún decía que el campo vacío metía `latest_validated`.
Cambio: una frase en «Visor y dashboard» y una línea de historial compactada para seguir en 100 líneas. Solo documentación.
Efectos: ninguno en código, motor ni huellas; no hace falta 00.
Pruebas: `comprobar_guardian_main.py todo`.
Riesgos: ninguno.
