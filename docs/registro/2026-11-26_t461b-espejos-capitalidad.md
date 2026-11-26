## 2026-11-26 — T-461b — Descubrir las leyes de capitalidad de Aragón, Baleares, Canarias, Cataluña y Galicia

**Causa.** T-461 (#1021) cubre 12 comunidades con las leyes de capitalidad del BOE; las otras cinco no están en el BOE consolidado y la nube solo llega a `boe.es` e `ine.es`.

**Cambio.** `configuracion/espejos_fuentes_oficiales.json` 1.4.0 (copia en `legacy/`): entrada `capitalidad-partidos-judiciales` solo de descubrimiento (sin url ni huella;
no se espeja ni sube) con los hosts de DOGC, DOG, BOA, BOIB y BOC y sus portales como páginas semilla. Sin tocar el workflow ni la herramienta.

**Uso y límite.** Con frase del propietario, el runner de P10 lanza «descubrir» con `capitalidad-partidos-judiciales`: el log trae estado, redirecciones y sha256 de cada portal.
`descubrir` solo mide ficheros de datos que citan el año o «auton/elecci/cortes»; las leyes son páginas HTML, así que la URL buena de cada ley se fija después por PR
y esa PR sustituye `SIN_CAPITAL`.

**Pruebas.** `tests.test_t461b_espejo_capitalidad`, `test_t448`, `test_t449`, `GovernanceHeaders`.
