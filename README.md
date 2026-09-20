# Diputado de Distrito — motor multi-territorio

**README v4.8.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO-OPERATIVO:INICIO -->
# Estado operativo del proyecto

**Fuente de verdad:** catálogo y evidencias durables del repositorio. Este bloque se genera automáticamente.

**Semáforo:** 🟢 completo · 🟡 parcial / pendiente de validación · 🔴 no incorporado / bloqueado · ⚪ no iniciado

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadenas completas** | 🟢 **1** | Galicia |
| **Generación territorial validada** | 🟢 **1** | Galicia |
| **Preparados para continuar** | 🔵 **3** | Aragón · Castilla y León · Extremadura |
| **Revalidación / validación pendiente** | 🟡 **1** | La Rioja |
| **Pendientes o bloqueados** | ⚪/🔴 **14** | Andalucía · Canarias · Cantabria · Castilla-La Mancha · Cataluña · Ceuta · Comunidad de Madrid · Comunidad Foral de Navarra · Comunidad Valenciana · Islas Baleares · Melilla · País Vasco · Principado de Asturias · Región de Murcia |

## Estado actual por territorio

FT = **fuentes territoriales** · FE = **fuentes electorales** · G = **generación territorial** · RE = **incorporación de resultados electorales**

| Territorio | FT | FE | G | RE | Estado |
|---|:---:|:---:|:---:|:---:|---|
| **Andalucía** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Aragón** | 🟢 | 🟢 | 🟡 | 🟡 | Fuentes territoriales preparadas |
| **Canarias** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporado |
| **Cantabria** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Castilla y León** | 🟢 | 🟢 | 🟡 | 🟡 | Fuentes territoriales preparadas |
| **Castilla-La Mancha** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Cataluña** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Ceuta** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad de Madrid** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad Foral de Navarra** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad Valenciana** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Extremadura** | 🟢 | 🟡 | 🟡 | ⚪ | Fuentes territoriales preparadas |
| **Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | Producto electoral incorporado |
| **Islas Baleares** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporado |
| **La Rioja** | ⚪ | ⚪ | 🟡 | ⚪ | Puerta de validación pendiente |
| **Melilla** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **País Vasco** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Principado de Asturias** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Región de Murcia** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |

## Cadena automática

01 Preparación de Datos Territoriales → **Puerta de validación territorial** → 02 Generación de Distritos Autonómicos → **Puerta de validación de generación** → 03 Preparación de Resultados Electorales → **Puerta de validación electoral** → 04 Incorporación de Resultados Electorales → **Puerta de validación del producto** → 05 Publicación del Visor.

**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales. La publicación es una operación de despliegue y no añade un estado territorial adicional.

## Última cadena validada

### 🟢 Galicia

| Métrica | Valor |
|---|---|
| **Run** | 35533666934 |
| **Etapa** | M08 |
| **Certificación** | PASS_WITH_GOVERNED_EXCEPTIONS |
| **Edición** | 2025 |

<!-- DDD:ESTADO-OPERATIVO:FIN -->

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
