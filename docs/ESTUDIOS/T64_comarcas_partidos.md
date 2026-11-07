# T-64 · Comarcas no oficiales frente a partidos judiciales (C-13)

Estudio, no implantación. Decide el propietario. Fecha 2026-11-07. Datos y huellas en `docs/ESTUDIOS/T64_comarcas_partidos/` (`SHA256SUMS.txt`).

## Recomendación
**Quedarse con los partidos judiciales** como unidad intermedia nacional. Con las comarcas agrarias del MAPA casan bien en agregado (NMI 0,90; ARI 0,60) y se solapan sin contradicción grave; el encaje es mediocre solo en algunas provincias de la meseta (ARI provincial mediano 0,47). Las comarcas agrarias no mejoran la cobertura (96,7 % frente a 98,7 %) y su criterio es agronómico, no de comunidad de interés. Opción alternativa (mezcla): usar la comarca oficial donde exista (Aragón, Cataluña), con partido judicial en el resto; añade una regla por territorio y no se justifica con estos números.

## 1. Fuentes de comarcas (cobertura nacional o amplia)
| Fuente | Autor / fecha | Cobertura | Licencia | Municipio→comarca descargable | Estado |
|---|---|---|---|---|---|
| **Comarcas agrarias** · Anexo I del RD 1076/2014 (BOE-A-2014-13257) | MAPA, 2014 (municipios del Catastro de rústica 2013; plan de regionalización de 1976) | España (316 comarcas; 7.861 de 8.132 municipios INE 2025 conciliados) | Texto del BOE, reutilizable | Sí, texto en `boe.es` (XML); parseado | **Usada.** sha256 XML `e3088680…a24df1` |
| Comarcas de Cataluña (Idescat) | Idescat, página «Códigos territoriales» (2026-11-07) | Solo Cataluña, 947 municipios, 43 comarcas (oficiales, no «no oficiales») | Idescat publica su licencia en su aviso legal; no verificada en esta sesión | Sí, tabla HTML | **Usada** (referencia). sha256 página `9111885f…1033` |
| Comarcas de Aragón (`inputs/COMARCAS.csv`, repo) | Gobierno de Aragón | Aragón, 731 municipios | del repo | Sí | **Usada** (referencia) |
| Comarcas ganaderas / agrarias del MAPA (capas IDE) | MAPA | España | — | No comprobado | `www.mapa.gob.es` corta la conexión (reset) aunque la red está abierta. **No obtenida** |
| Comarcas estadísticas autonómicas (IGE Galicia, Eustat, SADEI, Generalitat Valenciana…) | institutos autonómicos | cada comunidad | — | No comprobado | Hosts no pedidos. **No obtenidas** |
| INE | — | — | — | El INE no publica relación municipio→comarca nacional (solo códigos de municipio y provincia, `ine.es` responde) | — |

Limitación: sin los hosts autonómicos, solo hay una fuente no oficial de cobertura nacional (la agraria). Las comarcas agrarias salen del BOE, no de `mapa.gob.es`.

Conciliación agraria: 96,7 % de los municipios INE 2025; quedan 271 INE sin comarca y 379 nombres del anexo sin casar (fusiones, grafías en euskera/gallego/catalán o cambio de nombre desde 2013; p. ej. Echo, Gavín, Pueyo de Jaca en Huesca). Listado en `comarcas_agrarias_no_conciliados.csv`.

## 2. Encaje con los partidos judiciales (relación de #462, 8.028 municipios, 422 partidos)
Método: `encaje.py`. ARI y NMI entre las dos particiones de municipios; «mayoría única» = % de municipios cuyo partido tiene más del 50 % de sus municipios en una sola comarca; «comarca modal» = % de municipios situados en la comarca donde cae la mayoría de su partido.

| Comparación | Municipios | Partidos | Comarcas | ARI | NMI | Mayoría única | Comarca modal |
|---|---|---|---|---|---|---|---|
| Agrarias, España | 7.782 | 402 | 316 | 0,595 | 0,896 | 79,0 % | 73,5 % |
| Cataluña (Idescat) | 927 | 49 | 43 | 0,748 | 0,894 | 85,8 % | 80,8 % |
| Aragón | 727 | 16 | 33 | 0,472 | 0,760 | 55,6 % | 52,8 % |

Aviso: el ARI/NMI de España está inflado porque ambas particiones respetan la provincia; la medida honesta es la provincial. Agrarias por provincia (46 evaluables; Guipúzcoa y Vizcaya no, una sola unidad en un lado): ARI mediano 0,47, NMI mediano 0,66, «mayoría única» mediana 89,8 %; 12 provincias con ARI ≥ 0,6 y 8 con ARI < 0,3 (peores: Álava 0,11, Pontevedra 0,17, La Coruña 0,17, Cantabria 0,22, La Rioja 0,23). Por provincia: `encaje_agrarias.json`. Cataluña: ARI 0,92 en Gerona, 0,76 en Barcelona, 0,68 en Tarragona, 0,49 en Lérida. Aragón: Huesca 0,50, Zaragoza 0,55, Teruel 0,26.

## Desencajes notables (agrarias)
- Partido 19-01 (Guadalajara, 152 municipios): Campiña 67, Alcarria Alta 44, Alcarria Baja 23.
- Partido 44-03 (Teruel, 115): Sierra de Albarracín 32, Hoya de Teruel 30, Maestrazgo 26.
- Partido 47-01 (Valladolid, 114): Centro 68, Sureste 41.
- Partido 49-02 (Zamora, 108): Campos-Pan 31, Aliste 29, Sayago 24.
- Comarca Campos (Palencia): 61 municipios en un partido y 27 en otro; Rioja Alta (La Rioja): 44 y 31; Cuéllar (Segovia): 36, 20 y 11.
- Cataluña: el partido 25-04 (Lérida) reparte 32/24/8 entre tres comarcas.
Patrón: partidos grandes en provincias de pocos partidos agrupan varias comarcas (el partido es más grueso); en el cuadrante contrario hay comarcas partidas porque el partido sigue la cabecera judicial, no la comarca.

## Limitaciones
- Comarcas agrarias = criterio agronómico (1976), no comunidades de interés; no son «no oficiales» en sentido estricto (están en el BOE).
- Partidos judiciales de 1988 y municipios 2025: 1,3 % de municipios sin partido; las comarcas, 3,3 %.
- Sin pesos de población; todo cuenta municipios.
- Sin las capas autonómicas no se ha probado si una comarca estadística autonómica casa mejor.

## Reproducir
`python -I docs/ESTUDIOS/T64_comarcas_partidos/generar_comarcas_agrarias.py <rd1076.xml> …` y `python -I …/encaje.py <csv> codigo_ine id_comarca`. Relación de partidos: `configuracion/partidos_judiciales.csv` (sha256 `ae00cf82…89a`, de #462, commit e802cb59).
