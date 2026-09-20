# Diputado de Distrito — motor multi-territorio

**README v4.6.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**
**Anterior:** `legacy/docs/README_v4.3.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

## Estado actual por territorio

Instantánea operativa del **20-09-2026**. El criterio de esta tabla es la **cadena automática vigente** de preparación de fuentes, generación y resultados. Las ejecuciones anteriores a esta cadena no se consideran prueba suficiente por sí solas.

| Territorio | Preparación territorial | Preparación electoral | Ejecución automática vigente | Punto de continuidad |
|---|---|---|---|---|
| **Andalucía** | No | No | ⚪ Pendiente de incorporación | Tiene contrato, pero faltan declaración y preparación de fuentes. |
| **Aragón** | Integrada previamente | Integrada previamente | 🟡 No revalidada con la cadena separada actual | Contrato y productos existen; falta demostrar de nuevo la ruta automática vigente sin apoyarse en ejecuciones anteriores. |
| **Asturias** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Baleares** | No | No | 🔴 No incorporada | No consta todavía contrato territorial operativo en el catálogo actual. |
| **Canarias** | No | No | 🔴 No incorporada | No consta todavía contrato territorial operativo en el catálogo actual. |
| **Cantabria** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Castilla-La Mancha** | **Hecha** | Pendiente | 🟠 Preparada, con estado de catálogo pendiente de promoción | Existe paquete territorial nuevo; antes de ejecutar hay que alinear el catálogo con esa evidencia. |
| **Castilla y León** | Integrada previamente | Integrada previamente | 🟡 No revalidada con la cadena separada actual | Tiene contrato y productos; falta revalidación completa con la automatización vigente. |
| **Cataluña** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Ceuta** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin preparación territorial en la nueva cadena. |
| **Comunidad de Madrid** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Comunidad Valenciana** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Extremadura** | **Hecha** | Pendiente | 🟠 Preparada para continuar | El paquete territorial nuevo está preparado; siguiente paso: preparación electoral y generación automática. |
| **Galicia** | **Hecha** | **Hecha** | 🟢 **Generación territorial automática validada** | Run `35505298149`: 75 distritos, 2.134 secciones, población 2.714.741, auditoría geométrica `PASS_WITH_EXCEPTIONS` y publicación del visor completada. La incorporación electoral todavía no se ejecutó en ese run. |
| **La Rioja** | No | No | 🟡 Preflight | Contrato completo y estado de preflight; falta preparación territorial oficial. |
| **Melilla** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin preparación territorial en la nueva cadena. |
| **Murcia** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **Navarra** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |
| **País Vasco** | No | No | ⚪ Pendiente de incorporación | Tiene contrato; sin fuentes preparadas en la nueva cadena. |

La tabla debe mantenerse como **resumen operativo de entrada** al proyecto: cuando cambie el estado demostrable de un territorio, se actualiza aquí a partir de la evidencia reproducible de GitHub.

## Arquitectura

Un repositorio, una rama permanente (`main`), un motor común (`ddd_core/`, `modulos/`, `herramientas/`) y contratos territoriales declarativos en `territorios/<id>/`. Las etapas semánticas G10 preservan la compatibilidad M01–M08 y permiten reenganche sin recalcular productos certificados.

## Fase 1 — estado canónico

- Aragón: contrato ejecutable; el candidato métrico de 67 distritos está `BLOCKED_GEOMETRIC_CONTIGUITY` (60/67 conectados).
- Castilla y León: evidencia técnica de 82 distritos; publicación bloqueada.
- Extremadura: `EXPERIMENTAL_BLOCKED`; evidencia reproducible, sin promoción ni relajación de tolerancia.
- El estado factual y los contratos comparables están en `resultados/fase1/ESTADO_FACTUAL.json`.

No hay expansión territorial activa. Ninguna comunidad posterior se ejecuta sin instrucción expresa.

## Productos públicos

`resultados/finales/` contiene exclusivamente las fuentes canónicas de visualización. El workflow **Desplegar visor público** publica MapLibre para Aragón y Castilla y León sin ejecutar el motor ni reemplazar los GeoJSON.

## Motor alternativo GerryChain

GerryChain/ReCom se integra como M05 alternativo, con dependencias aisladas y
sin sustituir el motor determinista. La interfaz territorial principal es
`ejecucion-generacion-distritos.yml`; la limpieza debe retirar cualquier formulario
específico redundante. El orden obligatorio es prueba sintética, piloto
Aragón de 10 alternativas y lote de 50 únicamente tras revisar coste y
publicación. El piloto no arranca si la partición inicial falla la continuidad
de componentes poligonales. Véase `docs/ENSEMBLES_GERRYCHAIN.md`.

## Operación

Leer primero `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`. G10 admite tareas por huella y una evidencia idéntica debe producir `REUSED`, no una repetición de cálculo. Toda sustitución conserva el predecesor en `legacy/`.

El inventario de componentes activos y archivados está en
`docs/INVENTARIO_OPERATIVO.md`.
