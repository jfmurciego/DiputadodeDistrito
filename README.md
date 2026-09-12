# Diputado de Distrito — motor multi-territorio

**README v4.2.0** · 12-09-2026 · Estado: **R023 expansión nacional + G10 operativo inicial**  
**Anterior:** `legacy/docs/README_v4.0.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

## Arquitectura

Un repositorio, una rama permanente (`main`), un motor común (`ddd_core/`, `modulos/`, `herramientas/`) y territorios definidos por datos, configuración y contratos. M01–M03 preparan y auditan topología; M04–M06 construyen y consolidan; M07–M08 agregan resultados electorales después de fijar la geometría.

## Baselines

- Aragón: referencia principal, Run `34599224954`; 67 distritos, `fuera_12=0`, máximo desvío 9,930 %, todas las restricciones PASS.
- Castilla y León: segunda implantación validada hasta M06; 82 distritos, 3.506 secciones, `fuera_12=0`.
- Extremadura: M01–M03 cerrados; M04/M05 experimental; EXT-19 no promovido.
- Andalucía: M01–M03 cerrados; AND-04 reveló 4 distritos fuera de suelo/techo en M04.
- Cataluña: CAT-03 Run `34688242964` validó M01–M03 con 5.143 secciones y una pasarela administrativa auditada para Llívia.

## Expansión nacional

R022 Run `34688010656` ejecutó Madrid y otros 13 territorios pendientes. Todos completaron M01–M03 observable. Resultado ligero: `resultados/bootstrap/gh-34688010656/RESUMEN_NACIONAL.json`.

R023 audita geométricamente los siete territorios continentales con discontinuidades observadas. Los archipiélagos se tratan mediante contrato propio; ninguna pasarela se añade automáticamente.

## Gobernanza

Leer primero `docs/SALIDAS_CHATGPT/SALIDA_MAESTRA.md`, después `docs/ESTADO_MAESTRO_PROYECTO.md`. Toda sustitución conserva el predecesor en `legacy/`. El cálculo pesado, los logs y las geometrías viven en GitHub Actions; las salidas ligeras verificadas se materializan en el repositorio.

## Orquestación G10

El controlador G10 ya valida planes, crea matrices independientes, clasifica resultados y agrega artefactos sin cancelar el lote por un fallo parcial. La guía de bajo nivel distingue las capacidades activas de las piezas todavía pendientes de conectar: [`docs/G10_GUIA_BAJO_NIVEL.md`](docs/G10_GUIA_BAJO_NIVEL.md).
