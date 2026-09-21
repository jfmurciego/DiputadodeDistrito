# Diputado de Distrito — motor multi-territorio

**README v4.9.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-09-21T16:05:40.138842+00:00 · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **1** | Galicia |
| **Generación territorial validada** | 🟢 **2** | Galicia · Principado de Asturias |
| **Preparados para continuar** | 🔵 **2** | Castilla y León · Extremadura |
| **Validación pendiente** | 🟡 **2** | Aragón · La Rioja |
| **Pendientes o no incorporados** | ⚪/🔴 **13** | Andalucía · Canarias · Cantabria · Castilla-La Mancha · Cataluña · Ceuta · Comunidad de Madrid · Comunidad Foral de Navarra · Comunidad Valenciana · Islas Baleares · Melilla · País Vasco · Región de Murcia |

## Estado actual por territorio

FT = **fuentes territoriales** · G = **generación territorial** · FE = **fuentes electorales** · RE = **incorporación de resultados electorales**

| Territorio | FT | G | FE | RE | Estado |
|---|:---:|:---:|:---:|:---:|---|
| **Andalucía** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Aragón** | 🟡 | 🟡 | 🟡 | 🟡 | Validación pendiente |
| **Canarias** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporado |
| **Cantabria** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Castilla y León** | 🟢 | 🟡 | 🟡 | 🟡 | Fuentes territoriales preparadas |
| **Castilla-La Mancha** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Cataluña** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Ceuta** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad de Madrid** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad Foral de Navarra** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad Valenciana** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Extremadura** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | Cadena completa validada |
| **Islas Baleares** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporado |
| **La Rioja** | ⚪ | 🟡 | ⚪ | ⚪ | Puerta de validación pendiente |
| **Melilla** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **País Vasco** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Principado de Asturias** | 🟢 | 🟢 | ⚪ | ⚪ | Generación territorial validada |
| **Región de Murcia** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |

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
