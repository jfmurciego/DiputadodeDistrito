## 2026-11-10 — T-179 (nacional, 1.ª parte) — Naturalidad: C y D8 en las 52 provincias del Congreso

**Causa:** el Coordinador pide la evidencia nacional para decidir la función de calidad del motor nuevo antes del corte.
**Cambio:** `ddd_motor2/naturalidad_competicion.py` 1.2.0 (`--funciones` y `--reanudar`; islas con partición y puentes marítimos de `configuracion/particiones_insulares_2025.json`; enclaves con las `topology_bridges` del contrato, con el cero inicial repuesto; municipio en dos islas como dos unidades; con las cinco funciones y sin islas ni puentes, resultado idéntico a 1.1.0) y `ddd_motor2/naturalidad_informe.py` 1.2.0 (`--png`, nombres en español, columna k, `EMPEORA.md/.csv`). Entregable en `docs/ESTUDIOS/T179_naturalidad_nacional/`: C y D8 frente a A (= mapa vigente) en las 52 provincias; láminas de 12. Las autonómicas, en la 2.ª parte. Producción no lo importa; sin huellas ni workflows.
**Pruebas:** `tests.test_motor2_naturalidad` (12), `GovernanceHeaders`; León con 1.2.0 y las cinco funciones da la misma huella que 1.1.0.
**Riesgos:** ninguno en producción. El piloto de #656 se hizo sin puentes (Badajoz los tiene); aquí sí se usan.
