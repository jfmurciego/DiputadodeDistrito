# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.0.0  
**Fecha de corte:** 2026-09-11  
**Propósito:** documento de continuidad autosuficiente para retomar el proyecto desde una conversación, equipo o sesión nueva sin depender del historial de chat.

## 1. Regla de arranque en una sesión nueva

Antes de modificar código, leer en este orden:
1. `docs/ESTADO_MAESTRO_PROYECTO.md` — estado, restricciones, historia técnica y siguiente acción.
2. `docs/BITACORA.md` — rondas y ejecuciones.
3. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md` — contratos M01-M08.
4. `docs/POLITICA_DE_VERSIONES.md` — conservación y versionado.
5. `configuracion/aragon_2025.yaml` — contrato ejecutable vigente.
6. último documento de `docs/RONDAS/` y último expediente de `docs/EJECUCIONES/`.
7. workflow `.github/workflows/procedimiento-ddd.yml` si la tarea afecta ejecución GitHub.

No asumir que una salida generada únicamente en una sesión de IA es evidencia. La referencia es el repositorio y una ejecución reproducible por el usuario.

## 2. Objetivo del sistema

Construir un **Procedimiento de Distritación DDD** reproducible, auditable y generalizable que genere distritos uninominales a partir de unidades censales oficiales. Aragón es la primera implantación. Debe poder trasladarse después a Castilla y León, Extremadura y potencialmente a España completa sin bifurcar el motor por territorio.

Terminología oficial: sistema completo = **procedimiento**; etapa funcional = **módulo**; lanzamiento = **ejecución**; conjunto de cambios = **ronda**. Evitar `pipeline` y `step` en nomenclatura nueva.

## 3. Arquitectura vigente

M01 prepara secciones+población; M02 calcula adyacencias; M03 construye el grafo; M04 genera solución inicial; M05 optimiza; M06 consolida productos territoriales; M07 agrega resultados electorales; M08 integra geometría y resultados.

M01-M03 forman la **base territorial preparada**, costosa y reutilizable. M04-M06 son el núcleo iterativo de distritación. M07-M08 son capa electoral independiente. Cambiar M04/M05 no debe releer ni reprocesar fuentes nacionales.

Modos GitHub: `completo` reconstruye M01-M03 desde fuentes oficiales; `iterativo` reutiliza la preparación válida y ejecuta la parte mutable.

## 4. Restricciones duras Aragón

- exactamente **67 distritos**;
- contigüidad estricta medida sobre el grafo de secciones, no por componentes del polígono disuelto;
- población objetivo = población total / 67;
- suelo duro vigente = **0,80 × target**;
- techo duro vigente = **1,75 × target**;
- objetivo de equilibrio histórico: aproximarse a **±0,12** del target cuando sea compatible con las restricciones;
- máximo histórico de split = **3** para unidades sobredimensionadas donde aplique granularización;
- CUSEC canónico, único y sin nulos;
- conservación exacta de población;
- semillas y orden deterministas;
- la capa electoral no condiciona la geometría;
- una sola configuración canónica por territorio/año, sin parámetros redundantes.

Una ronda no se promociona si rompe una restricción ya satisfecha. En particular, no se acepta mejorar población perdiendo K=67 o contigüidad.

## 5. Criterios territoriales históricos que no deben perderse

### Zaragoza
El problema histórico de unidades demasiado grandes exige granularización de Zaragoza capital mediante unidades internas (`CUDIS`) y, si una unidad sigue siendo demasiado grande, fallback a secciones (`CUSEC`). Este criterio debe generalizarse, no codificarse como excepción arbitraria si se rediseña el motor.

### Contigüidad
V2 produjo fallos graves de distritos no contiguos. La contigüidad se convirtió en condición dura. Un `MultiPolygon` disuelto no demuestra por sí solo desconexión: la validación autorizada es conectividad del subgrafo de secciones asignadas a cada distrito.

### Nombres urbanos
V2 usó incorrectamente el término «eje» en distritos urbanos. La evolución posterior debe usar barrios/unidades urbanas reales para nombres, no inventar ejes como sustituto semántico.

## 6. Historia algorítmica relevante

En fases antiguas, varias versiones del motor quedaron atascadas alrededor de **H=61** y cada ejecución podía tardar unos 11 minutos sin mejorar. Esto motivó la exigencia de ejecutar y validar de extremo a extremo antes de entregar nuevas variantes y de separar preparación territorial del motor iterativo.

Baseline histórico recuperado v6, previo a las correcciones actuales: población total aproximada **1.364.621**, target **20.367,48**, suelo **16.293,98**, techo **35.643,09**, 30 distritos bajo suelo, 7 sobre techo, mínimo 3.451, máximo 37.042, `best_max_rel_dev ≈ 0,83056`, y 0 distritos desconectados sobre 67.

Referencia local determinista posterior a las correcciones de M04/M05: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**. SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`. Esta referencia aún **NO satisface** el suelo poblacional.

