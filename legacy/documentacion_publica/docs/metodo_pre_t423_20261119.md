# Método: módulos M01–M08

Revisión estructural sobre el commit `11f0ba2b775a889f2316e31ebdbd859cbc50ab13`. Los nombres efectivos de archivos y parámetros se resuelven desde cada contrato territorial. Los ejemplos de Aragón en documentos antiguos no deben interpretarse como cardinalidades nacionales.

| Módulo | Entradas principales | Productos que deben conservarse |
|---|---|---|
| M01 · Base territorial | Cartografía, población, contrato; comarcas opcionales | Secciones con población y geometría; informe de preparación |
| M02 · Adyacencias | Geometría M01 y criterio topológico | Aristas JSONL completas |
| M03 · Grafo | Secciones M01, aristas M02, política de conectividad | Grafo JSON con nodos/aristas e informe |
| M04 · Solución inicial | Grafo, geometría, K, límites y semilla | Asignación inicial GeoJSON ZIP e informe |
| M05 · Optimización | Asignación M04, grafo, estrategia, semillas y presupuesto | Asignación seleccionada, informe y portfolio cuando se ejecuta GerryChain |
| M06 · Consolidación | Asignación final M05 y contrato de validación | Resumen, catálogo, composición por sección, GeoJSON de secciones/distritos y diagnóstico, según salidas configuradas |
| M07 · Agregación electoral | Secciones M06 y contrato electoral con archivos verificados | CSV distrito/partido, resumen, reconciliación; geometría enriquecida opcional |
| M08 · Integración | Distritos M06 y resumen electoral M07 | Producto territorial con atributos electorales |

## Ejecución y conservación

La 00 organiza preparación territorial, generación, preparación electoral, incorporación y publicación opcional. No debe confundirse esa secuencia operativa con la numeración de los ocho módulos computacionales.

El workflow territorial copia la caché, el directorio de ejecución y el paquete de fuentes en checkpoints acumulados. Esto facilita la reanudación, pero duplica datos entre módulos. Los checkpoints de módulo auditados declaran 14 días de retención.

## Qué hace ya GerryChain

`materialise_portfolio()` en el motor de estrategia escribe un GeoJSON ZIP por semilla y un `portfolio.json` con hash, semilla, ranking y selección. El portfolio viaja en la caché del checkpoint. Solo el candidato seleccionado continúa normalmente a M06.

La cadena de ensembles `06 Escenarios y Ensembles` tiene además su propio empaquetado y Releases borrador. Ambos circuitos deben distinguirse al catalogar resultados. La presencia del código de portfolio no prueba que una ejecución histórica concreta lo conservara: hay que comprobar sus bytes.

## Evidencia canónica

- [Módulos y código](https://github.com/jfmurciego/DiputadodeDistrito/tree/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/modulos)
- [Workflow territorial](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/.github/workflows/_reutilizable-generacion-territorial.yml#L595)
- [Materialización de portfolio](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/ddd_core/m05_gerrychain_strategy.py#L1021)

*Versión 1.0.0 · 2026-11-03 · Archivo nuevo.*
