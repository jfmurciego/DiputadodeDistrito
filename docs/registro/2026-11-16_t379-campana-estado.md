## 2026-11-16 — T-379 — P00 Campaña, PR 1: estado de campaña

- Causa: el diseño de P00 Campaña 1.1 (T-378/T-387, D-143, D-145, §13) asigna a la PR 1 el estado de campaña sin workflows.
- Cambio: `herramientas/campana_estado.py` 1.0.0 (fichero nuevo): comprobación previa con semáforo por territorio
  (grupos `todos`/`congreso`/`autonómicas` o códigos desde la tabla maestra; elección `vigente` | `2026-11` → «ensayo
  2026-11-29»; otro `AAAA-MM`, código inexistente, id viejo o `congreso350_*` → rojo por territorio), marca
  «sin_resultado» al empezar cada paso, registro por (campaña, territorio, paso, run_attempt) idempotente, recuento con
  el último intento, parada sistémica (≥3 con la misma causa o ≥20 % de los lanzados con mínimo 3), re-ejecución solo
  de transitorios, `resultado` (rc 1 con apartados, parada o cierre pendiente), plan de cierre (rama `main` o
  `p00-cierre/<run_id>`, vacío en ensayo, rutas ⊆ `RUTAS_ROBOT`), objeto «cierre» idempotente por huella e informe
  markdown. Almacén R2 (aws, como `fuente_r2.py`) o directorio local. Sin workflows; no cambia nada existente.
- Revisor de #861 (7 menores, arreglados): semáforo inmutable en el almacén; causas transitorias solo las acreditadas
  en `main` con cita (`PUSH_RECHAZADO_TRAS_<N>`, `ARTIFACT_EGRESS_QUOTA`, `SIN_RESULTADO`, salida 75; 76/77/48/50 y
  `ARCHIVO_ORIGEN_FAILED` no transitorias); `registrar` también veta el intento N+1 de un no transitorio (rc 4) y la
  parada queda fijada (`parada.json`); «ausente» de R2 solo con el 404/NoSuchKey de HeadObject/GetObject; objeto no dict
  o desaparecido → rc 2; territorios y campaña saneados, `::error::` en una línea; causa normalizada y, si no es un
  código, `CAUSA_DESCONOCIDA` con el texto saneado aparte; umbral con enteros; D-147 en el cierre.
- Supuestos (no bloquean): claves bajo `campanas/<campaña>/` en el bucket de R2; los hechos de fuentes y puntos de
  control (ámbar/rojo) los aporta la comprobación previa del workflow (PR 3).
- Pruebas: `tests/test_t379_campana_estado.py` (37 tests; controles negativos de parada 2/3, 14/15 de 71, mínimo 3,
  idempotencia, sin_resultado, job verde sin salida, re-ejecución, lista mixta con ensayo, contrato del informe y uno por
  cada arreglo del revisor).
