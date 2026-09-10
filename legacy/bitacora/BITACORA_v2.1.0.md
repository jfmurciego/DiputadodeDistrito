# Bitácora de progreso

**Versión:** 2.1.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.0.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Referencia recuperada: 1.463 secciones, 67 distritos, contigüidad 67/67; equilibrio poblacional FAIL.

Tras corregir determinismo M04/M05, dos ejecuciones locales con `seed=12345` dieron el mismo resumen: **67 distritos, 0 desconectados, 29 bajo suelo 0,80×target, 0 sobre techo 1,75×target, best_max_rel_dev 0,5046**, SHA-256 `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## R002 — Preparación de la ejecución arbitral en GitHub
**Estado:** en curso. Se habilita Git LFS para inputs grandes, checkout LFS, Docker reproducible y GitHub Actions como árbitro. Los binarios canónicos siguen pendientes de bootstrap remoto. R002 solo cierra cuando GitHub reproduce la referencia o cualquier diferencia queda explicada y versionada.

## R003 — Ejecuciones inmutables y preparación reutilizable
**Estado:** candidato.

Se detectan dos defectos de infraestructura de R002: (1) `output/` compartido podía sobrescribir evidencia; (2) cambiar configuración exclusiva de M04-M08 invalidaba M01-M03 porque el hash incluía el YAML completo.

Se corrige de forma estructural:
- M01-M03 → `.cache/ddd/preparacion/{run_name}/`.
- M04-M08 + logs + manifiesto + validación → `ejecuciones/{run_id}/`.
- Nueva herramienta `calcular_clave_preparacion.py` calcula la huella únicamente con inputs, parámetros y código que afectan M01-M03.
- `.dockerignore` impide empaquetar inputs, cache, resultados y legacy en cada imagen; los inputs se montan de solo lectura.
- El workflow pasa a v2.2.0 y publica exclusivamente la ejecución actual.
- Todas las versiones sustituidas fueron archivadas antes en el commit `96ba2214`.

### Efecto esperado
Modificar M05 o lanzar diez semillas no debe volver a cargar/procesar los ficheros nacionales mientras M01-M03 no cambien. Cada corrida queda demostrable e independiente.

## Regla permanente de progreso
Una nueva versión solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
