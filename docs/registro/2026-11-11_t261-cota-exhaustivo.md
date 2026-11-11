## 2026-11-11 — T-261 — Exhaustivo motor2: no lanzarlo cuando una cota demuestra que no acaba

- Causa: T-254 (#721) midió que el exhaustivo agota los 200 000 nodos sin aportar candidato (`metodo=cadena`) y aun
  tras T-256 (#722) es el 37-71 % de la competición (medido en #722) en congreso_huesca, congreso_la_rioja y la_rioja (D-89: optimizar
  con mapas idénticos bit a bit; aquí se acepta otra `huella_resultado` solo en la parte «exhaustivo»).
- Cambio: nuevo `ddd_motor2/reglas/cota.py` 1.0.0: `cota_nodos` da una cota INFERIOR de los nodos de `enumerar()`.
  Argumento: el árbol cuenta 1 + Σ min(usadas+1, K) sobre los nodos internos no podados; `podar` solo da violaciones
  seguras, así que ningún prefijo de un plan válido se poda; el árbol de prefijos (etiquetas canónicas) de planes
  válidos, obtenidos en anchura desde el plan del canónico moviendo una unidad (determinista, tope 20 000
  evaluaciones), está dentro del árbol real. `exhaustivo.py` 1.0.0 → 1.1.0 (`enumerar_exacto(..., plan=)`): si la cota
  supera el presupuesto, no enumera (`intentada=False`, motivo «cota…», `cota_nodos`); si no, igual que antes.
  `competicion.py` 1.4.0 → 1.4.1 pasa el plan del canónico. Copias en `legacy/ddd_motor2/`. `enumerar.py` no cambia.
- Pruebas: `tests/test_motor2_cota_nodos.py` (nuevo): en 200 problemas sintéticos la cota ≤ nodos reales; cuando
  supera el presupuesto, `enumerar` con ese presupuesto no acaba (>10 casos); sin demostración, `enumerar_exacto` da
  el mismo dict que sin plan. Pasan también los 16 módulos `tests.test_motor2_*`, `test_certificador_nucleos`,
  `test_p30_motor2_produccion`, `test_estado_produccion_motor2`, `test_bateria_motor`, `test_huella_checkpoint_motor`
  y R015 `GovernanceHeaders` (unittest, local).
- Prueba local en los territorios de T-254 (`bateria_motor.py entradas … --seccionado shapefile`,
  `PYTHONHASHSEED=0 python3 -m ddd_motor2.competir`, D8, 10 cadenas; antes = `main` 8e4e268 en otro worktree):
  mismo ganador en los 3, las 47 composiciones CSV idénticas (sha256), el contenido de los 3 GeoJSON M06 idéntico y
  los COMPETICION.json iguales salvo tiempos, `exhaustivo` y `huella_resultado`. En Huesca se comprobó además con
  `podar` cada uno de los 100 878 nodos del árbol de prefijos: ninguno se poda.

| Territorio | Total antes (s) | Total después (s) | Cota (nodos) | Planes válidos / evaluaciones | Cota (s) |
|---|---|---|---|---|---|
| congreso_huesca | 65,3 | 27,9 | 200 072 | 843 / 982 | 1,2 |
| congreso_la_rioja | 86,2 | 25,9 | 200 134 | 911 / 1 932 | 2,0 |
| la_rioja | 68,4 | 42,0 | 201 979 | 55 / 170 | 0,2 |

- Huellas: cambia la huella `motor2` y, donde la cota salta el exhaustivo, `huella_resultado` (entra `exhaustivo`:
  metodo, completo, nodos, validos, huella). No toca M04, M05, `ddd_core/`, `modulos/` ni ficheros N08. Modo de 00: el
  que toque por el territorio (el P30 se rehace por la huella motor2, mismos mapas); no obliga a «Ejecutar desde el
  principio». Donde la enumeración puede acabar (la cota no lo descarta), resultado idéntico.
- Límites: medido en 1 repetición por territorio; `docs/ARQUITECTURA/DESLINDE_1_0.md` (línea del exhaustivo) no se
  actualiza aquí. Nada se lanza.
