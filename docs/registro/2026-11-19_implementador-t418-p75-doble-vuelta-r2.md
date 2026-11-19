## 2026-11-19 — T-418 — P75 «Doble vuelta desde R2» en P70 Archivo (V4 sin regenerar)

Causa: D-178/D-179, prioridad V4: calcular dv_base, dv_A y dv_B de los territorios publicados desde lo que ya hay en R2. Diseño: #923.
Cambio: `p70-archivo.yml` 1.1.0 (copia 1.0.0 en `legacy/` y congelada en `tests/fixtures/t418_workflows/`): acción nueva «P75 Doble vuelta desde R2» (sin entradas
nuevas: `territorios` vacío = los `nac`, `eleccion` vacía = 2023-07), job `doble_vuelta_r2` con `contents: read`, grupo `archivar-artefactos-r2` e informe en el resumen y como
artefacto. `herramientas/p75_doble_vuelta_r2.py` (nuevo): por territorio baja `ddd-minimo-<run>-M08` (herramientas/restaurar_estado_r2.py, sha256 contra `archivo_r2.json`),
informa de si trae `*_m07_resultados_partido.csv` (sin él, no se calcula), mide la cobertura del alias (>5 % sin casar = `COBERTURA_BAJA`, no se calcula), ejecuta
`doble_vuelta.py --alias --detalle` y sube `ddd-doble-vuelta-<run>.zip` (determinista) a la carpeta del paquete de entrada y `doble_vuelta/<AAAA-MM>/INFORME.json`. Sale 1 si algún
territorio no queda OK (el informe se sube igualmente). Tests: `test_t418_p75.py` (R2 simulado, valores a mano, workflow de solo lectura, demás acciones intactas) y la lista de
opciones de `test_t368_p70_equivalencia.py`. Decisiones de #923 con la recomendación (solo R2, `district_id` interno, detalle de #907, regenerar solo los que no traigan el CSV).
Límite: la elección no se lee del paquete (no hay copia del YAML en él): la fija la entrada y la cobertura del alias avisa de un desajuste. No lanza ni publica. Toca un workflow compartido. `no-automerge`.

Revisión de #923 aplicada aquí: (1) cada ejecución sube objetos nuevos (`…/ddd-doble-vuelta-<run>-p75-<run_p75>.zip` e `INFORME.json` en `doble_vuelta/<AAAA-MM>/<run_p75>/`, con
`GITHUB_RUN_ID`): nada se sobrescribe ni se borra; (2) el run vigente sale de `resultados_ligeros.vigente_por_eleccion` (ámbito NAC por el resolutor, no por prefijo) con la fecha de la
elección: un run mayor de otra elección se ignora; (3) un `aut` o un id desconocido en `territorios` se rechaza (`P75_FUERA_DE_ALCANCE`); la carpeta y el run de R2 son los del archivista
(legacy, `congreso_*`): se encuentran por run en `archivo_r2.json`; un M08 vigente que no está en R2 queda `SIN_PAQUETE_EN_R2` en el informe; (4) la descripción de `territorios` menciona P75.
Comprobado contra el repositorio real: 52 `nac` con M08 vigente de 2023-07 y los 52 con `ddd-minimo-<run>-M08` en `archivo_r2.json`.

Segunda revisión de #925: `subir_nuevo` comprueba con `aws s3api head-object` (`r2_existe`: 404 = no existe; otro fallo se propaga) ANTES de subir y falla (`P75_CLAVE_YA_EXISTE`; estado
`CLAVE_YA_EXISTE`) si la clave ya está: nunca sobrescribe ni borra (test con control negativo); se comprueba que la carpeta de R2 del paquete sea la del territorio pedido
(`territorio_ids.mismo_territorio`, `CARPETA_NO_ES_DEL_TERRITORIO`; los 52 reales cumplen); las descripciones de `territorios` y `eleccion` mencionan P75 y «vacío = todos los nac».
