## 2026-11-12 — T-268 — La 00 rechaza al principio los territorios del mapa de 350 (D-76)

- `herramientas/guarda_territorio_350.py` 1.0.0 (nuevo): `congreso350_*`, «Congreso 350 …» y «Nacional 350 …» salen con
  código 3 y `::error::TERRITORIO_350_FUERA_DEL_MOTOR` (D-76: fuera del motor y del registro; usar «Congreso <provincia>»
  o un territorio autonómico). El resto, 0.
- `ejecucion-completa-proyecto.yml` 1.9.1: paso «Rechazar territorios del mapa de 350» justo tras el checkout de
  «Planificar», antes de instalar el runtime y de resolver fases (con la semilla D-90 un P30 fallaba tarde con
  ErrorContrato). El selector conserva las 49 opciones; sin entradas nuevas; el paso T-246 no cambia.
- Tests: `tests/test_t268_guarda_350.py` (ejecuta el paso bajo `bash -eo pipefail`: rechazo con 3 y mensaje, admisión con 0;
  las 49 opciones 350 del selector se rechazan y ninguna otra; orden de pasos).
