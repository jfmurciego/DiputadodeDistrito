## 2026-11-09 — T-131 — Histórico autonómico, lote 1: Cataluña, Comunidad Valenciana, Navarra, País Vasco, La Rioja y Canarias

**Causa:** orden del propietario (vía Planificador): las 16 comunidades restantes desde 2011, cada una con su calendario; lotes con territorio de prueba (ya en main: Galicia, Madrid, Castilla y León).

**Cambio:** `reagregacion_autonomicas.py` 1.1.0 (copia 1.0.0 en `legacy/`): (1) La Rioja: el Observatorio mete el voto CERA como pseudo-sección sin geometría con exactamente los votos CERA del total autonómico; se identifica así y se excluye (sin ello fallaba el tope por el CERA: 0,6 %); (2) Canarias 2011: 8 secciones sin censo en la fuente cuentan 0 y se declaran en el MANIFEST. Datos en `datos/resultados/historico/autonomicas/<comunidad>/` (23 elecciones; 6 comunidades): todas cuadran, pérdida máxima 0,14 % (Comunidad Valenciana 2011, 3 335 votos). Aproximadas en distrito (secciones vigentes ausentes de la composición M06, asignadas por geometría): todas salvo Galicia y Castilla y León; cifras en la tabla de #570.
**Sin entrar en este lote (motivo):** Andalucía, Aragón, Illes Balears: sin composición M06 en el repositorio; Extremadura: solo dato provincial; Asturias, Cantabria, Castilla-La Mancha, Murcia: sección solo en alguna elección (el resto, municipal: lote aparte con peso D-13).

**Pruebas:** `tests/test_reagregacion_autonomicas.py` (CERA a mano; cuadre de las 9 comunidades entregadas).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Sin siglas nuevas (la tabla autonómica se regenerará con las decisiones del propietario). Nada lanzado ni publicado.
