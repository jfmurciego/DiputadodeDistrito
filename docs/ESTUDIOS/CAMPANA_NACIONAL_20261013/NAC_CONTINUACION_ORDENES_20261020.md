# Continuación NAC — órdenes de bosque y catálogo CNIG (20-10-2026)

Este expediente amplía, sin reemplazar, `NAC_CONTINUACION_20261020.md` y el artefacto de búsqueda de una sola orden. No modifica el histórico del 19-10-2026.

## Resultado K>1 con varios órdenes deterministas

Se extendió la búsqueda diagnóstica para probar, con presupuesto fijo, hasta diez órdenes de raíz/vecindad para el bosque BFS: `cusec`, `degree_desc`, `population_desc`, `hash_order`, `degree_asc`, `population_asc`, `degree_pop_asc`, `degree_pop_desc`, `hash_seed_1`, `hash_seed_2`. Los nombres definen ordenaciones estables descritas en `herramientas/diagnosticar_factibilidad_congreso_k_multiple.py`; cada orden se identifica además por SHA-256 de su secuencia CUSEC. La búsqueda se detiene en el primer testigo; un caso sin testigo ejecuta los diez órdenes.

Reproducción exacta desde la raíz del repositorio:

```sh
python3 herramientas/diagnosticar_factibilidad_congreso_k_multiple.py \
  --preflight-root docs/ESTUDIOS/CAMPANA_NACIONAL_20261013 \
  --product-root docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto \
  --contract territorios/congreso/contrato_congreso_2026.json \
  --max-states 1 --tree-max-states 5000 --tree-max-transitions 30000 \
  --forest-orderings cusec,degree_desc,population_desc,hash_order,degree_asc,population_asc,degree_pop_asc,degree_pop_desc,hash_seed_1,hash_seed_2 \
  --output /tmp/NAC_K_MULTIPLE_ORDERS_20261020.json
```

El archivo completo, con hashes de entradas, órdenes probados, presupuestos, testigos y estados, está en `NAC_K_MULTIPLE_ORDERS_20261020.json` (SHA-256 `e1dd017815854fc2012a87a41bd7f7a4d061b8ed02fb949c4bbe85868925311f`). Se reprodujo en dos procesos independientes y ambos generaron bytes idénticos.

Resultados entre las 44 unidades K>1. La reconciliación contra el artefacto previo es explícita: el resultado anterior era **6/30/8** (testigos condicionales / sin testigo dentro de la búsqueda acotada / límites de componentes condicionales). Los siete testigos nuevos trasladan siete casos de la segunda categoría a la primera; no cambian los ocho casos de componentes.

- **13** `TREE_WITNESS_FOUND_CONDITIONAL`: seis ya se encontraban con el orden CUSEC y siete adicionales se encontraron con otros órdenes: CPRO 21, 22, 24, 25, 26, 32 y 45.
- **23** `SEARCH_EXHAUSTED`: se agotaron los diez órdenes dentro de los presupuestos; no es prueba de inviabilidad ni búsqueda exhaustiva sobre todos los árboles o particiones del grafo.
- **8** `NECESSARY_CONDITION_FAILED_CONDITIONAL`: CPRO 04, 07, 09, 15, 17, 27, 30 y 36, por el conteo de componentes de partes del producto; requiere resolver la semántica/identidad de esas partes antes de elevar la conclusión.

Por tanto, el resultado actualizado es **13/23/8**, y coincide con el recuento de estados de ambos artefactos. El artefacto anterior `NAC_K_MULTIPLE_BOUNDED_20261020_final.json` tiene SHA-256 `bd48322c3d12f6c5a457cc510c19ea037d09ee8711bb4545a008463aa9b0dde7`; el nuevo mantiene SHA-256 `e1dd017815854fc2012a87a41bd7f7a4d061b8ed02fb949c4bbe85868925311f`.

Los testigos se validan internamente como cortes de aristas del bosque seleccionado. El grafo sigue siendo el de secciones CUSEC y no acredita conectividad entre partes multipartes, política municipal, excepción administrativa, contraste CNIG o factibilidad territorial integral. No se guardan asignaciones ni se generan distritos: `partition_emitted=false`, `districts_generated=0`, `generation_authorized=false`.

### Seguimiento del solver exacto acotado

Se volvió a ejecutar el solver exacto existente sobre los 23 casos sin testigo
en los diez bosques, con `max_groups=10000` y `max_states=5000`. Los 23
terminaron en `SEARCH_EXHAUSTED` por `CONNECTED_GROUP_BUDGET`, tras enumerar
10.001 grupos y antes de entrar a estados de cobertura exacta (`explored_states=0`).
El registro por CPRO, con cotas, SHA de entrada y presupuestos, está en
`NAC_K_EXACT_BUDGET_DIAGNOSTIC_20261020.json` (SHA-256
`c3299f38a448b60e1ac5142c6d2608f6b50aeca7f8ef262410bcff8ff39ea88e`). Este
resultado demuestra una limitación del presupuesto del enumerador, no
imposibilidad matemática ni factibilidad.

