# Memoria operativa del proyecto

**Versión:** 1.0.0  
**Fecha de corte:** 2026-09-11

## Objetivo

Construir un procedimiento reproducible, auditable y reutilizable para generar distritos uninominales a partir de unidades censales oficiales. Aragón es la primera implantación. La misma arquitectura debe admitir Castilla y León, Extremadura y, eventualmente, España completa sin duplicar el motor.

## Restricciones Aragón vigentes

- K exacto: 67 distritos.
- Contigüidad estricta medida sobre el grafo de secciones.
- Target = población total / 67.
- Suelo duro: 0,80 × target.
- Techo duro: 1,75 × target.
- Semillas deterministas.
- CUSEC único y sin nulos.
- Conservación total de población.
- La capa electoral es posterior y no condiciona la geometría.

## Estado conocido

El baseline recuperado ejecuta el procedimiento 01-08, pero falla el equilibrio poblacional. La prioridad algorítmica posterior a estabilizar GitHub es mejorar el módulo 05 sin romper cardinalidad ni contigüidad.

## Trazabilidad obligatoria

Cada ronda debe dejar commit, versiones internas, legacy, bitácora, manifiesto, validación y resultados identificados por commit/run. Ningún resultado generado solo dentro de una sesión de IA se considera evidencia suficiente: la prueba de referencia es una ejecución que el usuario puede repetir en GitHub.
