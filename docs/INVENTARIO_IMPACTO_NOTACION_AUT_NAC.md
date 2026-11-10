# Inventario de impacto: notación AUTnn / NACnn (T-148, paso 2)

Fecha: 2026-11-10 · Tabla maestra: `configuracion/notacion_territorial.csv` (71 filas: AUT01-19 = CODAUTO del INE; NAC01-52 = CPRO del INE; fuente `fuentes/ine_codigos_territoriales_2026-11-10/`, sha256 en `SHA256SUMS`).

Hoy el identificador interno (`andalucia`, `congreso_alava`…) y el nombre se usan como clave. La notación nueva se superpone: no sustituye al id interno (paso 4, sin ejecutar).
Ceuta y Melilla existen en los dos universos: AUT18/AUT19 (autonómica, `ceuta`, `melilla`) y NAC51/NAC52 (Congreso, `congreso_ceuta`, `congreso_melilla`). El código NAC es siempre el CPRO, así que Madrid es AUT13 (comunidad, `madrid`) y NAC28 (provincia, `congreso_madrid`). `pilot_code` del catálogo (`C01`…`C52`) ya coincide con `C` + CPRO.
Variante «Congreso 350» (`congreso350_*`, 49 ids, `pilot_code` Rnn): no tiene código propio; hereda NACnn de su provincia (decisión pendiente: sufijo o campo `variante`). Baleares, Las Palmas y Santa Cruz de Tenerife no tienen variante 350.

## Dónde aparece el id interno y qué se rompe si cambia
| Lugar | Uso | Si cambia el id |
|---|---|---|
| `configuracion/catalogo_territorios_espana_2025.yaml` (`territory_id`, `pilot_code`) | clave del catálogo; 19 + 101 entradas (52 Congreso + 49 «350») | Rompe `catalogo_territorios.py`, `ddd_core/territory_contract.py` (exige una entrada por `meta.territory_id`) y todos los contratos |
| `territorios/<id>/` (122 carpetas: config, evidencia, CONTINUIDAD) y `meta.territory_id` de cada config | ruta y contrato | Mover carpetas rompe rutas de evidencia, receipts y huellas |
| `configuracion/` (19 ficheros: `registro_electoral.yaml`, `preparacion_legislatura_vigente.yaml`, `politica_generacion_territorial_2025.yaml`, `elecciones_generales_2026.yaml`, `ensemble/<id>.json`, contratos Minsait, `f10_auto_tareas.json`) | referencias por id | Referencias colgantes; el registro electoral exige ids únicos |
| `herramientas/` (12 ficheros con ids literales, p. ej. `calendario_autonomicas.py`, `adaptador_eleccionesdb.py`; más `clave_eleccion.py`, `gestor_campana_nacional.py`, `resolver_*`, `generar_estado_operativo.py`) | resolución, Gestor, dashboard | Rompe claves de elección `ES-<ámbito>-<unidad>-<fecha>` y el seguimiento del Gestor |
| `ddd_core/congreso_contract.py`, `electoral_contract.py` | `territory_id` esperado en contratos | Rechaza productos con id distinto (`expected_territory_id`) |
| `.github/workflows/*` | input `territory_id` de tipo `choice` (opciones = catálogo; no hay ids literales en el YAML de la 00) y comprobaciones por test | Cambiar opciones invalida lanzamientos y el test que compara opciones con el catálogo |
| `orchestracion/publicaciones_visor.json` (197 productos: `territory_id`, id `m06-<id>-<run>`) | registro de solo adición | No se puede reescribir sin romper la regla de solo adición; el visor busca por este id |
| `orchestracion/archivo_r2.json` y claves R2 `r2://ddd-research-archive/<id>/<run>/…` | archivo de artefactos; campo `territorio` | Renombrar claves en R2 = copiar y borrar; los sha256 se conservan, las rutas no |
| `orchestracion/estado_operativo.json`, `catalogo_procedencia.json`, `publicado/dashboard/` | tablero y procedencia | Se regeneran, pero el histórico del dashboard usa ids |
| `datos_abiertos/<id>/` (52 carpetas) e `INDEX.json`, `index.html` | URL pública y claves del índice | Enlaces externos y DOI/citas rotos; cambia el sha256 del índice |
| `visor/` (`app.js`, `v2/`, `nacional/`) y `web/` | lee el registro y `datos_abiertos` por id | Rutas de datos y selector; los textos públicos usan la etiqueta, no el id |
| `datos/composicion`, `datos/distritos`, `datos/resultados` (incluye `MANIFEST*.json`) | ficheros y manifiestos por id | Manifiestos con sha256 por ruta |
| Huellas M05/N08 y checkpoints M04 (`.claude/rules/huellas.md`) | el id forma parte de la entrada del contrato; el motor lee `meta.territory_id` | Cambia la huella: invalida checkpoints; 00 «Generar desde fuente» obligatoria. Motor vedado |
| Histórico: `legacy/`, `docs/REGISTRO_DE_CAMBIOS.md`, `docs/AUDITORIAS/` | texto | No se toca (inmutable) |
| `tests/` (105 ficheros con ids; fixtures `raiz_congelada_aee8215e`) | literales | Reescribir tests y regenerar fixtures |
| Nombre visible | `name` del catálogo («Congreso Álava», «Comunidad Valenciana»…) | Solo etiqueta; seguro de cambiar en la capa visible |

## Capa visible (paso 3): propuesta de alcance
Etiqueta «AUT01 · Andalucía» / «NAC01 · Álava» tomada de la tabla maestra por id interno (lookup, alias = id actual, sin tocar claves). Ficheros afectados, a coordinar con sus dueños:
Gestor (`gestor_campana_nacional.py`, `gestor-campanas.yml` — resúmenes), dashboard (`generar_estado_operativo.py`), `visor/v2` y `visor/nacional`, `datos_abiertos` (fichas e `INDEX.json`, regenerable) y documentación/`docs/ESTADO.md`.
El workflow del Gestor y la 00 no se tocan en esta tarea.

## Paso 4 (no ejecutado): migración de ids internos
Orden de dificultad y riesgos: (a) alias en catálogo (`notacion: AUT01`), reversible, sin huella; (b) renombrar carpetas `territorios/<id>` y `datos_abiertos/<id>`: cambia huellas y enlaces; (c) claves del registro del visor (solo adición: habría que añadir entradas nuevas y dejar las antiguas como alias); (d) claves R2: copiar+verificar sha256, mantener las antiguas hasta migrar `archivo_r2.json`; (e) checkpoints M04/M05 y huellas: rehacer con 00 «Generar desde fuente» por territorio (coste de 71 ejecuciones). Recomendación: no migrar; mantener ids internos estables y usar AUT/NAC como notación de cara al exterior. Decide el propietario.
