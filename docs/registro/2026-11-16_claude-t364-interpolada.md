## 2026-11-16 — T-364 — Población por sección: interpolación y ajuste municipal (D-128)

Causa: D-128 (propietario, 16-11) sustituye el relleno por año más cercano de D-126 por una regla refinada.
Cambio: `herramientas/poblacion_seccion_historica.py` 1.1.0 (1.0.0 en `legacy/`): «.» → interpolación lineal entre el año anterior y
el siguiente de la misma sección (`interpolada`; un solo lado → `mas_cercana`); ajuste proporcional por municipio solo de las
secciones estimadas a la población oficial INE (tabla 29005, padrón; sha256 en `docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt`),
con aviso y sin ajuste si residuo ≤ 0, sin_dato o municipio ausente; salida por elección `sección,población,origen,ajustada,años_fuente`
e informes por provincia (población estimada, MARCA > 1 %, municipios ajustados, desajuste medio) y por municipio. 2011-11 no se ajusta
(Censo a 1-nov; fichero oficial censal municipal NO VERIFICADO). Sin cambios en motor ni workflows.
Ampliación (Planificador, misma PR): las secciones del seccionado INE del año que el Atlas no trae con valor (no listadas o vacías) se estiman como «.» (`origen=no_listada`; entrada `--seccionados`, sha256 verificado, falla cerrado si no cuadra); `--estricto` falla también con `sin_dato`.
Pruebas: `tests/test_t364_poblacion_seccion_historica.py` (sustituye a test_t358; controles negativos: un solo lado, empate, residuo negativo/cero,
sha256 distinto). Riesgos: ninguno en producción (herramienta de cálculo sin consumidores aún; T-365 consumirá la tabla). PR: ver T-364.
