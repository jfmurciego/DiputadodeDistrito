# Método: fases P21–P26 y P31–P32

Revisión estructural sobre el commit `11f0ba2b775a889f2316e31ebdbd859cbc50ab13`. Los nombres efectivos de archivos y parámetros se resuelven desde cada contrato territorial. Los ejemplos de Aragón en documentos antiguos no deben interpretarse como cardinalidades nacionales.

| Fase | Entradas principales | Productos que deben conservarse |
|---|---|---|
| P21 · Base y población | Cartografía, población, contrato; comarcas opcionales | Secciones con población y geometría; informe de preparación |
| P22 · Geometría y adyacencias | Geometría de P21 y criterio topológico | Aristas JSONL completas |
| P23 · Grafo | Secciones de P21, aristas de P22, política de conectividad | Grafo JSON con nodos/aristas e informe |
| P24 · Solución inicial | Grafo, geometría, K, límites y semilla | Asignación inicial GeoJSON ZIP e informe |
| P25 · Optimización | Asignación de P24, grafo, estrategia, semillas y presupuesto | Asignación seleccionada, informe y portfolio cuando se ejecuta GerryChain |
| P26 · Producto certificado | Asignación final de P25 y contrato de validación | Resumen, catálogo, composición por sección, GeoJSON de secciones/distritos y diagnóstico, según salidas configuradas |
| P31 · Agregación | Secciones de P26 y contrato electoral con archivos verificados | CSV distrito/partido, resumen, reconciliación; geometría enriquecida opcional |
| P32 · Resultados por distrito | Distritos de P26 y resumen electoral de P31 | Producto territorial con atributos electorales |

## Ejecución y conservación

La 00 organiza preparación territorial, generación, preparación electoral, incorporación y publicación opcional. No debe confundirse esa secuencia operativa con la numeración de los ocho módulos computacionales.

El workflow territorial copia la caché, el directorio de ejecución y el paquete de fuentes en checkpoints acumulados. Esto facilita la reanudación, pero duplica datos entre módulos. Los checkpoints de módulo auditados declaran 14 días de retención.

## Qué hace ya GerryChain

`materialise_portfolio()` en el motor de estrategia escribe un GeoJSON ZIP por semilla y un `portfolio.json` con hash, semilla, ranking y selección. El portfolio viaja en la caché del checkpoint. Solo el candidato seleccionado continúa normalmente a P26.

La cadena de ensembles `06 Escenarios y Ensembles` tiene además su propio empaquetado y Releases borrador. Ambos circuitos deben distinguirse al catalogar resultados. La presencia del código de portfolio no prueba que una ejecución histórica concreta lo conservara: hay que comprobar sus bytes.

## Evidencia canónica

- [Módulos y código](https://github.com/jfmurciego/DiputadodeDistrito/tree/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/modulos)
- [Workflow territorial](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/.github/workflows/_reutilizable-generacion-territorial.yml#L595)
- [Materialización de portfolio](https://github.com/jfmurciego/DiputadodeDistrito/blob/11f0ba2b775a889f2316e31ebdbd859cbc50ab13/ddd_core/m05_gerrychain_strategy.py#L1021)

*Versión 1.1.0 · 2026-11-19 · T-423: nomenclatura P de D-165 en el texto (los ficheros y el código conservan sus nombres). Anterior: `legacy/documentacion_publica/docs/metodo_pre_t423_20261119.md`.*
