# Continuidad del proyecto en un nuevo chat

**Versión:** 1.1.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.0.0.md`

## Fuente de verdad y lectura obligatoria
El repositorio `jfmurciego/DiputadodeDistrito` manda sobre cualquier recuerdo del chat. Al abrir una conversación nueva: leer `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, este documento, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflow y código afectado. Los dos `docs/MEMORIA*` están retirados y no son estado vigente.

## Objetivo
Construir el **Procedimiento de Distritación DDD**, reproducible, auditable y generalizable. Aragón es la primera implantación; Castilla y León, Extremadura y otros ámbitos deben incorporarse por datos/configuración, sin forks del motor. El producto es el procedimiento completo, no un mapa aislado.

## Arquitectura
M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final. M01–M03 son preparación cacheable; M04–M06 núcleo territorial; M07–M08 capa posterior. Los resultados electorales jamás condicionan la geometría.

## Reglas duras Aragón R012
- 67 distritos; 1.463 secciones; 1.364.621 habitantes.
- Provincia infranqueable: Huesca 11 / Teruel 7 / Zaragoza 49.
- Contigüidad estricta por M03.
- Suelo 0,80×target; techo 1,75×target; objetivo fino ±12%.
- Municipio que cabe bajo techo: indivisible.
- Municipio sobredimensionado: partición interna conexa; primero distritos exclusivamente municipales y solo el residual puede completarse con municipios menores adyacentes de la misma provincia.
- Prohibido el patrón de dispersión tipo “Barbastro en tres distritos mixtos”.
- Conservación exacta, CUSEC único/no nulo, determinismo y una configuración canónica.

## Ingeniería y auditoría
Toda versión relevante preserva anterior en `legacy/`, incrementa versión y actualiza bitácora/Estado Maestro. Cada ejecución relevante tiene expediente. Un informe o log nunca sustituye al producto. Los outputs ligeros completos viven en `resultados/ejecuciones/<RUN_ID>/Mxx/`; geometrías pesadas, en artefactos Actions con `PRODUCTOS.json` y SHA-256. Un resultado solo local/IA es diagnóstico, no referencia arbitral. Corregir siempre el primer módulo que viola su contrato.

## Historia que no debe perderse
**Run #5 `34584775443`:** R011 demostró outputs completos, pero su PASS era territorialmente incompleto: 13 distritos cruzaban provincias y 30 municipios aparecían fragmentados. No es referencia territorial.

**Run #6 `34587157452`:** FAIL. M04 v7.2.x creó el distrito 52 con 15 componentes; M05 lo detectó. Causa: bloques extraídos conexos pero residuo municipal no garantizado conexo.

**M04 v7.3.0:** corrige la causa mediante partición balanceada/conexa, ensamblaje rural conexo, sin fallback no adyacente y autovalidación antes de exportar.

## Estado vigente: Run #7
GitHub Run #7 **`34588834266` terminó SUCCESS** sobre commit `98a2e68907273fcd382a241687e645e8615bb47a`, modo iterativo.

- M01–M03: caché restaurada.
- M04 v7.3.0: K=67, cuotas 11/7/49, `hard=0`, min=18.345, max=31.563.
- M05 v7.2.0: `hard=0`, `fuera_12=1`, `max_rel_dev=0.5497`, **0 movimientos de unidad**.
- M06–M08: completados.
- Validación: **provincias PASS; disciplina municipal PASS; contigüidad PASS; población PASS**.
- Outputs M01–M08: materializados y publicados.

Run #7 es la primera evidencia GitHub de que R012 funciona estructuralmente. No es todavía solución final porque queda un distrito fuera de ±12%.

## Defecto operativo detectado en Run #7
El workflow muestra `PRODUCTOS.json: command not found` durante la generación del README de resultados. No invalida el run ni impide publicar los archivos. Causa: backticks interpretados por shell dentro de heredoc no protegido. Debe corregirse como mantenimiento del workflow, separado del algoritmo.

## Problema técnico inmediato
M04 ya entrega una solución estructuralmente válida. M05 no realiza ningún movimiento y deja el distrito de 31.563 habitantes fuera de ±12%. Hay que inspeccionar qué distrito es, sus `ddd_unit_id`, vecinos y restricciones que bloquean `candidates()`. Puede ser necesario permitir transferencias internas entre bloques del mismo municipio sobredimensionado sin abrir su frontera exterior; no debe relajarse provincia, contigüidad ni disciplina municipal.

## Outputs obligatorios
M01 secciones completas; M02 todas las aristas; M03 grafo completo; M04 asignación inicial completa; M05 asignación optimizada completa; M06 catálogo + composición + geometrías; M07 resultados por partido/distrito + resumen; M08 producto final. M06 debe seguir enriqueciéndose como ficha territorial: población/desviación, secciones, municipios/composición, provincia, superficie, perímetro, compacidad y atributos territoriales fiables.

## Orden exacto para continuar
1. Verificar si existe un run posterior al #7 antes de asumir que #7 sigue siendo el último.
2. Crear/leer expediente formal del Run #7.
3. Corregir el heredoc del workflow sin mezclar esa corrección con M05.
4. Auditar M05 del Run #7 y explicar por qué aceptó cero movimientos.
5. Diseñar R014/M05 siguiente manteniendo todos los PASS R012 y buscando `fuera_12=0`.
6. Tras el siguiente run, actualizar expediente, bitácora, Estado Maestro y este documento si cambia el estado.

## Regla de interacción
No repetir recaps innecesarios ni detenerse cuando existe una acción clara. El asistente debe inspeccionar GitHub/logs/artefactos directamente, no pedir al usuario que copie errores disponibles en el repo. **Cada respuesta sustantiva termina con “Siguiente paso” concreto.**
