## 2026-11-25 — T-460 — El bloque «Patriotas» pasa a «Derecha nacional» (en origen)

**Causa:** decisión del propietario (25-11), camino (b) del §6 de `docs/ESTUDIOS/T458_mapa_v4/T458_DISENO_MAPA_V4.md` (PR #1013): dato y web deben decir lo mismo. Actualiza D-167/D-182 (el Planificador numera la D nueva).

**Cambio:**
- Tablas nuevas fechadas `configuracion/bloques_partidos_2026-11-25.csv` y `bloques_partidos_autonomicas_2026-11-25.csv` (las aprobadas 11-17 y 11-19 no se tocan). Solo cambia el nombre del bloque; ningún partido cambia de bloque. «Izquierdas» y «Nacionalistas» igual.
- `herramientas/doble_vuelta.py` 1.5.0 (`BLOQUES`, `dv_B`), `bloques_autonomicas.py` 1.4.0 (`PAT`, lee/escribe las tablas nuevas), `p75_doble_vuelta_r2.py` 1.3.0 (`BLOQUES_AUT` nuevo).
- Corrección de un fallo latente: `bloques_vigente` (P75) y P30 1.0.5 elegían `bloques_partidos_*.csv` por orden alfabético y `autonomicas` ganaba a la fecha nacional; ahora `bloques_partidos_2*.csv`.
- Tests: `test_t409_*`, `test_t418_p75`, `test_t419_*`, `test_t421_*`, `test_t427_p75_aut` con el nombre nuevo; test nuevo `test_t460_derecha_nacional` (misma asignación con el nombre nuevo, generador reproduce la tabla, tabla nacional vigente).

**No tocado:** `visor/v4/mapa/` y `test_visor_v4_*` con fixtures «Patriotas» (el visor lee el nombre del dato en `dv.js`/`explorar.js`/`comprender.html`; lo hace T-459).

**Riesgos / efectos:** hasta relanzar P75 los ZIP publicados siguen diciendo «Patriotas» y el visor nuevo no los casará con la clase de color. Orden: P75 nacional (52) y autonómicas (16) → PR del pin de los dos informes → P40. Sin cambio en M04/M05/huellas.

**Qué tabla usó cada run publicado (revisión del Coordinador):** `bloques_vigente` (P75 nac) y P30 elegían `sorted(glob("bloques_partidos_*.csv"))[-1]`; desde que existe `bloques_partidos_autonomicas_*` (T-421, 19-11) esa ganaba a la nacional por orden alfabético, y sin filas 2023-07 todo partido quedaría «sin casar». Comprobado en el repositorio: el P75 nac 44556621000 (19-11 16:36) informó 0,0 % sin casar, o sea usó la nacional. NO verificado: el pin 44575597009-1 (19-11 18:17) y cualquier P75 nac posterior; sus `entradas.bloques.ruta`/`sha256` están en el INFORME de R2 (privado desde aquí). Comprobación pendiente del Operador: leer `doble_vuelta/2023-07/44575597009-1/INFORME.json` y confirmar `bloques.ruta` = `bloques_partidos_2026-11-17.csv` (sha256 `e50be2c8…2823`); si fuera la autonómica (`e6adaedf…2ff6`), la doble vuelta nacional publicada está mal y el P75 nac de esta PR la corrige.
