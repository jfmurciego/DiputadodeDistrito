## 2026-11-14 — T-291 — El adaptador común declara la tabla de equivalencia de seccionados (D-65)

- Causa: M07 7.4.0 (#749) consume `section_reconciliation.equivalence_table`, pero ningún contrato la declaraba. La noche
  del 29-11 usa `minsait_provisional` y el definitivo `infoelectoral_mesas`: los dos pasan por `adaptador_minsait_csv.py`.
- Cambio: `--section-equivalence RUTA` escribe en el contrato la ruta relativa al repositorio, el sha256 y las columnas de
  origen y destino de una tabla versionada (copia previa en `legacy/herramientas/`). Sin el argumento, el contrato no cambia.
- Efectos: ninguno hasta que la 03 pase el argumento (PR aparte).
- Pruebas: `tests/test_t291_adaptador_equivalencia.py` y los tests del adaptador.
