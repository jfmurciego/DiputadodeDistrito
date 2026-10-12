# Comunidad Valenciana 2023/2023: universo oficial y puerta geométrica

Fecha de auditoría: 2026-10-12. Rama de trabajo: `codex/f10-valencia-universo-2023`, base `34c8793cede82e1f82832c84fc43c6a990394905`.

## Resultado reproducible de identidad y población

La discrepancia de 360 no es una diferencia de edición ni una duplicación de secciones. La respuesta WFS INE `Secciones_2023` incluye dos tipos de entidad. En la provincia 46 hay 1.823 features `SECCIONADO` y 360 `DISTRITO`; al contar sin filtrar se suman 2.183 CUSEC. Los distritos llevan el código agregado terminado en `000` y no forman parte del universo de secciones. En toda la comunidad, los tres GeoJSON INE conservados tienen 3.503 `SECCIONADO` y 768 `DISTRITO`.

La selección de INE 65034 para periodo 2023, sexo Total y todas las edades contiene 3.503 CUSEC numéricos. Su conjunto coincide exactamente con el de las 3.503 geometrías oficiales `SECCIONADO`, sin duplicados ni valores inválidos. La población suma 5.216.195: Alicante 1.955.268 (1.236 secciones), Castellón 604.086 (444) y Valencia 2.656.841 (1.823). El detalle trazable está en [universo_2023.json](universo_2023.json), generado por `herramientas/auditar_universo_valencia_2023.py` desde los originales protegidos.

Las 46 filas en blanco de 65034 que el análisis anterior trató como secciones pendientes no pertenecen al conjunto `SECCIONADO` de 2023 ni a la capa oficial de personas del Censo 2023. Por tanto, no son secciones exigibles para esta pareja temporal. No se han convertido en cero. En la comprobación interanual, 35 identificadores aparecen en el seccionado 2025 y 11 no aparecen ni en 2023 ni en 2025; esa diferencia no permite atribuir por sí sola una causa estadística a cada fila en blanco. La ausencia de población para esas filas no bloquea la cobertura del universo 2023 acreditado.

La capa oficial de personas del Censo 2023 (servicio REST INE, capa 2) confirma por provincia las mismas 3.503 identidades y los mismos totales, sin nulos ni divergencias de valor. Es evidencia de contraste poblacional, no fuente de sustitución geométrica: sus metadatos señalan que el mapa de secciones de referencia parte de la cartografía electoral INE a 01-01-2018.

## Procedencia y hashes

| Artefacto oficial | URL / selección | SHA-256 |
|---|---|---|
| INE 65034 original, cuatro partes concatenadas | `https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv`; selección 2023 / Total / Todas las edades / CPRO 03, 12, 46 | `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3` |
| Población seleccionada TSV (evidencia derivada) | Almacén protegido `F10-20261012-cierre/comunidad_valenciana/population_ine_65034_2023_03_12_46.csv.tsv` | `e8edd7b1b684e8b3c6ef4d105b5af7b546ff6ed08544d64f5ff29efe53906f21` |
| Geometría INE 2023, Alicante | OGC Features `WMS_INE_SECCIONES_G01:Secciones_2023`, CPRO 03 | `b1ce66fcab1f7b418e1f56bd4ea23d0ab66f460c52707f87efe54854fcaad7cb` |
| Geometría INE 2023, Castellón | Misma colección, CPRO 12 | `886bb1ad78ad7f96d36e6c883eed3a38d43c858b4217c728ad851739a2cd2ff3` |
| Geometría INE 2023, Valencia | Misma colección, CPRO 46 | `4e0597c12ea2be75cf5e630578388c0825fdde97818abe142d155d7d378da58e` |
| WFS alternativo protegido, CPRO 46 | `https://www.ine.es/geoserver/WMS_INE_SECCIONES_G01/wfs`, colección `Secciones_2023`, ZIP original | `2f79e6cf3e8fbc014e67af41e7e8595f7761e86bd6dc7effd6e39cac8a15aea4` |
| INE Censo 2023 personas, metadatos capa 2 | servicio REST oficial; bytes originales preservados en almacén | `52746de646a65e0b1cfdcd139c305fbee437b88e021c39a46687d7ea8b6b25a8` |
| Respuesta Censo 2023, CPRO 03 / 12 / 46 | consultas originales por CPRO, bytes JSON preservados | `acbc7a60725e221612c71f9095dd96c0f279919b87b4717b02dadba6eb8eb5d2` / `25166f2b184e690379eb011798f62e00d19a774974b10804c8f1fbe1b0c91de0` / `6804ceeecdba53e2c8e2f1bb4fe0bd331cf987ec2c38303c4557a55548120953` |
| Geometría del servicio Censo 2023, CPRO 46 | Respuesta original GeoJSON EPSG:25830 | `2dee7414ae346153f021203b0fb50851edab65f9f9ce8821cb0213487247d5ac` |

