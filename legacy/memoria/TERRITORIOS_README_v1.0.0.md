# Territorios DDD

Cada subdirectorio representa una implantación del motor común. No contiene forks del motor.

## Activos

- `aragon/` — implantación de referencia validada; baseline Run #9 / R016.
- `castilla_y_leon/` — siguiente implantación; estado preparación R018.

## Próximos

Extremadura será el siguiente caso después de Castilla y León. El objetivo arquitectónico es que cada incorporación requiera progresivamente menos cambios en `ddd_core/` y `modulos/`.

## Regla

Un territorio aporta configuración, inputs, documentación y tests. Cualquier necesidad de modificar el motor debe justificarse como generalización reusable para todos los territorios, nunca como parche local escondido.