La prioridad algorítmica una vez estabilizada GitHub es M05: eliminar los 29 distritos bajo suelo sin romper 67 distritos ni contigüidad, y después mejorar desviación/compactación y criterios territoriales.

## 7. Población: diferencia histórica que debe investigarse, no ocultarse

Una fase histórica registró aproximadamente **1.358.812** habitantes. La ejecución con la fuente oficial INE 65034 de 2025 utilizada en la recuperación produjo **1.364.621**, diferencia **5.809**. No se consideran cifras intercambiables. La hipótesis es que el baseline antiguo utilizó una transformación/fuente previa (`cip_2025_secciones_like_v4.tsv` u otra base), pero debe demostrarse si vuelve a ser relevante.

R006 cambia además la adquisición: población 65034 y cartografía Secciones_2025 se materializan desde servicios oficiales del INE. La primera ejecución completa de R006 debe comprobar cardinalidad y población antes de promover esta adquisición como equivalente funcional al baseline.

## 8. Grafo y geometría

La recuperación histórica corrigió la construcción de adyacencias con índice espacial. Se manejó como referencia un grafo de alrededor de **4.302 aristas**; una ejecución posterior con fuente oficial produjo alrededor de **4.293**. La diferencia no debe darse por irrelevante: si R006 obtiene una cardinalidad distinta, investigar geometría, criterio `touches`, normalización y versión de fuente antes de continuar con M05.

## 9. Defectos históricos ya resueltos

- script original esperaba un Step7b inexistente mientras el archivo real era Step8;
- YAML original contenía una clave de salida Step8 duplicada y YAML conservaba silenciosamente solo una;
- resolución de raíz relativa de configuración no era portable;
- M08 leía una ruta de salida desde la configuración de M07;
- M01 cargaba cartografía y población nacionales completas y sufría OOM; se introdujeron filtro territorial temprano y lectura poblacional por bloques;
- CUSEC podía venir como texto enriquecido, p. ej. `0100101001 Alegría-Dulantzi sección 01001`; se normaliza tomando el bloque autónomo de 10 dígitos;
- validación por componentes de `MultiPolygon` generaba falsos positivos; sustituida por conectividad del grafo;
- GitHub Run #1 reveló YAML inválido por `{run_name}` sin comillas y un fallo Python ocultado dentro de `echo`; R005 corrigió ambos con YAML válido y fail-fast.

No reintroducir estos defectos al generalizar el procedimiento.

## 10. Fuentes y adquisición vigentes

R006 elimina la necesidad operativa de subir/trocear los dos ZIP territoriales grandes. `herramientas/adquirir_fuentes_ine.py` materializa:
- población: tabla INE **65034**;
- geometría: colección INE OGC API Features `WMS_INE_SECCIONES_G01:Secciones_2025`, provincias 22, 44 y 50;
- control de **1.463 secciones** esperadas;
- `inputs/FUENTES_ADQUIRIDAS.json` con URLs, fecha UTC, tamaños y SHA-256.

