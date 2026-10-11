# Contrato candidato de distritación DDD del Congreso

**Versión:** 0.1.0  
**Fecha:** 2026-10-11  
**Estado:** candidato `WAIT_OWNER`; no habilita ejecución productiva.  
**Identidad:** `execution_identity=congreso`, `territory_id=espana_congreso`.  
**Predecesor:** ninguno; incremento local separado de la PR #237.

## Ámbito y universo

El ámbito es una sola Nación para el estudio y eventual contrato DDD del Congreso. El universo estructural se cierra en 52 circunscripciones: 50 provincias, con códigos `01`–`50`, y Ceuta y Melilla, códigos `51` y `52`. El código identifica una circunscripción y no acredita que haya una geometría o fuente vigente. La admisión debe rechazar códigos ausentes, repetidos o ajenos al universo y cualquier sustitución por los 19 ámbitos autonómicos.

La barrera provincial es obligatoria: las unidades de una provincia no se asignan a otra circunscripción. Ceuta y Melilla se tratan como unidades separadas. No se permiten aristas entre circunscripciones. Las islas, enclaves, exclaves y discontinuidades físicas requieren inventario de fuente, regla explícita y resolución contractual antes de admitir datos; la conectividad por proximidad no crea por sí sola una arista.

## Fuentes, población y unidades

No se ha seleccionado una edición poblacional ni cartográfica. Antes de una ejecución deberán declararse organismo y producto de origen, edición, año de referencia, fecha de adquisición autorizada, cobertura 52/52, unidad geográfica y regla de correspondencia entre geometría y población. Se conservarán archivos originales, bytes, SHA-256, recibos auténticos, compatibilidad de esquema, identidad territorial y manifest de ejecución. Un derivado no sustituye el recibo del original.

La unidad mínima, la clave estable y el tratamiento de cambios entre ediciones quedan `WAIT_OWNER`. La sección censal es una candidata técnica, no una selección aprobada. También quedan pendientes la población objetivo, sus límites y su alineación temporal con la geometría. Municipios grandes y la indivisibilidad municipal requieren decisión expresa y una regla verificable.

La contigüidad deberá tener una definición geométrica reproducible, política de errores topológicos y tratamiento aprobado de componentes insulares y discontinuidades. Los umbrales de Aragón o de otros parlamentos autonómicos no se heredan como política nacional.

## Reparto electoral y K DDD

El reparto legal de escaños del Congreso y el número DDD de distritos uninominales son decisiones distintas. La Constitución fija un Congreso de entre 300 y 400 miembros y circunscripción provincial. La LOREG establece 350 escaños: dos iniciales por provincia, uno por Ceuta y Melilla y los 248 restantes distribuidos por población provincial para la convocatoria. Este reparto electoral no constituye por sí mismo cuotas DDD.

El proyecto registra cartografía histórica con 391 IDs y una incidencia documental 392/391 sin procedencia suficiente para resolverla. No se adopta como norma. El análisis exploratorio ha evaluado escenarios K=383, 407, 409 y 435; también registra dos escenarios con K=409 bajo métodos diferentes. Son comparaciones analíticas, no una recomendación automática ni un resultado institucional. No se selecciona K. El propietario debe aprobar K, método de cuotas por las 52 circunscripciones, fundamento y versión de decisión antes de continuar.

Referencias normativas: [Constitución Española, artículo 68](https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229#a68) y [LOREG, artículos 161–162](https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672#acientosesentayuno).

## Admisión, reproducibilidad y fallo cerrado

El validador exige identidad explícita `congreso`, universo exacto de 52 códigos y procedencia nacional para K; `scope=national` es solo metadato. Rechaza campos autonómicos, K de asambleas autonómicas y el Gestor de Campañas autonómico. Para considerar admisión contractual productiva faltan decisión aprobada, K, cuotas positivas que sumen K, acreditaciones 52/52, fuentes originales acreditadas con edición/año/hash/procedencia y decisiones firmadas sobre las dimensiones pendientes. La ausencia de cualquiera cierra la admisión.

Un manifest reproducible deberá fijar entradas y hashes, versiones de contrato y herramientas, entorno y dependencias, parámetros, semilla cuando corresponda, logs, outputs y recibos. El piloto de esta entrega es exclusivamente sintético y prueba admisión/rechazo estructural; no invoca M01–M08 ni produce distritos reales. La respuesta del validador es `generation_authorized=false` incluso ante una futura admisión contractual; la generación necesitaría una autorización separada.

## Dependencias del motor común

| Componente | Uso posible | Límite para Congreso |
| --- | --- | --- |
| M01 y validación territorial | Cargar y validar unidades y población | Requiere contrato nacional, edición y cobertura acreditadas |
| M02–M03 | Diagnóstico de contactos y componentes | Falta política nacional de aristas, islas y discontinuidades |
| M04 | Partición con cuotas y barreras | Requiere cuotas 52/52 y validar semántica provincial contra contrato |
| M05 | Optimización | Sin contrato y parámetros nacionales acreditados no se admite ejecución |
| M06 | Consolidación y salidas | Falta identidad/orquestación nacional de extremo a extremo |

No se ha acreditado que M01–M06 consuman este contrato de extremo a extremo. La ruta actual por catálogo y gestor se apoya en 19 ámbitos autonómicos; queda expresamente fuera de la ruta Congreso. Se propone como validación futura un piloto provincial sintético para Cantabria, Madrid y La Rioja. No se ejecuta ni se declara certificado.

## Estado

El JSON compañero enumera el universo y las puertas pendientes. Las pruebas positivas solo demuestran admisión estructural del fixture sintético; las negativas comprueban rechazo de universos incompletos, identidad ambigua, gestor autonómico y K autonómico. La generación nacional sigue `NO_GO` hasta decisión institucional, fuentes y cuotas acreditadas, integración nacional ejecutable y autorización específica.
