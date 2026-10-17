# N08 — Nueve casos físicos de componentes de partes mayores que K

**Análisis reproducible limitado, 2026-10-17.** Fuentes `D04_COMPONENTES_MAYORES_QUE_K.csv` y `MATRIZ_FACTIBILIDAD_52.csv`. No es una acreditación geométrica nueva ni prueba de factibilidad; `generation_authorized=false`.

| CPRO | K | P2025 | Target | Floor–Cap | Comp. partes / secciones | Multipartes | Estado del grafo |
|---|---:|---:|---:|---:|---:|---:|---|
| 04 Almería | 6 | 770554 | 128425.666666666667 | 109162–147689 | 8/1 | 3 | Sin bloqueo por este conteo |
| 07 Baleares | 10 | 1249844 | 124984.400000000000 | 106237–143732 | 144/4 | 34 | Sin bloqueo por este conteo |
| 09 Burgos | 3 | 362663 | 120887.666666666667 | 102755–139020 | 12/4 | 4 | K menor que componentes |
| 15 La Coruña | 9 | 1135623 | 126180.333333333333 | 107254–145107 | 21/1 | 9 | Sin bloqueo por este conteo |
| 17 Gerona | 7 | 830429 | 118632.714285714286 | 100838–136427 | 71/2 | 22 | Sin bloqueo por este conteo |
| 27 Lugo | 3 | 326022 | 108674.000000000000 | 92373–124975 | 9/1 | 6 | Sin bloqueo por este conteo |
| 30 Murcia | 13 | 1586989 | 122076.076923076923 | 103765–140387 | 25/1 | 4 | Sin bloqueo por este conteo |
| 34 Palencia | 1 | 158702 | 158702.000000000000 | 134897–182507 | 6/3 | 2 | K menor que componentes |
| 36 Pontevedra | 8 | 947818 | 118477.250000000000 | 100706–136248 | 9/2 | 5 | Sin bloqueo por este conteo |

**Criterio:** en Burgos (CPRO09, 4 componentes seccionales, K=3) y Palencia (CPRO34, 3, K=1), un grafo de ese número de componentes no puede cubrirse con K subgrafos conexos, salvo rectificación acreditada del dato o excepción nominal autorizada. No prueba imposibilidad administrativa. Las otras siete no fallan esta condición necesaria, pero no queda demostrada su factibilidad de población, continuidad de partes ni disciplina municipal. Los **nueve solapamientos intercomponentes del registro D son incidencias diferentes de estas nueve provincias**. Nunca se transformaron solapamientos en aristas.

## Tratamiento individual sin inventar evidencia

### 04 Almería
**K 6, componentes poligonales 8, seccionales 1.** Comprobar multipartes y geometría municipal; distinguir conexión CUSEC de conexión de sus partes.

Informe SHA256 `17e3428e1cdf486092224775d1d3fedf61072f2d79d14abea1103a36d8f1d17d`; checkpoint SHA256 `203a44d2a9c8333e3e3736bd85260d8c064e97b08aee89f20a4853fb03c7c675`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 07 Baleares
**K 10, componentes poligonales 144, seccionales 4.** Separar islas/islotes físicos y multipartes; ninguna conexión marítima automática.

Informe SHA256 `faf73864daf7ba313fd30d536b7c6c0d20eeabf8887ea8c69f4e71453c747746`; checkpoint SHA256 `a6bdc2fac66bc6dd2f07ea78fb9cc45796a5875b1cab1298d0eac68af6522ecd`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 09 Burgos
**K 3, componentes poligonales 12, seccionales 4.** Recuperar geometrías y buscar por qué cuatro componentes seccionales exceden K=3.

Informe SHA256 `532b811b867e3da2efb832835151432db451a9cf305dced5255cf993373edc43`; checkpoint SHA256 `0e44cdca04864ad1445a8af65f2ec89280622541dc7670f4cb21db7d24b80b8d`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 15 La Coruña
**K 9, componentes poligonales 21, seccionales 1.** Contrastar 9 multipartes; no atribuir discontinuidad administrativa por conteo.

Informe SHA256 `7f206870527596de1214a6677b4d92fe89445a1c57e095ebcda272873c36b2c1`; checkpoint SHA256 `7aca1132c7a5cae23a7995d57614948a41c97ab1fce17199c3999baa61d3be0b`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 17 Gerona
**K 7, componentes poligonales 71, seccionales 2.** Distinguir 71 fragmentos frente a 2 componentes seccionales y comprobar enclaves.

Informe SHA256 `bc5ecc0ec89e66030dcb4913901954afe9eabbfeba266ab816bbe6a01828a318`; checkpoint SHA256 `5990a5a78936e0455938ac847593ed0e51bccb967e3fc422ccb6a4c742a208c0`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 27 Lugo
**K 3, componentes poligonales 9, seccionales 1.** Revisar las 6 multipartes y posibles enclaves sin alterar aristas.

Informe SHA256 `789daf0f518834215d007bd180ddedccf2929262f99a732635a195f6d89f00c2`; checkpoint SHA256 `388bb101a5008ade2008390943d7261f3ccf6f8d9316d4a4fe601b9f3c84fcdd`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 30 Murcia
**K 13, componentes poligonales 25, seccionales 1.** Priorizar 17 solapamientos excluidos y cuatro multipartes.

Informe SHA256 `5ebf229df8e8d1e7f33b78350adac683e184691594c633f8bbdb896c39354247`; checkpoint SHA256 `cec8029b0cacd733224075671ebd10d050d9a823d5bea7b89b5f78d04a36be47`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 34 Palencia
**K 1, componentes poligonales 6, seccionales 3.** Investigar tres componentes seccionales con K=1; determinar si son discontinuidad legítima o defecto.

Informe SHA256 `22b069177b99e30ee97b7cdbd6f0e739a4c1a0935c404c9d44a177991c9f448a`; checkpoint SHA256 `e5bc9d3e43ad3e48c4d1ae2e0530d88a32391eb2d7ba58205a7157bbf4694685`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

### 36 Pontevedra
**K 8, componentes poligonales 9, seccionales 2.** Revisar 2 componentes seccionales y 5 multipartes en geometría original.

Informe SHA256 `7606ee42fe4247814cc850178e9b3e04651d37bb66aabc59c0c9741c3a384df5`; checkpoint SHA256 `75f537011429ea2c5ba13a8fd051edb2f0bb5534fe8cf556a02ab1b9a65d2a17`. Clasificación administrativa y cualquier excepción **pendientes de cotejo con origen geométrico y CNIG**.

## Vía de recuperación del INE ya versionado

Se comprobó en GitHub que existen `inputs/partes/seccionado_2025.zip.part00`, `.part01`, `.part02`, `MANIFEST_PARTES.sha256` y `reconstruir_fuentes.sh`. El script valida hashes individuales y el SHA del ZIP reunido `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`. Se verificó **presencia en repositorio y SHA declarados**, no bytes ni reconstrucción en esta ejecución. Ejecutar el script en un checkout que contenga también las cuatro partes del CSV poblacional para estudiar CRS, contactos por partes y su trazabilidad. La ausencia en worktrees no equivale a ausencia en GitHub. No imputar población de las 115 CUSEC multipartes por superficie ni introducir excepciones no aprobadas.

**Conclusión acotada:** nueve fichas y dos contradicciones necesarias del grafo clasificadas; siete casos sin esta contradicción concreta. No se acredita resolución causal de los nueve ni se propone todavía una decisión institucional nominal.
