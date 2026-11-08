## 2026-11-08 — T-97 — Tabla de homologación de siglas de las generales 2011-2023 (propuesta, sin aplicar)

**Causa.** La rotación del visor (T-84) cuenta «PP-EU → PP» como cambio de ganador (hallazgo de T-83A): las siglas cambian entre
elecciones y circunscripciones.

**Cambio.** `datos/homologacion_siglas/`: `homologacion_siglas_generales.csv` (3.501 filas: elección, circunscripción, sigla de la fuente,
votos, familia `f`, partido homologado, nivel de certeza ALTA/MEDIA/BAJA, regla, corroboración con Interior, ruta y sha256 del
fichero del espejo T-89), `.json` (huellas, recuento por certeza y las 83 filas BAJA agrupadas = decisiones para el propietario) y
`reglas_generales.json` (reglas a mano: familia `f` y excepciones por sigla/elección/provincia). `herramientas/homologacion_siglas.py`
1.0.0 (`construir`, `comprobar`). Interior solo corrobora 2019-11 y 2023 (BOE versionado); 2011, 2015, 2016 y 2019-04 no están
adquiridas. Discrepancias con la familia de la fuente: UPN-PP/NA+ (Navarra) → UPN, PDeCAT-E-CiU ≠ Junts (2023), Caballas y MDyC (Ceuta)
≠ CpM (Melilla). **Es criterio: se presenta al propietario antes de usarla; no se aplica a la rotación ni se toca el visor.**

**Pruebas.** `tests/test_homologacion_siglas.py` (sintético: precedencia, votos nulos, sha256, cobertura de Interior; y la tabla
versionada con los casos acordados); `comprobar` en verde. Todos los partidos con escaño de Interior (2019-11 y 2023) tienen fila.

**Efectos.** Ninguno en M04/M05/M06, huellas, checkpoints ni 00. No lanza ni publica.
