# R012 — Provincia dura y disciplina de división municipal

**Fecha:** 2026-09-11

## Motivo
La auditoría del Run #5 reveló 13 distritos que cruzan provincias y 30 municipios fragmentados. Ambas situaciones contradicen reglas territoriales fundamentales del Procedimiento DDD.

## Regla dura 1 — Integridad provincial
Ningún distrito puede contener secciones de más de una provincia.

La provincia no es una penalización ni una preferencia: es una frontera dura. M04 debe construir dentro de cada provincia y M05 no puede trasladar una sección a un distrito de otra provincia.

Con la población 2025 vigente:
- Huesca: 230.087 habitantes
- Teruel: 136.091 habitantes
- Zaragoza: 998.443 habitantes
- Aragón: 1.364.621 habitantes
- K total: 67

Aplicando Hamilton sobre la cuota poblacional salen 11 distritos para Huesca, 7 para Teruel y 49 para Zaragoza.

## Regla dura 2 — Disciplina municipal/urbana
Un municipio que cabe en un distrito no se fragmenta entre varios distritos.

Para un municipio cuya población obliga o aconseja varios distritos, el proceso es secuencial:
1. se forman primero uno o varios distritos internos al municipio;
2. esos distritos se llenan exclusivamente con secciones del propio municipio;
3. únicamente el último distrito residual puede incorporar municipios menores adyacentes de la misma provincia;
4. nunca puede haber varios distritos mixtos conteniendo simultáneamente fragmentos del mismo municipio y municipios externos.

Consecuencia práctica: Barbastro, Monzón, Calatayud, Utebo, etc. no pueden aparecer repartidos arbitrariamente entre múltiples distritos. Zaragoza, Huesca y Teruel pueden requerir varios distritos internos por volumen de población, pero todos salvo como máximo el residual deben ser íntegramente urbanos/municipales.

## Regla de cardinalidad municipal
Para un municipio con población P y target T:
- si P <= T, máximo 1 distrito que contenga secciones del municipio;
- si P > T, máximo ceil(P/T) distritos;
- el número mínimo viene dado por ceil(P/cap), para no forzar ningún distrito por encima del techo duro;
- como máximo uno de los distritos que contienen ese municipio puede ser mixto con otros municipios.

La optimización hacia ±12% decidirá dentro de ese rango cuántos distritos urbanos son finalmente necesarios.

## Cambio arquitectónico
M04 deja de ser un simple semillado global de secciones. Debe trabajar en dos niveles:
1. construcción de unidades atómicas municipales/urbanas dentro de cada provincia;
2. ensamblado contiguo de esas unidades en el número de distritos asignado a la provincia.

M05 optimizará después sin poder:
- cruzar provincia;
- fragmentar un municipio que deba permanecer íntegro;
- crear más de un distrito mixto para un municipio dividido.

## Nueva jerarquía de objetivos M05
### Restricciones duras
1. 67 distritos exactos.
2. Cardinalidad provincial 11/7/49.
3. Cero cruces provinciales.
4. Contigüidad de grafo.
5. Suelo 0,80×target y techo 1,75×target.
6. Disciplina de fragmentación municipal.

### Objetivos fuertes, en orden
1. llevar todos los distritos al intervalo ±12% cuando sea factible;
2. minimizar número de municipios fragmentados por encima del mínimo necesario;
3. minimizar número de distritos mixtos generados por municipios urbanos divididos;
4. reducir máximo desvío poblacional;
5. reducir error cuadrático poblacional.

### Preferencias territoriales posteriores
- compactación;
- superficie razonable;
- coherencia comarcal cuando exista capa fiable;
- nombres y cabeceras reales.

## Estatus del Run #5
Run #5 queda clasificado como PASS técnico bajo una puerta de validación incompleta. No es referencia territorial aceptable porque contiene cruces provinciales y fragmentación municipal no disciplinada.

## Siguiente implementación
1. ampliar validación con integridad provincial y disciplina municipal;
2. rediseñar M04 para construir por provincia y por unidades atómicas municipales/urbanas;
3. limitar M05 a movimientos compatibles con esas unidades;
4. volver a ejecutar en modo iterativo y exigir PASS de todas las puertas antiguas y nuevas.
