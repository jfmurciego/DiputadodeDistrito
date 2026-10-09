# Bitácora de progreso

**Versión:** 2.11.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.10.0.md`

## R001–R011 — Base reproducible, algoritmo poblacional y outputs auditables
Se recupera y profesionaliza el procedimiento, se formalizan M01-M08, caché territorial, validación, fuentes congeladas, reparación poblacional M05, concurrencia y publicación completa de outputs por módulo.

## GitHub Run #5 — 34584775443
R011 PASS técnico: 67 distritos, 1.463 secciones, población 1.364.621, 0 bajo suelo, 0 sobre techo, 0 desconectados. La auditoría posterior revela que esa puerta era territorialmente incompleta: 13 distritos cruzaban provincias y 30 municipios aparecían fragmentados.

## R012 — Provincia dura y disciplina municipal
Reglas estructurales vigentes:
- ningún distrito cruza provincia;
- reparto provincial exacto 11 Huesca / 7 Teruel / 49 Zaragoza;
- municipio que cabe bajo el techo duro permanece íntegro;
- municipio sobredimensionado se divide internamente en bloques conexos;
- todos los bloques urbanos salvo como máximo el residual permanecen exclusivamente municipales;
- solo el residual puede completarse con municipios menores adyacentes de la misma provincia.

Configuración: v7.4.0. Validación: v1.3.0. M05 vigente: v7.2.0.

## GitHub Run #6 — 34587157452
**FAIL en M05**, mensaje: `M05 produjo distrito desconectado 52`.

Auditoría posterior del producto real M04 frente al grafo M03: el distrito 52 ya salía de M04 con 15 componentes. M05 detectó correctamente la inconsistencia; no fue el origen.

Causa raíz: M04 v7.2.0/v7.2.1 construía bloques urbanos conexos individualmente, pero no garantizaba que el residuo municipal conservara conectividad. Zaragoza quedó fragmentada internamente.

Expediente: `docs/EJECUCIONES/GITHUB_RUN_0006_2026-09-11.md`.

## M04 v7.3.0 — Partición balanceada conexa por provincia
Se preserva v7.2.1 en `legacy/modulo04/04_generar_semillas_v7.2.1.py`.

Cambios:
- partición híbrida conexa de municipios grandes;
- reparación local de población preservando conectividad;
- municipio no se divide mientras quepa bajo el techo duro;
- ensamblaje de unidades rurales mediante particiones conexas y reparación local;
- se elimina todo fallback no adyacente;
- M04 valida por sí mismo 67 distritos, cuotas 11/7/49, provincia única, contigüidad y suelo/techo antes de exportar.

Prueba local con los artefactos reales del Run #6:
- 67 distritos;
- 11/7/49;
- 0 cruces provinciales;
- 0 distritos desconectados;
- 0 bajo suelo / 0 sobre techo;
- un único distrito rural de Zaragoza queda fuera de ±12% (31.563 habitantes), por lo que la optimización fina pasa legítimamente a M05.

## Regla permanente de auditoría
Un contador, log o informe nunca sustituye al producto de un módulo. Cada ejecución debe permitir inspeccionar las entidades producidas y rastrear los productos pesados por hash.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita.
