# Punto de reenganche DDD

Versión: 1.17.0
Fecha: 2026-09-13
Estado: C-01 en ejecución; protocolo de 50 semillas M05 fijado sin datos partidistas.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.16.0.md

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

C-01 reutiliza M03/M04 certificados del run `34599224954` y ejecuta solo M05
con 50 semillas. El protocolo y los umbrales se fijaron antes de observar el
resultado. Esperar la evidencia del workflow `C-01 — Robustez frente a semilla
Aragón`; no ejecutar otro barrido en paralelo. C-11 queda fuera de cálculo
partidista por decisión expresa de dirección. R038–R040 y toda expansión
territorial continúan suspendidos.
