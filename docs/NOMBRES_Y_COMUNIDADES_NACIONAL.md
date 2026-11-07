# Nombres de distrito y comarcas partidas — Nacional (T-59)

VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Nombres, comarcas y partidos judiciales
FECHA: 2026-11-07
ESTADO: activo
CAMBIOS: C-13 con partidos judiciales en toda España (T-64).
MOTIVO: documentar la definición de T-59 (en el repo C-12 = nombres, C-13 = comunidades de interés).
ANTERIOR: legacy/2026-11-07_nombres_comunidades_v1.0.0/NOMBRES_Y_COMUNIDADES_NACIONAL_v1.0.0.md

## Qué hay
- `herramientas/generar_nombres_comunidades_nacional.py` (1.0.0) lee los M06 publicados
  (`orchestracion/publicaciones_visor.json`, `canonical_m06`, run más reciente, sha256 verificado) y escribe en
  `datos/distritos/`: `nombres_<territorio>.csv`, `informe_<territorio>.md` y `MANIFEST.json`.
- 49 provincias, 325 distritos. Sin votos ni partidos. No toca motor, contratos, workflows ni M06.
- Regenerar: `python herramientas/generar_nombres_comunidades_nacional.py --m06-dir <dir> --descargar`.
- `municipios_ine_2025.csv` (código, nombre INE, población) sale del INE 65034
  (`--reconstruir-municipios 65034.csv.zip`; suma 49.128.297). El M06 trae los nombres en orden alfabético y los
  códigos en orden numérico, y con nombres cartográficos abreviados: por eso el nombre se toma del INE por código.

## Reglas de nombre (C-12 nacional)
1. Un solo municipio: «Municipio»; si está repartido entre k>1 distritos, «Municipio n» (n: norte a sur y, a igual
   latitud, oeste a este, por centroide).
2. Varios municipios: «Comarca» si todos están en una comarca de la fuente del repo; si no, «Principal y entorno»
   (principal = más poblado, INE 2025).
3. Colisión: « n» por posición; último recurso « (id)».
Topónimos solo en español: `datos/distritos/toponimos_es.csv` (por código INE); lo no resuelto (barra, apóstrofo
catalán) hace fallar la herramienta y el test.

## Comarcas partidas (C-13)
Fuentes en el repo: solo `inputs/COMARCAS.csv` (Aragón: Huesca, Teruel, Zaragoza). Castilla y León y el resto no
tienen comarcas ni partidos judiciales: `NOT_EVALUABLE` (no se infieren, según `AUDITORIA_C13`). Una comarca está
partida si sus municipios tocan más de un distrito; un municipio dividido cuenta en todos sus distritos. No se
asigna población por debajo del municipio, así que no hay retención poblacional.

## Partidos judiciales (T-64)
`configuracion/partidos_judiciales.csv` (`herramientas/generar_partidos_judiciales.py`) sale del Anexo I de la Ley 38/1988
(BOE-A-1988-29622; texto original del 30-12-1988, sha256 en la cabecera del CSV). El texto consolidado del BOE
(2026-07-09) omite los anexos, así que es la relación original de 1988: no recoge partidos creados después. Casa con el
INE por código+nombre (7.416), nombre parcial (246), nombre (35) o código solo (329, nombre en otra lengua; columna
`conciliacion`). Sin partido: 106 municipios del INE (creados o fusionados después de 1988) y 20 filas del anexo, en
`configuracion/partidos_judiciales_no_conciliados.csv`. C-13 evalúa las 49 provincias con partidos (cobertura en cada
informe); las comarcas siguen solo en Aragón: no hay otra fuente oficial con hash en el repo (Cataluña, El Bierzo
pendientes de una norma del BOE con la relación municipal).
