# Auditoría inicial de conservación y plataforma pública

**Fecha:** 3 de noviembre de 2026. **Base:** `11f0ba2b775a889f2316e31ebdbd859cbc50ab13`.
**Dictamen:** GO para empezar a utilizar Zensical y preparar un archivo piloto. La integración R2 y la publicación definitiva requieren completar sus hitos de aceptación.

## Alcance y límites

Se revisaron el árbol completo del repositorio, los ocho módulos, workflows de preparación, generación, incorporación electoral, ensembles y publicación; los catálogos y resolutores de activos; documentación de módulos; metadatos de Releases y artefactos de Cantabria. Se descargó además el checkpoint M05 de Cantabria y se verificaron sus 50 candidatos.

Es una auditoría de estructura y conservación con una muestra material, no una certificación independiente de todos los territorios. No se ejecutaron territorios, no se regeneraron mapas, no se modificó el motor y no se verificaron los bytes de los 70 assets de Releases. La existencia de un receipt no se ha tratado como prueba de descarga.

La trazabilidad de los archivos consultados se conserva en `documentacion_publica/evidencias/source-index.json`, junto con los resultados verificables del piloto. El corte queda fijado al SHA de base; `main` puede seguir cambiando.

## Qué existe realmente

| Componente | Evidencia observada | Implicación |
|---|---|---|
| Fuente de código y contratos | GitHub, ocho módulos y workflows | Mantener como centro de desarrollo |
| Catálogos y linaje | Catálogo de preparación, evidencias M06/M08 y resolutores | Crear una vista pública derivada; evitar otro registro manual |
| Checkpoints | Copia acumulada de caché, run y fuentes | Reanudación útil; duplicación y caducidad |
| Portfolio M05 | ZIP por semilla y `portfolio.json` | Los candidatos pueden archivarse sin volver a calcularlos |
| Circuito de ensembles | Workflow específico y Releases borrador | No confundir con el portfolio del candidato seleccionado de la 00 |
| Archivo en Releases | 21 Releases visibles para la conexión, 70 assets, 19 borradores | Persistencia parcial ya existente; el borrador no es descarga pública |
| Publicador del visor | Árbol candidato y despliegue único de Pages | Integrar documentación en ese árbol o en otro repositorio |
| Portal Zensical | No aparece configuración Zensical en el árbol base | Esta propuesta añade un portal aislado y CI de construcción |
| R2 | No se encontró integración en los archivos revisados | Diseño pendiente de conexión y prueba real |

## Hallazgos priorizados

### A01 · Conservación expuesta a caducidad — prioridad alta

Los workflows revisados fijan 14 días para checkpoints y algunos informes, 30 días para distintos diagnósticos y fuentes. El proveedor permite políticas más largas, pero el plazo efectivo del artefacto concreto es el que determina su riesgo.

En Cantabria, M05, M06 y M08 declaran expiración el **13 de noviembre de 2026**. El manifiesto M06 y los recibos permanecen en Git, pero no garantizan por sí mismos que los ZIP sigan descargándose después. La existencia de otros archivos en Releases no acredita una copia equivalente de estos mismos bytes.

**Acción:** añadir conservación de objetos con recibo verificable antes de depender del catálogo para recuperación a largo plazo. Empezar con un piloto y confirmar descarga antes de cambiar lectores o puertas.

### A02 · Cantabria sí conserva 50 candidatos — comprobado materialmente

Checkpoint `12973348423`, 102.460.319 bytes. SHA-256:

```text
facfbfcdef2566b24b55dea433d8ac289525727d97354fce0400b542e3914884
```

El ZIP contiene 50 candidatos y su índice. Se verificaron sus 50 hashes de archivo y se recalcularon 50 asignaciones distintas a partir de los atributos de los GeoJSON. Cada candidato contiene 460 secciones. Tamaño conjunto de los ZIP de candidatos: **24.735.141 bytes**.

**Corrección de la revisión anterior:** la conservación de los otros 49 mapas ya no está sin verificar en este caso. La consulta pública y la retención permanente siguen siendo cuestiones diferentes. Tampoco se ha repetido la auditoría geométrica de todos ellos.

### A03 · Persistencia y distribución pública tienen estados diferentes — prioridad alta

De las 21 Releases observadas, 19 son borradores. Los borradores con assets son útiles como almacenamiento autenticado, pero no deben anunciarse como descargas anónimas. Algunos borradores no tienen assets; una etiqueta o Release vacía tampoco acredita conservación.

**Acción:** separar en el catálogo ubicación de archivo, integridad comprobada, permisos de consulta, estado de publicación y derechos de reutilización. Probar las descargas destinadas al público sin credenciales.

### A04 · Segundo despliegue de Pages podría sustituir el visor — prioridad alta

El publicador existente sube `/tmp/site-candidate` como sitio completo. La receta estándar de publicar Zensical en el mismo Pages sustituiría el árbol publicado si solo incluyera la documentación.

**Acción:** esta PR únicamente construye el portal. La publicación se integra después en el publicador único bajo `documentacion/`, con comprobación de preservación del visor, o se hace en otro repositorio.

### A05 · Duplicación de checkpoints — prioridad media

En el run de muestra, los artefactos listados suman 871.650.900 bytes; los checkpoints `ddd-state-*` suman 794.881.540. La copia acumulativa de caché, fuentes y run explica parte del volumen repetido. No son 795 MB de datos científicos distintos.

