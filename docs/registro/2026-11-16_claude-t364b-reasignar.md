## 2026-11-16 — T-364b — Población por sección: residuo no bloqueante, provincias apartadas y reasignación (D-128)

Causa: el Planificador resuelve los avisos de T-364 (#840): residuo ≤ 0, secciones sin dato en ningún año y 52 secciones de 2019-11 sin pareja en el seccionado 2020.
Cambio: `herramientas/poblacion_seccion_historica.py` 1.2.0 (1.1.0 en `legacy/`): (a) residuo ≤ 0 = aviso no bloqueante, estimadas sin ajuste con `ajustada=sin_ajuste_municipal`;
(b) provincia-elección con `sin_dato` o sin sucesora única = APARTADA (sin filas en la tabla, `estado`/`motivo` en `informe_provincias.csv`); (c) población de las secciones que no existen
en el seccionado del año, entera a la sucesora de mayor población (`equivalencia_seccionados`, geometría del seccionado más cercano que la tenga), `origen=reasignada`; todo cuenta
en el % estimado. `--estricto` solo da 2 con provincias apartadas y las tablas se escriben siempre. Seccionados 2021 y 2022 medidos en `docs/ESTUDIOS/T364_*/SHA256SUMS.txt`.
Interfaz: mismas 5 columnas; `origen` gana `reasignada`, `ajustada` gana `sin_ajuste_municipal`.
Revisión: la sucesora debe ser de la misma provincia (si no, apartada) y las de otro municipio (segregaciones) se cuentan en `reasignadas_otro_municipio`; el README declara la conservación (cambia al sustituir una estimación) y el criterio conservador del 1 %. Siguiente paso: T-365b regenerar los 5 `configuracion/historico_epoca/contrato_*.json`, que anclan el sha256 de la tabla anterior; con la tabla nueva `materializar` falla cerrado hasta regenerarlos (main no se rompe: las tablas viven fuera del repo).
Pruebas: `tests/test_t364_poblacion_seccion_historica.py` (48; controles negativos: empate, sin geometría, sucesora fuera del seccionado, sin_dato, donante más cercano) y T-365/T-339/R015/T-220.
Riesgos: sin efecto en producción; T-365 debe regenerar sus contratos con las tablas nuevas (2015-12 y 2016-06 pierden las provincias apartadas). PR: ver T-364b.
