# Bitácora de progreso

## 2026-09-11 — v7.0.0 Profesionalización reproducible

**Estado:** candidato.

- Se adopta “procedimiento de distritación” y “módulo”.
- Se archivan íntegramente las versiones v6 conocidas en `legacy/recuperado_2026-09-11_v6/`.
- Se crean ocho módulos v7 con responsabilidad única, versión y descripción interna.
- Módulo 01: lectura incremental de población y corrección del CUSEC cuando la fuente oficial incluye texto descriptivo.
- Módulo 08: corrección del cableado de configuración heredado.
- Se crea contrato único `configuracion/aragon_2025.yaml`.
- Se crea `procedimiento.sh` con modos completo e iterativo.
- Se introduce caché de la base preparada producida por 01-03.
- Se añade manifiesto de ejecución y puerta de calidad independiente.
- Se renombra el workflow a “Procedimiento DDD — Aragón”.
- GitHub Actions se establece como entorno arbitral de validación.

### Referencia recuperada

La ejecución del baseline recuperado produjo 1.463 secciones y 67 distritos, con 67/67 distritos contiguos sobre el grafo. La restricción poblacional falló: 30 distritos bajo 0,80×target y 7 sobre 1,75×target. Este valor es referencia, no objetivo aceptable.

### Regla de progreso

Una nueva versión solo se califica como mejora si mantiene o mejora todos los criterios duros y mejora métricas respecto a la última versión validada. Si no, queda registrada como experimento o regresión y no sustituye la referencia.

## 2026-09-11 — Módulo 01 v7.0.1

**Estado:** candidato.

- La primera ejecución de v7.0.0 falló en ingestión por uso incorrecto de `Series.isin(..., na=False)`.
- Se conserva v7.0.0 en `legacy/2026-09-11_modulo01_v7.0.0/`.
- v7.0.1 reemplaza esa expresión por `isin(...) & notna()` sin cambiar la lógica funcional.
- Motivo: compatibilidad real con pandas 2.3.2 y eliminación de un fallo de arranque reproducible.

## 2026-09-11 — Correcciones de portabilidad y Módulo 08

**Estado:** candidato.

- `validar_ejecucion.py` v1.1.1: añade el raíz del proyecto a `sys.path`; anterior preservada en legacy.
- `registrar_ejecucion.py` v1.0.1: misma corrección de portabilidad; anterior preservada en legacy.
- Módulo 08 v7.0.1: deja de usar la ruta fallback de v6 y toma entradas/salida de su contrato modular v7; v7.0.0 preservada en legacy.

## 2026-09-11 — Determinismo Módulos 04/05 v7.0.1

**Estado:** candidato.

- Dos ejecuciones con seed=12345 producían resultados distintos; por tanto el baseline no era reproducible.
- Módulo 04 v7.0.1 ordena iteraciones sobre conjuntos y sustituye el fallback que podía asignar una sección no adyacente por una expansión desde una frontera real.
- Módulo 05 v7.0.1 ordena conjuntos antes de cualquier selección aleatoria o recorrido de conectividad.
- Las versiones v7.0.0 se conservan en `legacy/2026-09-11_modulo04_v7.0.0/` y `legacy/2026-09-11_modulo05_v7.0.0/`.
- Este cambio se clasifica como corrección de reproducibilidad/contigüidad, no como mejora del objetivo poblacional.

## 2026-09-11 — Verificación de reproducibilidad local v7.0.1

**Estado:** candidato a GitHub.

Se ejecutó dos veces consecutivas el modo iterativo sobre la misma base preparada y los mismos parámetros.

- Distritos: 67 en ambas ejecuciones.
- Distritos desconectados: 0 en ambas.
- Bajo suelo 0,80×target: 29 en ambas.
- Sobre techo 1,75×target: 0 en ambas.
- `best_max_rel_dev`: 0,5046 en ambas.
- SHA-256 del resumen distrital en ambas ejecuciones: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

Conclusión: la fuente de no determinismo detectada en Módulos 04/05 queda corregida para el producto distrital resumido. El equilibrio poblacional sigue en FAIL y constituye el siguiente problema algorítmico, no un problema de infraestructura.

## 2026-09-11 — Módulo 01 v7.0.2

**Estado:** candidato.

- Preserva v7.0.1 en `legacy/2026-09-11_modulo01_v7.0.1/`.
- Filtra la cartografía nacional con `pyogrio`/OGR por `CPRO` antes de cargar geometrías.
- Verificación directa sobre `seccionado_2025.zip`: el filtro 22/44/50 devuelve 1.463 secciones.
- Corrige además la expresión regular del CUSEC exacto de 10 dígitos.
