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
