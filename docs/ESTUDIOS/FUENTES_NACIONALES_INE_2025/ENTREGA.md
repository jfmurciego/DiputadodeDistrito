# Fuentes oficiales nacionales INE 2025/2025

## Producto

`territorios/congreso/fuentes/ine_2025_2025/` contiene la tabla de población unida por igualdad textual exacta de CUSEC a los seis atributos territoriales de las 36.554 geometrías N07, una copia del crosswalk, manifiesto de procedencia y hashes. Las coordenadas no se duplican: el manifiesto identifica el seccionado oficial protegido y su hash; el consumidor puede unir la tabla al Shapefile de origen por CUSEC. Los ZIP originales se reconstruyen desde las partes protegidas de `inputs/partes/`.

El manifiesto registra la versión 1.0.0, los contratos de entrada y salida, versiones del entorno, hashes de las partes y ZIP reconstruidos, el crosswalk y la evidencia N07, los recuentos y la orden reproducible. La reconstrucción no usa red ni repite adquisiciones oficiales.

## Reproducción independiente

La validación leyó las cuatro partes protegidas de `65034.csv.zip` y las tres partes del seccionado 2025; verificó cada hash contra `inputs/partes/MANIFEST_PARTES.sha256` y los hashes agregados protegidos. Se reprodujo también `herramientas/crosswalk_nacional.py` desde el ZIP geométrico y su crosswalk coincidió con el artefacto N07 por SHA-256.

La extracción poblacional filtra `Periodo=2025`, `Sexo=Total` y `Edad=Todas las edades`. El INE incluye códigos históricos sin observación (`Total` vacío); el sistema de adquisiciones los define como ausentes, no como cero. Se observaron 338 filas de esa clase, fuera del universo N07. El universo vigente quedó cubierto sin omisiones ni extras y no se aceptó ninguna sección adicional con valor. La tabla contiene CUSEC, CUMUN, CPRO, CMUN, CDIS, CSEC y `POB_2025`; antes de escribir se compara cada atributo con N07.

Resultado independiente: 36.554 CUSEC únicos, 36.554 de 36.554 geometrías, cero duplicados, cero valores inválidos, CRS EPSG:25830, geometrías individuales no vacías y válidas. La suma por sección es 49.128.297 y concilia exactamente con los 52 agregados provinciales y con el total nacional. Ceuta: 56 secciones y 83.567 habitantes. Melilla: 44 secciones y 87.067 habitantes. Cada código de circunscripción 01–52 está representado.

Una segunda reproducción del script completo generó los tres archivos del paquete con SHA-256 idéntico a los versionados: crosswalk `0ceb2cab…f14d54`, tabla poblacional `c4a22fc4…c4a988` y manifiesto `f99e1690…dbadc37`.

Comando de reproducción (requiere el entorno geoespacial instalado y directorio de salida nuevo):

```sh
python herramientas/materializar_fuentes_nacionales_ine.py \
  --parts-dir inputs/partes \
  --crosswalk docs/ESTUDIOS/N07_20261011/result/crosswalk.csv \
  --output /ruta/a/directorio-nuevo
```

## Contrato y límites

El contrato de fuentes de Nacional referencia las dos fuentes con acreditación técnica, año, autoridad, hashes y registro de adquisición. Su estado institucional sigue `CANDIDATO_WAIT_OWNER`; `population_reference`, unidad mínima, decisiones, K, cuotas y acreditación de circunscripciones continúan pendientes. `generation_authorized` permanece `false`. La pareja de fuentes no aprueba esas decisiones ni habilita producción.

La geometría se acredita a nivel de entidades y atributos frente a N07, con validez individual por entidad. Las limitaciones topológicas declaradas por N07 siguen vigentes: esta entrega no certifica adyacencias, solapes, conectividad física ni overlay provincial independiente. No adopta K ni cuotas, y no genera distritos.
