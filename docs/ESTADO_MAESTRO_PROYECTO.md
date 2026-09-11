# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.13.0
**Fecha de corte:** 2026-09-11
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.12.0.md`

## 1. Estado arbitral

La referencia territorial vigente es **GitHub Run #9 `34599224954`**, ejecutado sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`, modo iterativo, y publicado como `gh-34599224954-1`.

R016 queda validado y promocionado: 67 distritos; 1.463 secciones; 1.364.621 habitantes; Huesca 11 / Teruel 7 / Zaragoza 49; 0 cruces provinciales; 0 desconectados; 0 infracciones municipales; 0 bajo suelo; 0 sobre techo; **0 fuera de ±12 %**; máximo desvío relativo **0,099299365905**.

Frente a Run #8, el máximo desvío baja de `0.119431695687` a `0.099299365905` y el error cuadrático global de `0.182704485064` a `0.161271162560`. La mejora se obtiene sin cambiar restricciones, semilla ni configuración.

## 2. Implementación vigente

- Configuración Aragón: `configuracion/aragon_2025.yaml` **v7.5.1**.
- Workflow territorial: `.github/workflows/procedimiento-ddd.yml` **v2.7.2**.
- Workflow de pruebas: `.github/workflows/pruebas-ddd.yml` **v1.0.0**.
- Procedimiento: `procedimiento.sh` **v2.1.1**.
- M04: **v7.3.1**.
- M05: **v7.4.0**, lógica territorial validada por Run #9.
- Validación: `herramientas/validar_ejecucion.py` **v1.3.1**.

La cabecera de M05 v7.4.0 conserva el estado con el que fue publicada como candidata. No se modifica el ejecutable después de la validación solo para cambiar esa etiqueta; el estado canónico de promoción se mantiene en documentación y expediente de ejecución.

## 3. Resultado R016

Run #9 reproduce exactamente la primera factibilidad de Run #8 en la iteración **9.038**:

`objective_first_feasible = [0, 0.0, 0, 0.119431695687, 0.182704485064]`

Después continúa **10.962 iteraciones** más, hasta completar 20.000:

`objective_final = [0, 0.0, 0, 0.099299365905, 0.161271162560]`

Solo cambian 12 distritos frente a Run #8, todos en Zaragoza. El peor desvío provincial queda en:
- Huesca: distrito 0, -9,930 %;
- Teruel: distrito 11, -9,822 %;
- Zaragoza: distrito 63, +9,140 %.

Esto significa que R016 reduce el cuello de botella de Zaragoza por debajo de los ya existentes en Huesca y Teruel, sin modificar esas provincias.

## 4. Reglas duras Aragón

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

## 5. Regresión automática

`tests/test_r015_invariantes.py` protege las invariantes históricas R012/R014 y el determinismo. R016 añade pruebas específicas de refinamiento post-factibilidad y una regresión del nuevo baseline Run #9.

La CI verifica además que los componentes activos auditados tengan metadatos completos y que sus predecesores declarados existan físicamente en `legacy/`.

## 6. Evolución relevante

- Run #5 `34584775443`: outputs auditables, territorialmente inválido bajo R012.
- Run #6 `34587157452`: FAIL por distrito desconectado originado en M04.
- Run #7 `34588834266`: estructura R012 PASS; M05 v7.2.0 quedó en `fuera_12=1`.
- Run #8 `34592470470`: R014 PASS, `fuera_12=0`, máximo desvío 11,943 %.
- R015: primera puerta automática de regresión y normalización verificable de `legacy/`.
- Run #9 `34599224954`: R016 PASS, máximo desvío 9,930 %, nuevo baseline.

## 7. Gobernanza

Política vigente: `docs/POLITICA_DE_VERSIONES.md`. Los antiguos `docs/MEMORIA*` están retirados. La deuda histórica no materializada se mantiene explícita en `docs/DEUDA_HISTORICA_LEGACY.md`; no se inventan antecedentes.

`legacy/` conserva literalmente los predecesores inmediatos. Defectos cosméticos heredados dentro de una copia histórica no deben corregirse retroactivamente: la copia es evidencia.

**`main` es la única rama permanente y actualmente la única rama existente.** Si una operación técnica obliga a crear una rama temporal, debe eliminarse al terminar su integración.

## 8. Productos

Cada módulo M01–M08 expone su producto auditable. Outputs ligeros: `resultados/ejecuciones/<RUN_ID>/Mxx/`. Geometrías pesadas: artefactos Actions identificados en `PRODUCTOS.json`.

## 9. Regla para continuar

Run #9 es el baseline protegido. Toda nueva ronda funcional debe mantener sus PASS y demostrar una mejora explícita y medible antes de promoción.
