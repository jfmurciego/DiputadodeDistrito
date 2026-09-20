# Diputado de Distrito — motor multi-territorio

**README v4.7.0** · 20-09-2026 · Estado: **plataforma ejecutable; industrialización territorial en curso**  
**Anterior:** `legacy/docs/README_v4.6.0.md`

DDD es un motor modular y reproducible para construir, optimizar, validar y auditar distritos uninominales desde unidades censales oficiales.

# Estado operativo del proyecto

**Resumen ejecutivo de la cadena automática vigente**  
Fuente de verdad: **repositorio + evidencia reproducible en GitHub**.

**Semáforo:** 🟢 completo · 🟡 parcial / pendiente de revalidación · 🔴 no incorporado · ⚪ no iniciado

## Resumen

| Indicador | Estado | Territorios |
|---|---:|---|
| **Cadena territorial validada** | 🟢 **1** | Galicia |
| **Preparados para continuar** | 🔵 **2** | Extremadura · Castilla-La Mancha |
| **Revalidación pendiente** | 🟡 **2** | Aragón · Castilla y León |
| **Pendientes o no incorporados** | ⚪/🔴 **14** | Resto del mapa |

## Estado actual por territorio

FT = **fuentes territoriales** · FE = **fuentes electorales** · G = **generación territorial** · RE = **incorporación de resultados electorales**

| Territorio | FT | FE | G | RE | Estado |
|---|:---:|:---:|:---:|:---:|---|
| **Andalucía** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Aragón** | 🟡 | 🟡 | 🟡 | ⚪ | Revalidación pendiente |
| **Asturias** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Baleares** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporada |
| **Canarias** | 🔴 | 🔴 | 🔴 | 🔴 | No incorporada |
| **Cantabria** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Castilla-La Mancha** | 🟢 | ⚪ | ⚪ | ⚪ | Preparada; falta promoción de catálogo |
| **Castilla y León** | 🟡 | 🟡 | 🟡 | ⚪ | Revalidación pendiente |
| **Cataluña** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Ceuta** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad de Madrid** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Comunidad Valenciana** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Extremadura** | 🟢 | ⚪ | ⚪ | ⚪ | Preparada para continuar |
| **Galicia** | 🟢 | 🟢 | 🟢 | ⚪ | Cadena territorial validada |
| **La Rioja** | 🟡 | ⚪ | ⚪ | ⚪ | Preflight |
| **Melilla** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Murcia** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **Navarra** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |
| **País Vasco** | ⚪ | ⚪ | ⚪ | ⚪ | Pendiente de preparación |

> Esta tabla refleja únicamente la **cadena automática vigente**. Las ejecuciones anteriores no cuentan por sí solas como validación del estado actual.

## Cadena automática

| 1. Fuentes territoriales | 2. Fuentes electorales | 3. Generación territorial | 4. Resultados electorales |
|---|---|---|---|
| Preparar / reutilizar | Resolver / adquirir | M01–M06 + publicación | M07–M08 |

**Regla estructural:** la geometría de los distritos nunca depende de los resultados electorales.

## Último territorio validado

### 🟢 Galicia

| Métrica | Valor |
|---|---|
| **Run** | [35505298149](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/35505298149) |
| **Distritos** | 75 |
| **Secciones** | 2.134 |
| **Población** | 2.714.741 |
| **Auditoría geométrica** | `PASS_WITH_EXCEPTIONS` |
| **Visor** | Publicado |
| **Resultados electorales** | Fuente preparada; incorporación pendiente |

La ejecución automática recuperó las fuentes territoriales preparadas, consolidó los 75 distritos, superó la puerta geométrica admitida por contrato y publicó el producto territorial.

## Bloqueos y alertas

| Territorio | Semáforo | Situación |
|---|:---:|---|
| **Aragón** | 🟡 | Revalidar con la cadena separada actual |
| **Castilla y León** | 🟡 | Revalidar con la cadena separada actual |
| **Castilla-La Mancha** | 🟡 | Promover la evidencia territorial al catálogo |
| **Extremadura** | 🟡 | Preparar fuente electoral y ejecutar generación |
| **Baleares** | 🔴 | Incorporación territorial pendiente |
| **Canarias** | 🔴 | Incorporación territorial pendiente |

## Próximas acciones operativas

| Orden | Acción |
|---:|---|
| **1** | Extremadura — preparar fuentes electorales |
| **2** | Extremadura — ejecutar generación automática |
| **3** | Castilla-La Mancha — alinear catálogo con la preparación territorial existente |
| **4** | Aragón y Castilla y León — revalidar con la cadena automática vigente |

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
