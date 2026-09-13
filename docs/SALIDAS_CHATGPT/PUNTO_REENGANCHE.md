# Punto de reenganche DDD

**Versión:** 1.2.0  
**Fecha:** 2026-09-13  
**Estado:** VISOR PÚBLICO EN DESPLIEGUE; Fase 1 cerrada técnicamente.  
**Anterior:** `legacy/salidas_chatgpt/PUNTO_REENGANCHE_v1.1.0.md`

## Estado operativo

- Aragón y Castilla y León: productos territoriales certificados y publicados como fuentes canónicas.
- Extremadura: bloqueada explícitamente; no se promociona.
- Motor: no hay cálculo territorial pendiente ni autorizado.
- G10: reutiliza evidencia por huella; sólo se lanza si cambia un contrato, una evidencia o un producto.

## Trabajo en curso

**Nombre en GitHub Actions:** `Desplegar visor público`

Publica MapLibre con Aragón (67) y Castilla y León (82). El workflow valida ambos GeoJSON y no ejecuta M01–M06.

## Después del correo

1. Abrir la URL del job `Desplegar visor público`.
2. Verificar selector, 67 distritos de Aragón y 82 de Castilla y León.
3. Pulsar un distrito y comprobar su ficha.
4. Si el desplegado falla, revisar sólo ese workflow; no lanzar el motor territorial.

## Reenganche G10

Usar `G10 — Operar lote durable` exclusivamente tras un cambio material que invalide una huella. Un lote sin cambio debe devolver `REUSED`, no consumir runners ni recalcular.
