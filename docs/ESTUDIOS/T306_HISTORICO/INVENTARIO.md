# T-306 · Inventario del histórico electoral desde 2011 (solo lectura)

Fecha: 2026-11-14 · Base: `main` (be525c2) · Plan 1.0.44 (D-40, D-65, D-70, D-77, D-80). No se ha lanzado ni cambiado nada.
Todo lo de abajo sale de ficheros del repositorio (sha256 en §6); lo que no se ha podido comprobar se marca «no verificado».

## 1. Generales 2011, 2015, 2016, 2019-04, 2019-11 y 2023

| Concepto | Estado | Fuente |
|---|---|---|
| Datos por sección, 52 × 6 | **Hecho**: paso B (T-83/T-110) reagregado a las secciones vigentes 2025 con peso de población (D-13); 312/312 cuadran (votos distritos = votos espejo) | `datos/resultados/historico/MANIFEST.json`; 107 ficheros por elección en `datos/resultados/historico/<AAAAMM>/` |
| Pérdidas | 2011: 5.752 votos de 23.942.870 (0,024 %), solo Alicante, Asturias, León, Lugo, Orense (D-70). Las otras 5 elecciones: 0 | `MANIFEST.json` |
| Contraste oficial | Solo **2019-11** (BOE-A-2019-18147: 256 comparaciones, defecto máx. 3,08 %) y **2023** (BOE-A-2023-18907: 197, 7,37 %); defecto = CERA. **2011, 2015, 2016 y 2019-04: sin oficial local (AVISO)** | `orchestracion/inventario_fuentes_historico.json` |
| M07/M08 sobre mapas vigentes (paso A, T-83A/T-113) | **Solo 3 de 52 provincias** (Álava, Badajoz, Huesca) × 6: M07 PASS (2 con excepciones declaradas), M08 OK, ganador igual que B. **Faltan 49 provincias × 6 (294 pares)** | `datos/resultados/historico/MANIFEST_M07.json` |
| Visor con dimensión de elección | La dimensión existe en código (T-199 `election_date`/`election_id`; T-201 vigente por elección) pero **el registro real no tiene ninguna entrada con `election_date`**: 339 productos (174 M06, 163 M08, 2 estáticos), todos de 2023 por defecto. **Histórico publicado: ninguno.** Fuera del registro hay capas ligeras de rotación (`datos/resultados/historico/rotacion/`, 52 csv) | `orchestracion/publicaciones_visor.json` |
| Siglas | Tal cual (homologación 2011-2026 en T-97, `datos/homologacion_siglas`) | MANIFEST |

**Falta**: (a) paso A en 49 provincias × 6; (b) contraste oficial en 4 elecciones; (c) decidir el mapa destino (ver §4); (d) publicar con elección en el registro (cierra pendientes de T-201: `identity_key` ya con elección; revisar `generar_hemiciclo` etc. con entradas reales); (e) Infoelectoral por mesa (solo 2023-07).

## 2. Autonómicas (D-40)

Calendario: `configuracion/calendario_autonomicas.csv` (79 filas; en alcance **75 elecciones en 17 comunidades**; Ceuta y Melilla no tienen). Fechas por comunidad (aut01…aut17):

| Id (calendario) | Elecciones en alcance desde 2011 |
|---|---|
| aut01 | 2012-03, 2015-03, 2018-12, 2022-06, 2026-05 |
| aut02 | 2011-05, 2015-05, 2019-05, 2023-05, 2026-02 |
| aut03 | 2011-05, 2012-03, 2015-05, 2019-05, 2023-05 |
| aut04 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut05 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut06 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut07 | 2011-05, 2015-05, 2019-05, 2022-02, 2026-03 |
| aut08 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut09 | 2012-11, 2015-09, 2017-12, 2021-02, 2024-05 |
| aut10 | 2011-05, 2015-05, 2019-04, 2023-05 |
| aut11 | 2011-05, 2015-05, 2019-05, 2023-05, 2025-12 |
| aut12 | 2012-10, 2016-09, 2020-07, 2024-02 |
| aut13 | 2011-05, 2015-05, 2019-05, 2021-05, 2023-05 |
| aut14 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut15 | 2011-05, 2015-05, 2019-05, 2023-05 |
| aut16 | 2012-10, 2016-09, 2020-07, 2024-04 |
| aut17 | 2011-05, 2015-05, 2019-05, 2023-05 |

El CSV da los ids (autNN); los nombres de comunidad están en `COBERTURA.csv`. Fechas a mes; 2026 incluye las ya convocadas/celebradas según el CSV.

