# Punto de reenganche DDD

Versión: 1.18.0
Fecha: 2026-09-13
Estado: C-04 cerrado; C-01 permanece fuera de este bloque y C-10 es el siguiente hito.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.17.0.md

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

C-04 queda cerrado con una métrica reproducible del sesgo poblacional previo a
M04: Aragón alcanza 4,546 % absoluto y Castilla y León 9,674 %. La evidencia se
obtiene exclusivamente de resultados certificados; Extremadura permanece
`EXPERIMENTAL_BLOCKED`. Continuar por C-10, contrato único de esquema y
métricas. No tocar C-01. C-11 queda fuera de cálculo partidista por decisión
expresa de dirección. R038–R040 y toda expansión territorial siguen suspendidos.
