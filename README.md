# Diputado de Distrito — motor multi-territorio

**README v4.9.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-10-04T15:37:42.914372+00:00 · País: **ES · España** · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **3** | 02 Aragón · 03 Principado de Asturias · 12 Galicia |
| **Generación territorial validada** | 🟢 **7** | 02 Aragón · 03 Principado de Asturias · 07 Castilla y León · 08 Castilla-La Mancha · 11 Extremadura · 12 Galicia · 18 Ceuta |
| **Preparados para continuar** | 🔵 **12** | 01 Andalucía · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 09 Cataluña · 10 Comunidad Valenciana · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 19 Melilla |
| **Validación pendiente** | 🟡 **0** | — |
| **Pendientes o no incorporados** | ⚪/🔴 **0** | — |

## Estado actual por territorio

FT = **fuentes territoriales** · G = **generación territorial** · FE = **fuentes electorales** · RE = **incorporación de resultados electorales**

| Territorio | FT | G | FE | RE | Estado |
|---|:---:|:---:|:---:|:---:|---|
| **01 Andalucía** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **02 Aragón** | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada |
| **03 Principado de Asturias** | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada |
| **04 Islas Baleares** | 🟢 | 🟡 | 🟢 | ⚪ | Fuentes territoriales preparadas |
| **05 Canarias** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **06 Cantabria** | 🟢 | 🟡 | 🟢 | ⚪ | Fuentes territoriales preparadas |
| **07 Castilla y León** | 🟢 | 🟢 | 🟡 | 🟡 | Generación territorial validada |
| **08 Castilla-La Mancha** | 🟢 | 🟢 | 🟢 | 🟡 | Listo para incorporar resultados electorales |
| **09 Cataluña** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **10 Comunidad Valenciana** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **11 Extremadura** | 🟢 | 🟢 | 🟡 | ⚪ | Generación territorial validada |
| **12 Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada |
| **13 Comunidad de Madrid** | 🟢 | 🟡 | 🟢 | ⚪ | Fuentes territoriales preparadas |
| **14 Región de Murcia** | 🟢 | 🟡 | 🟢 | ⚪ | Fuentes territoriales preparadas |
| **15 Comunidad Foral de Navarra** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **16 País Vasco** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **17 La Rioja** | 🟢 | 🟡 | 🟢 | ⚪ | Fuentes territoriales preparadas |
| **18 Ceuta** | 🟢 | 🟢 | 🟢 | 🟡 | Listo para incorporar resultados electorales |
| **19 Melilla** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |

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
