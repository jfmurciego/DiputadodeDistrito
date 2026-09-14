# Inventario operativo

**Versión:** 1.0.0 — 2026-09-14

## Interfaces y workflows vigentes

- `.github/workflows/picadora-territorial.yml`: única interfaz manual para
  contratos, producción y ensembles.
- `.github/workflows/producir-territorio-por-contrato.yml`: cadena reutilizable
  M01–M08 con motor canónico.
- `.github/workflows/generar-alternativas-territoriales.yml`: cadena
  reutilizable GerryChain, sintética → Aragón 10 → Aragón 50.
- `.github/workflows/_reutilizable-bootstrap-territorio.yml`: preparación
  M01–M03 vigente.
- `.github/workflows/_reutilizable-auditoria-topologica.yml`: diagnóstico
  topológico vigente.
- `.github/workflows/pruebas-ddd.yml`: integración continua.
- `.github/workflows/desplegar-visor-publico.yml`: publicación manual del visor
  canónico.

Los workflows de regresión y auditoría territorial restantes son herramientas
manuales de evidencia, no interfaces generales de producción.

## Componentes GerryChain

- `ddd_core/m05_gerrychain_engine.py`: adaptador y motor alternativo.
- `ddd_ensemble/`: planificación, métricas, Pareto, reanudación y galería.
- `configuracion/ensemble/aragon.json`: contrato del primer piloto.
- `requirements-ensemble.lock`: entorno aislado.
- `inputs/COMARCAS.csv`: relación municipal-comarcal fijada por SHA-256.

## Archivado en esta limpieza

Se conservaron sin pérdida en `legacy/`:

- `legacy/workflows/cleanup_2026-09-14/`: promoción M01–M03 sustituida,
  exportador Flourish de una sola finalidad y antiguo publicador de sitio.
- `legacy/publication/sitio_geometria/`: copias de publicación que duplicaban
  la fuente canónica de `resultados/finales/`.

El archivado no cambia resultados certificados ni ejecuta territorios.
