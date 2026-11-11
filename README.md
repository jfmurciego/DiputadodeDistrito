# Diputado de Distrito — motor de distritos uninominales

**README rev. 4.9.0-r2** (revisión del documento; versión del proyecto 4.9.0) · 10-11-2026 · Estado: **motor ejecutable; mapas de Congreso publicados; trabajo en curso en el motor nuevo y el histórico autonómico**  
**Anterior:** `legacy/docs/README_v4.9.0-r1.md`

[![DOI de concepto](https://zenodo.org/badge/DOI/10.5281/zenodo.24093967.svg)](https://doi.org/10.5281/zenodo.24093967) Serie de versiones de mapa publicadas en Zenodo (hoy solo Congreso Huesca 1.0.0); no es la cita del proyecto entero. Cada depósito contiene el código fuente del repositorio en esa versión, no el paquete firmado `.tar.gz`.

## Qué es

Diputado de Distrito (DDD) es un **motor modular y reproducible** que construye, optimiza, valida y audita distritos uninominales a partir de unidades censales oficiales (secciones del INE). El producto es el motor/generador de distritos; los mapas que produce son un ejercicio de investigación y **no tienen valor oficial**.

La geometría de los distritos nunca depende de los resultados electorales: estos se incorporan después, sobre el mapa ya generado.

## Estado a 10-11-2026

Cifras comprobadas en el repositorio:

- **Publicadas** en `orchestracion/publicaciones_visor.json`: las **19 comunidades** (17 comunidades autónomas, Ceuta y Melilla) y las **52 circunscripciones** del Congreso (50 provincias, Ceuta y Melilla), cada una con su mapa territorial y su resultado de 2023 (71 territorios en total).
- **Histórico de generales** en `datos/resultados/historico/`: 6 elecciones (2011-11, 2015-12, 2016-06, 2019-04, 2019-11 y 2023-07), con ganador y votos por partido por distrito para las 52 circunscripciones, y rotación por distrito en `rotacion/`.
- **Visor**: v1 en la raíz del sitio (`visor/`) y v2 en `/v2/` (`visor/v2/`).
- **Datos abiertos** por provincia en `datos_abiertos/` (52 provincias; `INDEX.json` con sha256 de cada fichero): distritos en GeoJSON, ganador por distrito de las generales de 2023 en CSV y ficha estática de cada distrito.

En desarrollo (no se dan por hechos): el **motor nuevo**, el **histórico autonómico** (hay datos en `datos/resultados/historico/autonomicas/` solo para algunas comunidades) y la ampliación del mapa de Congreso de 350 diputados a todas las provincias.

El detalle por territorio es el bloque siguiente, que genera el sistema:

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-11-11T03:59:22.145012+00:00 · País: **ES · España** · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **25** | 01 Andalucía · 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Nacional Albacete · Nacional Almería · Nacional Ávila · Nacional Badajoz · Nacional La Rioja · Nacional 350 Madrid · Nacional 350 Soria · Nacional 350 Valladolid |
| **Generación territorial validada** | 🟢 **74** | 01 Andalucía · 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Nacional Álava · Nacional Albacete · Nacional Alicante · Nacional Almería · Nacional Ávila · Nacional Badajoz · Nacional Baleares · Nacional Barcelona · Nacional Burgos · Nacional Cáceres · Nacional Cádiz · Nacional Castellón · Nacional Ciudad Real · Nacional Córdoba · Nacional La Coruña · Nacional Cuenca · Nacional Gerona · Nacional Granada · Nacional Guadalajara · Nacional Guipúzcoa · Nacional Huelva · Nacional Huesca · Nacional Jaén · Nacional León · Nacional Lérida · Nacional La Rioja · Nacional Lugo · Nacional Madrid · Nacional Málaga · Nacional Murcia · Nacional Navarra · Nacional Orense · Nacional Asturias · Nacional Palencia · Nacional Las Palmas · Nacional Pontevedra · Nacional Salamanca · Nacional Santa Cruz de Tenerife · Nacional Cantabria · Nacional Segovia · Nacional Sevilla · Nacional Soria · Nacional Tarragona · Nacional Teruel · Nacional Toledo · Nacional Valencia · Nacional Valladolid · Nacional Vizcaya · Nacional Zamora · Nacional Zaragoza · Nacional Ceuta · Nacional Melilla · Nacional 350 Madrid · Nacional 350 Soria · Nacional 350 Valladolid |
| **Preparados para continuar** | 🔵 **0** | — |
| **Validación pendiente** | 🟡 **46** | Nacional 350 Álava · Nacional 350 Albacete · Nacional 350 Alicante · Nacional 350 Almería · Nacional 350 Ávila · Nacional 350 Badajoz · Nacional 350 Barcelona · Nacional 350 Burgos · Nacional 350 Cáceres · Nacional 350 Cádiz · Nacional 350 Castellón · Nacional 350 Ciudad Real · Nacional 350 Córdoba · Nacional 350 La Coruña · Nacional 350 Cuenca · Nacional 350 Gerona · Nacional 350 Granada · Nacional 350 Guadalajara · Nacional 350 Guipúzcoa · Nacional 350 Huelva · Nacional 350 Huesca · Nacional 350 Jaén · Nacional 350 León · Nacional 350 Lérida · Nacional 350 La Rioja · Nacional 350 Lugo · Nacional 350 Málaga · Nacional 350 Murcia · Nacional 350 Navarra · Nacional 350 Orense · Nacional 350 Asturias · Nacional 350 Palencia · Nacional 350 Pontevedra · Nacional 350 Salamanca · Nacional 350 Cantabria · Nacional 350 Segovia · Nacional 350 Sevilla · Nacional 350 Tarragona · Nacional 350 Teruel · Nacional 350 Toledo · Nacional 350 Valencia · Nacional 350 Vizcaya · Nacional 350 Zamora · Nacional 350 Zaragoza · Nacional 350 Ceuta · Nacional 350 Melilla |
| **Pendientes o no incorporados** | ⚪/🔴 **0** | — |

## Estado actual por territorio

FT = **fuentes territoriales (01)** · G = **generación territorial (02)** · FE = **fuentes electorales (03)** · RE = **incorporación de resultados electorales (04)** · PUB = **publicación del visor (05)**

| Territorio | FT | G | FE | RE | PUB | Estado | Última ejecución | Parada en | Motivo | Siguiente paso |
|---|:---:|:---:|:---:|:---:|:---:|---|---|---|---|---|
| **01 Andalucía** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42495072594 · SUCCESS | — | — | — |
| **02 Aragón** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42497101869 · SUCCESS | — | — | — |
| **03 Principado de Asturias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979477771 · SUCCESS | — | — | — |
| **04 Islas Baleares** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41033500476 · SUCCESS | — | — | — |
| **05 Canarias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42523951377 · SUCCESS | — | — | — |
| **06 Cantabria** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42707820760 · SUCCESS | 03/04 · rama electoral omitida | 03 produjo una fuente válida, pero no existe prepared_source_pair acreditado para M07/M08 | activar par de fuentes (Activación de Legislatura Vigente) y reutilizar |
| **07 Castilla y León** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42531122768 · SUCCESS | — | — | — |
| **08 Castilla-La Mancha** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979540141 · SUCCESS | — | — | — |
| **09 Cataluña** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41062562553 · SUCCESS | — | — | — |
| **10 Comunidad Valenciana** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41062567297 · SUCCESS | — | — | — |
| **11 Extremadura** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42720735134 · SUCCESS | 03/04 · rama electoral omitida | 03 produjo una fuente válida, pero no existe prepared_source_pair acreditado para M07/M08 | activar par de fuentes (Activación de Legislatura Vigente) y reutilizar |
| **12 Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41044499258 · SUCCESS | — | — | — |
| **13 Comunidad de Madrid** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41046373806 · SUCCESS | — | — | — |
| **14 Región de Murcia** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42504383790 · SUCCESS | — | — | — |
| **15 Comunidad Foral de Navarra** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41049986588 · SUCCESS | — | — | — |
| **16 País Vasco** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979640315 · SUCCESS | — | — | — |
| **17 La Rioja** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42920452778 · SUCCESS | — | — | — |
| **18 Ceuta** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42503542766 · SUCCESS | — | — | — |
| **19 Melilla** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42504386196 · SUCCESS | — | — | — |
| **Nacional Álava** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940320710 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Albacete** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42952791883 · SUCCESS | — | — | — |
| **Nacional Alicante** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940331557 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Almería** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42952468083 · SUCCESS | — | — | — |
| **Nacional Ávila** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42948760863 · SUCCESS | — | — | — |
| **Nacional Badajoz** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42949289470 · SUCCESS | — | — | — |
| **Nacional Baleares** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940350970 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Barcelona** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940355981 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Burgos** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41299221887 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Cáceres** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940366579 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Cádiz** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940371696 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Castellón** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940377493 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Ciudad Real** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940382446 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Córdoba** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940387433 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional La Coruña** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940392520 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Cuenca** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940397668 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Gerona** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940402050 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Granada** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940407337 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Guadalajara** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940412378 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Guipúzcoa** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940417361 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Huelva** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940422226 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional Huesca** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42519383275 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Jaén** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42940432935 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Nacional León** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41629735636 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Lérida** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41299033915 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional La Rioja** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42935762636 · SUCCESS | — | — | — |
| **Nacional Lugo** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42514986960 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Madrid** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41622703086 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Málaga** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42495070976 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Murcia** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41622862185 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Navarra** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41299128213 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Orense** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41295142111 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Asturias** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41296638877 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Palencia** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41298660623 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Las Palmas** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41442913288 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Pontevedra** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41353894475 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Salamanca** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41295298674 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Santa Cruz de Tenerife** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42519017008 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Cantabria** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41356175674 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Segovia** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41241846017 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Sevilla** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41297168461 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Soria** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41250310066 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Tarragona** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42514991952 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Teruel** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41250394074 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Toledo** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41296268720 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Valencia** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42525625044 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Valladolid** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41299313598 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Vizcaya** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41356074013 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Zamora** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41250479211 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Zaragoza** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41296815536 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Ceuta** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 42496569312 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional Melilla** | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | Generación territorial validada | 41293988485 · SUCCESS | — | — | preparar fuentes electorales |
| **Nacional 350 Álava** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Albacete** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Alicante** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Almería** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Ávila** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Badajoz** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Barcelona** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Burgos** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Cáceres** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Cádiz** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Castellón** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Ciudad Real** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Córdoba** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 La Coruña** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Cuenca** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Gerona** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Granada** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Guadalajara** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Guipúzcoa** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Huelva** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Huesca** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Jaén** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 León** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Lérida** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 La Rioja** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Lugo** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Madrid** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42599356804 · SUCCESS | — | — | — |
| **Nacional 350 Málaga** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Murcia** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Navarra** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Orense** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Asturias** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Palencia** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Pontevedra** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Salamanca** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Cantabria** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Segovia** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Sevilla** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Soria** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42612579208 · SUCCESS | — | — | — |
| **Nacional 350 Tarragona** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Teruel** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Toledo** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Valencia** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Valladolid** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 42613899978 · SUCCESS | — | — | — |
| **Nacional 350 Vizcaya** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Zamora** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Zaragoza** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Ceuta** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Nacional 350 Melilla** | 🟡 | 🟡 | ⚪ | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |

## Cadena automática

01 Preparación territorial → **Puerta de validación** → 02 Generación territorial → **Puerta de validación** → 03 Preparación electoral → **Puerta de validación** → 04 Incorporación electoral → **Puerta de validación** → 05 Publicación opcional

**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales.

<!-- DDD:ESTADO:FIN -->

## Arquitectura

Un repositorio, una rama permanente (`main`), un motor común (`ddd_core/`, `modulos/`, `herramientas/`) y contratos territoriales declarativos en `territorios/<id>/`. La cadena mantiene separadas la preparación territorial, la preparación electoral, la generación territorial y la incorporación posterior de resultados (módulos M01–M08). Descripción completa en `docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md` y `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.

## Cómo reproducir

1. Las dependencias están fijadas en los ficheros `requirements*.lock` y el entorno en el `Dockerfile`.
2. En local, con Docker: `./ddd-local.sh comprobar` y `./ddd-local.sh construir`; el resto de operaciones están en `docs/INSTALACION_LOCAL.md`.
3. La ejecución territorial completa se lanza con el flujo de GitHub Actions «00 Ejecución Completa del Proyecto» (`.github/workflows/ejecucion-completa-proyecto.yml`); la guía operativa está en `docs/INVENTARIO_OPERATIVO.md`.
4. Los datos abiertos se verifican con `sha256sum` contra `datos_abiertos/INDEX.json`.
5. Pruebas: `python -m unittest discover tests`.

## Componentes externos en uso

- **INE**: secciones censales, seccionado y padrón.
- **Ministerio del Interior (Infoelectoral)**: resultados electorales.
- **BOE**: escaños y normativa electoral.
- **GitHub** (repositorio y Actions) y **Cloudflare R2** (archivo de artefactos).
- **GerryChain**: optimización y conjuntos de planes alternativos.
- **MapLibre** y **OpenStreetMap**: visor cartográfico.
- **Zensical**: sitio de documentación (`documentacion_publica/`).
- **Zenodo** y **ORCID**: archivo y citación.
- **Sigstore**: firma y atestación de procedencia.

Las fuentes oficiales conservan sus propias condiciones de reutilización.

## Licencias

- **Código**: Apache-2.0 (`LICENSE`).
- **Datos** (`datos_abiertos/`): CC BY 4.0, citando «Diputado de Distrito» y el run de procedencia.

## Cómo citar

Jesus Murciego (Independent researcher). *Diputado de Distrito: motor reproducible de distritos uninominales*. Software, versión 4.9.0. <https://github.com/jfmurciego/DiputadodeDistrito>.

Serie de versiones de mapa en Zenodo: DOI de concepto (resuelve a la última; no es la cita del proyecto entero) [10.5281/zenodo.24093967](https://doi.org/10.5281/zenodo.24093967). Hoy contiene un solo depósito, el mapa Congreso Huesca 1.0.0 (9-11-2026), con DOI de versión [10.5281/zenodo.24093968](https://doi.org/10.5281/zenodo.24093968): para citar ese mapa, usa el DOI de versión. El depósito contiene el código fuente de esa versión; el paquete firmado y su manifiesto están en la Release de GitHub.

Metadatos en `CITATION.cff` y `.zenodo.json`.
