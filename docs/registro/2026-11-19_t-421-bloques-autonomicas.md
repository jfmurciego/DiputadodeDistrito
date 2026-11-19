## 2026-11-19 — T-421 — Bloques y alias PROPUESTOS de la doble vuelta para las autonómicas (sin lanzar)

- Causa: la segunda tanda de la V4 (D-179) lleva los `aut`; sus partidos no tienen bloque (la tabla aprobada solo cubre generales).
- Cambio: `herramientas/bloques_autonomicas.py` 1.0.0 genera `configuracion/bloques_partidos_autonomicas_PROPUESTA.csv` (13 comunidades, votos y sha256 de la fuente) y `configuracion/alias_partidos_autonomicas.csv`; `doble_vuelta.py` 1.4.0 añade `--comunidad` (alias por comunidad; sin él nada cambia); test `test_t421_bloques_autonomicas`.
- Cobertura de votos: 91,9 % con bloque, 5,5 % sin bloque decidido (D-168/D-170), 2,6 % dudoso. Sin datos por partido en el repositorio: aut03, aut08, aut11, aut14; aut18/aut19 no tienen autonómicas.
- Efectos: la tabla es PROPUESTA (no la lee ningún flujo); sin huellas ni checkpoints afectados; no se toca workflow ni visor.
