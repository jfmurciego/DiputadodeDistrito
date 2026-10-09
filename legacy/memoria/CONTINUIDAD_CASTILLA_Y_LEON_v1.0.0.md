# Continuidad — Castilla y León — nuevo hilo

**Versión:** 1.0.0
**Fecha:** 2026-09-11
**Estado:** listo para iniciar nueva implantación

## 1. Mandato

Continuar el proyecto `jfmurciego/DiputadodeDistrito` desde el estado R018 y crear la segunda implantación territorial: **Castilla y León**. No crear otro repositorio, no crear una rama permanente y no copiar/forkear el motor de Aragón. Trabajar sobre `main`; si una rama técnica temporal es imprescindible, integrarla y borrarla.

La misión de Castilla y León no es solo producir un mapa. Es **probar la generalidad del motor DDD** y detectar qué supuestos actualmente embebidos en código/configuración son realmente aragoneses y deben convertirse en contrato genérico.

## 2. Fuente de verdad

GitHub manda sobre el chat. Antes de modificar código leer:

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.
4. `docs/CONTRATO_TERRITORIO.md`.
5. este documento.
6. `territorios/castilla_y_leon/README.md`.
7. `docs/MODULOS/README.md` y contratos M01–M08.
8. `docs/POLITICA_DE_VERSIONES.md`.
9. baseline Aragón Run #9: `docs/EJECUCIONES/GITHUB_RUN_0009_2026-09-11.md`.

## 3. Estado heredado que NO debe perderse

Aragón es la implantación de referencia validada. Baseline territorial vigente: GitHub Run #9 `34599224954`, producto `gh-34599224954-1`, ejecutado sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`.

Resultado Aragón:
- 67 distritos;
- 1.463 secciones;
- 1.364.621 habitantes;
- Huesca 11 / Teruel 7 / Zaragoza 49;
- provincia: PASS;
- contigüidad: PASS;
- disciplina municipal: PASS;
- suelo 0,80×target: PASS;
- techo 1,75×target: PASS;
- distritos fuera de ±12 %: 0;
- máximo desvío relativo: 9,930 %.

M05 v7.4.0 es la lógica validada. En Run #9 alcanzó la primera solución factible en iteración 9.038 con máximo desvío 11,943 %, continuó hasta 20.000 iteraciones y acabó en 9,930 %. No relajar esas invariantes de Aragón ni modificar su baseline para facilitar Castilla y León.

R015 aporta suite automática de regresión, determinismo y gobernanza. Cualquier cambio al motor común debe mantener la CI verde y no degradar Aragón.

## 4. Arquitectura R018

Motor común:
- `ddd_core/`
- `modulos/`
- `herramientas/`
- `procedimiento.sh`

Paquetes territoriales:
- `territorios/aragon/`
- `territorios/castilla_y_leon/`

Aragón conserva rutas históricas de compatibilidad (`configuracion/`, `inputs/`, `resultados/ejecuciones/`) porque el workflow validado todavía las usa. No eliminarlas hasta que el workflow multi-territorio reproduzca Run #9.

`procedimiento.sh` v2.2.0 ya deriva `run_name` desde el YAML y elimina el nombre duro `aragon_2025` de la caché. La parte todavía especializada en Aragón es principalmente `.github/workflows/procedimiento-ddd.yml` y algunas convenciones de fuentes/configuración.

## 5. Objetivo inmediato Castilla y León

No empezar por M04/M05. Primero construir correctamente M01–M03.

Orden obligatorio:

### Fase CYL-01 — inventario de fuentes
Identificar y documentar:
- seccionado censal oficial más reciente compatible;
- población por sección con año y universo claros;
- claves de provincia, municipio y sección;
- geometría/CRS;
- divisiones administrativas útiles;
- resultados electorales, solo para M07–M08 y nunca para geometría.

Preferir fuentes oficiales reproducibles. Registrar URL/origen, fecha, checksum y transformación.

