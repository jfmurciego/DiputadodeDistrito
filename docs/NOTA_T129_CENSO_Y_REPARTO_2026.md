# T-129 — Población, censo y reparto de las generales (nota técnica cerrada)

Fecha: 2026-11-09 · Solo documentación, datos oficiales y tests; no toca motor, huellas ni contratos.

## Fuentes (todas del BOE, con sha256 del XML)
| Qué | Norma | Fichero | sha256 XML |
|---|---|---|---|
| Convocatoria 2026 (escaños) | RD 806/2026, BOE-A-2026-20742 | `configuracion/escanos_oficiales_congreso_2026.csv` | `5e1ae58f61d1031e085a1e60d1cccd86dd28d72639dd4d2b0ffded9ae5cb565e` |
| Cifras oficiales de población a 1-1-2025 | RD 1117/2025, BOE-A-2025-25362 | `configuracion/poblacion_oficial_provincias_2025-01-01.csv` | `c557f3932692291d19956e05748ca5f0aeaeeb5947bf56eeacc361bd11ae3d69` |
| Cifras oficiales de población a 1-1-2022 | RD 1037/2022, BOE-A-2022-21724 | `configuracion/poblacion_oficial_provincias_2022-01-01.csv` | `681d56a76ad304fff94724d956abfd3d405bd983204ca3589d5e5e013f31d340` |
| Escaños y votos 2023 | BOE-A-2023-18907 | `configuracion/resultados_oficiales_congreso_2023.csv` | `15950447…0323` (ya en el repo) |

## 1. Cifra que usa el reparto de 2026 (resuelto)
- El RD 806/2026 solo cita el art. 162 LOREG; la población es la de las **cifras oficiales** declaradas por real decreto (RD 1117/2025, a 1-1-2025, con efectos desde el 31-12-2025). Con ellas, el reparto del art. 162 (2 por provincia, 1 Ceuta y 1 Melilla, 248 por cociente y mayores restos) **reproduce el anexo en 50/50 provincias más Ceuta y Melilla** (52/52), incluidos Madrid 38, Cádiz 8, Ciudad Real 5 y Santa Cruz de Tenerife 7.
- Por qué difería: el proyecto usaba la tabla INE 65034 (padrón por sección, 49.128.297 hab.), que no es la cifra oficial (49.114.494 hab.). Santa Cruz de Tenerife: 1.087.319 (65034) frente a 1.082.421 (RD); Ciudad Real: 494.848 frente a 494.407. Con 65034 Tenerife gana el último resto por 241 hab. y sale 8/4. No he podido contrastar con el INE el origen exacto de la diferencia (servicios.ine.es no es accesible); el hecho comprobado es que son dos publicaciones con cifras distintas y solo la del RD reproduce el anexo.
- Efecto: Madrid 36,16 cuotas (36 enteras + 2 = 38); Cádiz 6,37 (6 + 2 = 8; sin el 9.º de 2023). Resultado cerrado: no queda nada pendiente de acreditar en el reparto.

## 2. 2023 (resuelto y probado)
Las cifras a 1-1-2022 (RD 1037/2022) reproducen los escaños de 2023 en 52/52 (test activo). Con los votos oficiales, D'Hondt reproduce los escaños por partido en todas las provincias.

## 3. Conclusión para el 29-N
- **Población para los 407 distritos:** la del proyecto. Dos usos distintos: (a) el K de cada provincia (N06: `K_i = max(1, ⌊(P_i+60.000)/120.000⌋)`, K2025=407) sale de población provincial 2025; (b) el trazado (M06) usa población y seccionado INE 2023 (contemporáneos de la elección de 2023, contratos `congreso_*`). Nada de esto depende del reparto de escaños de 2026 (N06 no es el reparto oficial) y los 407 no cambian por el RD 806/2026.
- **Hallazgo para decisión del propietario (K):** con las cifras oficiales del RD 1117/2025, Cádiz da P+60.000 = 1.317.041 → K=10, no 11 (con 65034: 1.321.420 → 11). El total sería 406, no 407. No lo cambio: K es decisión del propietario (N06) y el mapa de 407 no se regenera. Hay que decidir si K sigue con 65034 (como está) o con la cifra oficial.
- **Censo electoral (CER/CERA):** llega con los resultados de Interior (ZIP por mesa: censo, votantes y un registro CERA por provincia, ya cuadrado en `contratos_infoelectoral.yaml`). Sus secciones son las del censo electoral de la fecha de la elección, no el seccionado INE: se casan con el M06 por la tabla de equivalencia (D-17, tope 0,5 % de votos; `configuracion/equivalencia_secciones_congreso_2023.csv`). Esa tabla es de 2023: para el ZIP de 2026 hay que regenerarla con `herramientas/equivalencia_congreso_2023.py` cuando exista el ZIP (Interior no lo ha publicado: nada que probar hoy con 2026).
- **Cambios necesarios:** ninguno en contratos ni datos existentes. A hacer el 29-N, en cuanto haya ZIP: una tabla de equivalencia 2026 (fichero nuevo) y, si el propietario decide cambiar el K de Cádiz, el contrato `congreso_cadiz` y la política (ficheros compartidos: avisar al Coordinador antes).

## 4. Prueba de punta a punta con 2023 (Huesca)
`tests/test_reparto_art162.py::test_2023_dhondt_punta_a_punta_huesca`: cifras oficiales 1-1-2022 → 3 escaños → D'Hondt con los votos oficiales (PP 45.783, PSOE 40.307, VOX 15.155, SUMAR 13.774) → PP 2, PSOE 1, VOX 0, SUMAR 0 = resultado oficial. Además `test_2023_dhondt_todas_las_provincias`. No se ha ejecutado el archivista con el ZIP de Interior (no cabe sin el M06 de Huesca descargable aquí); queda cubierto por los tests de T-101.

## Reproducir
`python -m unittest tests.test_reparto_art162`
