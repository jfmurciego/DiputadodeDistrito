# Diputado de Distrito — motor multi-territorio

**README v4.9.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-10-31T21:25:58.183167+00:00 · País: **ES · España** · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **19** | 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Congreso Huesca |
| **Generación territorial validada** | 🟢 **26** | 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Congreso Ávila · Congreso Cuenca · Congreso Guadalajara · Congreso Huesca · Congreso Segovia · Congreso Soria · Congreso Teruel · Congreso Zamora |
| **Preparados para continuar** | 🔵 **7** | 01 Andalucía · Congreso Albacete · Congreso Lugo · Congreso Palencia · Congreso Santa Cruz de Tenerife · Congreso Ceuta · Congreso Melilla |
| **Validación pendiente** | 🟡 **36** | Congreso Álava · Congreso Alicante · Congreso Almería · Congreso Badajoz · Congreso Barcelona · Congreso Burgos · Congreso Cáceres · Congreso Cádiz · Congreso Castellón · Congreso Ciudad Real · Congreso Córdoba · Congreso La Coruña · Congreso Gerona · Congreso Granada · Congreso Guipúzcoa · Congreso Huelva · Congreso Jaén · Congreso León · Congreso Lérida · Congreso La Rioja · Congreso Madrid · Congreso Málaga · Congreso Murcia · Congreso Navarra · Congreso Orense · Congreso Asturias · Congreso Pontevedra · Congreso Salamanca · Congreso Cantabria · Congreso Sevilla · Congreso Tarragona · Congreso Toledo · Congreso Valencia · Congreso Valladolid · Congreso Vizcaya · Congreso Zaragoza |
| **Pendientes o no incorporados** | ⚪/🔴 **0** | — |

## Estado actual por territorio

FT = **fuentes territoriales (01)** · G = **generación territorial (02)** · FE = **fuentes electorales (03)** · RE = **incorporación de resultados electorales (04)** · PUB = **publicación del visor (05)**

| Territorio | FT | G | FE | RE | PUB | Estado | Última ejecución | Parada en | Motivo | Siguiente paso |
|---|:---:|:---:|:---:|:---:|:---:|---|---|---|---|---|
| **01 Andalucía** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 40972059931 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | generar y validar distritos |
| **02 Aragón** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979465420 · SUCCESS | — | — | — |
| **03 Principado de Asturias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979477771 · SUCCESS | — | — | — |
| **04 Islas Baleares** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41033500476 · SUCCESS | — | — | — |
| **05 Canarias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41062557004 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | — |
| **06 Cantabria** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41195453629 · SUCCESS | — | — | — |
| **07 Castilla y León** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979527162 · SUCCESS | — | — | — |
| **08 Castilla-La Mancha** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979540141 · SUCCESS | — | — | — |
| **09 Cataluña** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41062562553 · SUCCESS | — | — | — |
| **10 Comunidad Valenciana** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41062567297 · SUCCESS | — | — | — |
| **11 Extremadura** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41195457038 · SUCCESS | — | — | — |
| **12 Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41044499258 · SUCCESS | — | — | — |
| **13 Comunidad de Madrid** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41046373806 · SUCCESS | — | — | — |
| **14 Región de Murcia** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41062572613 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | — |
| **15 Comunidad Foral de Navarra** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41049986588 · SUCCESS | — | — | — |
| **16 País Vasco** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979640315 · SUCCESS | — | — | — |
| **17 La Rioja** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40979652189 · SUCCESS | — | — | — |
| **18 Ceuta** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41062577400 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | — |
| **19 Melilla** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 41062581404 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | — |
| **Congreso Álava** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Albacete** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Alicante** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Almería** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Ávila** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41235278274 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Badajoz** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Barcelona** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Burgos** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Cáceres** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Cádiz** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Castellón** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Ciudad Real** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Córdoba** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso La Coruña** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Cuenca** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Gerona** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Granada** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Guadalajara** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236816482 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Guipúzcoa** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Huelva** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Huesca** | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | Cadena completa validada | 41194447427 · FAILED | 05 · Publicación del Visor | ver log del run | — |
| **Congreso Jaén** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso León** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Lérida** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso La Rioja** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Lugo** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Madrid** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Málaga** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Murcia** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Navarra** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Orense** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Asturias** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Palencia** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41235453115 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Pontevedra** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Salamanca** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Santa Cruz de Tenerife** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Cantabria** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Segovia** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41235620157 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Sevilla** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Soria** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Tarragona** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Teruel** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41235966858 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Toledo** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Valencia** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Valladolid** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Vizcaya** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Zamora** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236140669 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Zaragoza** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Ceuta** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Melilla** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |

## Cadena automática

01 Preparación territorial → **Puerta de validación** → 02 Generación territorial → **Puerta de validación** → 03 Preparación electoral → **Puerta de validación** → 04 Incorporación electoral → **Puerta de validación** → 05 Publicación opcional

**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales.

<!-- DDD:ESTADO:FIN -->

## Arquitectura

Un repositorio, una rama permanente (`main`), un motor común (`ddd_core/`, `modulos/`, `herramientas/`) y contratos territoriales declarativos en `territorios/<id>/`.

La cadena funcional mantiene la separación entre:

1. **preparación territorial reutilizable**;
2. **preparación electoral independiente**;
3. **generación territorial**;
4. **incorporación posterior de resultados electorales**.

Las etapas semánticas G10 preservan la compatibilidad con M01–M08 y permiten reenganche sin recalcular productos certificados.

## Productos y operación

- `resultados/finales/` contiene las fuentes canónicas de visualización.
- Los productos pesados se conservan como artefactos reproducibles de GitHub Actions.
- Una evidencia idéntica debe poder reutilizarse sin repetir cálculo.
- Toda sustitución importante conserva el predecesor en `legacy/`.
- El detalle operativo está en `docs/INVENTARIO_OPERATIVO.md`.
- El punto de reenganche está en `docs/SALIDAS_CHATGPT/PUNTO_REENGANCHE.md`.

---

**19 territorios monitorizados** · **1 cadena territorial validada en la automatización vigente** · **README = tablero operativo de entrada**
