## 2026-11-26 — T-461 — Nombres de distrito por capital de partido judicial

**Causa.** El diseño T-458 §3.2 (1.4.1) cambia la regla del nombre: 267 de 407 distritos acababan en «y entorno». Faltaba el dato clave: la capital de
cada partido judicial (`partidos_judiciales.csv` no la trae; la fijan las leyes autonómicas, Ley 38/1988 art. 4.4).

**Cambio.**
- `configuracion/fuentes/capitalidad_partidos/`: texto oficial (BOE, con sha256) de las 13 leyes de capitalidad de Andalucía, Asturias, Cantabria,
  Castilla-La Mancha, Castilla y León, Extremadura, La Rioja, Madrid, Murcia, Navarra, País Vasco (+ Ley 5/1992 como fuente de cambios) y Comunidad Valenciana.
- `herramientas/generar_capitales_partidos_judiciales.py` 1.0.0 → `configuracion/capitales_partidos_judiciales.csv` (287 capitales; cada partido del CSV de
  esas provincias tiene la suya; Castro-Urdiales es partido posterior al Anexo I y se marca `nueva_creacion`). Casos explícitos (Pola de Lena, Luarca, Infiesto,
  «Laja» por Loja) citados en el código.
- `herramientas/generar_nombres_comunidades_nacional.py` 1.1.2 → 1.2.0 (copia en `legacy/`): un municipio → su nombre; varios → capital de partido del distrito
  (la más poblada), si no, el municipio más poblado; municipio repartido o nombre repetido → «Madrid 1…N» (numeración existente). Sin «y entorno» ni comarca.
  Nueva columna `estado_capital` (`COMPLETO`/`SIN_FUENTE`). Regenerados los 52 `datos/distritos/nombres_congreso_*.csv` e informes.
- `toponimos_es.csv`: +23 nombres en español (Vitoria, Guernica, Estella, Jávea, Moncada, Denia, Liria, Vergara, Tarrasa…).

**Límite.** Aragón, Baleares, Canarias, Cataluña, Galicia, Ceuta y Melilla no tienen ley de capitalidad en el BOE consolidado y la nube solo llega a `boe.es`
e `ine.es`: sus distritos salen con la regla 2 y `estado_capital=SIN_FUENTE` (nombre provisional) hasta tener fuente. No se toca `explorar.js`.

**Pruebas.** `tests.test_capitales_partidos_judiciales` (valores literales de las leyes, cobertura, huellas, regenerable), `tests.test_nombres_comunidades_nacional`,
`GovernanceHeaders`, guardián. Sin efectos en huellas M05 ni checkpoints (no toca motor ni política).
