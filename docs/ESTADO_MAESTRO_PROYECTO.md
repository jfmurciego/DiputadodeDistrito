# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.2.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.1.0.md`

## 1. Regla de arranque
Leer primero este documento; después `docs/BITACORA.md`, `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`, `docs/POLITICA_DE_VERSIONES.md`, `configuracion/aragon_2025.yaml`, última ronda, última ejecución y workflow si aplica.

## 2. Objetivo
Procedimiento de Distritación DDD reproducible, auditable y generalizable: Aragón primero; después Castilla y León, Extremadura y potencialmente España completa, sin bifurcar el motor.

## 3. Arquitectura
M01 secciones+población; M02 adyacencias; M03 grafo; M04 solución inicial; M05 optimización; M06 consolidación; M07 resultados electorales; M08 producto final. M01-M03 son base territorial preparada reutilizable; M04-M06 son núcleo iterativo; M07-M08 son capa electoral separada.

## 4. Restricciones Aragón
- 67 distritos exactos;
- contigüidad estricta por grafo;
- target = población/67;
- suelo duro 0,80×target;
- techo duro 1,75×target;
- objetivo histórico ±0,12 cuando sea compatible;
- split máximo 3 donde aplique;
- CUSEC único y sin nulos;
- conservación exacta de población;
- determinismo;
- resultados electorales no condicionan geometría.

## 5. Criterios territoriales históricos
Zaragoza capital: granularización por CUDIS y fallback a CUSEC si una unidad sigue sobredimensionada. V2 tuvo defectos graves de contigüidad y nombres urbanos basados en «eje»; la evolución debe mantener contigüidad dura y nombres apoyados en barrios/unidades urbanas reales.

## 6. Historia algorítmica
Versiones antiguas quedaron atascadas cerca de H=61 con ejecuciones de ~11 minutos. Baseline recuperado: población 1.364.621, target 20.367,48, suelo 16.293,98, techo 35.643,09, 30 bajo suelo, 7 sobre techo, min 3.451, max 37.042, best_max_rel_dev ≈0,83056, 0 desconectados. Referencia local posterior y GitHub Run #3 con M05 v7.0.1: **67 distritos, 29 bajo suelo, 0 sobre techo, best_max_rel_dev 0,5046**.

## 7. Base territorial demostrada en GitHub
GitHub Run #3 (`34580841510`, commit `2835938ed40a272c0e34f609c7b9966c7b5225ca`) prueba la ruta R008 completa:
- fragmentos y ZIP canónicos verificados;
- M01: 1.463 secciones, 0 población ausente;
- M02: 4.293 aristas;
- M03: 1.463 nodos, 4.293 aristas, 0 aislados;
- caché M01-M03 guardada;
- M04-M08 ejecutados correctamente;
- puerta final FAIL únicamente por 29 distritos bajo 0,80×target.

Esto reclasifica el bloqueo activo como **algorítmico M05**, no infraestructura.

## 8. Estrategia de fuentes
Durante desarrollo se usan los ZIP congelados reconstruidos desde `inputs/partes/`, con hashes canónicos:
- seccionado `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`;
- población `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`.
La adquisición INE de R006 se conserva para validación/certificación final.

## 9. Concurrencia vigente
Workflow **2.5.1** serializa exclusivamente `preparar-territorio` mediante grupo `ddd-preparacion-aragon-2025`, `cancel-in-progress: false`. No pueden reconstruirse simultáneamente dos bases M01-M03. Los jobs M04-M08 de ejecuciones distintas siguen siendo concurrentes.

## 10. M05 vigente — R009
M05 **v7.1.0** corrige la causa conceptual del Run #3. La función objetivo anterior miraba únicamente máximo desvío relativo y podía mejorar sin eliminar distritos ilegales. La nueva función prioriza, en este orden:
1. número de distritos que violan suelo/techo;
2. magnitud total de esas violaciones;
3. máximo desvío respecto del target;
4. error cuadrático global.

Incluye una fase dirigida de reparación y solo permite transferencias que preserven conectividad del distrito donante y entren por adyacencia al receptor. Después realiza pulido local sin empeorar la tupla anterior.

## 11. Diferencias históricas a vigilar
Una fase registró 1.358.812 habitantes frente a 1.364.621 con INE 65034; diferencia 5.809 que no debe ocultarse. El grafo tuvo referencia aproximada de 4.302 aristas y ahora la ejecución reproducible R008 confirma 4.293; la diferencia histórica queda abierta para arqueología, no bloquea R009 mientras la fuente/hash sea estable.

## 12. Auditoría y versionado
Todo cambio funcional conserva versión previa en `legacy/`, incrementa versión, registra ronda, bitácora, estado maestro y expediente de ejecución. Una ejecución solo es referencia si el usuario puede reproducirla desde GitHub.

## 13. Generalización futura
Castilla y León, Extremadura y nacional deben entrar por configuración/datos/estrategias genéricas, no mediante forks territoriales del motor.

## 14. Siguiente acción exacta
Ejecutar ahora el workflow en modo **`iterativo`**. La caché territorial del Run #3 debe restaurarse; no deben repetirse reconstrucción de ZIP ni M01-M03. La validación debe medir el efecto de M05 v7.1.0 sobre los 29 distritos bajo suelo. Si quedan violaciones, inspeccionar el nuevo reporte M05 (`under_district_ids`, movimientos de reparación y `objective_final`) y evolucionar la estrategia, sin tocar M01-M03.

## 15. Condición de autosuficiencia
Si cambia objetivo, restricción, baseline, fuente, arquitectura, estado de ejecución o siguiente acción, actualizar este documento en la misma ronda.