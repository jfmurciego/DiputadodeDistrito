# RESULTADO — Limpieza institucional de la interfaz GitHub Actions

**Fecha:** 2026-09-15  
**Repositorio:** `jfmurciego/DiputadodeDistrito`  
**Rama:** `main`  
**Ámbito:** exclusivamente interfaz, nomenclatura, pruebas asociadas y legacy de workflows.

## Resultado

La interfaz territorial principal ha quedado renombrada físicamente como:

`/.github/workflows/operacion-territorial.yml`

El nombre histórico `picadora-territorial.yml` ya no existe en la ruta activa. La
versión que estaba vigente antes del renombrado se conservó íntegramente en:

`legacy/workflows/interfaz/picadora-territorial_v2.1.0.yml`

Antes de retirarla se volvió a leer desde `main` y se comprobó que su blob SHA
seguía siendo `7e87f8575214fedbaef068dd368dd435fd533d91`, el mismo observado al
inicio de esta tarea. Por tanto, no se sobrescribió ningún cambio concurrente.

El HEAD de partida fue
`ea6b305640af34f700e1954315f66314b1219035`. Inmediatamente antes de crear
este informe se volvió a comprobar `main`, que estaba en
`0ff74049278e633c04cd20f8576fe17a1e2514d8`.

## Interfaz pública

El selector territorial muestra ahora, en este orden:

1. Andalucía
2. Aragón
3. Principado de Asturias
4. Islas Baleares
5. Canarias
6. Cantabria
7. Castilla-La Mancha
8. Castilla y León
9. Cataluña
10. Comunidad Valenciana
11. Extremadura
12. Galicia
13. Comunidad de Madrid
14. Región de Murcia
15. Comunidad Foral de Navarra
16. País Vasco
17. La Rioja
18. Ceuta
19. Melilla

También se sustituyeron en la interfaz los identificadores técnicos visibles de
operaciones y fases GerryChain por etiquetas legibles en español, sin modificar
los contratos internos.

## Compatibilidad con IDs técnicos

No se han cambiado los IDs territoriales existentes, las rutas de contratos ni la
configuración territorial. La nueva interfaz incorpora un trabajo ligero
`resolver_interfaz` que traduce la etiqueta pública al ID técnico antes de llamar
a los workflows reutilizables. Ejemplos:

- `Aragón` → `aragon`
- `Castilla y León` → `castilla_y_leon`
- `Islas Baleares` → `illes_balears`
- `Comunidad de Madrid` → `madrid`

El mismo resolvedor reconoce además los identificadores técnicos históricos como
alias de entrada. Los workflows reutilizables siguen recibiendo los valores
contractuales anteriores. No se han modificado `ddd_core`, `ddd_ensemble`,
`procedimiento.sh`, configuraciones territoriales, resultados ni baseline.

## Limitación de GitHub Actions

`workflow_dispatch` con `type: choice` no ofrece un mecanismo limpio para
definir por separado una etiqueta humana y un valor técnico. Cada opción del
selector es el propio valor recibido por el workflow.

Para evitar cambiar los contratos del proyecto se ha aplicado la solución menos
invasiva: las opciones interactivas son etiquetas humanas en español y un
resolvedor interno las transforma a los IDs vigentes. Esto mantiene estables las
rutas y los workflows reutilizables.

La compatibilidad con IDs históricos está implementada en el resolvedor. No
obstante, un cliente externo que invoque directamente un `workflow_dispatch`
con un valor que GitHub decida validar estrictamente contra las opciones del
`choice` puede necesitar enviar la etiqueta pública en lugar del ID técnico. Esa
limitación pertenece a la capa de despacho de GitHub; el contrato interno del
proyecto no ha cambiado.

## Pruebas y CI

Se añadió `tests/test_workflow_interfaz_institucional.py` y se actualizaron las
referencias de pruebas preexistentes que apuntaban al nombre retirado. Las
pruebas exigen:

- presencia de `operacion-territorial.yml` y ausencia de
  `picadora-territorial.yml` en workflows activos;
- nombres territoriales públicos exactamente en español y con mayúsculas y
  tildes correctas;
- `Islas Baleares` como etiqueta visible y `illes_balears` como ID interno;
- operaciones y fases con nombres públicos legibles;
- conservación explícita de todos los IDs territoriales, de operación y de
  ensemble usados por los contratos;
- mantenimiento de la línea común `producir-territorio-por-contrato.yml` como
  workflow reutilizable, no como segunda interfaz territorial general.

El primer CI posterior al renombrado, run `34960075145`, detectó tres referencias
obsoletas de pruebas al antiguo nombre de fichero. Esas tres referencias se
corrigieron sin modificar código productivo. Tras las correcciones, el run
`34960294090` completó el job `pruebas` con **success**, incluida la verificación
de evidencia publicada y determinismo sintético.

No se lanzó ningún workflow territorial. Los únicos workflows ejecutados durante
esta tarea fueron las pruebas CI automáticas provocadas por commits a `main`.

## Commits de la tarea

- `d4d6da38b07ee5a668c533a4b8501d6ad6a116c1` — preservar en legacy la interfaz v2.1.0.
- `7e1b1985b3d60c57545696595d59d0cdc65015e6` — crear `operacion-territorial.yml` con etiquetas públicas y resolvedor.
- `3c4f151d0921cbb9ace47f610eea417d3ef113fb` — actualizar prueba de seguridad al nuevo nombre.
- `4b59c0629bfde2c415247516cb734f4cd6af389a` — retirar `picadora-territorial.yml` de la ruta activa.
- `23b4d76fe6878de894648b448c62ecccebb1f53a` — añadir prueba específica de interfaz institucional.
- `4f84b704ccf00295866598e7f43bc16eb6fe8351` — actualizar inventario operativo.
- `973d6de16cbeb7cfe4a519792f16abf708bb8abc` — integrar la nueva prueba en `unittest discover`.
- `6fbf06a62f5c6fd1447bef502068b3e5804a514e` — actualizar referencia de integración GerryChain al nuevo nombre del workflow.
- `273d8c49c354dd4be65cf1686c83dd6a0417a3be` — actualizar referencia de interfaz de producción.
- `0ff74049278e633c04cd20f8576fe17a1e2514d8` — adaptar trinquetes R038 a las etiquetas públicas españolas.

## Cierre

La limpieza queda cerrada como cambio de interfaz. La arquitectura de workflow
único territorial general se conserva, la nomenclatura pública queda en español,
los IDs técnicos permanecen estables y existe copia histórica de la interfaz
retirada. No se ejecutó ningún territorio ni se alteró el motor territorial.
