## 2026-11-10 — T-179 (nacional) — Naturalidad: C y D8 en todos los territorios con mapa vigente

**Causa:** el Coordinador pide la evidencia nacional para decidir la función de calidad del motor nuevo antes del corte.
**Cambio:** `ddd_motor2/naturalidad_competicion.py` 1.2.0 (`--funciones` y `--reanudar`; con las cinco funciones, resultado idéntico a 1.1.0) y `ddd_motor2/naturalidad_informe.py` 1.2.0 (`--png`, nombres en español, `EMPEORA.md/.csv`). Entregable en `docs/ESTUDIOS/T179_naturalidad_nacional/`: C y D8 frente a A (= mapa vigente) en los 67 territorios de `datos/composicion/`; láminas de 12. Producción no lo importa; sin huellas ni workflows.
**Pruebas:** `tests.test_motor2_naturalidad`, `GovernanceHeaders`; León con 1.2.0 y las cinco funciones da la misma huella que 1.1.0.
**Riesgos:** ninguno en producción.
