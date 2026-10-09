# Verificación del visor — run 35032376745

**Fecha de comprobación:** 2026-09-16 (Europe/Madrid)  
**Run de despliegue:** `35032376745`  
**Run territorial referenciado:** `35029919726`  
**URL registrada:** `https://jfmurciego.github.io/DiputadodeDistrito/`  
**Commit funcional desplegado:** `e5d96dc34ded987497c74c894693e429a896c392`

## Resultado

**Visual E2E: FAIL / no certificable como PASS.** El despliegue de Pages es SUCCESS y los artefactos publicados son coherentes, pero este entorno no puede abrir el sitio en un navegador con acceso de red (fallo de resolución DNS), por lo que no se atribuye una observación visual que no se haya realizado. Además, el visor actual no implementa ningún componente `legend`/`leyenda` en `visor/index.html`, `visor/app.js` o `visor/styles.css`; por tanto el requisito de comprobar que la leyenda funciona no puede pasar en el estado actual.

No se ha lanzado ningún workflow, M01–M08 ni GerryChain durante esta verificación.

## Comprobaciones mecánicas sobre el artefacto publicado

- `data/viewer-results.json` contiene `m08-35029919726` y `m06-35029919726`.
- Ambos registros declaran `run_id: 35029919726`, `expected_districts: 67` y `observed_districts: 67`.
- `data/results/m06-35029919726.geojson`: 67 features, 67 identificadores de distrito únicos, sin miembro `crs`; bbox WGS84 lon `-2.1736709793..0.7716694855`, lat `39.8467779632..42.9244964628`.
- `data/results/m08-35029919726.geojson`: 67 features, 67 identificadores de distrito únicos, sin miembro `crs`; mismo bbox WGS84.
- La geometría publicada se puede renderizar mecánicamente con forma y extensión coherentes con Aragón. Se generaron dos capturas locales de evidencia geométrica a partir de los GeoJSON publicados; no se presentan como capturas del navegador desplegado.
- El código del visor contiene `fitBounds(boundsFor(data))`, selector de territorio/resultado y manejadores de click que construyen ficha y `maplibregl.Popup`; esto acredita presencia de la lógica, no ejecución visual E2E.

## Incidencias

1. **Leyenda ausente:** no existe implementación de leyenda en el visor actual. Esto impide un PASS del checklist visual solicitado.
2. **Limitación de verificación externa:** el entorno de inspección no resuelve `jfmurciego.github.io`, por lo que no se certifican visualmente mapa base, centrado efectivo en navegador, popup ni selector. No es una incidencia demostrada del producto.
3. **Semántica conservadora existente:** `visor/app.js` considera bloqueado cualquier `technical_status` distinto de `PASS`; por tanto `PASS_WITH_EXCEPTIONS` se muestra en modo diagnóstico. No se modifica.

## Inventario de `publication_status: BLOCKED`

### Establecimiento activo

- `herramientas/preparar_visor_ejecucion.py`
  - `add_production()`: fija literalmente `"publication_status": "BLOCKED"` para M06/M08 publicados.
  - `add_ensemble()`: fija literalmente `"publication_status": "BLOCKED"` para candidatos ensemble.
  - `add_static()`: hereda `product["publication_status"]` y usa `"BLOCKED"` como valor por defecto.
- `orchestracion/productos_publicos.json`
  - Aragón: `publication_status: BLOCKED`.
  - Castilla y León: `publication_status: BLOCKED`.
- `resultados/fase1/EVIDENCIA_PUBLICABILIDAD.json`
  - Aragón, Castilla y León y Extremadura: `publication_status: BLOCKED`.
- `resultados/fase1/ESTADO_FACTUAL.json`
  - Aragón: `publication_status: BLOCKED`.
  - El mismo fichero usa estados específicos distintos para los otros territorios (`BLOCKED_SHAPE`, `BLOCKED_TECHNICAL`) y un estado global `NO_PUBLICABLE_MAPS`; no se normalizan ni modifican.

### Política y guardas, no setters de runtime

- `docs/POLITICA_PUBLICABILIDAD.md`: define la política de publicabilidad vigente.
- `tests/test_publicabilidad_policy.py`: exige mecánicamente que los productos del registro técnico permanezcan `BLOCKED`.
- `tests/test_comunidades_interes_contract.py`: protege la semántica de bloqueo vinculada a la evidencia de publicabilidad.

### Histórico / legacy

- `legacy/visor/app_v1.2.0.js`: fallback a `BLOCKED`.
- `legacy/resultados/EVIDENCIA_PUBLICABILIDAD_v1.0.0.json`: registros históricos `BLOCKED`.
- `legacy/resultados/EVIDENCIA_PUBLICABILIDAD_v1.1.0.json`: registros históricos `BLOCKED`.

No se ha cambiado el significado de ninguno de estos estados ni se ha promovido Aragón.
