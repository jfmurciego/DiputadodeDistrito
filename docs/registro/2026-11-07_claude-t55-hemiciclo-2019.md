## 2026-11-07 — T-55 — Hemiciclo: columna (b) con el oficial de 2019-11

Causa: la columna (b) «elección anterior» salía «sin fuente».
Cambio: `configuracion/resultados_oficiales_congreso_2019_11.csv` y `.json` (BOE-A-2019-18147, corrección de 17-12-2019 de la
BOE-A-2019-17344, publicada el 18-12-2019; sha256 del XML y del CSV en el `.json`), extraídos del BOE con
`generar_hemiciclo.py --extraer-boe-2019`. `generar_hemiciclo.py` 1.2.0 rellena (b), exige 350 escaños y que cada
circunscripción cuadre. Siglas homologadas con `HOMOLOGACION_2019`: ERC, JUNTS y CCa se renombran; Unidas Podemos y sus
confluencias (PODEMOS-IU, ECP-GUANYEM EL CANVI, PODEMOS-EU) se asimilan a SUMAR (convención de comparación); el resto
conserva su sigla del BOE (Cs, MÁS PAÍS-EQUO, MÉS COMPROMÍS, NA+, PP-FORO…).
Pruebas: `tests.test_generar_hemiciclo` (total 350; Soria y Teruel contra el BOE; totales estatales).
Sin efecto en huellas ni en checkpoints; no requiere 00. Pendiente: regenerar y publicar el hemiciclo (fuera de alcance).
