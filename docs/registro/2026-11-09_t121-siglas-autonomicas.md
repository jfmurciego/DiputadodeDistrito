## 2026-11-09 — T-121 — Siglas de las autonómicas (paso 4, D-20) y rotación homologada de las 3 comunidades de prueba

**Causa:** la rotación autonómica no debe contar variantes de la misma marca («PP-EU → PP», «PSC → PSOE») como cambio de ganador.

**Cambio:** `herramientas/homologacion_siglas_autonomicas.py` 1.0.0 (nuevo; reutiliza el `resolver` de T-97 sin modificar `homologacion_siglas.py`), `datos/homologacion_siglas/reglas_autonomicas.json` (reglas propias, se suman a `reglas_generales.json`: las familias del Observatorio son las mismas) y `homologacion_siglas_autonomicas.csv` (314 filas: comunidad, elección, sigla, familia, homologado, nivel, regla, sha256). Una familia sin regla no es error: sigla tal cual con nivel BAJA. Regla nueva para Navarra (las generales usan el código de provincia 31; sin ella UPN-PP caería en la familia del PP). `reagregacion_autonomicas.py` aplica la tabla y `rotacion.csv` de Galicia, Madrid y Castilla y León queda homologada (distritos que cambian de ganador alguna vez: 7/75, 103/135, 52/82).
**Dudosas para decisión del propietario:** BAJA (sin regla, 9 siglas): DO (Galicia), PCAS-TC (CyL, Madrid), CB, P.P.SO., VBM, ADEIZA-UPZ, ZAMORA DECIDE, CRA, CONTIGO (CyL). MEDIA con criterio razonado: Podemos y confluencias → «Podemos–Sumar», marcas de IU → «IU», ESCAÑOS EN BLANCO (EB/Eb), RECORTES CERO(-GRUPO VERDE), AHORA DECIDE(/AS), C 21/C.XXI, PCTE, CILUS. Lista regenerable con `homologacion_siglas_autonomicas.py dudosas`.

**Pruebas:** `tests/test_homologacion_siglas_autonomicas.py` (6, a mano; tabla real revalidada).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Apilada sobre #570. Nada lanzado ni publicado.
