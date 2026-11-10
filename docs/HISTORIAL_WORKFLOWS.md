# Historial de workflows retirados o desactivados

T-150 (10-11). Inventario de los workflows que ya no tienen fichero en `main` pero siguen en la lista de Actions (estado `disabled_manually`), obtenido con `gh api repos/jfmurciego/DiputadodeDistrito/actions/workflows` y cruzado con `git log --all --full-history`. Los 12 se crearon y se borraron en ramas de PR (`fix/electoral-input-19-territories`, `chatgpt/fuentes-wfs-20261017`), por eso sus runs son de evento `pull_request` o `push` en esas ramas, nunca en `main`.

El borrado de runs está en `docs/HISTORIAL_WORKFLOWS_BORRADO_RUNS.csv` (222 runs; decisión del propietario vía Planificador: 14 con evidencia verificada y 208 sin nada que conservar, con su motivo en `verificada` y `nada_que_conservar`). **No ejecutado**: es irreversible y lo hace el Operador con frase del propietario, tras revisión del Planificador. Sin runs y sin fichero, el workflow desaparece de la lista.

| workflow_id | Nombre | Fichero | Alta → baja (git) | Runs | Primera / última ejecución | Resultado | Para qué servía | Lo sustituye | Evidencia |
|---|---|---|---|---|---|---|---|---|---|
| 367997057 | Verificar registro EleccionesDB · diez elecciones | `verificar-registro-eleccionesdb.yml` | 2026-09-27 → 2026-09-27 (`398d786d`) | 96 | 2026-09-26T23:06Z / 2026-09-27T09:11Z | 94 success, 2 failure | Validaba en PR el registro de EleccionesDB de las elecciones. | Validación dentro del productor del snapshot (test_workflow_safety). | ninguna requerida (check de CI, sin salida) |
| 368014567 | Diagnóstico descubrimiento fuentes electorales | `diagnostico-descubrimiento-fuentes.yml` | 2026-09-27 → 2026-09-27 (`e50aa5f6`) | 17 | 2026-09-26T23:58Z / 2026-09-27T00:54Z | 1 failure, 16 success | Diagnóstico de descubrimiento de fuentes electorales (SIEL Andalucía). | Adaptador durable SIEL Andalucía 2026 (e50aa5f6) y 03 Preparación de Resultados Electorales. | ninguna requerida (check de CI, sin salida) |
| 368024959 | Verificar bloqueos definitivos Andalucía y Extremadura | `verificar-bloqueos-definitivos.yml` | 2026-09-27 → 2026-09-27 (`19191b4f`) | 87 | 2026-09-27T00:30Z / 2026-09-27T09:13Z | 87 success | Contrastaba en PR los estados provisional/pendiente/bloqueo de Andalucía y Extremadura. | Un único check de estados pendientes junto a la muestra SIEL (19191b4f). | ninguna requerida (check de CI, sin salida) |
| 368026774 | Verificar Cataluña 2024 · paquete y registro en copia | `verificar-registro-cataluna.yml` | 2026-09-27 → 2026-09-27 (`0b97414c`) | 4 | 2026-09-27T00:36Z / 2026-09-27T00:42Z | 4 success | Verificaba en PR el paquete y registro de Cataluña 2024 en copia. | verificar-cataluna-2024.yml (hoy en legacy/workflows/retirados_20261031) y 03/04. | ninguna requerida (check de CI, sin salida) |
| 387564637 | F10 - diagnostico variaciones callejero oficial INE | `f10-investigar-variaciones-callejero-ine.yml` | 2026-10-17 → 2026-10-17 (`4a5b1ecc`) | 7 | 2026-10-17T10:52Z / 2026-10-17T10:59Z | 7 success | F10: inspección de variaciones del callejero oficial INE (adquisición temporal). | herramientas/inspeccionar_variaciones_callejero_f10.py (uso local). | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261017/INE_CALLEJERO_TRAM_CAMBIOS_15_2025_2026.json@c5bf5ae4c5 |
| 388507652 | F10 preservacion original INE callejero 2025-2026 | `f10-preservar-ine-callejero-20261018.yml` | 2026-10-18 → 2026-10-18 (`e429b0ef`) | 1 | 2026-10-18T14:33Z / 2026-10-18T14:33Z | 1 success | F10: archivo de los ZIP originales INE del callejero 2025-2026 con huellas. | Originales versionados en git. | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261017/INE_CALLEJERO_ORIGINALES_20261018.json@5a70055182<br>docs/AUDITORIAS/F10_CROSSWALK_INE_20261020/originales/Var_Callejero_0125_0725.zip@6747f8ea1f<br>docs/AUDITORIAS/F10_CROSSWALK_INE_20261020/originales/Var_Callejero_0725_0126.zip@742e3dd2bc<br>docs/AUDITORIAS/F10_CROSSWALK_INE_20261020/originales/Var_Callejero_0126_0726.zip@b9dace23be |
| 388513437 | F10 Andalucia source geometries 2025 2026 | `f10-andalucia-crossyear-20261018.yml` | 2026-10-18 → 2026-10-18 (`c3d12dcb`) | 2 | 2026-10-18T14:41Z / 2026-10-18T15:01Z | 1 failure, 1 success | F10: auditoría geométrica interanual de secciones INE Andalucía 2025-2026. | herramientas/auditar_ine_andalucia_secciones_2025_2026.py (uso local). | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_MATRIZ_34_RESULTADO_20261018.json@53d620b667<br>docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_CANDIDATOS_GEOMETRICOS_34_20261019.csv@cdf2d32df2 |
| 389268467 | F10 evidencia BOP Huelva electoral 2026 | `f10-huelva-boletin-20261019.yml` | 2026-10-19 → 2026-10-19 (`9e803a24`) | 2 | 2026-10-19T10:11Z / 2026-10-19T10:12Z | 1 failure, 1 success | F10: evidencia del BOP de Huelva (mesas electorales 2026). | Manifiestos durables en git. | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261019/CORTEGANA_BOP_OFICIAL_MESAS_2026.json@aac44da6f4 |
| 389275351 | F10 Andalucia riesgo electoral interanual | `f10-andalucia-riesgo-votos-20261019.yml` | 2026-10-19 → 2026-10-19 (`da22041b`) | 1 | 2026-10-19T10:19Z / 2026-10-19T10:19Z | 1 success | F10: cuantificación del riesgo electoral interanual SIEL Andalucía. | herramientas/cuantificar_riesgo_interanual_siel_andalucia.py (uso local). | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261019/ANDALUCIA_SIEL_RIESGO_CONSOLIDADO_20261019.json@05a049cefb |
| 389301363 | F10 — documento INE Cortegana 2026 | `f10-cortegana-ine-bop-2026.yml` | 2026-10-19 → 2026-10-19 (`74923f2b`) | 2 | 2026-10-19T10:52Z / 2026-10-19T10:54Z | 1 failure, 1 success | F10: verificación del documento INE/BOP de Cortegana 2026. | herramientas/verificar_bop_huelva_cortegana_2026.py + test_f10_andalucia_cortegana_bop_oce.py. | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_CORTEGANA_BOP_OCE_2026_EVIDENCIA.json@e4c6d32e24 |
| 389307684 | F10 — conciliar originales INE OCE y SIEL de Cortegana | `f10-conciliar-bop-siel-andalucia-2026.yml` | 2026-10-19 → 2026-10-19 (`74923f2b`) | 1 | 2026-10-19T11:00Z / 2026-10-19T11:00Z | 1 success | F10: conciliación de originales INE/OCE y SIEL de Cortegana. | herramientas/consolidar_f10_andalucia_bop_siel_2026.py. | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_CORTEGANA_BOP_OCE_2026_EVIDENCIA.json@e4c6d32e24<br>docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_INE_6045_SIEL_6044_DIFERENCIA_NOMINAL.json@4f227c407a |
| 389335534 | F10 estudio Jan-Jul 2025 y linaje 86 secciones | `f10-andalucia-tram-periodos-20261019.yml` | 2026-10-19 → 2026-10-19 (`b9626c7d`) | 2 | 2026-10-19T11:34Z / 2026-10-19T11:37Z | 1 failure, 1 success | F10: estudio de tres periodos del callejero y linaje de 86 secciones. | Manifiesto durable en git. | git (SI): docs/AUDITORIAS/CIERRE_FUENTES_20261019/ANDALUCIA_INE_TRAM_3_PERIODOS_86_CUSEC.json@e298902757 |

