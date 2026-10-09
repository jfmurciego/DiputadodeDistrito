# Diputado de Distrito — Procedimiento de Distritación DDD

**README v3.1.0** · 11-09-2026 · Estado: R012 validado estructuralmente; optimización fina pendiente

Sistema modular para construir, validar y auditar distritos uninominales a partir de unidades censales oficiales. El objetivo no es producir un mapa aislado, sino un **procedimiento repetible**: mismo código + mismos inputs + misma configuración ⇒ mismo resultado verificable por terceros. Aragón es la primera implantación; el motor debe generalizarse a otros ámbitos por configuración y datos, sin forks territoriales.

## Estado actual

El procedimiento tiene ocho módulos M01–M08, ejecución reproducible en GitHub Actions, preparación territorial cacheable, outputs intermedios completos, manifiestos, hashes, validación automática y conservación de versiones.

La regla territorial vigente es **R012: provincia dura y disciplina municipal**. Aragón tiene 67 distritos con reparto **Huesca 11 / Teruel 7 / Zaragoza 49**. Ningún distrito cruza provincia. Un municipio que cabe bajo el techo de un distrito se conserva íntegro; los municipios sobredimensionados se particionan internamente en bloques contiguos, llenando primero los distritos exclusivamente municipales y permitiendo que solo el residual se complete con municipios menores adyacentes de la misma provincia.

### Última ejecución territorial: Run #7
GitHub Run #7 `34588834266`, commit `98a2e68907273fcd382a241687e645e8615bb47a`, terminó **SUCCESS** en modo iterativo.

M04 v7.3.0 produjo 67 distritos, cuotas 11/7/49, cero violaciones duras, mínimo 18.345 y máximo 31.563. M05 v7.2.0 mantuvo todas las reglas duras pero dejó **1 distrito fuera de ±12%** y aceptó 0 movimientos. La validación final confirmó: **provincias PASS, disciplina municipal PASS, contigüidad PASS y población dentro del suelo/techo PASS**. M06–M08 y los outputs auditables M01–M08 se publicaron correctamente.

Por tanto, Run #7 es la primera evidencia GitHub de R012 estructuralmente válida. **No es todavía la solución final**: el siguiente problema es M05 y el único distrito de 31.563 habitantes fuera de ±12%.

## Reglas territoriales Aragón

1. **67 distritos exactos.**
2. **Provincia = frontera dura:** Huesca 11, Teruel 7, Zaragoza 49.
3. **Contigüidad estricta** sobre M03.
4. Conservación de **1.463 secciones** y **1.364.621 habitantes**.
5. Target = población total / 67.
6. Suelo duro = `0,80 × target`; techo duro = `1,75 × target`.
7. Objetivo fino = **±12%**.
8. Municipio que cabe bajo techo = **indivisible**.
9. Municipio sobredimensionado = partición interna conexa; distritos completos exclusivamente municipales y solo residual mezclable.
10. Resultados electorales nunca condicionan la geometría.
11. CUSEC único/no nulo, determinismo, configuración e inputs versionados y productos identificados por hash.

## Módulos y productos

| Módulo | Responsabilidad | Producto auditable |
|---|---|---|
| **M01** | Base territorial + población | secciones completas con CUSEC, atributos y geometría |
| **M02** | Adyacencias | lista canónica de aristas |
| **M03** | Grafo territorial | nodos, población y aristas |
| **M04** | Construcción inicial | asignación CUSEC→distrito válida estructuralmente |
| **M05** | Optimización | asignación optimizada sin romper reglas duras |
| **M06** | Consolidación | catálogo de 67 distritos + composición sección a sección + geometrías |
| **M07** | Agregación electoral | resultados por partido/distrito |
| **M08** | Producto final | geometría distrital enriquecida con resultados |

Los contratos detallados están en `docs/MODULOS/`. **Un informe explica cómo fue un módulo; nunca sustituye al producto que produjo.**

## Ejecución

Workflow: `.github/workflows/procedimiento-ddd.yml`, desde **Actions → Procedimiento DDD — Aragón**.

- `completo`: reconstruye M01–M03 desde fuentes congeladas y continúa hasta M08.
- `iterativo`: reutiliza M01–M03 si la preparación es compatible y recalcula M04–M08.

M01–M03 = preparación reutilizable. M04–M06 = núcleo territorial. M07–M08 = capa electoral posterior.

## Outputs y auditabilidad

Cada ejecución publica `resultados/ejecuciones/<RUN_ID>/M01...M08/`. CSV/JSON/JSONL completos permanecen navegables en Git. Las geometrías pesadas se conservan como artefactos M01–M08 de GitHub Actions. `PRODUCTOS.json` identifica los productos pesados por ruta, tamaño y SHA-256.

M06 publica `catalogo_distritos.csv` y `composicion_distritos.csv`, además de GeoJSON de secciones y distritos. Debe permitir reconstruir qué territorio forma cada distrito y seguirá enriqueciéndose como ficha territorial.

## Validación y aceptación

`herramientas/validar_ejecucion.py` es la puerta final y los módulos críticos validan también sus invariantes antes de exportar. Un PASS solo vale si las reglas certificadas están realmente implementadas. Run #5 demostró el peligro de una puerta incompleta; Run #6 demostró que M05 debe rechazar una mala salida de M04; Run #7 demuestra las reglas R012 completas.

Una versión nueva solo sustituye a la anterior si mantiene todas las restricciones ya aceptadas y mejora una capacidad o métrica explícita.

## Trazabilidad

- Versiones explícitas y anteriores preservadas en `legacy/`.
- Rondas en `docs/RONDAS/`.
- Expedientes de ejecución en `docs/EJECUCIONES/`.
- Evolución en `docs/BITACORA.md`.
- Estado canónico en `docs/ESTADO_MAESTRO_PROYECTO.md`.
- Handoff entre conversaciones en `docs/CONTINUIDAD_NUEVO_CHAT.md`.

Los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` están retirados como fuentes vigentes porque contenían estados históricos que podían inducir regresiones.

## Orden de lectura para continuar

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/CONTINUIDAD_NUEVO_CHAT.md`.
4. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`.
5. `docs/MODULOS/README.md` + contrato del módulo en curso.
6. `docs/BITACORA.md`.
7. Última ronda y última ejecución.
8. Configuración, workflow y código afectado.

## Incidencia operativa menor vigente
Run #7 mostró `PRODUCTOS.json: command not found` durante la generación del README de resultados por un heredoc de shell que interpreta backticks. No afectó al resultado ni a la publicación; debe corregirse separadamente del algoritmo.

## Principio rector

**Un resultado que solo existe en memoria, en un log o dentro de una sesión de IA no es un producto del procedimiento.** Cada transformación debe dejar una salida accesible, visible, reproducible y auditable. La evidencia arbitral es el repositorio y una ejecución GitHub reproducible por el usuario.
