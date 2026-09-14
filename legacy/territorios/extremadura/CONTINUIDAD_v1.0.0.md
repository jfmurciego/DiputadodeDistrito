# Continuidad — Extremadura

**Proyecto:** Diputado de Distrito  
**Versión:** 1.0.0  
**Fecha:** 2026-09-11  
**Estado:** EXT-02 cerrado; EXT-03 en diagnóstico M04

## Baseline certificado

- Fuente territorial/poblacional: fuentes nacionales 2025 reconstruibles desde GitHub.
- Secciones: **964**.
- Población total: **1.053.345**.
- Badajoz (06): **553 secciones / 665.155 habitantes**.
- Cáceres (10): **411 secciones / 388.190 habitantes**.
- Faltantes de población: **0**.
- K institucional fundamentado: **65**.
- Reparto DDD Hamilton puramente poblacional: **41 Badajoz / 24 Cáceres**.

## EXT-02 — cerrado

Contrato topológico actual: `config/extremadura_2025.yaml` v0.4.0.

M02 v7.2.0 utiliza `contact` en EPSG:3035 para aceptar borde compartido pese a micro-solapes cartográficos inferiores al umbral configurado.

Pasarelas administrativas auditadas:

- `0604405005 ↔ 0604405003` — Don Benito, componente separada ~2.074 m.
- `0604405006 ↔ 0604405004` — Don Benito, componente separada ~0.869 m.

Ejecución de cierre EXT-02:

- M01: 964 nodos, 0 población faltante.
- M02: 2.607 aristas = 2.605 geométricas + 2 administrativas.
- M03: 964 nodos; 0 aislados; 0 provincias desconectadas; 0 municipios desconectados.

## EXT-03 — M04

Se ejecutó un barrido diagnóstico con K=65 y cuotas 41/24. Ninguno de los tres escenarios se promovió a contrato:

| Escenario | Suelo | Techo | Tolerancia | Atomicidad | Resultado |
|---|---:|---:|---:|---:|---|
| tight | 0.85 | 1.50 | ±10% | 1.10 | falla al extraer núcleo factible en Don Benito |
| reference | 0.80 | 1.75 | ±12% | 1.12 | grafo de unidades abiertas desconectado en Badajoz; unidad `06:06005:M` |
| wide | 0.75 | 2.00 | ±15% | 1.15 | grafo de unidades abiertas desconectado en Cáceres; unidad `10:10018:M` |

### Hipótesis arquitectónica activa

M03 es completamente conexo. Por tanto, las desconexiones `06:06005:M` y `10:10018:M` aparecen **después** de transformar municipios en unidades M04. El motor v7.4.8 exige que el subgrafo inducido exclusivamente por unidades abiertas sea globalmente conexo por provincia. Esa condición puede ser excesiva cuando un núcleo urbano cerrado actúa como separador territorial: cada distrito final debe ser conexo, pero no necesariamente todas las unidades todavía abiertas deben formar una sola componente después de retirar distritos ya cerrados.

Además, M04 protege actualmente todos los extremos declarados en `topology_bridges`. En Don Benito los dos puentes son internos al mismo municipio; forzar los cuatro extremos a permanecer en el residuo puede restringir innecesariamente la extracción de núcleos urbanos.

Estas dos hipótesis deben probarse antes de modificar M04.

## Diagnóstico en curso

Workflow: `EXT-03 — Auditoría conectividad M04`.

Herramienta reusable: `herramientas/auditar_conectividad_m04.py`.

Municipios inspeccionados:

- `06005` — unidad aislada en escenario reference.
- `06044` — Don Benito, para analizar el papel de puentes internos.
- `10018` — unidad aislada en escenario wide.

## Regla de cambio

M04 v7.4.8 está congelado en `legacy/modulo04/04_generar_semillas_v7.4.8.py` antes de cualquier generalización. Una futura 7.5.x solo podrá promoverse si:

1. resuelve causalmente EXT-03 sin puentes ficticios;
2. preserva contigüidad, K y cuotas;
3. pasa regresión completa de Aragón;
4. pasa regresión completa de Castilla y León;
5. deja evidencia y outputs en GitHub Actions.
