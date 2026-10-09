# Arquitectura multi-territorio DDD

**Versión:** 1.0.0
**Fecha:** 2026-09-11
**Estado:** vigente — R018

## Principio

DDD es un **producto único** con múltiples implantaciones territoriales. El motor no se copia por comunidad ni por país. Los territorios aportan contratos declarativos y fuentes; el motor interpreta esos contratos.

## Capas

1. **Motor común** — `ddd_core/`, `modulos/`, `herramientas/`.
2. **Contrato territorial** — YAML y documentación de cada territorio.
3. **Fuentes territoriales** — geometría, población, divisiones administrativas y, opcionalmente, resultados electorales.
4. **Tests territoriales** — invariantes propias y regresiones de baselines aceptados.
5. **Resultados** — ejecuciones inmutables y artefactos GitHub.
6. **Gobernanza** — `docs/`, `legacy/`, bitácora y registros.

## Estructura canónica

```text
territorios/<id>/
├── README.md
├── config/
│   └── <id>_<año>.yaml
├── inputs/
│   ├── README.md
│   ├── MANIFEST.sha256
│   └── ...
├── docs/
│   └── ...
├── tests/
│   └── ...
└── resultados/   # referencias o materialización territorial cuando proceda
```

## Reglas de aislamiento

- Nunca introducir lógica electoral en M01–M06.
- Nunca introducir `if territory == ...` si la diferencia puede expresarse en configuración o estrategia genérica.
- Una excepción territorial inevitable debe quedar declarada como extensión del contrato, no como fork.
- Un territorio no puede importar código desde otro territorio.
- Los tests de un territorio pueden reutilizar helpers comunes, pero sus expectativas pertenecen a su paquete.

## Ciclo de incorporación de un territorio

1. Inventariar fuentes oficiales y licencias.
2. Resolver unidad territorial mínima y clave estable.
3. Definir población y año de referencia.
4. Definir niveles administrativos que actúan como barreras o preferencias.
5. Definir K y método de reparto por provincias/estados/departamentos si aplica.
6. Crear YAML conforme a `docs/CONTRATO_TERRITORIO.md`.
7. Ejecutar M01 y validar universo/población.
8. Ejecutar M02–M03 y validar grafo/contigüidad.
9. Solo entonces ejecutar M04–M06.
10. Incorporar resultados electorales en M07–M08 de forma posterior.
11. Promocionar baseline únicamente tras CI + run territorial reproducible.

## Madurez

- **Nivel A — implantación:** requiere cambios frecuentes del motor.
- **Nivel B — generalización:** un segundo territorio descubre supuestos ocultos y los extrae.
- **Nivel C — reutilización:** un tercer territorio exige principalmente configuración/datos.
- **Nivel D — producto:** territorios ordinarios entran sin modificar motor.
- **Nivel E — internacional:** el contrato soporta esquemas administrativos y electorales distintos sin forks.

Aragón demuestra Nivel A. Castilla y León debe llevarnos hacia Nivel B. Extremadura será la primera prueba real de Nivel C.

## Compatibilidad R018

Las rutas antiguas de Aragón permanecen temporalmente para no romper el workflow validado. Deben considerarse adaptadores de compatibilidad y retirarse solo cuando el workflow multi-territorio haya reproducido Run #9.