Datos (T-176/T-207c, `docs/ESTUDIOS/T176_HISTORICO_AUTONOMICO/COBERTURA.csv`): **11 de 17 comunidades completas y cuadradas; 54 de 75 elecciones cuadran (≤ 0,5 %); 21 huecos** (el «había 3» está superado):

| Hueco | Elecciones | Causa |
|---|---|---|
| Aragón 2011, 2015 | 2 | fuente solo por municipio |
| Asturias | 5 | solo municipio (SADEI) |
| Cantabria 2011, 2015, 2019 | 3 | 2011 sin datos; 2015/2019 municipio incompleto |
| Castilla-La Mancha 2011, 2015, 2023 | 3 | solo municipio |
| Murcia 2011, 2015, 2023 | 3 | solo municipio (CREM) |
| Extremadura | 5 | solo provincia, incompleto |

Los 12 cuadres de Andalucía, Aragón y Baleares son contra el total del espejo, **sin total oficial** (boletines no alcanzables desde la nube). Reparto por población dentro de municipio: no se hace sin decisión del propietario. Publicados en el visor: ninguno (mismo registro sin `election_date`).

## 3. Fuentes: qué hay y dónde

**Votos y censo por sección (generales 2011-2023)** — Observatorio Electoral de las Naciones, `orchestracion/fuente_nazioenbehatokia.json`: 625 ficheros con sha256 (52 `data/<elección>/sekzioa/<cpro>.json` × 6 + 52 `geo/sekzioak/<año>` × 6 + `index.json`). **No están en git ni en `archivo_r2.json` ni en `fuentes_r2.json`**; la copia R2 (`fuentes/nazioenbehatokia/`) figuraba «pendiente de subir» en T-81 y no la encuentro indexada: no verificado. Es la única fuente completa y secundaria.

**Seccionados INE por año** (URL oficial `https://www.ine.es/prodyser/cartografia/seccionado_<año>.zip`; sha256 de T-85, `docs/AUDITORIAS/T85_EQUIVALENCIA_SECCIONADOS/informe.json`):

| Año (elección) | sha256 | ¿En R2 (`fuentes_r2.json`)? |
|---|---|---|
| 2012 (2011-11) | 772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a | No |
| 2015 (2015-12) | 50dda58ed4afb57c7f1f38e6b6b8150768efaa225bfc3a523b9c210a2a218c03 | No |
| 2016 (2016-06) | 3410af763bfe58d1b0f9c0d0038cbdd6417e0f3f6d0fce6a3e70bef64c84b3e1 | No |
| 2019 (2019-04) | 656119dadadb57ef3fa9d20a8ba33399fe606e553c9fef3fc338786e52fae967 | No |
| 2020 (2019-11) | 07544bb49256e9e9f290b6f459a0a833e69c97900eb840c3f5bbe863914ede6e | No |
| 2024 (2023-07) | df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7 | Sí, `arc-e/fuentes/ine/seccionado_2024_df931fa0d372.zip` |
| 2023 (mapas vigentes) | 7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f | Sí, `…/seccionado_2023_7a15e700a459.zip` |
| 2025 | 55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4 | Sí |
| Padrón INE 65034 | 91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3 | Sí |

INE sí se descarga desde runner (los 3 de 2023-2025 se bajaron el 14-11), así que los 5 históricos que faltan en R2 **no exigen al propietario**: basta repetir la descarga con `adquirir_fuentes_ine.py` y comprobar el sha256 de arriba.

**Infoelectoral por mesa (Interior)**: solo `02202307_MESA.zip` (sha256 e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8, 4.578.794 B): release `fuente-infoelectoral-02202307` y R2 `arc-e/fuentes/interior/02202307_MESA_e78fc231326a.zip`. **Faltan 2011, 2015, 2016, 2019-04 y 2019-11.** Los bloquea Interior a runners y nube; los tendrá que bajar el propietario. Por el patrón del nombre (2023-07 = `02` + `2023` + `07`), los ficheros serían `02201111_MESA.zip`, `02201512_MESA.zip`, `02201606_MESA.zip`, `02201904_MESA.zip`, `02201911_MESA.zip` en `https://infoelectoral.interior.gob.es/estaticos/docxl/apliextr/` — **patrón inferido, no verificado**: confirmar nombre y existencia en la web de Infoelectoral (descarga de ficheros por mesa) antes de pedírselo. Son **opcionales**: sirven de contraste independiente (CERA) y de segunda fuente; el paso A funciona con el espejo del Observatorio.

**BOE de resultados** (contraste local): 2019-11 y 2023 hechos. Faltan las resoluciones de la JEC de 2011, 2015, 2016 y 2019-04 (BOE, descargables desde la nube: `boe.es` está permitido; el identificador hay que localizarlo, no lo doy de memoria).

