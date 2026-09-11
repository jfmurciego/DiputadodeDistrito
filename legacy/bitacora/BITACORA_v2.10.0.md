# Bitácora de progreso

**Versión:** 2.10.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.9.0.md`

## R001–R011 — Base reproducible, algoritmo poblacional y outputs auditables
Se recupera y profesionaliza el procedimiento, se formalizan M01-M08, caché territorial, validación, fuentes congeladas, reparación poblacional M05, concurrencia y publicación completa de outputs por módulo.

## GitHub Run #5 — 34584775443
R011 PASS técnico: 67 distritos, 1.463 secciones, población 1.364.621, 0 bajo suelo, 0 sobre techo, 0 desconectados. La auditoría posterior revela que esa puerta era territorialmente incompleta: 13 distritos cruzaban provincias y 30 municipios aparecían fragmentados.

## R012 — Provincia dura y disciplina municipal
Documento: `docs/RONDAS/R012_2026-09-11_provincia_y_disciplina_municipal.md`.

Reglas estructurales:
- ningún distrito puede cruzar una provincia;
- reparto provincial de los 67 distritos: Huesca 11, Teruel 7, Zaragoza 49;
- un municipio que cabe en un distrito no se fragmenta;
- un municipio grande se divide internamente en bloques contiguos; los bloques urbanos completos quedan cerrados y solo el residual puede completarse con municipios menores adyacentes de la misma provincia.

Configuración **7.4.0** y validación **1.3.0** convierten cruces provinciales o fragmentación municipal inválida en FAIL.

### Implementación R012
- M04 pasa de **v7.0.1** a **v7.2.0** (`Provincia primero y disciplina municipal`).
- M04 construye por provincia y materializa `ddd_unit_id` y `ddd_closed_urban`.
- Los municipios no sobredimensionados son unidades atómicas.
- Los municipios grandes generan bloques urbanos contiguos; los bloques completos se asignan a distritos cerrados.
- M05 pasa de **v7.1.0** a **v7.2.0** (`Optimización por unidades territoriales protegidas`).
- M05 deja de mover secciones individuales: mueve unidades completas.
- M05 rechaza cruces provinciales y no permite entradas/salidas en distritos urbanos cerrados.
- La función objetivo prioriza restricciones duras, después número de distritos fuera de ±12%, máximo desvío y error cuadrático.

M04 v7.0.1 y M05 v7.1.0 quedan preservados en `legacy/modulo04/` y `legacy/modulo05/`.

## Estatus de Run #5
Run #5 deja de ser referencia territorial aceptable. Se conserva como PASS técnico bajo una validación incompleta y como evidencia de R011. La siguiente referencia debe superar también las puertas R012.

## Regla permanente de auditoría
Un contador, log o informe nunca sustituye al producto de un módulo. Cada ejecución debe permitir inspeccionar las entidades producidas y rastrear los productos pesados por hash.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita.
