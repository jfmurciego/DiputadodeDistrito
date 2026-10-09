# Bitácora de progreso

**Versión:** 2.0.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/2026-09-11_bitacora_v1/BITACORA.md`

## R001 — Recuperación y profesionalización

- Se adopta “Procedimiento de Distritación DDD” y “módulo”.
- Se archivan las versiones recuperadas y se crean ocho módulos con responsabilidad única.
- Se crea contrato único `configuracion/aragon_2025.yaml`.
- Se crea `procedimiento.sh` con modos completo e iterativo.
- Se introduce caché de la base preparada M01-M03.
- Se añade manifiesto de ejecución y puerta de calidad independiente.
- GitHub Actions se establece como entorno arbitral de validación.

### Baseline recuperado

Ejecución completa: 1.463 secciones, 67 distritos y 67/67 contiguos sobre el grafo. Balance poblacional: FAIL.

Referencia inicial: 30 distritos bajo 0,80×target y 7 sobre 1,75×target.

### Correcciones realizadas dentro de R001

- M01: lectura incremental de población, CUSEC robusto y filtrado territorial temprano.
- M08: corrección del cableado heredado de configuración.
- Herramientas de registro/validación: portabilidad del `sys.path`.
- M04/M05: orden determinista de conjuntos antes de decisiones aleatorias.
- Versiones salientes preservadas bajo `legacy/`.

### Reproducibilidad local

Dos ejecuciones consecutivas con seed=12345 y la misma base preparada produjeron exactamente el mismo resumen distrital:

- 67 distritos.
- 0 desconectados.
- 29 bajo suelo 0,80×target.
- 0 sobre techo 1,75×target.
- `best_max_rel_dev`: 0,5046.
- SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

Conclusión: infraestructura/determinismo local PASS; balance poblacional FAIL.

## R002 — Preparación de la ejecución arbitral en GitHub

**Estado:** en curso.

### Cambios

1. Workflow `procedimiento-ddd.yml` elevado a v2.1.0.
2. La versión v2.0.1 se conserva en `legacy/2026-09-11_workflow_v2.0.1/` antes de modificarla.
3. `actions/checkout` materializa ahora Git LFS (`lfs: true`).
4. La clave de caché de la base M01-M03 depende de hashes de entradas, módulos territoriales, configuración y cargador de configuración.
5. El modo `iterativo` reutiliza M01-M03; el modo `completo` fuerza su reconstrucción.
6. Cada ejecución publica `output/**` como artefacto identificado por `github.run_id` y `github.sha`.

### Decisión sobre entradas pesadas

Para la primera reproducción exacta no se sustituirán silenciosamente las fuentes nacionales por derivados regionales. Los binarios originales `seccionado_2025.zip` y `65034.csv.zip` se conservarán mediante Git LFS y se comprobarán contra `inputs/MANIFEST.sha256`. Una vez construida M01-M03, las iteraciones posteriores no vuelven a procesarlos mientras la clave de caché sea válida.

Se ha comprobado además que es posible producir derivados Aragón mucho menores (1.463 geometrías y 1.468 registros poblacionales brutos), pero no se adoptan todavía como entrada canónica porque eso constituiría un cambio del contrato de entrada y debe evaluarse/versionarse como ronda independiente.

### Bloqueo actual para el primer run de GitHub

El código ya está preparado para materializar LFS, pero los tres ficheros de entrada todavía no existen físicamente en el repositorio remoto. La API conectada permite editar código Git, pero no transferir directamente estos binarios locales al almacenamiento LFS. Es una operación de bootstrap única; después GitHub será autosuficiente para ejecuciones repetidas.

### Criterio de cierre de R002

R002 solo se cierra cuando un commit de GitHub ejecutado por Actions reproduce 67 distritos, 0 desconectados y el mismo SHA-256 del resumen que la referencia local determinista, o cuando cualquier diferencia quede explicada y versionada.

## Regla permanente de progreso

Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se registra y conserva, pero no se promociona como versión de referencia.
