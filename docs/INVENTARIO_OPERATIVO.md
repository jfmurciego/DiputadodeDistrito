# Inventario operativo

**Versión:** 1.3.0 — 2026-09-20
**Anterior:** versión 1.2.0 en historial Git

## Interfaces y workflows vigentes

- `.github/workflows/ejecucion-generacion-distritos.yml`: única interfaz humana
  para contratos, producción, visor, ensembles y orquestación. El formulario
  expone nombres institucionales en español, usa únicamente entradas `choice`
  y `boolean`, y resuelve internamente los IDs técnicos necesarios.
- `.github/workflows/_reutilizable-operacion-territorial.yml`: router interno que
  delega exclusivamente la ruta institucional seleccionada.
- `.github/workflows/producir-territorio-por-contrato.yml`: única cadena
  reutilizable M01–M08 con motor canónico para admisión, verificación,
  preparación, certificación y producción territorial.
- `.github/workflows/generar-alternativas-territoriales.yml`: cadena
  reutilizable GerryChain, sintética → Aragón 10 → Aragón 50.
- `.github/workflows/_reutilizable-auditoria-topologica.yml`: diagnóstico
  topológico reutilizable.
- `.github/workflows/desplegar-visor-publico.yml`: publicador manual y reutilizable del
  sitio GitHub Pages. Expone `workflow_dispatch` con selector `Sitio completo`,
  `Visor territorial` o `Dashboard operativo`; empaqueta siempre el sitio completo
  para no borrar rutas existentes.
- `.github/workflows/orquestacion-control.yml`: control de ejecución reutilizable.
- `.github/workflows/orquestacion-durable.yml`: resolución durable de
  reutilización y estado.
- `.github/workflows/pruebas-ddd.yml`: integración continua automática.
- `.github/workflows/validar-contratos-territoriales.yml`: puerta automática de
  validación estructural de contratos.
- `.github/workflows/validar-productos-publicos.yml`: puerta automática de
  validación de productos públicos.

`_reutilizable-bootstrap-territorio.yml` ya no forma parte del árbol operativo:
su predecesor se conserva en
`legacy/workflows/consolidacion-interfaz/_reutilizable-bootstrap-territorio_v1.0.0.yml`.

Las interfaces humanas vigentes incluyen las operaciones de preparación, generación,
incorporación electoral y publicación web. Las puertas CI conservan sus disparadores
automáticos. El critical path manual está documentado en
`docs/ORQUESTACION/CRITICAL_PATH_EJECUTABLES.md`.

## Compatibilidad de la interfaz

GitHub Actions no permite definir en un `choice` una etiqueta visible distinta
del valor enviado. Por ello la interfaz principal muestra etiquetas humanas y
las traduce dentro del propio workflow a los contratos técnicos ya existentes,
incluido `Islas Baleares` → `illes_balears`. Los run IDs necesarios para
reutilización no son campos humanos: la interfaz resuelve automáticamente el
último checkpoint compatible y, cuando se solicita republicación, el último
Aragón-10 válido.

No se cambian rutas territoriales, configuraciones, geometrías, umbrales ni
motores por esta actualización documental.

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
- `legacy/workflows/interfaz/`: interfaces humanas sustituidas.
- `legacy/workflows/consolidacion-interfaz/`: reutilizables y regresiones
  retirados del árbol operativo durante la consolidación.
- `legacy/workflows/g10/`: workflows G10 sustituidos por la cadena actual.
- `legacy/publication/sitio_geometria/`: copias de publicación que duplicaban
  la fuente canónica de `resultados/finales/`.

El archivado no cambia resultados certificados ni ejecuta territorios.
