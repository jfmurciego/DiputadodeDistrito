# Diputado de Distrito — motor multi-territorio

**README v4.9.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

<!-- DDD:ESTADO:INICIO -->
# Estado operativo del proyecto

**Estado generado automáticamente desde el catálogo y las evidencias durables. No editar manualmente este bloque.**

Actualizado: 2026-10-29T22:32:16.045264+00:00 · País: **ES · España** · Edición: **2025**

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena completa validada** | 🟢 **12** | 03 Principado de Asturias · 05 Canarias · 06 Cantabria · 08 Castilla-La Mancha · 09 Cataluña · 12 Galicia · 13 Comunidad de Madrid · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla |
| **Generación territorial validada** | 🟢 **18** | 02 Aragón · 03 Principado de Asturias · 04 Islas Baleares · 05 Canarias · 06 Cantabria · 07 Castilla y León · 08 Castilla-La Mancha · 09 Cataluña · 10 Comunidad Valenciana · 11 Extremadura · 12 Galicia · 13 Comunidad de Madrid · 14 Región de Murcia · 15 Comunidad Foral de Navarra · 16 País Vasco · 17 La Rioja · 18 Ceuta · 19 Melilla |
| **Preparados para continuar** | 🔵 **1** | 01 Andalucía |
| **Validación pendiente** | 🟡 **0** | — |
| **Pendientes o no incorporados** | ⚪/🔴 **0** | — |

## Estado actual por territorio

FT = **fuentes territoriales (01)** · G = **generación territorial (02)** · FE = **fuentes electorales (03)** · RE = **incorporación de resultados electorales (04)** · PUB = **publicación del visor (05)**

| Territorio | FT | G | FE | RE | PUB | Estado | Última ejecución | Parada en | Motivo | Siguiente paso |
|---|:---:|:---:|:---:|:---:|:---:|---|---|---|---|---|
| **01 Andalucía** | 🟢 | 🟡 | 🟡 | ⚪ | ⚪ | Fuentes territoriales preparadas | 40958892613 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | generar y validar distritos |
| **02 Aragón** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40898231736 · SUCCESS | — | — | preparar fuentes electorales |
| **03 Principado de Asturias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40706742818 · SUCCESS | — | — | — |
| **04 Islas Baleares** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40957888543 · SUCCESS | — | — | preparar fuentes electorales |
| **05 Canarias** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40951280657 · SUCCESS | — | — | — |
| **06 Cantabria** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40701656466 · SUCCESS | — | — | — |
| **07 Castilla y León** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40964570303 · FAILED | 04 · Incorporación de Resultados Electorales | ver log del run | preparar fuentes electorales |
| **08 Castilla-La Mancha** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40706698510 · SUCCESS | — | — | — |
| **09 Cataluña** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40952013601 · SUCCESS | — | — | — |
| **10 Comunidad Valenciana** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40896263473 · SUCCESS | 03/04 · rama electoral omitida | PREPARED_PAIR_BLOCK: falta evidence.prepared_source_pair para Comunidad Valenciana edición 2025; complete la preparación conjunta antes de ejecutar | activar par de fuentes (Activación de Legislatura Vigente) y reutilizar |
| **11 Extremadura** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40965231300 · FAILED | Reanudación de producto electoral durable | ver log del run | preparar fuentes electorales |
| **12 Galicia** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40832139215 · SUCCESS | — | — | — |
| **13 Comunidad de Madrid** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40787900559 · SUCCESS | — | — | — |
| **14 Región de Murcia** | 🟢 | 🟢 | 🟡 | 🟡 | ⚪ | Generación territorial validada | 40957577850 · FAILED | Reanudación de producto electoral durable | ver log del run | preparar fuentes electorales |
| **15 Comunidad Foral de Navarra** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40847881909 · SUCCESS | — | — | — |
| **16 País Vasco** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40951146225 · SUCCESS | — | — | — |
| **17 La Rioja** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40867482289 · FAILED | 02 · Generación de Distritos Autonómicos | M04–M06 o certificación territorial (ver log del run) | — |
| **18 Ceuta** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40784389253 · SUCCESS | — | — | — |
| **19 Melilla** | 🟢 | 🟢 | 🟢 | 🟢 | ⚪ | Cadena completa validada | 40840795932 · SUCCESS | — | — | — |

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