## Notas

- Columna `verificada` (sí/no + ruta) por run; ninguno de los 222 está en `orchestracion/archivo_r2.json`. 
- Evidencia «git»: ruta@sha corto del blob en `origin/main`; todas existen. La asignación workflow→evidencia se hizo por nombre, fecha y herramienta que invocaba el workflow; los artefactos de Actions de estos runs ya han caducado. R2 contrastado solo con `orchestracion/archivo_r2.json` (sin coincidencias), sin acceso directo al almacén.
- Los cuatro de septiembre (`verificar-*`, `diagnostico-descubrimiento-fuentes`) eran checks de PR sin salida conservable; borrar sus runs no pierde evidencia.
- Workflows retirados con fichero aún en `legacy/` o ya sustituidos pero con runs en `main` (p. ej. `legacy/workflows/retirados_20261031`) no se tocan aquí: los gestiona T-149. Si se retiran más, se añaden filas y el CSV se regenera con `gh api repos/<r>/actions/workflows/<id>/runs`.

## Borrado (para el Operador; sin workflow)

CSV fijado por sha256 `765d4ac2261d6358a7443a17b14ce9fd48d2aee03fdff0bdd7a8fc5f9ec90ab8`. Simulación primero (no borra, no usa la red):

```bash
R=jfmurciego/DiputadodeDistrito; F=docs/HISTORIAL_WORKFLOWS_BORRADO_RUNS.csv
echo "765d4ac2261d6358a7443a17b14ce9fd48d2aee03fdff0bdd7a8fc5f9ec90ab8  $F" | sha256sum -c - || exit 1
python3 -I -c "import csv,sys;[print(r['run_id']) for r in csv.DictReader(open(sys.argv[1]))]" $F > /tmp/runs.txt; wc -l /tmp/runs.txt   # 222
while read id; do echo "SIMULACIÓN DELETE repos/$R/actions/runs/$id"; done < /tmp/runs.txt | head -3
```