Las respuestas REST se adquirieron el 2026-10-12 entre 12:42 y 12:45 UTC; manifiesto y payloads originales están en `F10-20261012-valencia-investigacion/` dentro del almacén protegido. Los tres GeoJSON de secciones ya estaban protegidos en la adquisición F10-20261011. No se repitieron descargas.

## Bloqueo geométrico restante

El contrato M02 aplicable conserva CRS de trabajo EPSG:3035 y máximo de solapamiento de precisión de 1 m². La geometría 2023 oficial produce dos intersecciones superiores al límite: `4617201001/4619401008` = 11,8277092397 m² y `4617201001/4619401013` = 12,1112377964 m². Ambos pares no crean arista según el predicado del consumidor, pero incumplen la regla de solapamiento. La normalización de consenso de las cuatro geometrías inválidas conserva las fronteras y no cambia la topología; no elimina esos dos defectos.

La alternativa WFS tiene el mismo conjunto de 1.823 secciones de Valencia y es prácticamente coincidente con la geometría oficial previa, pero declara seis geometrías inválidas (tres `SECCIONADO`: `4613201001`, `4614503005`, `4615101001`, y tres filas `DISTRITO`). También mantiene los solapamientos: en su evaluación EPSG:3035 miden 11,622500542 m² y 11,901114100 m². La geometría de Censo 2023 tiene el mismo conjunto y las mismas intersecciones; tampoco es una representación alternativa que corrija el defecto. La normalización topológica previa acredita la corrección de invalidez para cuatro secciones de la fuente principal, pero M02 sigue `BLOCKED`.

No hay una corrección geométrica legítima acreditada con la evidencia oficial consultada. Recortar o desplazar esas fronteras alteraría geometría fuente sin fe de erratas o cartografía oficial corregida. No se ha cambiado tolerancia, no se han usado `buffer(0)`, snap ni recortes. La puerta de identidad/cobertura poblacional queda superada; la pareja territorial valenciana no queda certificada mientras esos dos solapamientos excedan el contrato.

## Decisión mínima requerida de Work

Solicitar al INE una geometría oficial 2023 corregida o una fe de erratas que resuelva los dos pares concretos, conservando identificadores y cobertura. Si no existe corrección oficial, Work debe decidir contractualmente entre mantener la puerta bloqueada o aceptar explícitamente una excepción técnica de precisión para esos pares; esa excepción no se presume y no puede presentarse como acreditación geométrica ordinaria. La tolerancia vigente no se ha alterado.

## Validación

Reproducir con:

```sh
python3 herramientas/auditar_universo_valencia_2023.py \
  --population /ruta/protegida/population_ine_65034_2023_03_12_46.csv.tsv \
  --geometry-dir /ruta/protegida/comunidad_valenciana/evidence/raw/secciones_censales/2023 \
  --out docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/universo_2023.json
python3 -m unittest tests.test_f10_valencia_2023_universe -v
```

Las entradas se pasan explícitamente; el programa no descarga ni altera originales. El conjunto de identidades de secciones tiene SHA-256 `896acc73b089709bd07802c9f301d9f5bcc224ca0f5620210542dfd76ff682c4`.
