# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.1.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.0.0.md`

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
Versiones antiguas quedaron atascadas cerca de H=61 con ejecuciones de ~11 minutos. Baseline recuperado: población 1.364.621, target 20.367,48, suelo 16.293,98, techo 35.643,09, 30 bajo suelo, 7 sobre techo, min 3.451, max 37.042, best_max_rel_dev ≈0,83056, 0 desconectados. Referencia local posterior: 67 distritos, 0 desconectados, 29 bajo suelo, 0 sobre techo, best_max_rel_dev 0,5046; SHA-256 `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## 7. Diferencias históricas a vigilar
Una fase registró 1.358.812 habitantes frente a 1.364.621 con INE 65034; diferencia 5.809 que no debe ocultarse. El grafo tuvo referencias aproximadas de 4.302 y 4.293 aristas; cualquier cambio debe investigarse.

## 8. Defectos ya resueltos
Step7b inexistente; clave YAML duplicada; raíz relativa no portable; M08 leyendo config M07; OOM M01; normalización CUSEC; falsos positivos MultiPolygon; Run #1 con YAML inválido y error Python ocultado.

## 9. Estrategia de fuentes vigente — R008
Durante **desarrollo** no se depende del tiempo de respuesta del INE. Los inputs grandes se almacenan partidos en `inputs/partes/` y se reconstruyen automáticamente antes de M01 cuando hace falta una preparación nueva.

ZIP canónicos reconstruidos:
- `inputs/seccionado_2025.zip` → SHA-256 `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`;
- `inputs/65034.csv.zip` → SHA-256 `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`.

`inputs/partes/reconstruir_fuentes.sh` valida primero los fragmentos mediante `MANIFEST_PARTES.sha256`, reconstruye los dos ZIP y vuelve a verificar sus hashes canónicos. La configuración 7.3.0 consume esos ZIP.

La adquisición directa INE de R006 **se conserva**, no se elimina: `herramientas/adquirir_fuentes_ine.py` queda para validación/certificación final y para demostrar independencia respecto de los inputs congelados. Durante desarrollo no debe introducir latencia en cada ejecución.

El input electoral `inputs/rtve_aragon_2026_secciones.json` está en GitHub y mantiene hash canónico `bd091a2a878afd3aa0e9bf2af52f2484e24d967020c56cee5b1e320c339aa94c`.

## 10. Ejecución GitHub
Workflow vigente tras R008: 2.5.0. Configuración: 7.3.0. `completo` reconstruye fuentes congeladas y recalcula M01-M03. `iterativo` debe reutilizar la preparación territorial si la clave coincide, para que cambios de M04/M05 no repitan GIS ni fuentes pesadas.

GitHub Run #1 (`34575702377`) falló antes de M01 y está documentado. R006 intentó adquisición directa INE pero resultó demasiado lenta para el ciclo de desarrollo; R008 sustituye esa ruta operativa de desarrollo por fuentes congeladas verificadas.

## 11. Auditoría y versionado
Todo cambio funcional conserva versión previa en `legacy/`, incrementa versión, registra ronda, bitácora, estado maestro y, cuando sea ejecutable, expediente de ejecución. Una ejecución solo es referencia si el usuario puede reproducirla desde GitHub.

## 12. Generalización futura
Castilla y León, Extremadura y nacional deben entrar por configuración/datos/estrategias genéricas, no mediante forks territoriales del motor.

## 13. Siguiente acción exacta
1. Ejecutar una vez el workflow vigente en modo **`completo`** para construir la caché M01-M03 a partir de los ZIP reconstruidos.
2. Inspeccionar directamente el run y registrar resultado.
3. Si M01-M03 pasan, verificar 1.463 secciones, población total, aristas y conectividad contra referencias.
4. Después cambiar a **`iterativo`** para las rondas algorítmicas M04/M05.
5. Objetivo inmediato de M05: **67 exactos + 0 desconectados + 0 bajo suelo + 0 sobre techo**; después optimizar desviación y calidad territorial.

## 14. Condición de autosuficiencia
Si cambia objetivo, restricción, baseline, fuente, arquitectura, estado de ejecución o siguiente acción, actualizar este documento en la misma ronda.