Se amplió el presupuesto exacto a 50.000 grupos, con 5.000 estados, solo para
diez casos previamente agotados y de K bajo (CPRO 01, 02, 06, 13, 20, 23, 31,
39, 43 y 47). Los diez volvieron a agotar `CONNECTED_GROUP_BUDGET` antes de
explorar estados de cobertura; no hubo testigo ni certificado de imposibilidad.
El solver informa 50.001 grupos porque comprueba el umbral tras insertar el
grupo centinela; esa semántica está cubierta por su prueba existente. Detalle y
hashes de entrada: `NAC_K_EXACT_LOW_K_FOLLOWUP_20261020.json` (SHA-256
`c3a4bb159e4547fde5ff9f7b656dfd63ef2555239ed4cf6c30a2fb1824b39a7c`). No se
guardan asignaciones.

Se completó el mismo presupuesto para los otros trece casos agotados que no
estaban en esa selección (CPRO 03, 08, 11, 14, 18, 28, 29, 33, 35, 38, 41,
46 y 48). Los trece agotaron `CONNECTED_GROUP_BUDGET` antes de explorar
estados de cobertura exacta; no se encontró testigo y no se probó inviabilidad.
El registro por CPRO, con poblaciones, cotas y hashes de entrada, está en
`NAC_K_EXACT_REMAINING_FOLLOWUP_20261020.json` (SHA-256
`cdb0f4d3c9353b956ca22e8126a21c3d086ae209b6b93c7e856d9682860dda91`). En
conjunto, los 23 casos `SEARCH_EXHAUSTED` tienen ahora una búsqueda exacta
adicional de hasta 50.000 grupos y 5.000 estados; todos agotaron grupos y
ninguno alcanzó la cobertura exacta. Esto sigue siendo límite de presupuesto,
no conclusión de factibilidad ni de inviabilidad.

Como búsqueda distinta, se evaluó la partición por cortes de bosque sobre los
mismos 23 casos: cinco órdenes deterministas de raíz/vecindad, hasta 10.000
estados y 50.000 transiciones por bosque. Los 115 árboles se completaron sin
agotar el presupuesto, pero ninguno admitió una partición dentro de su bosque
(`TREE_WITNESS_NOT_FOUND`). Esto descarta únicamente esos cinco bosques por
caso; no prueba inviabilidad del grafo completo. El artefacto por CPRO, orden,
hashes y presupuesto es `NAC_K_MULTIFOREST_FOLLOWUP_20261020.json` (SHA-256
`2dcc11868813ad952634adb3b3473a655e988b509fd2305b380aee39db146a8c`). No se
emitieron asignaciones.

## Hechos adicionales del catálogo oficial CNIG/IGN

Consulta del catálogo oficial el 20-10-2026. La colección pública de “Límites municipales, provinciales y autonómicos” lista snapshots históricos GeoPackage de **2023** y **2024**, pero no lista un archivo histórico 2025 en la ficha consultada. El detalle del producto 2024 identifica `BDDAE20240101_CONHISTO.GPKG`, fecha 01/01/2024, toda España, escala 1:25.000 y tamaño publicado de 222,71 MB. Es un producto nacional utilizable como contraste temporal cercano, pero no acredita por sí mismo el estado efectivo al 01/01/2025.

La descripción oficial indica que la geometría interpreta títulos inscritos en el Registro Central de Cartografía; advierte que algunos tramos son provisionales por carecer de título jurídico y que la incertidumbre de líneas puede ser de unos 40 m por mediciones históricas, trazado sobre mapa y digitalización, salvo tramos con trabajos posteriores de precisión. Esto limita el uso: el producto sirve para contrastar adscripción administrativa y documentación registral según su edición; no sustituye la frontera física INE entre secciones ni permite convertir tolerancias cartográficas en aristas.

La nota IGN del 03-03-2026 describe `TIME` en el WMS como visualización histórica desde 2009. El WMS no ofrece, según la evidencia localizada, un snapshot vectorial lossless 2025 ni una precisión que permita certificar vértices. El esquema publicado por OGC API define `date_boundary` y `endlifespanversion` como cadenas con formato de fecha, `legalstatus` y `accuracy` como cadenas, pero no declara en el esquema la inclusividad temporal ni una tolerancia numérica uniforme; el CRS de almacenamiento es CRS84 sin época declarada. La OGC API sigue necesitando documentación oficial de semántica temporal, completitud atómica del snapshot y exactitud/precisión de geometrías.

Fuentes oficiales consultadas:

- [Catálogo del producto y archivos disponibles](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=LILIM)
- [Detalle del archivo histórico 2024](https://centrodedescargas.cnig.es/CentroDescargas/detalleArchivo?sec=12969664)
- [Aviso IGN sobre el WMS temporal](https://www.ign.es/web/ign/portal/noticias?_IGNNoticias_WAR_IGNNoticiasportlet_advancedSearch=false&_IGNNoticias_WAR_IGNNoticiasportlet_andOperator=true&_IGNNoticias_WAR_IGNNoticiasportlet_cur=100&_IGNNoticias_WAR_IGNNoticiasportlet_delta=1&_IGNNoticias_WAR_IGNNoticiasportlet_keywords=&_IGNNoticias_WAR_IGNNoticiasportlet_resetCur=false&p_p_col_count=1&p_p_col_id=column-1&p_p_id=IGNNoticias_WAR_IGNNoticiasportlet&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal)
- [Colección IGN OGC API Features](https://api-features.ign.es/collections/administrativeboundary)

No se descargó geometría ni se modificó el recibo CNIG. **NAC-01 sigue `BLOCKED_EXTERNAL`**: hace falta el snapshot 2025 exacto o una reconstrucción oficial certificada, más metadatos de temporalidad, registro jurídico, precisión y hashes. El catálogo ofrece un producto 2024, que no llena el hueco temporal.

## Publicación y base actual

El `main` vigente verificado es `cdcf56c1bfbe185c674857e0bd8b96146e57568f`, e incluye #276 y #288. La rama de integración local `codex/nac-integracion-main-20261020` conserva como segundo padre el candidato original y fusionó `main` en el commit `7e6e11a2a08fb8de2e3c31627630d279e61c2d40`; la fusión fue automática, sin conflictos. La candidata original `codex/nac-continuacion-20261020` queda intacta en `2ae21c9a64908dc458c8f1225c82baeb17d6c0a6`. Desde la base común `bcbad45ee4a285547682f087824430f11fd88876`, las rutas modificadas por `main` y por la línea NAC no se solapan. El cambio de contrato local conserva el guard de generación desactivada; no cambia K ni políticas.

La rama integrada no se pudo publicar: el canal GitHub había rechazado la escritura bajo `approval policy is never`; no se reintentó ni se eludió el control. El patch binario se preparó y verificó contra el SHA exacto de `main`; la ruta y sus hashes están en el manifiesto externo de entrega. No hay PR ni CI remota para esta candidata. El artefacto de los 44 casos se reprodujo sobre la integración y coincidió byte por byte con SHA-256 `e1dd017815854fc2012a87a41bd7f7a4d061b8ed02fb949c4bbe85868925311f`.

## Estado al checkpoint

- NAC-01/NAC-02: `BLOCKED_EXTERNAL` (snapshot exacto 2025 y metadatos oficiales ausentes).
- NAC-03: `PARTIAL_PROGRESS` (auditor estricto y búsqueda con múltiples órdenes; falta prueba de captura real completa y acreditación).
- NAC-04/NAC-05: `NOT_EXECUTABLE` hasta recibo histórico validado.
- NAC-08: `REVIEW_PASS_WITH_SCOPE_LIMITS` para el diff integrado y revisión `REVIEW_PASS` del seguimiento de los 13 casos restantes. La revisión cubre código/evidencias entregadas, no certifica topología ni factibilidad territorial.
- NAC-09: `PARTIAL_PROGRESS`, con 13 testigos condicionales, 23 agotamientos entre los diez órdenes de bosque y 8 límites de componentes condicionales; los 23 casos agotados también se sometieron a un presupuesto exacto mayor sin llegar a cobertura exacta.
- Integración: `main` incorporado localmente en `7e6e11a2…`; el HEAD final y su hash constan en el manifiesto externo de entrega. Patch binario aplicable y verificado contra `cdcf56c1bfbe185c674857e0bd8b96146e57568f`; su manifiesto de entrega registra ruta y SHA-256. PR/CI: no existe PR ni CI por la restricción de escritura.
- Producción: `generation_authorized=false`, ningún distrito generado ni producto certificado.

La actualización preserva las versiones funcionales anteriores de los dos módulos en
`legacy/nac_continuacion_20261020/`. La prueba
`test_explicit_node_order_is_deterministic_and_must_cover_graph` ejecuta dos
órdenes válidos distintos y confirma que `input_sha256` es idéntico aunque el
bosque BFS pueda variar.

En la candidata integrada se ejecutaron 150 pruebas de Congreso con PASS y 25
pruebas focales de excepciones/WMS/API con PASS (algunas regresiones se repiten
intencionadamente). Dos módulos no pudieron importarse por dependencias del
entorno ausentes: `test_congreso_preflight_adapter` requiere Shapely y
`test_congreso_topology` requiere GeoPandas; no se marcaron como PASS.

La rama integrada incorpora las modificaciones de `main` de #276 y #288 sin
conflictos; el conjunto de pruebas de #276/#288 ejecutado y las regresiones NAC
no detectaron interferencias. Las dos suites geoespaciales siguen sin poder
ejecutarse en este entorno y permanecen `NOT_VERIFIED`.
