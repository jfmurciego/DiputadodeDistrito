# Diputado de Distrito — Procedimiento de Distritación DDD

**README v3.2.0** · 11-09-2026 · Estado: **R014 validado en GitHub**

Sistema modular para construir, validar y auditar distritos uninominales a partir de unidades censales oficiales. El producto es un procedimiento repetible: mismo código + mismos inputs + misma configuración ⇒ mismo resultado reproducible. Aragón es la primera implantación; otros territorios deben entrar por datos y configuración, no mediante forks del motor.

## Estado vigente

La referencia aceptada es **GitHub Run #8 `34592470470`**, ejecutado sobre commit `d57dc9cd77af4fa09780794401381d9727d1c71b` y publicado como `gh-34592470470-1`.

Resultado territorial:
- 67 distritos exactos;
- Huesca 11 / Teruel 7 / Zaragoza 49;
- 1.463 secciones y 1.364.621 habitantes conservados;
- provincia PASS;
- disciplina municipal PASS;
- contigüidad PASS;
- suelo/techo PASS;
- **0 distritos fuera de ±12 %**;
- máximo desvío relativo final: **11,943 %**.

M04 v7.3.0 sigue construyendo la solución inicial. **M05 v7.3.0 — Escape determinista de mínimos locales** resuelve el bloqueo de Run #7 mediante greedy determinista + recocido reproducible dentro del espacio duro válido. La configuración vigente es `configuracion/aragon_2025.yaml` **v7.5.0**. La validación final sigue en `herramientas/validar_ejecucion.py` v1.3.0.

El workflow `.github/workflows/procedimiento-ddd.yml` **v2.7.1** está también verificado por Run #8: el defecto de heredoc `PRODUCTOS.json: command not found` de Run #7 no reaparece.

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

La aceptación arbitral exige ejecución reproducible en GitHub Actions y puerta de validación. Una ejecución local o de IA solo es diagnóstico.

## Trazabilidad y gobernanza

- Estado canónico: este README + `docs/ESTADO_MAESTRO_PROYECTO.md`.
- Continuidad: `docs/CONTINUIDAD_NUEVO_CHAT.md`.
- Progreso: `docs/BITACORA.md`.
- Cambios: `docs/REGISTRO_DE_CAMBIOS.md`.
- Política de versiones: `docs/POLITICA_DE_VERSIONES.md`.
- Rondas: `docs/RONDAS/`.
- Ejecuciones: `docs/EJECUCIONES/`.
- Versiones retiradas: `legacy/`.

Los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md` están retirados y **no** son fuentes de estado.

Existen huecos históricos de `legacy/` anteriores a la disciplina actual; están catalogados en `docs/AUDITORIAS/DEUDA_HISTORICA_LEGACY_2026-09-11.md`. No se considera lícito inventar rutas de versiones no recuperadas.

Las ramas `infra/fuentes-reproducibles*` son históricas y no canónicas; `main` es la rama activa mientras no se reactive expresamente otra.

## Orden de lectura para continuar

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/CONTINUIDAD_NUEVO_CHAT.md`.
4. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`.
5. `docs/MODULOS/README.md` y contrato del módulo en curso.
6. `docs/BITACORA.md`.
7. Última ronda y última ejecución.
8. Configuración, workflow y código afectado.

## Próximo frente

R014 queda cerrado funcionalmente. El siguiente trabajo no debe relajar R012 ni el ±12 %. Antes de nuevas mejoras algorítmicas se abordará la deuda de ingeniería explícita: cobertura de pruebas unitarias, normalización de cabeceras auxiliares y saneamiento documentado de referencias históricas `legacy`.

**Principio rector:** un resultado que solo existe en memoria, en un log o en una sesión de IA no es un producto del procedimiento.
