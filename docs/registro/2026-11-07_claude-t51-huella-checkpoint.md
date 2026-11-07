## 2026-11-07 — T-51 — Huella de motor, contrato y política en los checkpoints

Causa: «Reutilizar progreso existente» restauraba checkpoints M04/M05/M06 hechos con otro motor, otro contrato u otra
política (causa raíz nº 1: Las Palmas, run 41432561787; Murcia, `CHECKPOINT_RUN_ID` antiguo). Solo se comprobaban la
huella M05 y la K/atomicidad del informe M04. Cambio: `herramientas/huella_checkpoint_motor.py` 1.0.0 calcula una huella
por capas: M04 (motor `modulos/04_generar_semillas.py`, `ddd_core/m04_*.py`, `configuracion/m04_engine.json`, secciones
del contrato materializado que gobiernan M04 y `population_limits` de la política) y M05 (la de
`huella_checkpoint_m05.py`). `_reutilizable-generacion-territorial.yml` 1.2.9 la guarda en `compatibility/motor.json` de
los checkpoints M04-M06. `seleccionar_checkpoint_productivo.py` la compara al reutilizar: capa M04 distinta → rechazo con
`CHECKPOINT_ENGINE_MISMATCH` y el selector baja de etapa (rehace desde M04); solo M05 distinta → deriva M04 y rehace
desde M05; sin huella (checkpoint anterior, caducan a los 14 días) → aviso `CHECKPOINT_ENGINE_UNVERIFIED`. La 04 que
consume un M06 certificado no se ve afectada. Pruebas: `tests/test_huella_checkpoint_motor.py` (8, con un checkpoint de
huella antigua), selector y configuración M04 en verde.
