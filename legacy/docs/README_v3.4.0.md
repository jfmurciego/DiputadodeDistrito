# Diputado de Distrito — Procedimiento de Distritación DDD

**README v3.4.0** · 11-09-2026 · Estado: **R014 territorial validado + R015 cerrada + R016 candidato**
**Anterior:** `legacy/docs/README_v3.3.1.md`
**Cambio:** abre R016 con M05 v7.4.0 candidato para completar el objetivo canónico después de la primera solución dentro de ±12 %.

Sistema modular para construir, validar y auditar distritos uninominales a partir de unidades censales oficiales. El producto es un procedimiento repetible: mismo código + mismos inputs + misma configuración ⇒ mismo resultado reproducible. Aragón es la primera implantación; otros territorios deben entrar por datos y configuración, no mediante forks del motor.

## Estado territorial vigente

La referencia territorial aceptada sigue siendo **GitHub Run #8 `34592470470`**, ejecutado sobre `d57dc9cd77af4fa09780794401381d9727d1c71b` y publicado como `gh-34592470470-1`.

Resultado: 67 distritos; Huesca 11 / Teruel 7 / Zaragoza 49; 1.463 secciones; 1.364.621 habitantes; provincia PASS; disciplina municipal PASS; contigüidad PASS; suelo/techo PASS; **0 distritos fuera de ±12 %**; máximo desvío relativo **11,943 %**.

R015 no modifica ese algoritmo ni promociona un nuevo mapa. Las versiones activas pasan por PATCH de gobernanza: M04 **v7.3.1**, M05 **v7.3.1**, configuración Aragón **v7.5.1**, validación **v1.3.1**, `procedimiento.sh` **v2.1.1** y workflow principal **v2.7.2**. En todos esos casos la lógica funcional se hereda sin cambios de la versión validada por Run #8; el cambio normaliza estado, versión y predecesor `legacy/`.

## R015 — pruebas y gobernanza verificable

La suite `tests/test_r015_invariantes.py` y el workflow `.github/workflows/pruebas-ddd.yml` convierten en controles automáticos las invariantes principales de R012/R014. GitHub Run `34594827070` terminó SUCCESS después de retirar el migrador temporal: pasaron la auditoría de cabeceras/`legacy`, la regresión sobre Run #8 y la prueba de determinismo de M05. Ejecuciones posteriores de la misma puerta, incluida `34595195694`, también terminaron SUCCESS antes de este cierre documental.

La regresión comprueba, entre otros puntos: universo exacto de secciones y población; K=67; reparto provincial 11/7/49; provincia única; contigüidad por M03; suelo/techo; disciplina municipal; M04 con su outlier histórico; M05 con `fuera_12=0`; máximo desvío R014; atomicidad de `ddd_unit_id`; y dos ejecuciones sintéticas de M05 con misma semilla y salida idéntica.

La gobernanza automática comprueba además que los componentes funcionales auditados y los documentos canónicos versionados que declaran un predecesor apunten a un fichero que exista realmente en `legacy/`.

## R016 — refinamiento canónico post-factibilidad — CANDIDATO

M05 **v7.4.0** corrige una incoherencia de v7.3.x: el objetivo canónico ordena minimizar, tras `fuera_12`, el máximo desvío y el error cuadrático, pero el recocido se detenía al primer `fuera_12=0`. R016 conserva todos los límites y restricciones duras y continúa la búsqueda hasta agotar el presupuesto configurado, manteniendo siempre la mejor solución canónica encontrada.

El candidato registra la primera iteración factible y el objetivo de ese instante para compararlo con el resultado final. **No está promocionado**: Run #8 sigue siendo la referencia territorial hasta que un nuevo run de GitHub confirme todos los PASS y una mejora real del objetivo.

## Arquitectura

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final.

M01–M03 son preparación territorial cacheable. M04–M06 forman el núcleo territorial. M07–M08 son capa electoral posterior. Los resultados electorales nunca condicionan la geometría.

## Reglas territoriales Aragón

1. 67 distritos exactos.
2. Provincia infranqueable: Huesca 11, Teruel 7, Zaragoza 49.
3. Contigüidad estricta sobre M03.
4. Conservación exacta de secciones y población.
5. Suelo duro = 0,80×target; techo = 1,75×target.
6. Objetivo fino = ±12 %.
7. Municipio que cabe bajo techo: indivisible.
8. Municipio sobredimensionado: partición interna conexa; distritos completos exclusivamente municipales y solo residual mezclable.
9. CUSEC único/no nulo y determinismo.
10. La elección analizada nunca condiciona el mapa.

## Outputs y aceptación

Cada ejecución publica productos auditables M01–M08 en `resultados/ejecuciones/<RUN_ID>/`; las geometrías pesadas quedan en artefactos GitHub Actions y sus `PRODUCTOS.json` registran ruta, tamaño y SHA-256.

La aceptación territorial exige ejecución reproducible del procedimiento y puerta de validación. Las pruebas R015 constituyen además una puerta de regresión de ingeniería; no sustituyen un run territorial cuando cambie lógica funcional.

## Trazabilidad y gobernanza

- Estado canónico: este README + `docs/ESTADO_MAESTRO_PROYECTO.md`.
- Continuidad: `docs/CONTINUIDAD_NUEVO_CHAT.md`.
- Progreso: `docs/BITACORA.md`.
- Cambios: `docs/REGISTRO_DE_CAMBIOS.md`.
- Política: `docs/POLITICA_DE_VERSIONES.md`.
- Rondas: `docs/RONDAS/`.
- Ejecuciones: `docs/EJECUCIONES/`.
- Versiones retiradas: `legacy/`.
- Deuda histórica no recuperada: `docs/DEUDA_HISTORICA_LEGACY.md`.

Los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` están retirados y no son fuentes de estado. `main` es la rama canónica; `infra/fuentes-reproducibles*` son ramas históricas/no activas.

## Orden de lectura para continuar

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/CONTINUIDAD_NUEVO_CHAT.md`.
4. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`.
5. `docs/MODULOS/README.md` y contrato del módulo en curso.
6. `docs/BITACORA.md`.
7. Última ronda y última ejecución.
8. Configuración, workflows, tests y código afectado.

## Próximo frente

R014 y R015 quedan cerrados. R016 está abierto como candidato funcional de M05. Debe superar la puerta R015 y un nuevo run territorial antes de cualquier promoción; Run #8 continúa como baseline mientras tanto.

**Principio rector:** un resultado que solo existe en memoria, en un log o en una sesión de IA no es un producto del procedimiento.
