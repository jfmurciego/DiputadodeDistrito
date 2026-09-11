# Bitácora de progreso

**Versión:** 2.9.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.8.0.md`

## R001–R011 — Base reproducible, algoritmo poblacional y outputs auditables
Se recupera y profesionaliza el procedimiento, se formalizan M01-M08, caché territorial, validación, fuentes congeladas, reparación poblacional M05, concurrencia y publicación completa de outputs por módulo.

## GitHub Run #5 — 34584775443
R011 PASS técnico: 67 distritos, 1.463 secciones, población 1.364.621, 0 bajo suelo, 0 sobre techo, 0 desconectados. La auditoría posterior revela que esa puerta era territorialmente incompleta: 13 distritos cruzaban provincias y 30 municipios aparecían fragmentados.

## R012 — Provincia dura y disciplina municipal
Documento: `docs/RONDAS/R012_2026-09-11_provincia_y_disciplina_municipal.md`.

Se elevan a reglas estructurales:
- ningún distrito puede cruzar una provincia;
- reparto provincial de los 67 distritos mediante Hamilton sobre población 2025: Huesca 11, Teruel 7, Zaragoza 49;
- un municipio que cabe en un distrito no se fragmenta;
- un municipio grande puede ocupar como máximo `ceil(P/target)` distritos y como mínimo `ceil(P/cap)`;
- todos sus distritos salvo como máximo uno deben ser íntegramente municipales; solo el residual puede completarse con municipios menores adyacentes de la misma provincia.

La configuración pasa a **7.4.0**. La herramienta de validación pasa a **1.3.0** y convierte cruces provinciales o fragmentación municipal inválida en FAIL. M04 se redefine como construcción province-first y municipality-aware; M05 se redefine como optimización dentro de ese espacio válido.

## Jerarquía M05 R012
Restricciones duras: 67 distritos; 11/7/49 por provincia; cero cruces provinciales; contigüidad; suelo/techo; disciplina municipal.

Objetivos fuertes: minimizar distritos fuera de ±12%; magnitud fuera de tolerancia; fragmentación municipal evitable; distritos mixtos; máximo desvío y error cuadrático. Compactación y coherencia comarcal quedan como capa territorial posterior, con fuentes explícitas.

## Estatus de Run #5
Run #5 deja de ser referencia territorial aceptable. Se conserva como PASS técnico bajo una validación incompleta y como evidencia de R011. La siguiente referencia debe superar también las puertas R012.

## Regla permanente de auditoría
Un contador, log o informe nunca sustituye al producto de un módulo. Cada ejecución debe permitir inspeccionar las entidades producidas y rastrear los productos pesados por hash.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita.
