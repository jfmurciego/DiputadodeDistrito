## 2026-11-10 — T-211 (2.ª parte) — D8 de la competición: fuera de tolerancia como los cuenta el contrato

**Causa:** en la batería r3 ganaron mapas con más distritos fuera de tolerancia que el canónico: Aragón 0→2, Castilla-La Mancha 5→8, Castilla y León 2→4, Galicia 6→8 (`CANDIDATOS.csv` de T-196). Con varias circunscripciones, el primer término de D8 contaba los fuera de tolerancia contra el objetivo de cada circunscripción. El contrato, el núcleo (`reglas.evaluar`) y el M04 (`outside_target_tolerance`) los cuentan contra el objetivo regional, en todos los distritos. En esos cuatro territorios, el ganador empataba con el canónico en el recuento por circunscripción y en el exceso sobre el tope, y ganaba por demarcaciones. No venía del tope, que solo ordena y no entra en el recuento, ni de las exenciones: ninguno de esos cuatro contratos tiene exentos, y las exenciones solo relajan el suelo. En Canarias, 14 de los distritos fuera de tolerancia contienen una partición exenta y el contrato también los cuenta. Los dos recuentos no van siempre en el mismo sentido (Canarias: el canónico tiene 21 por circunscripción y 20 por el objetivo regional; el ganador de r3, 20 y 21), así que la cifra publicada puede subir o bajar según el candidato. La 1.3.1 (#689) publicaba el recuento por circunscripción; esta versión vuelve al del contrato y lo hace también primer término de la clave.
**Cambio:**
- `ddd_motor2/naturalidad_clave.py` 1.1.0: en la competición (`natural_desde_m06`, también en las cadenas del Ponderado), el primer término es el recuento del contrato; el tope del 8 %, las demarcaciones, la frontera y el desvío siguen midiéndose por circunscripción. El laboratorio no cambia.
- `ddd_motor2/competicion.py` 1.3.2: lo publicado coincide con el primer término; los valores por circunscripción van a `extra.metricas_circunscripcion`.
- Copias en `legacy/`. Congreso y `HUELLAS_FIJAS`, sin cambios.
- Estudio actualizado en `docs/ESTUDIOS/T211_ponderado_autonomicas/` (con los 3 menores de la revisión de #689: cifras del laboratorio con su salida, exenciones medidas y el sentido cruzado de Canarias).

**Antes y después (en sesión, D8, 10 cadenas; el canónico sale igual que en r3):** Aragón 2→0, Castilla-La Mancha 8→5, Castilla y León 4→2, Galicia 8→6. El ganador iguala al canónico en fuera de tolerancia.
**Pruebas:**
- `tests.test_motor2_competicion_d8.FueraDelContrato`: falla con el código de `main` (gana la cadena con un distrito fuera del contrato) y pasa ahora.
- `AutonomicaReal`: País Vasco real, con `DDD_BATERIA_OUT`; en la CI se salta.
- Suite `test_motor2_*` y `GovernanceHeaders`.

**Riesgos:** ninguno en producción. Para que la batería dé las cifras nuevas hay que volver a correrla (la lanza el Operador). El M03 de la batería no trae `shared_border_m` (la frontera vale 0): queda como tarea aparte.