**Autonómicas**: ver `COBERTURA.csv`; proveedores en el calendario (SIEL Andalucía, etc.). Descargas manuales de los 21 huecos: lista en `docs/DESCARGAS_MANUALES.md`.

## 4. Método (reutilizable y decisión pendiente)

1. **Paso B actual (hecho)**: equivalencia año→2025 con `herramientas/equivalencia_seccionados.py` (1:1 al 95 %, peso de población, astillas < 1 %), tablas T-85. Reparte votos de secciones no 1:1 (no 1:1 por elección: 23,3 %, 12,4 %, 11,3 %, 6,4 %, 5,9 %, 1,6 %).
2. **Regla T-291/M07 7.4.0** (D-65): sección entera al distrito con mayor población, **sin repartir votos**; clases 1:1, contenida, partida, sin_vigente; ya implementada para 2026→2023 (`herramientas/equivalencia_seccionado_2026_2023.py`, tabla de 1.277 secciones, `section_reconciliation.equivalence_table`). Su cruce usa `equivalencia_seccionados.equivalencia`, genérico: reutilizable para año→2023 (o →2025) sin motor nuevo.
3. **Pérdidas de 2011**: D-70, aceptadas y documentadas (5 provincias, 0,024 % nacional); heredar tal cual.
4. **Decisión del propietario que condiciona todo**: ¿mapa destino **2023** (D-65, T-291) o **2025** (T-85 y la edición 2026, D-80)? Las tablas existentes y los 312 cuadres son contra 2025; D-65 y la regla «sin repartir votos» piden 2023. Con 2023 hay que regenerar las tablas año→2023 (5 seccionados por descargar, §3) y re-cuadrar; con 2025 solo falta el paso A. Además B reparte votos y la regla de M07 no: si se adopta la regla de T-291, el cuadre por provincia cambia (los votos de secciones partidas van enteros), conviene que lo confirme el propietario. D-77: «después del corte»; D-65/propietario lo adelanta (según el encargo).

## 5. Plan por pasos y coste estimado (sin lanzar nada)

Tomo T-155 como referencia: 135 min de jobs por provincia 00; el histórico no pasa por M04/M05 (T-83A), así que es mucho más barato. Las cifras de runs son estimaciones mías, no medidas.

| Paso | Qué | Chats / runs | Coste aprox. |
|---|---|---|---|
| 0 | Decidir mapa destino (§4) y si hay contraste por mesa | propietario | 0 |
| 1 | Subir el espejo del Observatorio a R2 y descargar a R2 los 5 seccionados INE con sha256 de §3 | 1 implementador + 1 run de fuentes (Operador) | ~1 chat + ~20 min de job |
| 2 | Tablas de equivalencia año→destino (regla T-291) para 6 años × 52 | 1 implementador (local, ~minutos por provincia) | ~1 chat; sin run |
| 3 | Paso A en 49 provincias × 6 (`historico_m07m08.py` desde el Gestor, T-113) con puerta 04 | 1 campaña autorizada (D-52) + 1 chat Operador | estimo 294 pares × ~2-5 min = 10-25 h de job (no medido) |
| 4 | Contraste oficial: 4 BOE (2011, 2015, 2016, 2019-04) y, opcional, Infoelectoral por mesa descargado por el propietario | 1 implementador | ~1 chat |
| 5 | Publicación con `election_date` (≥ 6 entradas × 52 en el registro), pendientes de T-201 | 1 implementador + 1 run `05` autorizado | ~1-2 chats + 1 run |
| 6 | Autonómicas: los 21 huecos son descarga manual (propietario); el resto, publicar las 54 que cuadran | propietario + 1 chat | según decisión |

Total: ~4-5 chats de implementación, 1 campaña de paso A, 2 runs menores, con la incertidumbre de pasos 3 y 5 marcada.

## 6. Huellas de los ficheros citados (sha256 inicial)

`configuracion/resultados_oficiales_congreso_2019_11.csv` 9a533386… · `…_2023.csv` c7a636f2… · `configuracion/calendario_autonomicas.csv` 5c866ec5… · `orchestracion/fuente_nazioenbehatokia.json` b22ff749… · `orchestracion/inventario_fuentes_historico.json` 63b87495… · `datos/resultados/historico/MANIFEST.json` 978109f7… · `MANIFEST_M07.json` fa846347… · `configuracion/equivalencia_seccionado_ine_2026_a_2023.csv` d57d5fcf… · `COBERTURA.csv` c28cf610…
