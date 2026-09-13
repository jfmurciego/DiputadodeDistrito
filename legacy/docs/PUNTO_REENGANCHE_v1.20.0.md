# Punto de reenganche DDD

Versión: 1.20.0
Fecha: 2026-09-13
Estado: C-10 implementado; pendiente certificación CI antes de avanzar a C-07.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.19.0.md

## Fuente operativa

- Estado de máquina: orchestracion/estado_operativo_g10.json
- Estado legible: docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md
- Productos públicos declarados: orchestracion/productos_publicos.json
- Control independiente de publicación: .github/workflows/validar-productos-publicos.yml
- Puerta de admisión: herramientas/validar_contrato_territorial.py
- CI de contratos: .github/workflows/validar-contratos-territoriales.yml
- Lista de cierre: docs/CIERRE_INGENIERIA_PRODUCCION.md
- Línea única: .github/workflows/producir-territorio-por-contrato.yml
- Migración al nuevo hilo: docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md
- Prompt breve: docs/SALIDAS_CHATGPT/PROMPT_CORTO_AUDITORIA_PLATAFORMA.md

## Regla de ejecución

Aragón y Castilla y León ya son productos certificados. Extremadura permanece EXPERIMENTAL_BLOCKED. No se repite M01–M06 ni se abre otra comunidad sin cambio material y orden expresa.

## Publicación pendiente

El visor MapLibre y su contrato exhaustivo están verificados. **Validar productos públicos** produce un artefacto estático descargable sin Pages y sin ejecutar el motor. GitHub Pages requiere una única habilitación del propietario en Settings > Pages > GitHub Actions; después se relanza Desplegar visor público.

## Reenganche G10

Usar G10 — Operar lote durable sólo tras una huella nueva. Si no cambia contrato, fuente o producto, el resultado esperado es REUSED.

## Siguiente bloque de ingeniería

C-10 fija `polsby_popper` y el resto del catálogo M06 como contrato único. Los
runs históricos no se reescriben: pasan por un adaptador de aliases explícito y
auditable. La validación cubre 67/82/65 distritos sin ejecutar M01–M06. Tras CI,
continuar por C-07, prueba sintética adversarial. No tocar C-01. C-11 queda fuera
de cálculo partidista por decisión expresa de dirección. R038–R040 y toda
expansión territorial siguen suspendidos.
