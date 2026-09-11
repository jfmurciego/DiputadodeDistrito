# Diputado de Distrito — Procedimiento de Distritación DDD

**README v3.0.0** · 11-09-2026 · Estado: desarrollo reproducible y auditable

Sistema modular para construir, validar y auditar distritos uninominales a partir de unidades censales oficiales. El objetivo no es producir un mapa aislado, sino un **procedimiento repetible**: mismo código + mismos inputs + misma configuración ⇒ mismo resultado verificable por terceros.

Aragón es la primera implantación. El motor debe generalizarse después a Castilla y León, Extremadura y otros ámbitos sin bifurcar el código territorial.

## Estado actual

El procedimiento tiene ocho módulos M01–M08, ejecución reproducible en GitHub Actions, caché de preparación territorial, outputs intermedios auditables, manifiestos, hashes, validación automática y conservación de versiones anteriores.

La ronda vigente es **R012: provincia dura y disciplina municipal**. Para Aragón se exigen 67 distritos con reparto provincial **Huesca 11 / Teruel 7 / Zaragoza 49**. Ningún distrito puede cruzar provincia. Un municipio que cabe dentro del techo de un distrito se conserva íntegro; los municipios sobredimensionados se particionan internamente en bloques contiguos, llenando primero los distritos urbanos y permitiendo que solo el residual se complete con municipios menores adyacentes de la misma provincia.

El Run #6 (`34587157452`) detectó correctamente una regresión de M04: el distrito 52 nacía con 15 componentes. Esa versión no es referencia. **M04 v7.3.0** corrige el particionado municipal y añade autovalidación antes de entregar datos a M05. Sobre los datos reales del Run #6, la comprobación previa a GitHub produjo 67 distritos, cuotas 11/7/49, cero cruces provinciales, cero desconectados, cero distritos bajo suelo o sobre techo y un único distrito fuera de ±12%. La siguiente ejecución GitHub es la puerta de aceptación de esta versión.

## Reglas territoriales vigentes en Aragón

1. **67 distritos exactos.**
2. **Provincia = frontera dura:** Huesca 11, Teruel 7, Zaragoza 49.
3. **Contigüidad estricta** sobre el grafo territorial M03.
4. Conservación exacta de las **1.463 secciones** y **1.364.621 habitantes** de la preparación vigente.
5. Target poblacional = población total / 67.
6. Suelo duro = `0,80 × target`; techo duro = `1,75 × target`.
7. Objetivo de equilibrio fino: **±12%**.
8. Municipio que cabe bajo el techo: **indivisible**.
9. Municipio sobredimensionado: partición interna conexa; los distritos urbanos completos permanecen exclusivamente municipales y solo el residual puede mezclarse con municipios menores.
10. La geometría se calcula **sin resultados electorales**. M07/M08 son una capa posterior de análisis.
11. CUSEC único y no nulo, determinismo, inputs/configuración versionados y productos identificados por hash.

## Los ocho módulos

| Módulo | Responsabilidad | Producto auditable principal |
|---|---|---|
| **M01** | Base territorial + población | 1.463 secciones, CUSEC, atributos y geometría |
| **M02** | Adyacencias | lista canónica de aristas entre secciones |
| **M03** | Grafo territorial | nodos + población + aristas; base de contigüidad |
| **M04** | Construcción inicial | CUSEC→distrito respetando provincia/municipio/contigüidad |
| **M05** | Optimización | asignación optimizada sin romper restricciones duras |
| **M06** | Consolidación | catálogo de 67 distritos + composición sección a sección + geometrías |
| **M07** | Agregación electoral | resultados por partido y distrito |
| **M08** | Producto final | geometría distrital enriquecida con resultados |

Cada módulo tiene su contrato detallado en `docs/MODULOS/`. Un informe explica cómo se ejecutó un módulo; **nunca sustituye al producto que el módulo produjo**.

## Ejecución y reutilización

El workflow es `.github/workflows/procedimiento-ddd.yml` y se lanza manualmente desde **Actions → Procedimiento DDD — Aragón**.

- `completo`: reconstruye M01–M03 desde las fuentes congeladas y continúa hasta M08.
- `iterativo`: reutiliza la preparación M01–M03 cuando su clave de caché es compatible y recalcula M04–M08.

M01–M03 son preparación territorial reutilizable. M04–M06 constituyen el núcleo de distritación. M07–M08 son posteriores y no intervienen en la construcción de los distritos.

## Outputs y auditabilidad

Cada ejecución publica `resultados/ejecuciones/<RUN_ID>/M01...M08/`. Los CSV/JSON/JSONL navegables permanecen en Git. Las geometrías pesadas se conservan como artefactos separados de GitHub Actions para no inflar el historial. Cada módulo publica `PRODUCTOS.json` con ruta, tamaño y SHA-256 del producto pesado.

M06 no es un resumen de dos columnas: publica `catalogo_distritos.csv` y `composicion_distritos.csv`, además de los GeoJSON completos. Debe permitir reconstruir qué territorio y qué secciones forman cada distrito.

## Validación y criterio de aceptación

`herramientas/validar_ejecucion.py` es la puerta final, pero los módulos críticos también deben validar sus invariantes antes de exportar. Un `PASS` solo es aceptable si las reglas que pretende certificar están realmente implementadas; el Run #5 demostró por qué un PASS con una puerta incompleta no constituye una referencia territorial.

Una versión nueva no sustituye a la anterior porque “termine”: debe mantener todas las restricciones duras y mejorar una capacidad o métrica explícita. Las regresiones se documentan y no se promocionan.

## Trazabilidad y versionado

- Código, configuración y documentación tienen versión explícita.
- Antes de sustituir un archivo relevante se conserva la versión anterior en `legacy/`.
- Cada desarrollo significativo es una **ronda** (`docs/RONDAS/`).
- Cada ejecución relevante tiene expediente (`docs/EJECUCIONES/`).
- `docs/BITACORA.md` registra la evolución cronológica.
- `docs/ESTADO_MAESTRO_PROYECTO.md` es la **fuente canónica del estado vigente**.
- `docs/CONTINUIDAD_NUEVO_CHAT.md` contiene el protocolo para retomar el proyecto sin depender del contexto de una conversación anterior.

## Documentación: orden de lectura

Para incorporarse al proyecto o continuar en un nuevo chat, leer en este orden:

1. `README.md` — propósito, reglas y mapa general.
2. `docs/ESTADO_MAESTRO_PROYECTO.md` — estado técnico vigente y siguiente acción.
3. `docs/CONTINUIDAD_NUEVO_CHAT.md` — protocolo de continuidad y hechos que no deben perderse.
4. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md` — arquitectura M01–M08.
5. `docs/MODULOS/README.md` y el contrato del módulo que se vaya a modificar.
6. `docs/BITACORA.md` — evolución y decisiones.
7. Última ronda de `docs/RONDAS/` y última ejecución de `docs/EJECUCIONES/`.
8. `configuracion/aragon_2025.yaml`, workflow y código del módulo afectado.

Los documentos históricos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` no deben utilizarse como estado vigente; se mantienen únicamente por trazabilidad histórica y remiten al Estado Maestro.

## Principio rector

**Un resultado que solo existe en memoria, en un log o dentro de una sesión de IA no es un producto del procedimiento.** Cada transformación debe dejar una salida accesible, visible, reproducible y auditable. La evidencia arbitral es el repositorio y una ejecución GitHub reproducible por el usuario.
