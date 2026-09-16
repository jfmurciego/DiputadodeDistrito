# Diputado de Distrito — motor multi-territorio

**README v4.5.0** · 15-09-2026 · Estado: **plataforma ejecutable; productos territoriales bloqueados para publicación**
**Anterior:** `legacy/docs/README_v4.3.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

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
