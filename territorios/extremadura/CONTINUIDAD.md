# Continuidad — Extremadura

**Proyecto:** Diputado de Distrito  
**Versión:** 3.0.0  
**Fecha:** 2026-09-12  
**Estado:** F1.4 cerrada como experimental bloqueada  
**Anterior:** `legacy/territorios/extremadura/CONTINUIDAD_v2.0.0.md`

## Contrato reproducible

- YAML canónico 0.5.1: K=65, Hamilton 41 Badajoz / 24 Cáceres.
- Ratios: suelo 0.85, techo 1.50, tolerancia ±10 %.
- Partición interna c020: atomicidad 1.10, chunk 0.20.
- M03: 964 secciones, 1.053.345 habitantes, dos pasarelas Don Benito auditadas.

## Resultado F1.4

Run [34703213474](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34703213474), commit `ab525ce6`:

- M01-M06 completados.
- 65 distritos; cuotas 41/24; hard=0; contigüidad 65/65.
- 2 distritos fuera de ±10 %; máximo desvío 13,3000109 %.
- Estado: `EXPERIMENTAL_BLOCKED`; no promovido.
- Evidencia: `resultados/ejecuciones/gh-34703213474-1/`.

EXT-19 se conserva bajo `resultados/experimentos/ext19-gh-34652238246/` y se descarta como promoción: fue dirigido, no aplicado y dejaba un outlier.

## Regla de reapertura

Solo con un operador general que cierre los dos outliers sin excepciones ocultas y mantenga Aragón/CyL verdes.
