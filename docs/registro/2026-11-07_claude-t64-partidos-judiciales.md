## 2026-11-07 — T-64 — Partidos judiciales para C-13 en toda España

Causa: C-13 solo era evaluable en Aragón (comarcas); faltaba una unidad intermedia oficial nacional.
Cambio: `herramientas/generar_partidos_judiciales.py` 1.0.0 (Anexo I de la Ley 38/1988, BOE-A-1988-29622, con URL y sha256),
`configuracion/partidos_judiciales.csv` y `_no_conciliados.csv`; `generar_nombres_comunidades_nacional.py` 1.1.0 (C-13 con
partidos; nombres de distrito sin cambios); 49 informes y `MANIFEST.json` regenerados; `tests/test_partidos_judiciales.py`.
Límite: el consolidado del BOE omite los anexos; es la relación de 1988 (98,7 % de municipios, 98,9 % de población;
106 municipios posteriores a 1988 sin partido, listados). Sin comarcas nuevas (no hay fuente con hash).
Pruebas: tests nuevos, R015 `GovernanceHeaders`, `comprobar_guardian_main.py todo`. Sin cambios en motor, contratos ni M06.
Riesgos: ninguno para checkpoints; no exige ninguna 00. Depende de #456.
