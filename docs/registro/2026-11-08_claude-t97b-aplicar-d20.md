## 2026-11-08 — T-97 — Aplicar D-20 a la tabla de siglas (83 filas BAJA → DECIDIDA)

**Causa.** El propietario resolvió en D-20 (docs/PLAN.md, 08-11) las 83 filas de certeza BAJA de la tabla de #524.

**Cambio.** `reglas_generales.json` 1.1.0 y tabla regenerada: familias «Podemos–Sumar» (Podemos, En Comú, Podemos-Compromís,
Podemos-En Marea 2015 y las demás de a0/a1), «CiU–Junts» (CiU, DL, CDC y JxCAT-JUNTS), «UPN y coaliciones» (UPN-PP, NA+, U.P.N.),
«CHA-IU»; PDeCAT-E-CiU → PDeCAT, PSM-IV-EXM-EQUO → MÉS; En Marea, Caballas y MDyC tal cual. Nivel nuevo `DECIDIDA` (83 filas; ya no
queda ninguna BAJA); la sigla real de cada año sigue en `sigla_fuente`. `herramientas/homologacion_siglas.py` 1.1.0 (copia 1.0.0 en
`legacy/herramientas/`). Las etiquetas de familia sustituyen a SUMAR/JUNTS/UPN de la propuesta; el hemiciclo no usa esta tabla.
No toca la rotación de T-84 ni el visor.

**Pruebas.** `tests/test_homologacion_siglas.py` (D-20 con valores literales; ninguna fila BAJA; 83 DECIDIDA); `comprobar` en verde;
Interior (2019-11, 2023) sigue cubierto. **Efectos.** Ninguno en M04/M05/M06, huellas ni 00. PR apilada sobre #524.
