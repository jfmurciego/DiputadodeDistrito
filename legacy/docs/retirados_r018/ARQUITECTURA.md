# Arquitectura del proyecto

**Versión:** 1.0.0  
**Fecha:** 2026-09-11

## Terminología oficial

El conjunto completo se denomina **procedimiento de distritación**. Cada unidad funcional indivisible se denomina **módulo**. Una ejecución concreta se denomina **ejecución**. La palabra “pipeline” queda reservada para productos externos que la utilicen.

## Principio de diseño

Cada módulo tiene una sola responsabilidad, entradas y salidas explícitas y una razón para ocupar su posición. Se separan las operaciones costosas y estables (01-03), las operaciones algorítmicas y experimentales (04-05) y las operaciones de consolidación y análisis (06-08).

## Estructura óptima

- `modulos/`: ocho módulos vigentes.
- `ddd_core/`: utilidades transversales y configuración.
- `configuracion/`: un contrato por territorio/año; no se duplica código por comunidad autónoma.
- `herramientas/`: validación y trazabilidad.
- `inputs/`: fuentes controladas por hash.
- `.cache/ddd/`: derivados reutilizables de 01-03; nunca son fuente de verdad.
- `output/`: resultados de la ejecución actual.
- `legacy/`: versiones anteriores completas e inmutables.
- `docs/`: arquitectura, catálogo, bitácora y memoria del proyecto.
- `.github/workflows/`: ejecución demostrable en GitHub Actions.

## Regla de versionado

Ningún fichero vigente se sustituye sin:

1. conservar la versión anterior en `legacy/<fecha>_<version>/...`;
2. incrementar la versión dentro del propio fichero;
3. declarar qué hace, por qué cambia y qué versión sustituye;
4. registrar el cambio en `docs/BITACORA.md`;
5. ejecutar validación sintáctica y funcional;
6. no declararlo **validado** hasta que el mismo commit supere GitHub Actions y la puerta de calidad.

Estados: `experimental` → `candidato` → `validado`. Cambiar código no equivale a mejorar. Toda versión nueva se compara con la última versión validada.

## Diez ejecuciones en un día

Los módulos 01-03 producen una **base preparada**: secciones+población, adyacencias y grafo. La clave de caché depende de hashes de las fuentes, la configuración y el código de esos módulos. Si se cambia solo el algoritmo (04-05), el procedimiento restaura esa base y evita releer los ficheros nacionales y recalcular geometrías.

Esto permite distinguir:

- **modo completo**: reconstruye desde las fuentes oficiales;
- **modo iterativo**: reutiliza 01-03 y ejecuta 04-08.

La caché nunca sustituye la reproducibilidad: cualquier cambio en una fuente o en los módulos 01-03 debe invalidarla.
