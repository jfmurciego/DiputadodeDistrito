# Nombres de distrito y comarcas partidas — Nacional (T-59)

VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Nombres y comarcas nacionales
FECHA: 2026-11-07
ESTADO: activo
CAMBIOS: documento nuevo.
MOTIVO: documentar la definición de T-59 (en el repo C-12 = nombres, C-13 = comunidades de interés).
ANTERIOR: ninguna (fichero nuevo)

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
