# Diputado de Distrito — motor multi-territorio

**README v4.0.0** · 11-09-2026 · Estado: **R018 arquitectura multi-territorio**
**Anterior:** `legacy/docs/README_v3.5.0.md`

## Qué es

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales a partir de unidades censales oficiales. El motor común vive en `ddd_core/`, `modulos/` y `herramientas/`. Cada territorio aporta sus datos, configuración, reglas y pruebas dentro de `territorios/<territorio>/`.

La regla arquitectónica es: **un solo repositorio, una sola rama permanente (`main`), un solo motor; muchos territorios como paquetes de configuración/datos.** No se crean repositorios ni ramas permanentes por comunidad autónoma.

## Baseline territorial vigente

Aragón es la primera implantación de referencia. GitHub Run #9 `34599224954` / R016 es el baseline aceptado: 67 distritos, 1.463 secciones, 1.364.621 habitantes, reparto 11/7/49, provincia PASS, contigüidad PASS, disciplina municipal PASS, suelo/techo PASS y `fuera_12=0`. Máximo desvío relativo: **9,930 %**.

M05 v7.4.0 alcanzó la primera solución factible en la iteración 9.038 y continuó hasta 20.000, reduciendo el máximo desvío desde 11,943 % y el error cuadrático global desde 0,182704485064 a 0,161271162560.

## Estructura

```text
DiputadodeDistrito/
├── ddd_core/                    # núcleo común
├── modulos/                     # M01–M08 comunes
├── herramientas/                # utilidades comunes
├── territorios/
│   ├── aragon/
│   │   ├── config/
│   │   ├── inputs/
│   │   ├── docs/
│   │   └── resultados/
│   └── castilla_y_leon/
│       ├── config/
│       ├── inputs/
│       ├── docs/
│       └── tests/
├── resultados/                  # compatibilidad histórica y baselines publicados
├── tests/                       # regresión común
├── docs/                        # arquitectura/gobernanza global
└── legacy/                      # versiones retiradas y arqueología
```

Durante R018 se mantienen temporalmente `configuracion/`, `inputs/` y `resultados/ejecuciones/` como rutas de compatibilidad con el workflow de Aragón ya validado. La estructura canónica nueva es `territorios/`. No se duplican blobs grandes: Aragón referencia los mismos objetos Git versionados.

## Arquitectura del procedimiento

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final.

M01–M03 preparan territorio; M04–M06 son el núcleo territorial; M07–M08 añaden resultados electorales después. Los resultados electorales nunca condicionan la geometría.

## Territorios

- `territorios/aragon/`: implantación validada; Run #9 es baseline. R017 de calidad territorial queda pendiente para retomarse en este hilo.
- `territorios/castilla_y_leon/`: siguiente implantación. Su objetivo no es clonar Aragón sino descubrir y extraer cualquier supuesto aragonés oculto en el motor.
- futuros: Extremadura y restantes comunidades; después España completa y adaptación internacional.

La medida de madurez del motor será cuánto código común hay que cambiar al incorporar un territorio nuevo. El objetivo final es **datos + configuración + reglas + pruebas, con cero cambios del motor**.

## Contrato de territorio

Leer `docs/CONTRATO_TERRITORIO.md`. Todo paquete debe declarar identidad, fuentes, claves geográficas, población, niveles administrativos, número/reparto de distritos, límites poblacionales, reglas de atomicidad, criterios de contigüidad, inputs electorales opcionales y pruebas propias.

## Ejecución

`procedimiento.sh` v2.2.0 acepta cualquier YAML compatible mediante `DDD_PARAMS` y deriva `run_name` desde el propio YAML. El workflow GitHub actual de Aragón se conserva por compatibilidad; su generalización para seleccionar territorio será una de las primeras tareas al iniciar Castilla y León.

## Gobernanza

- Estado canónico: `README.md` + `docs/ESTADO_MAESTRO_PROYECTO.md`.
- Continuidad general: `docs/CONTINUIDAD_NUEVO_CHAT.md`.
- Continuidad Castilla y León: `docs/CONTINUIDAD_CASTILLA_Y_LEON.md`.
- Arquitectura multi-territorio: `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.
- Contrato: `docs/CONTRATO_TERRITORIO.md`.
- Versiones retiradas: `legacy/`.
- Rama permanente: únicamente `main`.

**Principio rector:** un resultado que solo existe en memoria, un chat o un log no forma parte del procedimiento hasta quedar materializado, versionado y validado en GitHub.
