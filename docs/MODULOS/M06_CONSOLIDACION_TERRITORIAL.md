# M06 — Consolidar y describir distritos

## Versión vigente
**7.2.0 — Catálogo con comunidades de interés opcionales**.

## Propósito
M06 transforma la asignación interna producida por M05 en **entidades distritales auditables**. No optimiza, no mueve secciones y no cambia `district_id`. Su responsabilidad es materializar, medir, describir y validar una solución ya cerrada antes de incorporar resultados electorales u otros atributos posteriores.

Esta separación es obligatoria: si M06 pudiera corregir población o contigüidad, se perdería la trazabilidad entre optimización y publicación.

## Entradas
La entrada canónica es el GeoJSON de secciones generado por M05. Debe contener al menos identificador de sección, distrito y población; puede conservar además provincia, municipio, CUDIS y metadatos de unidades M04.

## Productos
M06 genera cuatro familias de producto:

1. **Resumen poblacional por distrito**: población, target, diferencia absoluta y relativa, ratio población/target, suelo, techo, cumplimiento duro y cumplimiento de tolerancia.
2. **Catálogo distrital auditable**: una fila por distrito con población, secciones, municipios, provincias y métricas geométricas.
3. **Composición territorial exacta**: una fila por sección con su distrito y atributos administrativos suficientes para reconstruir la asignación sin abrir GIS.
4. **Productos GIS**: GeoJSON de secciones con asignación final y GeoJSON disuelto con una geometría por distrito.

## Catálogo distrital
El catálogo incluye, cuando los campos existen en la fuente:
- `district_id`;
- `district_pop`;
- `target`;
- diferencia y desviación relativa;
- `population_target_ratio`;
- suelo y techo poblacionales;
- cumplimiento de límites duros y tolerancia;
- número de secciones;
- número/códigos/nombres de municipios;
- número/códigos/nombres de provincias;
- número/códigos/nombres de comunidades de interés, cuando existen;
- superficie en km²;
- perímetro en km;
- compacidad Polsby–Popper;
- centroide en CRS métrico;
- bounding box;
- CRS métrico utilizado.

El CRS para métricas es configurable. Castilla y León CYL-05 utiliza `EPSG:3035`, evitando que el módulo dependa de una zona UTM concreta y permitiendo su reutilización europea.

## Composición territorial
El CSV de composición conserva una fila por sección y permite responder exactamente a la pregunta «¿qué secciones forman este distrito?». Incluye `CUSEC_KEY`, `district_id`, población y, cuando están disponibles, provincia, municipio, comarca, CUDIS, `ddd_unit_id` y `ddd_closed_urban`.

## Invariantes duras
M06 debe abortar si incumple cualquiera de estas condiciones configuradas:
- identificadores de sección únicos;
- K esperado;
- conservación exacta de filas;
- conservación exacta de población;
- ausencia de violaciones poblacionales duras heredadas;
- provincia única por distrito cuando el contrato territorial lo exige;
- catálogo con una fila por distrito;
- composición con una fila por sección.

La puerta territorial CYL-05 añade además una comparación externa M05↔M06: el mapa `CUSEC_KEY → district_id` debe ser idéntico antes y después de consolidar.

## Por qué estas métricas
Población mide equilibrio; composición proporciona trazabilidad; municipio y provincia describen coherencia administrativa; área, perímetro y compacidad ayudan a detectar formas territorialmente aberrantes; centroide y bounding box facilitan inspección GIS y automatización posterior.

## Denominación humana
La denominación del distrito no pertenece todavía a M06. Se incorporará únicamente cuando exista una capa fiable de barrios/toponimia y reglas explícitas de denominación. No se inventarán nombres mediante «ejes» urbanos ni heurísticas no auditadas.

## Evolución
M06 puede incorporar densidad, población por municipio, continuidad municipal, comarca, cabecera y métricas geométricas adicionales sin alterar la identidad básica del distrito ni asumir responsabilidades de M05.
