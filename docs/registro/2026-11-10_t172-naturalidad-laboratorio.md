## 2026-11-10 — T-172 — Laboratorio de naturalidad: competición A/B/C y mapas lado a lado

**Causa:** el propietario quiere ver, con mapas, cuánta población cuesta un mapa más natural antes de fijar criterio.
**Cambio:** `ddd_motor2/naturalidad_competicion.py` (20 cadenas ReCom por función desde el mapa vigente, núcleo como juez en cada paso, semillas públicas; A = función vigente, B = tolerancia y después demarcaciones partidas y frontera cortada, C = B con árbol ponderado por partido judicial, comarca agraria, área de movilidad y longitud de frontera) y `ddd_motor2/naturalidad_informe.py` (PNG A/B/C y tabla). Entregable en `docs/ESTUDIOS/T172_naturalidad/`. Producción no lo importa; sin huellas ni workflows.
**Pruebas:** `tests.test_motor2_naturalidad` (10), `GovernanceHeaders`; reproducibilidad bit a bit comprobada (misma huella y mismos CSV en dos ejecuciones).
**Riesgos:** ninguno en producción. Laboratorio sobre secciones y mapa vigente (no rehace M04/M05); sin ríos ni relieve.
