## 2026-11-19 — T-409 — La doble vuelta informa de los partidos sin casar (menores del revisor de #904)

Causa: el revisor de #904 dejó dos menores: las siglas de votos que no están en la tabla de bloques se trataban en silencio como sin
bloque, y un test de la tabla real se saltaba si faltaba. Cambio: `herramientas/doble_vuelta.py` 1.2.0 (copia 1.1.0 en `legacy/`):
`cargar_tabla` y `sin_casar`; el manifiesto lleva `sin_casar` (partidos, votos y lista) y stderr un ::warning
`DOBLE_VUELTA_SIN_CASAR`; el cálculo no cambia. `tests/test_t409_doble_vuelta.py` 1.2.0: 3 tests nuevos y sin `skipUnless` (la tabla ya
está en main: falla si falta). Pruebas: 19 tests OK en local, guardian y GovernanceHeaders. Sin tocar workflows ni modulos/. `no-automerge`.
