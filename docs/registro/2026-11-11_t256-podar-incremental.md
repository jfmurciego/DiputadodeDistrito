## 2026-11-11 — T-256 — Exhaustivo: `podar` con constantes precalculadas (bit a bit)

- Causa: T-254 (#721) midió que el exhaustivo es el 60-87 % de la competición en congreso_huesca, congreso_la_rioja y
  la_rioja, y que casi todo es `podar`: en cada nodo recalcula constantes del problema y llama 8,7 M veces a
  `Contexto.rango_municipal` (divisiones de `Fraction`). D-89: optimizar solo con mapas idénticos bit a bit.
- Cambio: `ddd_motor2/reglas/enumerar.py` 1.1.0 → 1.2.0 (anterior en `legacy/ddd_motor2/reglas/enumerar_v1.1.0_20261110.py`).
  `_Constantes` calcula una vez por enumeración los ids, las claves R012 por unidad, población y nº de unidades por
  municipio, `rango_municipal` de cada municipio y los núcleos cerrados; `podar(..., pre=None)` las usa (sin `pre`,
  las calcula: misma interfaz). Mismos bucles y mismo orden de violaciones. No cambia ningún otro fichero del motor.
- Pruebas: `tests/test_motor2_poda_constantes.py` (nuevo): 150 problemas sintéticos × 40 parciales aleatorios (semilla
  256), la lista de violaciones de la 1.2.0 es igual a la de la 1.1.0; y 80 enumeraciones (semilla 4, presupuestos 50,
  500 y 10⁶, completas y agotadas) visitan y podan exactamente los mismos nodos, en el mismo orden, con el mismo
  resultado. Pasan también `test_motor2_reglas`, `test_motor2_exhaustivo` y `test_certificador_nucleos`.
- Prueba bit a bit en local (mismo entorno que T-254: `requirements.lock` + gerrychain 1.0.0 `--no-deps`,
  `bateria_motor.py entradas … --seccionado shapefile`, `PYTHONHASHSEED=0 python3 -m ddd_motor2.competir` con D8 y 10
  cadenas; antes = `main` fdc9995 en otro worktree, después = esta rama; 3 repeticiones alternas de cada uno):
  en las 6 ejecuciones son idénticos `huella_resultado`, ganador, `exhaustivo` (200 000 nodos, `metodo=cadena`,
  0 válidos), los 13 JSON (COMPETICION.json incluido, quitando solo tiempos y rutas absolutas), los 4 `.md` (quitando
  tiempos), las 50 composiciones CSV (sha256 conjunto `8c77bb919c9feff7…`) y el contenido de los 3 GeoJSON M06
  (`89637c65b7faf917…`).

| Territorio | Total antes (s) | Total después (s) | Δ | Exhaustivo antes (s) | Exhaustivo después (s) | Δ |
|---|---|---|---|---|---|---|
| congreso_huesca | 161,8 ± 1,0 | 69,0 ± 0,5 | −57,3 % | 132,7 ± 0,6 | 40,7 ± 0,7 | −69,3 % |
| congreso_la_rioja | 201,4 ± 3,9 | 90,2 ± 3,4 | −55,2 % | 175,4 ± 4,0 | 63,9 ± 2,6 | −63,6 % |
| la_rioja | 118,6 ± 2,9 | 74,7 ± 1,0 | −37,0 % | 72,4 ± 2,0 | 27,6 ± 0,3 | −61,8 % |

  Total = reloj de pared de `competir` por territorio (incluye M04/M05/M06 del canónico); media ± desviación de 3.
  La máquina de esta sesión es más lenta que la de T-254 (antes: 161,8 s frente a 114,1 s en Huesca); vale la proporción.
- Huellas: cambia solo la huella `motor2` (`produccion.huella_motor`: todo `ddd_motor2/**`). No toca M04, M05,
  `ddd_core/`, `modulos/` ni ficheros con huella N08: no hace falta `no-automerge` por huella. Checkpoints motor2:
  101 evidencias de generación (`territorios/*/evidencia/generaciones_m06/*.json`, `execution.p30.motor=motor2`)
  llevan la huella anterior; su P30 no se reutiliza y la siguiente 00 lo rehace (mismo resultado). Modo de 00: el que
  toque por el territorio; esta PR no obliga a «Ejecutar desde el principio».
- Límites: medido en 3 territorios pequeños (≤ 202 unidades); no es la optimización 2 (saltar el exhaustivo que no
  acaba) ni la 3 (cadenas). Nada se lanza.