El fichero electoral pequeño `inputs/rtve_aragon_2026_secciones.json` está almacenado en GitHub y su hash canónico histórico es `bd091a2a878afd3aa0e9bf2af52f2484e24d967020c56cee5b1e320c339aa94c`.

Hashes de los antiguos inputs locales de recuperación, útiles solo para arqueología/comparación:
- `seccionado_2025.zip`: `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`;
- `65034.csv.zip`: `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`.

No comparar el hash del CSV remoto descomprimido con el hash del ZIP histórico: son objetos binarios distintos.

## 11. Estado GitHub a este corte

Repositorio: `jfmurciego/DiputadodeDistrito`, rama `main`.

R005 formalizó auditoría de ejecuciones. GitHub Run #1: ID `34575702377`, modo `completo`, commit `416b06dd1044acbad74ddc400d86ba2b99cf03f5`, FAIL de infraestructura antes de M01. Expediente: `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md`.

R006 — adquisición automática de fuentes oficiales — está implementada. Commit de R006: `d92296e472a6dde0e8ba7c1c188643d9dfeed789`. Configuración vigente en ese commit: 7.2.0; workflow: 2.4.0; herramienta de adquisición: 1.0.0.

La siguiente ejecución solicitada al usuario es **GitHub Run #2, modo completo, sobre `main`**. Su misión no es todavía demostrar que el algoritmo es bueno: primero debe demostrar que R006 puede adquirir las fuentes, construir M01-M03 y llegar a M04-M08. Sea PASS o FAIL, registrar el run en `docs/EJECUCIONES/` y actualizar bitácora/memoria antes de otra ronda.

## 12. Política de auditoría y conservación

Todo fichero funcional modificado debe conservar previamente su versión anterior en `legacy/`, incrementar SemVer y explicar en cabecera qué cambia y por qué. Cada ronda debe tener documento propio. Cada ejecución de referencia debe registrar run ID, commit, rama, modo, versiones, fases alcanzadas, error o métricas, clasificación y acción correctiva. Los resultados de ejecuciones son inmutables.

El usuario quiere poder ejecutar el procedimiento repetidamente en su propio GitHub; no entregar scripts que apunten a archivos ausentes ni exigirle ciclos manuales de prueba/error cuando los logs de GitHub pueden inspeccionarse directamente.

## 13. Generalización futura

Después de Aragón: Castilla y León y Extremadura. El motor no debe bifurcarse por comunidad. Las diferencias territoriales deben expresarse en configuración, datos auxiliares o estrategias genéricas. Posteriormente puede adaptarse a elecciones generales/nivel nacional.

## 14. Próxima secuencia de trabajo

1. Esperar/inspeccionar GitHub Run #2 `completo` de R006.
2. Crear expediente de ejecución y actualizar bitácora/memoria.
3. Si falla infraestructura/adquisición, corregirla en una nueva ronda preservando R006.
4. Si M01-M03 pasan, comparar: 1.463 secciones, población total, CUSEC, aristas del grafo y contigüidad con referencias conocidas.
5. Solo con infraestructura y base territorial estabilizadas, volver a M05.
6. Objetivo inmediato de M05: 67 exactos + 0 desconectados + 0 bajo suelo + 0 sobre techo; después optimizar desviación y criterios de calidad territorial.

## 15. Condición para considerar el repositorio autosuficiente

Una sesión nueva debe poder reconstruir **qué se intenta conseguir, por qué existe cada módulo, qué restricciones no puede romper, qué errores ya se cometieron, cuál es el baseline, qué fuentes se usan, cuál fue la última ronda/ejecución y qué acción viene después** leyendo este documento y los documentos enlazados. Si una nueva decisión cambia cualquiera de esos puntos, este documento debe actualizarse en la misma ronda.