## 2026-11-08 — T-112 — Candidaturas proclamadas 2026 y homologación de siglas

**Causa.** D-25: faltaba el censo de partidos de las generales del 29-11-2026 y su enlace con las familias de D-20.

**Cambio.** (1) `configuracion/candidaturas_congreso_2026.csv` (+ `.json` con fuente y sha256): 551 candidaturas de Congreso en 52 circunscripciones, de BOE-A-2026-23103 (sha256 XML `8513892d…f276d`) con la corrección BOE-A-2026-23383 (`4c9ada8d…ba85`: Navarra «EH BILDU-ERC»→«EH BILDU» y La Rioja PCTE 4+1). 21 «No proclamada». Cada lista proclamada tiene tantos candidatos como escaños del RD 806/2026 (Cádiz 8, Madrid 38). (2) `herramientas/extraer_candidaturas_boe.py` (reproduce el CSV desde los XML con sha256). (3) `datos/homologacion_siglas/reglas_candidaturas_2026.json` + `homologacion_candidaturas_2026.csv` + `herramientas/homologacion_candidaturas_2026.py` (construir/comprobar): familias D-20 («Podemos–Sumar», «CiU–Junts», «UPN y coaliciones», «CHA-IU»). Tabla 2011-2023 y mapa Interior intactos (no se renombra nada).

**Para el propietario (BAJA, sin decidir).** Frente Amplio (FA y rotulaciones) ¿«Podemos–Sumar» o propio?; Comuns-Front Ampli; Aramés-EU-MS (Aragón); Compromís-EUPV-Podem-ERPV (en 2023 iba dentro de SUMAR); Unidad del Pueblo Canario (NC-BC+Podemos+IU+Sumar); Convergents (escisión CDC); Ceuta «PODEMOS (PAZ,CASA Y TRABAJO)».

**Pruebas.** `tests/test_homologacion_candidaturas_2026.py` y `tests.test_homologacion_siglas`: OK. Sin efecto en M04/M05/huellas ni en ningún modo de 00.

**Riesgos.** Las siglas son las del BOE; la tabla no se aplica aún a la rotación (T-84).
