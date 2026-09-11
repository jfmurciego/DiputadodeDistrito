# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.10.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.9.0.md`

## 1. Estado arbitral

La referencia vigente es **GitHub Run #8 `34592470470`**, ejecutado sobre `d57dc9cd77af4fa09780794401381d9727d1c71b`, modo iterativo. Terminó **SUCCESS** y publicó `gh-34592470470-1`.

R014 queda **validado**. El resultado final conserva 67 distritos, 1.463 secciones y 1.364.621 habitantes; reparto provincial Huesca 11 / Teruel 7 / Zaragoza 49; cero cruces provinciales, cero distritos desconectados, cero infracciones municipales, cero distritos bajo suelo o sobre techo y **cero distritos fuera de ±12 %**. Máximo desvío relativo: **0,119431695687**.

## 2. Implementación vigente

- Configuración Aragón: `configuracion/aragon_2025.yaml` **v7.5.0**.
- Workflow: `.github/workflows/procedimiento-ddd.yml` **v2.7.1**.
- M04: **v7.3.0**, partición y ensamblaje conexos por provincia.
- M05: **v7.3.0**, greedy determinista + escape reproducible de mínimos locales.
- Validación: `herramientas/validar_ejecucion.py` **v1.3.0**.

M01–M03 permanecen cacheables y Run #8 los reutilizó correctamente.

## 3. Reglas duras Aragón

1. 67 distritos exactos.
2. Provincia infranqueable: 11/7/49.
3. Contigüidad estricta por M03.
4. Conservación exacta de población y secciones.
5. Suelo 0,80×target; techo 1,75×target.
6. Objetivo fino ±12 %.
7. Municipio que cabe bajo techo: indivisible.
8. Municipio sobredimensionado: partición interna conexa; distritos completos exclusivamente municipales y solo residual mezclable.
9. Resultados electorales nunca condicionan geometría.
10. Determinismo, CUSEC único/no nulo y configuración canónica.

## 4. Evolución relevante

- Run #5 `34584775443`: outputs auditables, pero territorialmente inválido bajo R012.
- Run #6 `34587157452`: FAIL por distrito 52 desconectado desde M04.
- Run #7 `34588834266`: primera estructura R012 PASS; M05 v7.2.0 quedó atrapado con `fuera_12=1` y 0 movimientos.
- Auditoría R014: demostró mínimo local, no ausencia de candidatos.
- Run #8 `34592470470`: M05 v7.3.0 alcanza `hard=0`, `fuera_12=0`, `max_rel_dev=0.119431695687`; validación global PASS.

M05 reporta 1.030 movimientos exploratorios aceptados por recocido, 75 unidades finalmente cambiadas y 9.038 iteraciones ejecutadas; la salida seleccionada es la mejor solución encontrada según el objetivo canónico, no el último estado explorado.

## 5. Mantenimiento workflow

El defecto de Run #7 `PRODUCTOS.json: command not found` fue corregido en workflow v2.7.1. Run #8 verifica la corrección: publicación M01–M08 y commit automático de resultados completados sin ese error.

## 6. Gobernanza

Los antiguos `docs/MEMORIA*` están retirados. La política vigente es `docs/POLITICA_DE_VERSIONES.md` v1.1.0.

Existe deuda histórica de versiones predisciplina que no fueron materializadas en `legacy/`; está catalogada en `docs/AUDITORIAS/DEUDA_HISTORICA_LEGACY_2026-09-11.md`. Desde la política vigente no se admite sustituir un fichero funcional sin copia previa ni declarar rutas legacy inexistentes.

`main` es canónica. Las ramas `infra/fuentes-reproducibles*` son históricas/no activas. La suite unitaria completa sigue siendo deuda de ingeniería; la evidencia arbitral actual es workflow reproducible + validaciones integradas.

## 7. Productos

Cada módulo M01–M08 expone su producto auditable. Outputs ligeros completos: `resultados/ejecuciones/<RUN_ID>/Mxx/`. Geometrías pesadas: artefactos Actions, identificadas en `PRODUCTOS.json`.

## 8. Próximo frente

R014 está cerrado. No tocar M04/M05 para “mejorar” el 11,943 % sin una nueva ronda explícita y sin mantener todos los PASS actuales. El siguiente frente seguro es deuda de ingeniería: pruebas unitarias, normalización de cabeceras auxiliares y saneamiento de referencias históricas verificables.
