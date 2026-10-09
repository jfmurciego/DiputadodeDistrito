# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.0.0  
**Fecha de corte:** 2026-09-11  
**Propósito:** documento de continuidad autosuficiente para retomar el proyecto desde una conversación, equipo o sesión nueva sin depender del historial de chat.

## 1. Regla de arranque en una sesión nueva
Antes de modificar código, leer en este orden: `docs/ESTADO_MAESTRO_PROYECTO.md`, `docs/BITACORA.md`, `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`, `docs/POLITICA_DE_VERSIONES.md`, `configuracion/aragon_2025.yaml`, último documento de `docs/RONDAS/`, último expediente de `docs/EJECUCIONES/` y workflow si aplica.

## 2. Objetivo del sistema
Construir un Procedimiento de Distritación DDD reproducible, auditable y generalizable para Aragón, después Castilla y León, Extremadura y potencialmente España completa sin bifurcar el motor.

## 3. Arquitectura vigente
M01 secciones+población; M02 adyacencias; M03 grafo; M04 solución inicial; M05 optimiza; M06 consolida; M07 agrega resultados; M08 integra resultados. M01-M03 son base territorial reutilizable.

## 4. Restricciones duras Aragón
67 distritos exactos; contigüidad estricta por grafo; target = población/67; suelo 0,80×; techo 1,75×; objetivo histórico ±0,12; split máximo 3 donde aplique; CUSEC único; conservación de población; determinismo; capa electoral posterior.

## 5. Criterios territoriales históricos
Zaragoza: granularización CUDIS y fallback CUSEC si persisten unidades sobredimensionadas. V2 tuvo distritos no contiguos y nomenclatura urbana basada erróneamente en «eje»; usar barrios/unidades urbanas reales.

## 6. Historia algorítmica
Versiones antiguas quedaron atascadas alrededor de H=61 con ejecuciones de unos 11 minutos. Baseline histórico recuperado: 1.364.621 habitantes, target 20.367,48, suelo 16.293,98, techo 35.643,09, 30 bajo suelo, 7 sobre techo, mínimo 3.451, máximo 37.042, best_max_rel_dev ≈0,83056, 0 desconectados. Referencia local posterior: 67 distritos, 0 desconectados, 29 bajo suelo, 0 sobre techo, best_max_rel_dev 0,5046; SHA-256 d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f.

## 7. Diferencia poblacional histórica
Una fase registró 1.358.812 habitantes frente a 1.364.621 con INE 65034; diferencia 5.809 que no debe ocultarse.

## 8. Grafo y geometría
Referencia histórica ~4.302 aristas; otra ejecución oficial ~4.293. Si cambia, investigar fuente/geometría/criterio touches.

## 9. Defectos históricos resueltos
Step7b inexistente; YAML duplicado; raíz relativa no portable; M08 leyendo config M07; OOM M01; normalización CUSEC; falsos positivos MultiPolygon; Run #1 con YAML inválido y error Python ocultado.

## 10. Fuentes vigentes
R006 materializa población INE 65034 y cartografía Secciones_2025 desde INE. RTVE JSON está en GitHub. Hashes históricos: seccionado ZIP 55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4; población ZIP 91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3.

## 11. Estado GitHub
R006 commit d92296e472a6dde0e8ba7c1c188643d9dfeed789; config 7.2.0; workflow 2.4.0. Siguiente ejecución: GitHub Run #2 completo para validar adquisición y M01-M08.

## 12. Auditoría
Todo cambio funcional conserva legacy, incrementa versión, registra ronda, ejecución, bitácora y estado maestro.

## 13. Generalización futura
Castilla y León, Extremadura y después nacional, sin bifurcar motor.

## 14. Próxima secuencia
Inspeccionar Run #2; registrar; corregir infraestructura si falla; comparar M01-M03; luego volver a M05.

## 15. Autosuficiencia
Actualizar este documento si cambia objetivo, restricción, baseline, fuente, arquitectura, estado de ejecución o siguiente acción.
