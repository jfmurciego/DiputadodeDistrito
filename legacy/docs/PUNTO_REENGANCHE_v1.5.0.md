# Punto de reenganche DDD

Versión: 1.5.0
Fecha: 2026-09-13
Estado: ingeniería de admisión territorial en curso; R034 completada.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.4.0.md

## Fuente operativa

- Estado de máquina: orchestracion/estado_operativo_g10.json
- Estado legible: docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md
- Productos públicos declarados: orchestracion/productos_publicos.json
- Control independiente de publicación: .github/workflows/validar-productos-publicos.yml
- Puerta de admisión: herramientas/validar_contrato_territorial.py
- CI de contratos: .github/workflows/validar-contratos-territoriales.yml

## Regla de ejecución

Aragón y Castilla y León ya son productos certificados. Extremadura permanece EXPERIMENTAL_BLOCKED. No se repite M01–M06 ni se abre otra comunidad sin cambio material y orden expresa.

## Publicación pendiente

El visor MapLibre y su contrato exhaustivo están verificados. **Validar productos públicos** produce un artefacto estático descargable sin Pages y sin ejecutar el motor. GitHub Pages requiere una única habilitación del propietario en Settings > Pages > GitHub Actions; después se relanza Desplegar visor público.

## Reenganche G10

Usar G10 — Operar lote durable sólo tras una huella nueva. Si no cambia contrato, fuente o producto, el resultado esperado es REUSED.

## Siguiente bloque de ingeniería

R034 convierte el contrato en una puerta ejecutable y certifica Aragón/Castilla y León sin recalcular. Siguiente hueco de producción: unificar el workflow completo M01–M06 por `territory_id`, eliminando las selecciones codificadas por territorio y haciendo obligatoria esta admisión antes del primer módulo. Mantener congelada toda ejecución territorial mientras no exista orden explícita.
