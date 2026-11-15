## 2026-11-15 — T-358 — Población por sección con relleno para el histórico de las generales (D-126)

Causa: D-126 fija la población por sección de 2011-11, 2015-12, 2016-06, 2019-04 y 2019-11 (Censo 2011 / Atlas 30832 del año)
y el relleno de «.» con el año del Atlas más cercano, con informe por provincia y marca > 1 %.
Cambio: `herramientas/poblacion_seccion_historica.py` 1.0.0 (solo cálculo, rutas locales con sha256 verificado contra
SHA256SUMS.txt de T-357, fallo si difiere), `tests/test_t358_poblacion_seccion_historica.py` (13 tests), y
`docs/ESTUDIOS/T358_POBLACION_SECCION_RELLENO/` (README + informe por provincia). El CSV real trae `""` por sección inexistente
y `..` (18 filas) además de `.`: `..` se trata como `.`. Resultado: 34 provincias-elección MARCA (>1 %): 12 en 2015-12, 11 en 2016-06, 11 en 2019-04.
Pruebas: test_t358 y test_t220 en verde; ejecución real determinista. Riesgos: ninguno en motor/workflows/contratos; la tabla completa
(5,4 MB) no se versiona. Se reabsorbe tras #831 (T-357).
