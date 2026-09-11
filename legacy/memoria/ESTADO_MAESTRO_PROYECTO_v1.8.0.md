# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.8.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.7.0.md`

## 1. Fuente de verdad y arranque
Leer `README.md`, este documento, `docs/CONTINUIDAD_NUEVO_CHAT.md`, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflow y código afectado. Los dos archivos antiguos `MEMORIA*` están retirados y no son fuentes de estado.

## 2. Reglas duras Aragón — R012
1. 67 distritos exactos.
2. Provincia como frontera dura: Huesca 11 / Teruel 7 / Zaragoza 49.
3. Contigüidad estricta por grafo M03.
4. Conservación de 1.463 secciones y 1.364.621 habitantes.
5. Suelo 0,80×target; techo 1,75×target.
6. Objetivo fino ±12%.
7. Municipio que cabe bajo techo: indivisible.
8. Municipio sobredimensionado: partición interna conexa; distritos completos exclusivamente municipales y solo residual mezclable con municipios menores adyacentes de la misma provincia.
9. Resultados electorales nunca condicionan geometría.
10. Determinismo, CUSEC único/no nulo y una configuración canónica.

## 3. Implementación vigente
Configuración `configuracion/aragon_2025.yaml` v7.4.0. Validación `herramientas/validar_ejecucion.py` v1.3.0.

M04 **v7.3.0**: construcción provincia-first, partición municipal balanceada/conexa, ensamblaje rural conexo, sin fallback no adyacente y autovalidación de cardinalidad, cuotas, provincia, contigüidad y suelo/techo.

M05 **v7.2.0**: optimización por unidades territoriales protegidas, sin cruces provinciales y preservando conectividad. Actualmente no logra mover ninguna unidad en la solución de M04 v7.3.0.

## 4. Ejecuciones relevantes
Run #5 `34584775443`: R011 demuestra outputs auditables, pero no es referencia territorial por cruces provinciales y fragmentación municipal detectados después.

Run #6 `34587157452`: FAIL. M04 produjo distrito 52 con 15 componentes; M05 lo detectó. Causa corregida en M04 v7.3.0.

### Run #7 — `34588834266` — SUCCESS
Commit ejecutado: `98a2e68907273fcd382a241687e645e8615bb47a`. Modo `iterativo`; M01–M03 restaurados desde caché.

Resultados:
- M04 v7.3.0: `hard=0`, K=67, cuotas 11/7/49, min=18.345, max=31.563.
- M05 v7.2.0: `hard=0`, `fuera_12=1`, `max_rel_dev=0.5497`, `movimientos_unidad=0`.
- M06–M08 completados.
- Validación final: **67 distritos; provincias PASS; disciplina municipal PASS; contigüidad PASS; población dentro de [16.294,0, 35.643,1]**.
- Outputs M01–M08 materializados y publicados.

Run #7 es la primera ejecución GitHub que demuestra simultáneamente las reglas duras R012. Todavía **no es solución final de equilibrio** porque queda 1 distrito fuera de ±12%.

## 5. Hallazgo operativo adicional Run #7
Durante la publicación aparece `/...sh: line 10: PRODUCTOS.json: command not found`. La ejecución no falla y los `PRODUCTOS.json` sí se publican; la causa es el uso de backticks dentro de un heredoc no protegido en el README de resultados. Es un defecto del workflow de presentación que debe corregirse en la próxima ronda de mantenimiento, sin mezclarlo con el algoritmo territorial.

## 6. Outputs y auditabilidad
R011 sigue siendo obligatoria: cada módulo expone su producto completo. Los ligeros se publican en `resultados/ejecuciones/<RUN_ID>/Mxx/`; los GeoJSON pesados quedan en artefactos Actions y `PRODUCTOS.json` los identifica por hash/tamaño/ruta.

M06 debe seguir evolucionando como ficha territorial completa del distrito, no como mero resumen poblacional.

## 7. Próximo problema algorítmico
M04 ya entrega una estructura dura válida. El cuello de botella pasa a M05: debe resolver el único distrito fuera de ±12% sin abrir provincia, romper municipio, perder contigüidad ni degradar los otros 66. Antes de cambiar M04 debe existir evidencia de defecto propio.

## 8. Siguiente acción exacta
1. Registrar expediente formal del Run #7.
2. Corregir separadamente el heredoc del workflow que interpreta `PRODUCTOS.json` como comando.
3. Auditar M05 Run #7: identificar el distrito de 31.563 habitantes, sus unidades vecinas y por qué `candidates()` produce cero movimientos aceptados.
4. Diseñar una optimización que permita transferencias válidas —incluidas, si son necesarias, transferencias internas entre bloques del mismo municipio sobredimensionado— sin violar R012.
5. Ejecutar nuevamente y buscar `fuera_12=0` manteniendo todos los PASS duros.
