# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 2.2.0  
**Fecha de corte:** 2026-09-12  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v2.1.0.md`

## Estado arbitral

El motor cuenta con dos implantaciones validadas hasta M06, una tercera validada hasta M03 y una expansión nacional observable.

- **Aragón:** baseline principal Run `34599224954`; 67 distritos; 1.463 secciones; 1.364.621 habitantes; 11/7/49; hard PASS; `fuera_12=0`; máximo 9,930 %.
- **Castilla y León:** validada hasta M06; 82 distritos; 3.506 secciones; 2.401.221 habitantes; hard PASS; `fuera_12=0`; M07 bloqueado por fuente electoral.
- **Extremadura:** M01–M03 cerrados; c020/EXT-19 demuestra operador 2×2 válido pero deja un outlier; no promovida.
- **Andalucía:** M01–M03 cerrados; AND-04 falla en M04 con 4 hard outliers; requiere barrido territorial propio.
- **Cataluña:** CAT-03 Run `34688242964` SUCCESS; 5.143 secciones; 8.124.126 habitantes; 14.376 aristas; 0 aislados; 0 desconexiones; pasarela Llívia–Puigcerdà auditada.

## Motor vigente

M03 v7.2.0 separa observación topológica (`audit_*`) de enforcement (`require_*`). Esto permite medir territorios nuevos sin ocultar desconexiones ni promoverlas. Aragón y Castilla y León siguen siendo regresiones obligatorias.

## Cobertura España

R022 Run `34688010656` procesó Madrid primero y después Comunidad Valenciana, Galicia, Castilla-La Mancha, País Vasco, Murcia, Asturias, Navarra, Cantabria, La Rioja, Illes Balears, Canarias, Ceuta y Melilla.

- Observación conexa: Madrid, Asturias, La Rioja, Ceuta y Melilla.
- Diagnóstico continental R023: Comunidad Valenciana, Galicia, Castilla-La Mancha, País Vasco, Murcia, Navarra y Cantabria.
- Contrato archipelágico pendiente: Illes Balears y Canarias.

Referencia: `resultados/bootstrap/gh-34688010656/RESUMEN_NACIONAL.json`.

## Orden operativo

1. Cerrar R023 y declarar únicamente pasarelas justificadas.
2. Promover contratos M01–M03 de territorios conexos.
3. Diseñar contrato por isla para Baleares y Canarias.
4. Fijar K/reparto de Cataluña y Madrid antes de M04.
5. Resolver EXT-19 y barrido M04 de Andalucía sin relajar restricciones.
6. Mantener regresiones Aragón/Castilla y León.

## Fuente de continuidad

Leer en este orden: `docs/SALIDAS_CHATGPT/SALIDA_MAESTRA.md`, último hito enlazado, este Estado Maestro y el contrato del territorio activo.
