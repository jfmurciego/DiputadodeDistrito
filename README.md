# Diputado de Distrito — motor multi-territorio

**README v4.9.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-10-31T23:21:54.671486+00:00 · País: **ES · España** · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **21** | 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Congreso Ávila · Congreso Huesca · Congreso Segovia |
| **Generación territorial validada** | 🟢 **47** | 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla · Congreso Albacete · Congreso Almería · Congreso Ávila · Congreso Cáceres · Congreso Castellón · Congreso Córdoba · Congreso La Coruña · Congreso Cuenca · Congreso Granada · Congreso Guadalajara · Congreso Huesca · Congreso Jaén · Congreso León · Congreso La Rioja · Congreso Lugo · Congreso Orense · Congreso Asturias · Congreso Salamanca · Congreso Santa Cruz de Tenerife · Congreso Segovia · Congreso Sevilla · Congreso Soria · Congreso Tarragona · Congreso Teruel · Congreso Toledo · Congreso Zamora · Congreso Zaragoza · Congreso Ceuta · Congreso Melilla |
| **Preparados para continuar** | 🔵 **20** | 01 Andalucía · Congreso Álava · Congreso Alicante · Congreso Badajoz · Congreso Barcelona · Congreso Burgos · Congreso Cádiz · Congreso Ciudad Real · Congreso Gerona · Congreso Guipúzcoa · Congreso Lérida · Congreso Madrid · Congreso Málaga · Congreso Murcia · Congreso Navarra · Congreso Palencia · Congreso Pontevedra · Congreso Cantabria · Congreso Valladolid · Congreso Vizcaya |
| **Validación pendiente** | 🟡 **4** | Congreso Baleares · Congreso Huelva · Congreso Las Palmas · Congreso Valencia |
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
| **Congreso Álava** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41240137880 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | generar y validar distritos |
| **Congreso Albacete** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41240260992 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Alicante** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Almería** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41242160179 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Ávila** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41241662219 · SUCCESS | — | — | — |
| **Congreso Badajoz** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41242287390 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Baleares** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Barcelona** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Burgos** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41240386898 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Cáceres** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41240512324 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Cádiz** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Castellón** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41241768943 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Ciudad Real** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41241133485 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Córdoba** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso La Coruña** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Cuenca** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236647382 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Gerona** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41242933360 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Granada** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41243199582 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Guadalajara** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236816482 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Guipúzcoa** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41242557327 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Huelva** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | 41241257412 · FAILED | 01 · Preparación de Datos Territoriales | ver log del run | preparar fuentes territoriales |
| **Congreso Huesca** | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | Cadena completa validada | 41194447427 · FAILED | 05 · Publicación del Visor | ver log del run | — |
| **Congreso Jaén** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41241896061 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso León** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41241377284 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Lérida** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41241496894 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso La Rioja** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41240637295 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Lugo** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41240766116 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Madrid** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | — | — | — | generar y validar distritos |
| **Congreso Málaga** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41244216073 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Murcia** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41244085018 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Navarra** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41242678275 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Orense** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41240887712 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Asturias** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Palencia** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41235453115 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Las Palmas** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | — | — | — | preparar fuentes territoriales |
| **Congreso Pontevedra** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41243452235 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Salamanca** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41241010241 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Santa Cruz de Tenerife** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41239505387 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Cantabria** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41242029481 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Segovia** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada | 41241846017 · SUCCESS | — | — | — |
| **Congreso Sevilla** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Soria** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41235794328 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Tarragona** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Teruel** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41235966858 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Toledo** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41242809451 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Valencia** | 🟡 | 🟡 | 🟡 | ⚪ | ⚪ | Validación pendiente | 41244586540 · FAILED | 01 · Preparación de Datos Territoriales | ver log del run | preparar fuentes territoriales |
| **Congreso Valladolid** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41241636977 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Vizcaya** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 41243819237 · FAILED | 02 · Generación de Distritos Autonómicos | La evidencia habilitante se calculó, pero su validación o persistencia no terminó correctamente. | generar y validar distritos |
| **Congreso Zamora** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236140669 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Zaragoza** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | — | — | — | preparar fuentes electorales |
| **Congreso Ceuta** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236313879 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |
| **Congreso Melilla** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 41236482346 · SUCCESS | 03/04 · rama electoral omitida | alcance territorial solicitado | preparar fuentes electorales |

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
