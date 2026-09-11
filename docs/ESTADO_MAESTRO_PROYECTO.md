# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.3.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.2.0.md`

## 1. Regla de arranque
Leer este documento; `docs/BITACORA.md`; `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`; los ocho contratos de `docs/MODULOS/`; configuración; última ronda; última ejecución; workflow.

## 2. Objetivo
Procedimiento de Distritación DDD reproducible, auditable y generalizable. Aragón es la primera implantación; Castilla y León, Extremadura y España completa deben entrar por datos/configuración, no mediante forks del motor.

## 3. Arquitectura
M01 secciones+población; M02 adyacencias; M03 grafo; M04 solución inicial; M05 optimización; M06 consolidación territorial; M07 agregación electoral; M08 producto final. M01-M03 son preparación reutilizable; M04-M06 núcleo iterativo; M07-M08 capa electoral desacoplada.

## 4. Restricciones Aragón
67 distritos exactos; contigüidad estricta por grafo; target=población/67; suelo 0,80×target; techo 1,75×target; objetivo histórico ±0,12; split máximo 3 donde aplique; CUSEC único/no nulo; conservación de población; determinismo; resultados electorales no condicionan geometría.

## 5. Referencia vigente
GitHub Run #4 `34581760340`: 67 distritos, contigüidad PASS, población total 1.364.621, 0 distritos bajo suelo, 0 sobre techo y `best_max_rel_dev≈0,3382`. M01-M03 se restauraron desde caché; M05 aceptó 114 movimientos de reparación y 1.267 de pulido.

## 6. Fuentes
Desarrollo: ZIP canónicos reconstruidos desde `inputs/partes/`. Hash seccionado `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`; población `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`. Validación/certificación final: adquisición directa INE de R006.

## 7. Regla de producto por módulo — R011
**Ningún módulo puede quedar representado únicamente por un log, un contador o un informe.** Debe existir el estado completo que produjo y debe poder auditarse.

Por ejecución se materializa `resultados/ejecuciones/<run_id>/M01..M08/`:
- M01: `secciones.csv` completo + referencia SHA-256 al GeoJSON de secciones;
- M02: `adyacencias.jsonl` completo;
- M03: `grafo.json` completo;
- M04: `asignacion_inicial.csv` completa + GeoJSON;
- M05: `asignacion_optimizada.csv` completa + GeoJSON;
- M06: `catalogo_distritos.csv` rico + `composicion_distritos.csv` + GeoJSON de secciones y distritos;
- M07: resultados completos por partido + resumen + GeoJSON de secciones electorales;
- M08: `distritos_resultados.csv` + GeoJSON final.

Las tablas y estructuras ligeras permanecen en Git. Las geometrías pesadas se conservan como artefactos separados por módulo de GitHub Actions; cada `PRODUCTOS.json` registra ruta canónica, bytes y SHA-256. Esto da auditabilidad sin añadir ~20 MB al historial Git por ejecución.

## 8. Contrato rico de distrito
M06 deja de entender un distrito como `{id,población}`. El catálogo incluye población, target, diferencia y desviación, ratio, límites y cumplimiento, número de secciones, municipios y provincias, superficie, perímetro, compacidad Polsby–Popper, centroide y bounding box. La composición enumera todas las secciones de cada distrito con CUSEC, municipio, provincia, CUDIS y población. Futuras capas fiables añadirán nombres/barrios/comarca/cabecera sin inventar topónimos.

## 9. Documentación modular
Existen ocho documentos `docs/MODULOS/M01_...` a `M08_...`, uno por módulo, con propósito, necesidad, entradas, transformación, productos, validaciones, reutilización y relación con módulos vecinos.

## 10. Concurrencia y rendimiento
Solo `preparar-territorio` está serializado. M04-M08 pueden correr concurrentemente. M01-M03 se cachean y una ejecución iterativa referencia/reutiliza la preparación vigente, pero sigue haciendo accesible su producto canónico.

## 11. Diferencias históricas abiertas
Persisten como arqueología la población antigua 1.358.812 frente a 1.364.621 actual y la referencia histórica ~4.302 aristas frente a 4.293 reproducibles. No se ocultan ni bloquean la referencia vigente.

## 12. Siguiente acción exacta
Ejecutar workflow 2.7.0 en modo `iterativo`. Debe: restaurar M01-M03; reproducir el PASS de Run #4; generar `auditoria/M01..M08`; publicar ocho artefactos separados con productos pesados; y crear en Git `resultados/ejecuciones/<nuevo_run_id>/` con las entidades completas auditables. Después revisar `M06/catalogo_distritos.csv` y `M06/composicion_distritos.csv` antes de modificar de nuevo el algoritmo hacia ±12%.
