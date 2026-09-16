# Migración de G10 a Orquestación O01/O02

Fecha: 2026-09-16

La denominación **G10** pasa a considerarse histórica para la capa activa de orquestación. La función vigente se expresa mediante:

- **O01 · Controlar ejecución** (`.github/workflows/orquestacion-control.yml`)
- **O02 · Resolver reutilización y estado durable** (`.github/workflows/orquestacion-durable.yml`)

Herramientas canónicas nuevas:

- `herramientas/orquestar_ejecucion.py`
- `herramientas/informe_orquestacion.py`
- `herramientas/materializar_checkpoints.py`

Los nombres `herramientas/g10_*.py` se conservan temporalmente como wrappers de compatibilidad para planes, scripts o documentación operativa que todavía los invoquen. El paquete interno `g10/`, los esquemas `ddd.g10.*`, identificadores de planes y documentación histórica no cambian en esta migración: son contratos de estado/esquema y requieren una migración independiente.

O02 produce como nombres canónicos `RESUMEN_LOTE_ORQUESTACION.json`, `ESTADO_OPERATIVO_ORQUESTACION.json` y `ESTADO_OPERATIVO_ORQUESTACION.md`. Durante la transición mantiene también los destinos persistidos históricos `estado_operativo_g10.json` y `ESTADO_OPERATIVO_G10.md` como alias compatibles; los artefactos nuevos publicados por Actions usan únicamente prefijo `orquestacion-`.

No cambia lógica territorial, contratos, fingerprints, política de admisión, checkpoints, K, tolerancias, geometrías ni algoritmos.