### Fase CYL-02 — contrato territorial
Completar `territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml` y documentación asociada conforme a `docs/CONTRATO_TERRITORIO.md`.

No copiar automáticamente valores de Aragón. Deben decidirse y documentarse para Castilla y León:
- K total de distritos;
- reparto provincial si las provincias son barrera;
- método de reparto;
- suelo/techo;
- tolerancia fina;
- regla municipal;
- tratamiento de municipios/capitales sobredimensionados;
- posibles islas/exclaves o singularidades de contigüidad.

### Fase CYL-03 — generalizar workflow
Convertir el workflow territorial en seleccionable por paquete/configuración o crear un único workflow genérico que reciba `territorio`/`params`. Debe seguir reproduciendo Aragón y no contener lógica duplicada por comunidad.

### Fase CYL-04 — M01
Ejecutar solo preparación base y validar:
- número exacto de secciones de Castilla y León;
- población total;
- CUSEC/clave equivalente única y no nula;
- provincias correctas;
- ausencia de pérdidas silenciosas.

### Fase CYL-05 — M02/M03
Construir adyacencias y grafo. Auditar componentes desconectados, errores de geometría, enclaves y criterios de `touches/shared border` antes de generar distritos.

Solo cuando M01–M03 estén aceptados abrir M04.

## 6. Reglas de ingeniería

- Si aparece un supuesto específico de Aragón en código común, no parchearlo con `if castilla_y_leon`; extraer un concepto genérico/configurable.
- No mezclar varias correcciones grandes en una versión.
- Antes de sustituir un fichero versionado, guardar el predecesor exacto en `legacy/`.
- Cabecera: versión, nombre, fecha, qué hace, cambios, motivo, anterior/origen.
- Registrar progreso en Bitácora y Registro de Cambios.
- GitHub Actions reproducible es evidencia; pruebas locales/IA son diagnóstico.
- No usar resultados electorales para construir la geometría.

## 7. Qué NO hacer

- No crear `DiputadodeDistrito-CastillaLeon`.
- No crear una rama permanente `castilla-y-leon`.
- No copiar `modulos/` dentro del territorio.
- No editar Aragón para que “se parezca” a Castilla y León.
- No asumir que 0,80 / 1,75 / ±12 %, Hamilton o reglas municipales son universales sin decisión explícita.
- No avanzar a optimización si el grafo de base no está auditado.

## 8. Criterio de éxito de esta segunda implantación

El objetivo no es solo un PASS de Castilla y León. Debe quedar claro qué porcentaje del trabajo fue:
- datos/configuración territorial;
- generalización reusable del motor;
- código específico inevitable.

La señal de madurez será que el tercer territorio, Extremadura, requiera sustancialmente menos cambios comunes.

## 9. Estado del paquete al abrir el hilo

Existe `territorios/castilla_y_leon/` con carpetas lógicas `config/`, `inputs/`, `docs/` y `tests/`. La plantilla YAML es deliberadamente incompleta y no debe ejecutarse como si fuera configuración validada. Primero resolver fuentes y parámetros.

## 10. Primera respuesta esperada en el nuevo hilo

Al comenzar, auditar el paquete y el motor y devolver, en lenguaje claro:
1. qué información/fuentes de Castilla y León ya están disponibles en el proyecto o fuentes del chat;
2. qué falta;
3. qué supuestos de Aragón impiden hoy una ejecución genérica;
4. cuál es el menor cambio seguro para ejecutar M01 de Castilla y León sin romper Aragón.

Después avanzar directamente, documentando cada ronda.

## 11. Aragón queda abierto por separado

Este nuevo hilo no cierra Aragón. En el hilo actual queda pendiente R017: auditoría fina de calidad territorial del Run #9 (compactación, cuellos, tentáculos, fronteras naturales y agrupación administrativa). No mezclar esa optimización fina con el arranque de Castilla y León.
