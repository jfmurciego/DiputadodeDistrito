# Diputado de Distrito — Procedimiento de Distritación DDD

**README v3.5.0** · 11-09-2026 · Estado: **R014 validado + R015 cerrada + R016 validado**
**Anterior:** `legacy/docs/README_v3.4.0.md`
**Cambio:** promociona Run #9 como nuevo baseline territorial y registra la limpieza de ramas; no cambia lógica ni parámetros.

Sistema modular para construir, validar y auditar distritos uninominales a partir de unidades censales oficiales. El producto es un procedimiento repetible: mismo código + mismos inputs + misma configuración ⇒ mismo resultado reproducible. Aragón es la primera implantación; otros territorios deben entrar por datos y configuración, no mediante forks del motor.

## Estado territorial vigente

La referencia territorial aceptada es **GitHub Run #9 `34599224954`**, ejecutado sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`, modo iterativo, y publicado como `gh-34599224954-1`.

Resultado: 67 distritos; Huesca 11 / Teruel 7 / Zaragoza 49; 1.463 secciones; 1.364.621 habitantes; provincia PASS; disciplina municipal PASS; contigüidad PASS; suelo/techo PASS; **0 distritos fuera de ±12 %**; máximo desvío relativo **9,930 %**.

Frente a Run #8, R016 reduce el máximo desvío de **11,943 % a 9,930 %** —2,013 puntos porcentuales, un 16,9 % menos— y reduce el error cuadrático global de `0.182704485064` a `0.161271162560` —11,7 % menos— sin relajar ninguna restricción.

## R015 — pruebas y gobernanza verificable

La suite `tests/test_r015_invariantes.py` y el workflow `.github/workflows/pruebas-ddd.yml` protegen las invariantes territoriales, el determinismo y la trazabilidad hacia `legacy/`. El workflow de pruebas sigue siendo una puerta obligatoria para cualquier cambio posterior.

## R016 — refinamiento canónico post-factibilidad — VALIDADO

M05 **v7.4.0** corrige la parada prematura de v7.3.x. Run #9 demuestra el efecto: alcanza exactamente la primera solución factible de Run #8 en la iteración **9.038**, pero continúa **10.962 iteraciones** más hasta completar las 20.000 y encuentra una solución mejor.

`objective_first_feasible = [0, 0.0, 0, 0.119431695687, 0.182704485064]`

`objective_final = [0, 0.0, 0, 0.099299365905, 0.161271162560]`

Solo cambian 12 distritos respecto de Run #8 y todos están en Zaragoza. El peor distrito de Zaragoza pasa de 11,943 % a 9,140 %. Huesca y Teruel quedan sin cambios; el máximo global final es el distrito 0 de Huesca, con -9,930 %.

La cabecera del ejecutable v7.4.0 conserva el estado de publicación como candidato. No se reescribe el código ya probado únicamente para cambiar esa etiqueta: la promoción canónica se registra en este README, Estado Maestro y el expediente de Run #9.

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

La aceptación territorial exige ejecución reproducible del procedimiento y puerta de validación. Las pruebas automáticas son una puerta de regresión adicional; no sustituyen un run territorial cuando cambia la lógica funcional.

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

Los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` están retirados y no son fuentes de estado. **`main` es la única rama permanente y actualmente la única rama existente.**

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

R014, R015 y R016 están cerrados. Cualquier R017 debe partir de un objetivo territorial explícito y demostrar mejora sobre Run #9 sin perder ninguna de sus invariantes.

**Principio rector:** un resultado que solo existe en memoria, en un log o en una sesión de IA no es un producto del procedimiento.
