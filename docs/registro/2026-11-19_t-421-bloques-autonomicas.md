## 2026-11-19 — T-421 — Bloques y alias PROPUESTOS de la doble vuelta para las autonómicas (sin lanzar)

- Causa: la segunda tanda de la V4 (D-179) lleva los `aut`; sus partidos no tienen bloque (la tabla aprobada solo cubre generales).
- Cambio: `herramientas/bloques_autonomicas.py` 1.0.1 genera `configuracion/bloques_partidos_autonomicas_PROPUESTA.csv` (13 comunidades, por partido tras el alias; votos y sha256 de la fuente) y `configuracion/alias_partidos_autonomicas.csv` (una fila por sigla); `doble_vuelta.py` 1.4.0 añade `--comunidad` (tabla y alias por comunidad; exige `--alias`; sin él nada cambia); test extremo a extremo `test_t421_bloques_autonomicas`.
- Cobertura de votos: 95,7 % con bloque, 2,0 % sin bloque decidido, 2,3 % dudoso (JUNTS+ → Nacionalistas, Planificador; CONTIGO-ZUREKIN, DO y 100x100 → Nacionalistas, propietario 19-11). Sin datos por partido en el repositorio: aut03, aut08, aut11, aut14; aut18/aut19 no tienen autonómicas.
- Efectos: la tabla es PROPUESTA (no la lee ningún flujo); sin huellas ni checkpoints afectados; no se toca workflow ni visor.
