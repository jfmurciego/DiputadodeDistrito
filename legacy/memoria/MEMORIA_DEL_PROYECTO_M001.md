# Memoria viva — Diputado de Distrito

**Memoria:** M001  
**Fecha de corte:** 2026-09-11  
**Estado:** recuperación consolidada / profesionalización en curso

## Propósito
Construir un procedimiento generalizable de distritación que pueda aplicarse primero a Aragón, después a Castilla y León y Extremadura y, potencialmente, a unas elecciones generales. Debe ser reproducible por terceros a partir del código, inputs identificados y parámetros; no puede depender de una caja negra ni de una ejecución privada del asistente.

## Principios no negociables
- Resultado demostrable ejecutando el repositorio por el usuario.
- 67 distritos exactos para el caso Aragón actual.
- Contigüidad estricta medida sobre el grafo territorial.
- Suelo poblacional 0,80×target y techo 1,75×target como restricciones duras actuales.
- Máximo de split 3 donde aplique la granularización de unidades sobredimensionadas.
- Una sola configuración canónica; evitar ficheros de parámetros redundantes.
- Entradas y salidas identificadas por hash.
- Semillas y orden deterministas cuando exista aleatoriedad.
- No sobrescribir versiones ni ejecuciones anteriores.
- Separar ingestión/preparación territorial del motor iterativo para no reprocesar fuentes pesadas en cada prueba.

## Baseline recuperado
Código histórico recuperado en ocho transformaciones. La ejecución de recuperación alcanza de principio a fin los productos territoriales y electorales. Diagnóstico actual: cardinalidad y contigüidad correctas; balance poblacional inaceptable. Esto fija un punto de comparación objetivo para cualquier versión nueva.

## Próximos hitos
1. Incorporar y renombrar los ocho módulos activos con cabeceras de versión y copias del baseline en `legacy/`.
2. Implementar preparación/cache de inputs y base territorial M1–M3.
3. Completar manifiesto de ejecución y almacenamiento inmutable de resultados.
4. Ejecutar el mismo commit en GitHub Actions y comparar sus métricas con el baseline recuperado.
5. Solo después, evolucionar el Módulo 5 hasta satisfacer restricciones poblacionales sin romper contigüidad ni cardinalidad.
6. Generalizar configuración territorial para Castilla y León sin bifurcar el motor.

## Criterio de avance
Una ronda avanza si mejora una métrica o capacidad explícita sin degradar una restricción ya satisfecha, salvo decisión documentada. Si una ronda empeora un criterio previamente aprobado, debe registrarse como regresión y no sustituye la versión aceptada.