Ejecución (solo con la frase del propietario): mismo bloque y luego `while read id; do gh api -X DELETE repos/$R/actions/runs/$id || echo "FALLO $id"; done < /tmp/runs.txt`. Irreversible. Después, `gh api repos/$R/actions/workflows` no debe listar los 12.

## Retirados por T-149 (PR #603, sin fusionar al redactar esto)

Aún con fichero en `main` hasta que se fusione #603; después quedarán sin fichero y con runs. **No entran en el CSV de los 222** (sha256 intacto): sus 844 runs están en `docs/HISTORIAL_WORKFLOWS_BORRADO_RUNS_T149.csv`, sha256 `68cf4fdc01696eedb42c2f48557e11865cfb4cd6eff38441b95b3372e50b4cb3`, que necesita visto bueno aparte del propietario. Recuentos de runs a 10-11 (REST):

| workflow_id | Fichero | Runs | Fechas | Motivo de retirada (T-149) |
|---|---|---|---|---|
| 356619278 | `notificar-finalizacion-orquestacion.yml` | 89 (20 push, 69 workflow_run) | 2026-09-12 → 2026-09-21 | disparador inexistente |
| 359048691 | `_reutilizable-operacion-territorial.yml` | 27 | 2026-09-21 | cadena sin llamador en main |
| 356992156 | `producir-territorio-por-contrato.yml` | 14 | 2026-09-21 | cadena sin llamador en main |
| 356442862 | `_reutilizable-auditoria-topologica.yml` | 30 | 2026-09-21 | cadena sin llamador en main |
| 359605904 | `orquestacion-durable.yml` | 18 | 2026-09-21 | cadena sin llamador en main |
| 359527963 | `orquestacion-control.yml` | 666 (352 pull_request, 314 push) | 2026-09-21 → 2026-11-10 | cadena sin llamador en main |

