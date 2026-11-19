## 2026-11-19 — T-409 — Enganche de la doble vuelta a P30 con archivo en origen (D-171)

Causa: D-171 manda ejecutar la doble vuelta tras P32 y archivarla en origen. Hallazgos: (1) la tabla por partido y distrito de M07
(`<run>_m07_resultados_partido.csv`) YA se archiva en R2 con sha256 (el paquete `ddd-minimo-<run>-M08` la incluye por `_m0[678]_`);
(2) sus ids de partido son los del diccionario de cada contrato, no las siglas homologadas de la tabla de bloques: entre el 16 %
(2023) y el 54 % (2011) de los votos de los CSV históricos no casan (se abstendrían en silencio).
Cambio: `p30-resultados-electorales.yml` 1.0.2 (copia 1.0.1 en `legacy/`): paso «Doble vuelta con coaliciones» tras M08, no fatal
(`continue-on-error`), solo con persistir y sin `campana` (D-163), que ejecuta `doble_vuelta_cobertura.py` (nuevo; % de votos sin
casar, distinto de sin bloque, con ::warning si >0) y `doble_vuelta.py`; su salida va al paquete de R2 con `--extra` en el paso de
archivo en origen ya existente (sin subida nueva). Tests: `test_t409_enganche_p30.py` (archivo en origen fijado, no fatal, sin
escritura en main, igual que la 1.0.1 sin la doble vuelta con copia congelada en `tests/fixtures/t409_workflows/`, cobertura con
valores a mano); `_t379_2b.deshacer` y `test_t376_p30_equivalencia` ignoran lo añadido por T-409.
Riesgos: la doble vuelta archivada tiene sin casar hasta la PR de tabla de alias (b); recomputable porque el CSV de entrada queda en
R2. Efectos: toca el workflow de P30 (compartido); no lanza nada. `no-automerge`.
