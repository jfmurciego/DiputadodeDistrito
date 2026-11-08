## 2026-11-08 — T-104 — Partida contenida en un distrito fuera del tope D-17; Valencia sin caso aparte

- `herramientas/resultados_partidos.py` 1.3.0: una sección del ZIP partida cuyas secciones M06 candidatas caen todas en
  el mismo distrito es «contenida_distrito»: distrito exacto, fuera del tope D-17 (reparto entre secciones con D-13 en
  el informe). Regla general (decisión del propietario, 08-11); se retira `CASOS_APARTE` de Valencia.
- Valencia: las 10 partidas de Bétera (46070) caen en el distrito 22 → 0 % partido. Sin regenerar M06 ni tocar huellas.
- `tests/test_desajuste_d17.py` 1.2.0: caso sintético, caso negativo y Valencia/Bétera con la composición versionada.
