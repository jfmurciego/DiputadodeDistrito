# Bitácora de progreso

**Versión:** 2.8.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.7.0.md`

## R001–R008 — Base profesional y ejecución reproducible
Se recupera el procedimiento, se formalizan M01-M08, configuración única, caché territorial, fuentes congeladas para desarrollo y adquisición INE para certificación.

## GitHub Run #3 — 34580841510
Infraestructura completa PASS; algoritmo antiguo deja 29 distritos bajo suelo.

## R009 — Restricciones poblacionales y concurrencia
M05 v7.1.0 prioriza restricciones duras; workflow serializa únicamente preparación M01-M03.

## GitHub Run #4 — 34581760340
**Referencia algorítmica:** 67 distritos, contigüidad PASS, 0 bajo suelo, 0 sobre techo, `best_max_rel_dev≈0,3382`. M01-M03 se reutilizan correctamente desde caché.

## R010 — Primera visibilidad de resultados
Se publica `resultados/ejecuciones/<run_id>/`, pero la revisión detecta que un informe no sustituye al producto real de cada módulo.

## R011 — Completud y auditabilidad de cada módulo
Se establece la regla: **todo módulo debe exponer el estado que produce, no solo métricas sobre ese estado**. Workflow 2.7.0 materializa outputs completos navegables y ocho artefactos independientes M01-M08.

## GitHub Run #5 — 34584775443
**Aceptación R011: PASS.** Se restauran M01-M03 desde caché, M04-M08 ejecutan con éxito, se materializan outputs auditables M01-M08, se publican ocho artefactos separados y se crea `resultados/ejecuciones/gh-34584775443-1/`.

Validación: 67 distritos, 1.463 secciones, población 1.364.621, target 20.367,48, 0 bajo suelo, 0 sobre techo, 0 desconectados.

## Auditoría territorial Run #5
Expediente: `docs/AUDITORIAS/AUDITORIA_TERRITORIAL_RUN5_2026-09-11.md`.

Hallazgos principales:
- **65 de 67 distritos** están dentro de ±12% del target.
- Solo los distritos **16 y 37**, ambos de Teruel, quedan fuera: +33,82% y +33,64%.
- **13 distritos cruzan provincias**; 2 contienen secciones de las tres provincias.
- Máximo territorial: distrito 64, **4.771,16 km² y 78 municipios**.
- Se detectan **30 municipios fragmentados entre más de un distrito**; algunas divisiones son inevitables (Zaragoza), otras deben evaluarse y penalizarse si son evitables.
- La compacidad mínima Polsby-Popper es ~0,0412.

Conclusión: la solución es poblacionalmente válida y topológicamente contigua, pero el motor M05 sigue siendo demasiado pobre territorialmente. La siguiente evolución debe ser multiobjetivo: conservar restricciones duras y añadir integridad provincial/municipal, compacidad y coherencia territorial, mientras se resuelven de forma localizada los distritos 16 y 37.

## Regla permanente de auditoría
Un contador, log o informe nunca sustituye al producto de un módulo. Cada ejecución debe permitir inspeccionar las entidades producidas y rastrear los productos pesados por hash.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita.
