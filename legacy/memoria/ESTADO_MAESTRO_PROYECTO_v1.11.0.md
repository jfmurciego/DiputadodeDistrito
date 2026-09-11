# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.11.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.10.0.md`

## 1. Estado arbitral

La referencia territorial vigente es **GitHub Run #8 `34592470470`**, ejecutado sobre `d57dc9cd77af4fa09780794401381d9727d1c71b`, modo iterativo. Terminó SUCCESS y publicó `gh-34592470470-1`.

R014 está validado: 67 distritos; 1.463 secciones; 1.364.621 habitantes; Huesca 11 / Teruel 7 / Zaragoza 49; 0 cruces provinciales; 0 desconectados; 0 infracciones municipales; 0 bajo suelo; 0 sobre techo; **0 fuera de ±12 %**; máximo desvío relativo **0,119431695687**.

R015 está cerrado como ronda de ingeniería. **Pruebas DDD — R015, Run `34594827070`, SUCCESS** sobre el estado posterior a retirar la migración temporal: auditoría de cabeceras/legacy PASS y regresión territorial + determinismo PASS.

## 2. Implementación vigente

- Configuración Aragón: `configuracion/aragon_2025.yaml` **v7.5.1**.
- Workflow territorial: `.github/workflows/procedimiento-ddd.yml` **v2.7.2**.
- Workflow de pruebas: `.github/workflows/pruebas-ddd.yml` **v1.0.0**.
- Procedimiento: `procedimiento.sh` **v2.1.1**.
- M04: **v7.3.1**.
- M05: **v7.3.1**.
- Validación: `herramientas/validar_ejecucion.py` **v1.3.1**.

Los incrementos PATCH de R015 normalizan metadatos y predecesores `legacy/`; **no modifican la lógica funcional heredada de R014**. Por ello Run #8 sigue siendo la referencia territorial aceptada.

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

## 4. Regresión automática R015

`tests/test_r015_invariantes.py` protege el baseline Run #8 y comprueba cardinalidad, conservación, provincia, contigüidad, suelo/techo, disciplina municipal, objetivo ±12 %, máximo desvío R014, consistencia M04→M05 y validación publicada. Un fixture sintético ejecuta M05 dos veces con la misma semilla y exige informe/asignación idénticos y atomicidad de `ddd_unit_id`.

La CI verifica también que los componentes activos auditados tengan versión, nombre, fecha, estado, cambios, motivo y `ANTERIOR`, y que ese predecesor exista físicamente en `legacy/`.

## 5. Evolución relevante

- Run #5 `34584775443`: outputs auditables, pero territorialmente inválido bajo R012.
- Run #6 `34587157452`: FAIL por distrito desconectado originado en M04.
- Run #7 `34588834266`: estructura R012 PASS; M05 v7.2.0 quedó en `fuera_12=1`.
- Run #8 `34592470470`: R014 PASS completo, `fuera_12=0`.
- R015: primera puerta automática de regresión y normalización verificable de `legacy/`.

## 6. Gobernanza

Política vigente: `docs/POLITICA_DE_VERSIONES.md` **v1.2.0**. Los antiguos `docs/MEMORIA*` están retirados. La deuda histórica pre-R015 no materializada se mantiene explícita en `docs/DEUDA_HISTORICA_LEGACY.md`; no se inventan antecedentes.

`legacy/` conserva literalmente los predecesores inmediatos de las versiones activas normalizadas en R015. Defectos cosméticos heredados dentro de una copia histórica no deben corregirse retroactivamente: la copia es evidencia.

`main` es canónica. Las ramas `infra/fuentes-reproducibles*` siguen históricas/no activas.

## 7. Productos

Cada módulo M01–M08 expone su producto auditable. Outputs ligeros: `resultados/ejecuciones/<RUN_ID>/Mxx/`. Geometrías pesadas: artefactos Actions identificados en `PRODUCTOS.json`.

## 8. Regla para continuar

No modificar M04/M05 ni sus criterios sin abrir una nueva ronda. Todo cambio funcional posterior debe conservar los PASS de Run #8, superar la suite R015 y obtener un nuevo run territorial reproducible antes de promoción.