Renombrados (solo `name:`, siguen activos y sin retirar): «- Activación por Elección», «- Archivar artefactos en R2», «- Extraer composición M06», «- Activación de Legislatura Vigente» → «Auxiliar — <nombre>»; «_Interno — Generación Territorial» → «Interno · Generación territorial»; «_Interno — Publicador del Sitio» → «Interno · Publicador del sitio». Detalle: `docs/ESTUDIOS/T149_LISTA_ACTIONS/INVENTARIO.md` (en #603).

Versiones anteriores de los ficheros retirados: en git (historial de `main`) y, si T-149 las copia, en `legacy/workflows/`.

### Verificación de los 844 runs de T-149

Por run (REST `actions/runs/<id>/artifacts`) y contra `orchestracion/archivo_r2.json` (ninguno está en R2):
- **197 runs sin artefactos**: nada que verificar ni conservar (`nada_que_conservar` = sí).
- **647 runs de `orquestacion-control`** con 3 artefactos cada uno (`g10-validar-config-*`, `g10-g10-selftest`, `g10-resumen-lote-*`; muestra de 12 runs idéntica, 0,5-7 KB, no caducados), sin archivar en git ni R2: marcados «no · sin decidir». El propietario debe decidir si se pierden.
- Simulación y ejecución: mismo bloque de «Borrado» cambiando fichero y sha256.

### Decisión propuesta para los 844 (T-167, 10-11; sin ejecutar)

Listas separadas: **222 aprobadas** (`HISTORIAL_WORKFLOWS_BORRADO_RUNS.csv`, sha256 `765d4ac2…90ab8`, intacto) y **844** de T-149 con decisión (`HISTORIAL_WORKFLOWS_BORRADO_RUNS_T149_DECISION.csv`, sha256 `d1adffffdcc7400ffcfa8c68268500cc3cf20478d534bfdbf88aa2dd06f1eff5`; el original de 844, sha256 `68cf4fdc…cb3`, queda intacto). Columnas nuevas: `verificada`, `decision_propuesta`, `motivo_decision`.

- **197 sin artefactos**: borrar (solo log de CI).
- **647 de `orquestacion-control`**: 1941 artefactos (3 por run; 4,4 MB en total), todos vivos (caducan 2026-12-15 → 2027-02-08). Son `g10-g10-selftest` (log de las pruebas g10, ~0,7 KB), `g10-validar-config-aragon` (log de validación de la configuración de Aragón, 3-7 KB) y `g10-resumen-lote-<run>` (JSON de resumen, 488 B); un run de 16-09 usa el prefijo `orquestacion-`. No contienen producto territorial ni electoral. No están en `archivo_r2.json` (0 de 624 entradas) ni en git. Se reproducen con el workflow y el código de su SHA (git: historial y `legacy/workflows/`). El contenido no se pudo leer desde la sesión cloud (el host de descarga de artefactos está bloqueado): la descripción sale del workflow y de los tamaños.
- **Propuesta: borrar los 647**, sin archivar el contenido. Mínimo que se conserva: la ficha de los 1941 artefactos (run, id, nombre, bytes, huella, fechas, SHA) en `HISTORIAL_WORKFLOWS_ARTEFACTOS_G10_T167.csv`, sha256 `7dfa5cc90a9534a6d34f8141c0fe1bc05a1a46cdd36c0dcffb89a3e144891b04`. Si el propietario prefiere conservar el contenido, bastaría un ZIP de ~4,4 MB al archivo ARC; no se propone.
- Los artefactos desaparecen con el run al borrarlo.

Simulación para el Operador (no borra; solo comprobación local; el borrado real exige la frase del propietario):

```bash
R=jfmurciego/DiputadodeDistrito; F=docs/HISTORIAL_WORKFLOWS_BORRADO_RUNS_T149_DECISION.csv
echo "d1adffffdcc7400ffcfa8c68268500cc3cf20478d534bfdbf88aa2dd06f1eff5  $F" | sha256sum -c - || exit 1
python3 -I -c "import csv,sys;[print(r['run_id']) for r in csv.DictReader(open(sys.argv[1])) if r['decision_propuesta']=='borrar']" $F > /tmp/runs149.txt; wc -l /tmp/runs149.txt   # 844
while read id; do echo "SIMULACIÓN DELETE repos/$R/actions/runs/$id"; done < /tmp/runs149.txt | head -3
```

Ejecución (solo con la frase del propietario, irreversible): mismo bloque y `while read id; do gh api -X DELETE repos/$R/actions/runs/$id || echo "FALLO $id"; done < /tmp/runs149.txt`. `orquestacion-control` tenía 666 runs (647 con artefactos + 19 sin ellos); los runs posteriores a la lista quedan fuera: repetir el inventario antes de ejecutar.
