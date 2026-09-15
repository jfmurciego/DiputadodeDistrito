# CI verde y reenganche Aragón M01–M06 — 2026-09-15

## Estado

`main` queda nuevamente verde tras separar correctamente las verificaciones que deben ejecutarse sobre el checkout completo de las que deben ejecutarse dentro de la imagen reproducible, que por diseño excluye datasets y `legacy/`.

## Incidencias cerradas

1. `tests/test_ensemble_integration.py` ya no interpreta la ausencia deliberada de `inputs/COMARCAS.csv` dentro de Docker como pérdida de gobierno. Cuando el fichero existe verifica SHA-256, 731 municipios y 33 comarcas; cuando Docker lo excluye exige la misma huella canónica en `inputs/MANIFEST.sha256`.
2. `tests/test_workflow_safety.py` mantiene obligatoria la ausencia de workflows retirados en `.github/workflows/`. La existencia histórica bajo `legacy/` se verifica cuando `legacy/` está materializado; dentro de Docker la omisión solo se admite con `DDD_SKIP_LEGACY_CHECK=1`, después de la auditoría exterior del checkout.
3. Las versiones anteriores de ambas pruebas están preservadas en `legacy/tests/`.

## Evidencia CI

- Commit final: `d08d4dbd2e8a181067dc1f4615c3fc705bc99d7c`
- Workflow: `Pruebas DDD — R015`
- Run: `34958884168`
- Resultado: `SUCCESS`
- Pasos críticos: auditoría de cabeceras/legacy, construcción reproducible y suite de evidencia/determinismo, todos `SUCCESS`.

## Reenganche operativo autorizado

El siguiente paso no es GerryChain. Debe ejecutarse la certificación territorial Aragón M01–M06 sobre el HEAD actual para comprobar la reparación M04 v7.4.6 con el grafo depurado de frontera compartida mínima de 1 metro.

Formulario manual:

- Workflow visible: `Operación territorial DDD — M01 a M08`
- `territory_id`: `aragon`
- `operation`: `certificar_territorio_m01_m06`
- `execution_authorization`: `EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION`
- `ensemble_stage`: dejar valor por defecto; no interviene en esta operación.
- `ensemble_promotion_authorization`: vacío.

## Criterios de aceptación del run

Antes de fijar un nuevo baseline deben cumplirse simultáneamente:

- 1.463 secciones y 1.364.621 habitantes;
- grafo M02 depurado con 4.063 aristas y sin nodos aislados;
- K=67;
- cuotas provinciales 11 / 7 / 49;
- `hard=0` en M04;
- `fuera_12=0` tras M05/M06;
- contigüidad completa por grafo;
- conservación exacta de población y universo M01→M06;
- disciplina municipal y provincia única por distrito.

## Después del SUCCESS territorial

1. calcular el nuevo `maxdev` canónico y sustituir el trinquete heredado de la topología anterior;
2. disolver geométricamente los 67 distritos y exigir una sola componente por distrito;
3. registrar el nuevo baseline y los hashes de artefactos;
4. solo entonces lanzar `aragon_10` de GerryChain;
5. `aragon_50` continúa bloqueado hasta revisión explícita del piloto de 10.

## Limitación operativa de esta sesión

La conexión GitHub disponible permite leer, escribir repositorio, inspeccionar y reejecutar runs existentes, pero no expone una acción para crear un nuevo `workflow_dispatch`. Por ello el nuevo run manual M01–M06 debe iniciarse desde la interfaz de GitHub; una vez creado, cualquier sesión puede continuar desde su `run_id` y auditarlo sin reconstruir contexto.
