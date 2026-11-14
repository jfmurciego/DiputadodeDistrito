# Territorio: Castilla y León

**Estado:** preparación — R018
**Objetivo:** segunda implantación DDD y prueba de generalización del motor.

## Principio

Castilla y León no tendrá un motor propio. Este paquete aportará configuración, fuentes, documentación y tests al motor común.

## Orden de trabajo

1. Inventario de fuentes oficiales.
2. Completar contrato territorial.
3. Generalizar workflow para seleccionar territorio/configuración.
4. Validar M01: universo, población y claves.
5. Validar M02–M03: adyacencias y grafo.
6. Solo después abrir M04–M06.
7. M07–M08 únicamente tras fijar geometría.

## Carpetas

- `config/`: plantilla inicial; no ejecutable como baseline hasta completar parámetros.
- `inputs/`: fuentes congeladas y manifiestos cuando se incorporen.
- `docs/`: decisiones, auditorías y expedientes propios.
- `tests/`: invariantes territoriales propias.

## Continuidad

Abrir el nuevo chat leyendo `docs/CONTINUIDAD_CASTILLA_Y_LEON.md`.
