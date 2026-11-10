## 2026-11-10 — T-196 — Informe de la batería r3 (motor 2, D8, N=10) frente al canónico y al laboratorio

**Causa:** el run 42886114842 (71 territorios, aceptación SÍ) debía analizarse frente al canónico y al laboratorio T-179.
**Cambio:** `docs/ESTUDIOS/T196_BATERIA_D8/`: `README.md`, `analizar.py` (cifras recalculables), `extraer_filas.py`, `datos/` (filas por territorio desde los logs de los jobs, ids de job, `COMPARACION.csv`). No toca código de producción.
**Hallazgos:** mejora 55, empata 16, empeora 0 (Congreso 40/12/0; autonómicas 15/4/0). Congreso reproduce el laboratorio (fuera de tolerancia 7 frente a A 7 / D8 6). Las autonómicas no: fuera de tolerancia del ganador 187 frente a A 171 y D8 115 en las 15 con dato; causa probable (no verificada): el `Ponderado` de la batería no usa el objetivo por circunscripción del laboratorio.
**Límites:** los artefactos dan 403 desde la nube, así que no hay partidos/comarcas ni los fuera de tolerancia del canónico; las cifras salen de las filas de los logs.
**Pruebas:** `python docs/ESTUDIOS/T196_BATERIA_D8/analizar.py` reproduce las cifras de r3 y de la comparación con el laboratorio calculadas con la clave aproximada; el 40/3/1 del laboratorio es el de su README (otra definición). Sin 00 ni publicación.
**Pruebas:** `python docs/ESTUDIOS/T196_BATERIA_D8/analizar.py` reproduce todas las cifras del informe. Sin 00 ni publicación.

## 2026-11-10 — T-196b — Competición real del canónico en autonómicas
- Bajados los 71 artefactos del run 42886114842 (entorno con host de artefactos). Versionado: `datos/CANDIDATOS.csv` (~130 kB), `datos/MANIFEST_ARTEFACTOS.tsv` (id y sha256), `bajar_competicion.py` y adenda en el README con la tabla de las 19 autonómicas.
- Hallazgo: «fuera de tolerancia» bruto ≠ componente de la clave; con la bruta el ganador puede ser peor que el canónico (Aragón, CLM, CyL, Galicia). Cifras publicadas sin editar.
