# M01 — Preparar base territorial y población

## Propósito
M01 convierte dos fuentes oficiales heterogéneas —cartografía censal y población— en la **unidad territorial canónica del procedimiento**. Su producto no es «1.463 secciones»: son las 1.463 entidades censales individualizadas, con identificador CUSEC normalizado, atributos administrativos, población y geometría.

## Por qué existe
Todo lo posterior opera sobre secciones. Si una sección falta, se duplica, tiene población incorrecta o CUSEC ambiguo, el error se propaga a adyacencias, grafo, distritos y resultados electorales. M01 aísla la ingestión pesada del algoritmo iterativo y permite reutilizar una base estable.

## Entradas
Cartografía, población y, opcionalmente, una tabla de comunidades de interés. El adaptador comarcal usa exclusivamente `Municipio código` normalizado a cinco dígitos, equivalente al prefijo municipal de `CUSEC_KEY`; nunca une por nombre.

## Transformaciones
Filtra Aragón antes de cargar innecesariamente toda España; normaliza CUSEC a 10 dígitos; filtra población por año/sexo total/edad total; asocia población por CUSEC; conserva atributos administrativos y geometría.

## Producto canónico
`aragon_2025_m01_secciones_poblacion.geojson.zip`: una feature por sección, con geometría y atributos. La capa auditable añade `M01/secciones.csv`, que expone todas las filas y atributos no geométricos. `PRODUCTOS.json` identifica el GeoJSON por ruta, bytes y SHA-256.

## Validaciones mínimas
CUSEC no nulo y único; población asociada; provincias declaradas; hash de fuentes conocido. Si `io.input.comarcas.enabled` está activo, se rechazan códigos municipales inválidos, asignaciones comarcales contradictorias y, por defecto, cualquier municipio sin cobertura. El informe M01 registra total, coincidencias, faltantes y ratio de cobertura.

## Reutilización
M01 pertenece a la preparación M01-M03. En ejecución iterativa no se recalcula si la clave de preparación coincide; la ejecución debe referenciar explícitamente la preparación reutilizada y hacer accesible su producto.