**Acción:** conservar primero, deduplicar después por contenido. Guardar asignaciones separadas de la geometría común puede reducir el coste futuro, pero requiere un formato de reconstrucción y validación antes de sustituir los GeoJSON actuales.

### A06 · Fechas, licencias y límites académicos — prioridad previa a apertura

El catálogo oficial identifica proveedores y endpoints; no certifica por sí solo todos los derechos de redistribución. La edición territorial tampoco sustituye la fecha de referencia de población, cartografía o elección.

**Acción:** revisar cada licencia, declarar procedencia y versiones separadas. Para uso académico, documentar también entorno, semillas, contratos, métricas, restricciones y diseño estadístico del ensemble. Cincuenta mapas distintos no bastan para afirmar muestreo imparcial.

## Matriz de conservación

| Familia | Soporte observado | Riesgo | Destino objetivo |
|---|---|---|---|
| Código, contratos y documentación | Git | Cambios de rama; fijar SHA | Git con referencias de versión |
| Recibos, catálogos y manifiestos | Git + artefactos | Referencia durable a bytes caducables | Git + manifiesto de ubicación verificada |
| Originales y paquete de fuentes | Paquetes de trabajo y artefactos; circuitos específicos existentes | Caducidad; licencia por verificar | Objetos privados con hash y procedencia |
| M01–M03 | Caché y checkpoints acumulados | Retención limitada | Objetos deduplicados por preparación |
| M04 | Asignación e informe en checkpoint | Retención limitada | Objetos por ejecución y contrato |
| M05 y portfolio | Caché y checkpoint; 50 candidatos comprobados en Cantabria | Retención limitada | Asignación seleccionada y todos los candidatos identificados |
| M06 | Checkpoint, certificación y manifiesto productor; algunos almacenes en Releases | Cobertura histórica parcial | Producto, informe y auditoría enlazados |
| M07–M08 | Checkpoints electorales y recibos | Retención limitada | Producto electoral y reconciliación con linaje M06 |
| Ensembles específicos | Artefactos y Releases borrador | Privacidad y estado editorial | Archivo privado; versión pública seleccionada |
| Visor | Árbol de publicación y registro de activos | Vista derivada; no sustituye el archivo | Mantener y enlazar a evidencias |

## Dimensión y coste: medición frente a extrapolación

El árbol completo declara **5.488 blobs**, **825.569.835 bytes** y **1.263 archivos bajo `docs/`**. Es la suma de tamaños del árbol, no el tamaño comprimido del repositorio ni su historial.

Los 70 assets de las Releases observadas suman **2.300.937.069 bytes**. Esta medición procede de metadatos, no de descargar y verificar todos sus contenidos. No incluye todos los artefactos históricos de Actions.

La muestra Cantabria suma aproximadamente **0,872 GB** de artefactos y **0,0247 GB** de candidatos comprimidos. No es válido multiplicar esa muestra directamente para presupuestar todos los territorios: geometría, secciones, estrategias y compresión cambian.

La tarifa R2 Standard consultada incluye 10 GB-mes y cobra 0,015 USD por GB-mes adicional, además de operaciones. A 100 GB constantes, el componente de almacenamiento sería aproximadamente 1,35 USD/mes tras ese tramo incluido. Es un escenario, no una factura prevista. Medir crecimiento, descargas, operaciones y segunda copia antes de fijar presupuesto.

El coste computacional no se ha estimado de forma general: no se midieron tiempos y recursos de todas las etapas. Esta auditoría descargó y leyó evidencia sin repetir GerryChain.

## Modelo de metadatos propuesto

Reutilizar identificadores existentes y añadir un índice de consulta con: territorio, edición, elección, run e intento; SHA de código y workflow; hash de contrato; fuentes y sus fechas; algoritmo, semilla y parámetros; candidatos y asignaciones; métricas y controles; objetos con tamaño/hash/ubicación; verificación, retención, licencia y publicación.

Registrar conservación, validación y publicación como dimensiones separadas. El índice no sustituye los manifiestos de productor ni debe editarlos retroactivamente. Un depósito en Zenodo y un DOI son una fase posterior, no una propiedad automática del archivo R2.

## Siguientes PR

1. Portal y auditoría: esta entrega, aislada de los workflows productivos.
2. Archivador optativo: escritura idempotente, recibos y prueba independiente de recuperación.
3. Integración en salida de workflows: coordinar ficheros compartidos; sin regenerar ni promover productos históricos.
4. Catálogo público generado y despliegue documental dentro del publicador único.
5. Paquete académico seleccionado, licencias y depósito citable.

La activación de R2 necesita una cuenta configurada. La primera prueba debe ser privada y pequeña. La fusión de esta propuesta y la publicación permanecen pendientes.

## Referencias comprobables

- [Base auditada](https://github.com/jfmurciego/DiputadodeDistrito/tree/11f0ba2b775a889f2316e31ebdbd859cbc50ab13)
- [Empaquetado y retención de checkpoints](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/.github/workflows/_reutilizable-generacion-territorial.yml#L595)
- [Manifiesto M06 de Cantabria](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/territorios/cantabria/evidencia/generaciones_m06/41037133327.json)
- [Retención de Actions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [Zensical: publicación](https://zensical.org/docs/publish-your-site/)
- [R2: tarifas](https://developers.cloudflare.com/r2/pricing/) y [retención de objetos](https://developers.cloudflare.com/r2/buckets/bucket-locks/)

*Versión 1.0.0 · Archivo nuevo.*
