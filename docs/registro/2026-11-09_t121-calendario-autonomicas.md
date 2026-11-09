## 2026-11-09 — T-121 — Calendario de elecciones autonómicas por comunidad (paso 1)

**Causa:** orden del propietario (09-11): histórico autonómico desde 2011; las legislaturas autonómicas no comparten calendario y el visor necesita una barra temporal por comunidad.

**Cambio:** `herramientas/calendario_autonomicas.py` 1.0.0 (fichero nuevo) y `configuracion/calendario_autonomicas.csv` (79 elecciones, 17 comunidades): mes, vigente, fin de legislatura = siguiente convocatoria, duración, adelanto sobre 48 meses, proveedor/URL/granularidad/completitud de los resultados y sha256 de la fuente. Instantáneas con sha256 en `fuentes/observatorio_autonomicas/` (índice autonómico y tabla de fuentes del Observatorio). Incluye 4 elecciones previas a 2011 (`en_alcance=no (previa)`: Andalucía 2008, Galicia y País Vasco 2009, Cataluña 2010), que son las legislaturas en curso en enero de 2011.
Hallazgos: Ceuta y Melilla (en el catálogo de 19) no tienen elecciones autonómicas: sus asambleas se eligen con las municipales; no figuran. Cantabria 2011 sin datos. Huecos de granularidad: Extremadura solo por provincia; municipio en Aragón 2011/2015, Asturias, Cantabria 2015/2019, Castilla-La Mancha 2011/2015/2023, Murcia 2011/2015/2023.
**Límite:** el día exacto solo consta en la elección vigente (de `legislatura_vigente.yaml`, comprobado contra el mes); el resto `precision=mes` hasta contrastar con boletín. La disolución anticipada es DERIVADA (adelanto ≥ 2 meses «si», 1 «revisar»), no de boletín.

**Pruebas:** `tests/test_calendario_autonomicas.py` (valores a mano de la tabla pública; CSV al día; sha256).

**Efectos:** ninguno en huellas, checkpoints ni workflows. Nada lanzado ni publicado.
