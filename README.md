# Diputado de Distrito — motor de distritos uninominales

**README rev. 5.0.0-r0** (BORRADOR para el corte 5.0.0; revisión del documento)  
**Anterior:** `legacy/docs/README_v4.9.0-r2.md`

[![DOI de concepto](https://zenodo.org/badge/DOI/10.5281/zenodo.24093967.svg)](https://doi.org/10.5281/zenodo.24093967) Serie de versiones de mapa publicadas en Zenodo; no es la cita del proyecto entero. Cada depósito contiene el código fuente del repositorio en esa versión, no el paquete firmado `.tar.gz`.

## Qué es

Diputado de Distrito (DDD) es un **motor modular y reproducible** que construye, optimiza, valida y audita distritos uninominales a partir de unidades censales oficiales (secciones del INE). El producto es el motor/generador de distritos; los mapas que produce son un ejercicio de investigación y **no tienen valor oficial**.

La geometría de los distritos nunca depende de los resultados electorales: estos se incorporan después, sobre el mapa ya generado.

El estado operativo por territorio no está en este documento: lo genera el sistema en `docs/ESTADO.md` y en el dashboard (`dashboard/`).

<!-- DDD:ESTADO:INICIO -->
<!-- DDD:ESTADO:FIN -->

## El motor: Deslinde 1.0

Deslinde 1.0 es la delimitación reproducible de distritos: **trazado canónico + 10 cadenas ReCom + elección D8 + mapa vigente como candidato**. Definición formal, con cita a código: `docs/ARQUITECTURA/DESLINDE_1_0.md`.

- **Trazado canónico**: el M06 que produce la cadena modular (M01–M06) del propio run.
- **10 cadenas ReCom ponderado** de GerryChain (N=10), con semillas públicas derivadas del sha256 del padrón y del seccionado y del código oficial del territorio (`configuracion/notacion_territorial.csv`). No usa semilla fija.
- **Reglas núcleo** (`ddd_motor2/reglas/`): una sola definición ejecutable de «plan válido» (K distritos, suelo y techo de población, contigüidad, provincia única, disciplina municipal, núcleos cerrados), tomada del contrato del territorio. Nunca se publica un plan inválido.
- **Elección D8**: orden lexicográfico entre candidatos (válido, distritos fuera de tolerancia, exceso sobre el 8 % de desvío, partidos judiciales y comarcas agrarias repartidos, frontera cortada, desvío máximo, huella del plan). El tope del 8 % sirve para elegir, no es regla.
- **Mapa vigente como candidato**: `datos/composicion/<territorio>.csv` compite con el resto; si incumple el núcleo, se intenta una reparación mínima y determinista.
- **Implementación**: «motor 2», en `ddd_motor2/`. Los ensembles de planes alternativos están en `ddd_ensemble/` y `docs/ENSEMBLES_GERRYCHAIN.md`.

Límites (ver §7 de `DESLINDE_1_0.md`): el ganador es el mejor de un conjunto finito de candidatos, no un óptimo demostrado; y la reproducibilidad bit a bit exige las mismas entradas, `PYTHONHASHSEED=0` y el mismo entorno.

## Arquitectura y ejecución

Un repositorio, una rama permanente (`main`), un motor común (`ddd_core/`, `modulos/`, `herramientas/`, `ddd_motor2/`) y contratos territoriales declarativos en `territorios/<id>/`. La cadena mantiene separadas la preparación territorial, la preparación electoral, la generación territorial y la incorporación posterior de resultados (módulos M01–M08). Fases P00–P60: `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md`; visión multiterritorio: `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.

Se ejecuta con flujos de GitHub Actions (`.github/workflows/`):

| Fase | Flujo | Fichero |
|---|---|---|
| P00 | **P00 Campaña**: ejecución completa de un territorio | `ejecucion-completa-proyecto.yml` |
| P00 | **P00 Campaña — Gestor**: planifica (modo plan) y lanza campañas (nacional, autonómicas, provincias); guía en `docs/GUIA_GESTOR_CAMPANAS.md` | `gestor-campanas.yml` |
| P50 | **P50 Publicación**: despliegue del visor público | `desplegar-visor-publico.yml` |

El visor solo muestra lo registrado en `orchestracion/publicaciones_visor.json`. Guía operativa: `docs/INVENTARIO_OPERATIVO.md`.

## Estructura de carpetas

| Carpeta | Contenido |
|---|---|
| `ddd_core/`, `modulos/` | Núcleo y módulos M01–M08 de la cadena |
| `ddd_motor2/` | Motor 2 (Deslinde 1.0): reglas, candidatos, competición, semilla |
| `ddd_ensemble/` | Ensembles de planes alternativos |
| `herramientas/` | Scripts de operación, auditoría y baterías |
| `territorios/` | Contrato, entradas, resultados y evidencias por territorio |
| `configuracion/`, `schemas/` | Política de generación, tablas maestras y esquemas |
| `fuentes/`, `inputs/` | Catálogo de fuentes oficiales y entradas con sha256 |
| `datos/` | Composición del mapa vigente y resultados electorales |
| `datos_abiertos/` | Paquete de datos abiertos (ver abajo) |
| `orchestracion/` | Campañas, catálogo de procedencia, registro de publicaciones |
| `visor/`, `dashboard/` | Visor público y dashboard |
| `documentacion_publica/` | Sitio de documentación |
| `docs/` | Arquitectura, guías, estudios y registro de cambios |
| `tests/`, `evals/` | Pruebas y conjunto de oro |
| `legacy/` | Copias anteriores de los ficheros versionados |

## Datos abiertos

`datos_abiertos/` contiene, por territorio, los distritos en GeoJSON, el ganador por distrito de las generales de 2023 en CSV y una ficha estática de cada distrito. `datos_abiertos/INDEX.json` recoge run de origen y sha256 de cada fichero. Detalle y licencia: `datos_abiertos/README.md`.

## Cómo reproducir

1. Las dependencias están fijadas en los ficheros `requirements*.lock` y el entorno en el `Dockerfile`.
2. En local, con Docker: `./ddd-local.sh comprobar` y `./ddd-local.sh construir`; el resto de operaciones están en `docs/INSTALACION_LOCAL.md`.
3. La ejecución territorial se lanza con «P00 Campaña» o con el Gestor (arriba). El motor se ejecuta con `PYTHONHASHSEED=0`; sin él, `competir` falla cerrado.
4. Los datos abiertos se verifican con `sha256sum` contra `datos_abiertos/INDEX.json`.
5. Pruebas: `python -m unittest discover tests`.

## Fuentes oficiales y licencias

- **INE**: secciones censales, seccionado y padrón. Sus códigos territoriales están en `fuentes/ine_codigos_territoriales_2026-11-10/` con `SHA256SUMS`.
- **Ministerio del Interior (Infoelectoral)**: resultados electorales.
- **BOE**: escaños y normativa electoral.
- Catálogo de fuentes: `fuentes/catalogo_oficial.yaml`; las entradas de cada territorio llevan su sha256 en el contrato (`generation_state.source_inputs`).
- Otros componentes: GitHub (repositorio y Actions), Cloudflare R2 (archivo de artefactos), GerryChain, MapLibre y OpenStreetMap (visor), Zensical (documentación), Zenodo y ORCID (archivo y citación), Sigstore (firma y atestación).

Las fuentes oficiales conservan sus propias condiciones de reutilización.

- **Código**: Apache-2.0 (`LICENSE`).
- **Datos** (`datos_abiertos/`): CC BY 4.0, citando «Diputado de Distrito» y el run de procedencia.

## Cómo citar

Jesus Murciego (Independent researcher). *Diputado de Distrito: motor reproducible de distritos uninominales*. Software, versión 4.9.0 (la versión citada sigue a `CITATION.cff`; se actualiza en el corte 5.0.0). <https://github.com/jfmurciego/DiputadodeDistrito>.

Metadatos en `CITATION.cff` y `.zenodo.json`. Serie de versiones de mapa en Zenodo: DOI de concepto (resuelve a la última; no es la cita del proyecto entero) [10.5281/zenodo.24093967](https://doi.org/10.5281/zenodo.24093967). Para citar un mapa concreto, usa su DOI de versión; el depósito vigente es [10.5281/zenodo.24093968](https://doi.org/10.5281/zenodo.24093968). El depósito contiene el código fuente de esa versión; el paquete firmado y su manifiesto están en la Release de GitHub.
