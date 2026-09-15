# Punto de reenganche DDD

Versión: 1.34.0
Fecha: 2026-09-15
Estado: corrección de certificación geométrica y estado de producción.
Anterior: legacy/docs/PUNTO_REENGANCHE_v1.33.0.md

## Fuente operativa

- Estado de máquina: orchestracion/estado_operativo_g10.json
- Estado legible: docs/SALIDAS_CHATGPT/ESTADO_OPERATIVO_G10.md
- Productos públicos declarados: orchestracion/productos_publicos.json
- Control independiente de publicación: .github/workflows/validar-productos-publicos.yml
- Puerta de admisión: herramientas/validar_contrato_territorial.py
- CI de contratos: .github/workflows/validar-contratos-territoriales.yml
- Lista de cierre: docs/CIERRE_INGENIERIA_PRODUCCION.md
- Interfaz territorial principal: .github/workflows/operacion-territorial.yml
- Motor reutilizable sin formulario propio: .github/workflows/producir-territorio-por-contrato.yml
- Migración al nuevo hilo: docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md
- Prompt breve: docs/SALIDAS_CHATGPT/PROMPT_CORTO_AUDITORIA_PLATAFORMA.md

## Regla de ejecución

Aragón conserva productos históricos y un contrato ejecutable, pero el candidato del run `34960965537` está bloqueado: 60 de 67 distritos superan la continuidad geométrica independiente. No es baseline canónico. Castilla y León conserva su evidencia técnica con publicación bloqueada; Extremadura permanece `EXPERIMENTAL_BLOCKED`.

Producción escribe `production_status.json`; el visor obtiene identidad y K del contrato y no infiere `PASS` por la presencia de un ZIP. La regresión de Aragón y el preflight GerryChain exigen ahora continuidad de componentes poligonales. El motor GerryChain valida también las piezas de secciones `MultiPolygon`; comarca continúa como objetivo blando.

## Publicación pendiente

El visor MapLibre y su contrato exhaustivo están verificados. **Validar productos públicos** produce un artefacto estático descargable sin Pages y sin ejecutar el motor. GitHub Pages requiere una única habilitación del propietario en Settings > Pages > GitHub Actions; después se relanza Desplegar visor público.

## Reenganche G10

Usar G10 — Operar lote durable sólo tras una huella nueva. Si no cambia contrato, fuente o producto, el resultado esperado es REUSED.

## Paquete local-first actual

M01 incorpora un adaptador comarcal opcional por código municipal normalizado,
con cobertura, duplicados y faltantes verificables. M03 y M06 conservan esos
atributos sin convertirlos en una restricción. La interfaz territorial principal cubre
M01–M08 con nomenclatura institucional. No se ha habilitado ninguna fuente
comarcal territorial ni se ha ejecutado comunidad alguna.

La suite `34874697663`, la puerta contractual `34874697606`, el control G10 y
la validación de productos terminaron SUCCESS sobre `636f732`. La restauración
del árbol activó incidentalmente C‑01, que terminó FAIL conforme al resultado
de robustez ya conocido y sin modificar productos. El siguiente commit elimina
todos los disparadores automáticos de cálculo pesado, exportación y publicación.

El blindaje queda certificado en `24eb07e`, suite `34882876061` SUCCESS. Ese fue
el único workflow activado: cero territorios, C‑01, regresiones, exportaciones o
publicaciones. R040 continúa bloqueado hasta orden expresa.

`COMARCAS.csv` se verificó sin GIS: 731 códigos municipales únicos, 33 comarcas,
cero claves inválidas y cero asignaciones contradictorias. Sigue deshabilitado.

## Siguiente bloque de ingeniería

R039 sustituye la configuración artesanal de M07 por el contrato común
`ddd-election` 1.0.0. La fuente se verifica por SHA-256 antes de leerse, el
adaptador y el diccionario de partidos están fuera del código y M08 exige
cobertura distrital exacta. La validación usa pruebas sintéticas y el input
electoral ya materializado; no ejecuta M01–M08. El primer CI `34832589193`
detectó únicamente que `inputs/` no existe dentro de la imagen. La prueba ahora
verifica bytes fuera y coherencia contrato–manifiesto dentro, sin introducir un
bypass en M07. El commit `6e8162b` supera la suite general `34833051502`.
R039 queda cerrado. Tras certificar este paquete con la suite general, R040 y
toda ejecución territorial permanecen congelados hasta orden expresa.
