# Continuidad del proyecto en un nuevo chat

**Versión:** 1.0.0  
**Fecha de corte:** 2026-09-11  
**Función:** permitir que una nueva conversación continúe DDD sin reconstruir el proyecto de memoria ni repetir decisiones ya cerradas.

## 1. Fuente de verdad

El repositorio `jfmurciego/DiputadodeDistrito` es la evidencia del proyecto. No se debe asumir que una afirmación de un chat es cierta si contradice el código, los outputs o los expedientes del repositorio.

Al comenzar una conversación nueva, leer obligatoriamente:
1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/BITACORA.md`.
4. `docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`.
5. `docs/MODULOS/README.md` y el contrato del módulo en curso.
6. última ronda en `docs/RONDAS/`.
7. última ejecución en `docs/EJECUCIONES/`.
8. `configuracion/aragon_2025.yaml`, workflow y código vigente del módulo afectado.

No usar `docs/MEMORIA_DEL_PROYECTO.md` ni `docs/MEMORIA_PROYECTO.md` como estado actual: son documentos históricos anteriores al Estado Maestro.

## 2. Objetivo del proyecto

Construir el **Procedimiento de Distritación DDD**, reproducible, auditable y generalizable. Aragón es la primera implantación; después deben poder incorporarse Castilla y León, Extremadura y otros ámbitos mediante datos/configuración, no mediante forks del motor.

El producto no es un GeoJSON aislado. Es el procedimiento completo capaz de demostrar cómo se llega desde fuentes censales oficiales hasta distritos y, posteriormente, hasta la agregación electoral.

## 3. Terminología

- **Procedimiento:** sistema DDD completo.
- **Módulo:** transformación funcional M01–M08.
- **Ejecución:** lanzamiento completo o parcial del procedimiento.
- **Ronda:** conjunto coherente de cambios de desarrollo.
- **Preparación:** outputs reutilizables M01–M03 identificados por clave/hash.
- Evitar llamar `step` a los módulos en documentación nueva.

## 4. Arquitectura funcional

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 solución inicial → M05 optimización → M06 consolidación territorial → M07 agregación electoral → M08 producto territorial electoral.

M01–M03 se cachean. M04–M06 son el motor territorial iterativo. M07–M08 están desacoplados: los resultados electorales jamás condicionan la geometría.

## 5. Reglas duras Aragón vigentes

- K = 67.
- Población preparada = 1.364.621; secciones = 1.463.
- Provincia es frontera dura.
- Reparto provincial fijo R012: Huesca 11, Teruel 7, Zaragoza 49.
- Contigüidad estricta por grafo M03.
- Conservación exacta de secciones y población.
- Suelo poblacional = 0,80×target.
- Techo poblacional = 1,75×target.
- Objetivo fino = ±12% del target.
- Municipio cuya población cabe bajo el techo: indivisible.
- Municipio sobredimensionado: partición interna en bloques contiguos; se llenan primero los distritos exclusivamente urbanos/municipales y solo el residual puede completarse con municipios menores adyacentes de la misma provincia.
- No puede ocurrir el patrón “Barbastro repartido entre tres distritos mixtos”: si el municipio cabe, permanece en uno; si necesita varios, primero se agotan los distritos internos y solo el último puede ser mixto.
- CUSEC único/no nulo; determinismo; una sola configuración canónica.

## 6. Reglas de ingeniería y auditoría

1. Todo cambio de archivo relevante incrementa versión y preserva la versión anterior en `legacy/`.
2. Toda ronda actualiza bitácora y Estado Maestro.
3. Toda ejecución relevante debe tener expediente en `docs/EJECUCIONES/`.
4. Un informe/log no sustituye al producto. Si un módulo crea 1.463 secciones, las 1.463 deben ser accesibles.
5. Outputs ligeros completos permanecen navegables en `resultados/ejecuciones/<RUN_ID>/Mxx/`.
6. GeoJSON pesados se guardan como artefactos de Actions por módulo; `PRODUCTOS.json` registra ruta/tamaño/SHA-256.
7. Un resultado generado solo en el entorno del asistente sirve para diagnóstico, no como referencia final. La referencia debe poder reproducirla el usuario en GitHub.
8. No lanzar ciclos de “prueba y dime el error” cuando el asistente puede inspeccionar logs/artefactos directamente.
9. No modificar M05 a ciegas si el defecto nace en M04; corregir siempre el primer módulo que viola el contrato.

## 7. Historia reciente que importa

### Run #5 — 34584775443
R011 demostró publicación completa de outputs. Obtuvo 67 distritos, contigüidad y límites poblacionales bajo la validación de entonces, pero una auditoría reveló 13 distritos interprovinciales y 30 municipios fragmentados. Por ello no es referencia territorial: demostró que la puerta de validación estaba incompleta.

### R012
Se elevó provincia a frontera dura y se formalizó disciplina municipal. La configuración pasó a 11/7/49 y la validación debe fallar ante cruces provinciales o fragmentación municipal inválida.

### Run #6 — 34587157452
M04 v7.2.x respetó las cuotas provinciales, pero produjo el distrito 52 con 15 componentes. M05 detectó la desconexión y el run falló. Diagnóstico: el particionador extraía bloques conexos sin garantizar que el residuo urbano siguiera conexo.

### Corrección vigente
M04 **v7.3.0** sustituye ese mecanismo por partición municipal conexa, elimina el fallback de asignación no adyacente y se autovalida antes de exportar. Sobre los artefactos reales del Run #6, la comprobación local produjo 67 distritos, 11/7/49, cero cruces provinciales, cero desconectados, cero bajo suelo, cero sobre techo y un único distrito fuera de ±12% (Zaragoza, 31.563 habitantes). Esto todavía debe ser ratificado por la siguiente ejecución GitHub.

M05 vigente: v7.2.0, optimización por unidades territoriales protegidas. Debe trabajar dentro del espacio válido creado por M04 y no romper provincia, municipio ni contigüidad.

## 8. Outputs que deben existir

M01: secciones completas + geometría + informe.  
M02: todas las adyacencias.  
M03: grafo completo.  
M04: asignación inicial de las 1.463 secciones + GeoJSON + informe.  
M05: asignación optimizada completa + GeoJSON + informe.  
M06: `catalogo_distritos.csv`, `composicion_distritos.csv`, GeoJSON de secciones y GeoJSON de distritos.  
M07: resultados completos por partido/distrito + resumen + geometría electoral.  
M08: producto final distrital electoral.

M06 debe evolucionar hacia una ficha territorial rica: población, target/desviación, secciones, municipios y composición, provincia, superficie, perímetro, compacidad, centroides/bbox y, cuando existan fuentes fiables, comarca, municipio dominante, densidad, urbano/rural, barrios y fragmentación administrativa.

## 9. Estado al cerrar este documento

El usuario está ejecutando en GitHub la primera aceptación de M04 v7.3.0. La siguiente conversación debe **buscar primero el último workflow run** y no asumir su resultado.

Orden de diagnóstico del próximo run:
1. confirmar commit/versiones ejecutadas;
2. M04: 67, 11/7/49, 0 cruces, 0 desconectados, disciplina municipal, suelo/techo;
3. M05: comprobar que no degrada ninguna regla dura y medir fuera de ±12%;
4. validación final;
5. outputs M01–M08 y publicación;
6. registrar expediente, bitácora y Estado Maestro.

Si M04 pasa y M05 falla, trabajar exclusivamente sobre M05. Si todo pasa, auditar calidad territorial y completar M06 antes de promocionar una nueva referencia.

## 10. Regla de interacción

No quedarse en un resumen o diagnóstico cuando existe una acción clara. Cada respuesta sustantiva del proyecto debe terminar con un **Siguiente paso** concreto. Evitar recaps repetitivos. El usuario espera que el asistente inspeccione el repositorio, los runs y los artefactos directamente y que preserve continuidad/versionado sin que tenga que recordarlo en cada conversación.
