# Criterio de aceptación del motor 2 («puede relevar») — T-194

Versión 1.0.0 · 2026-11-10 · automatizado en `tests/test_motor2_aceptacion.py` (suite de CI, solo stdlib).
El motor nuevo puede relevar al canónico si se cumplen **todos** los puntos. Parámetros: N de semillas (`N_CADENAS`, 5) y
función de calidad / criterio (`CRITERIO`) están al principio del test; los fijan T-179 y T-180.

| # | Criterio | Cómo se comprueba | Estado |
|---|---|---|---|
| a | Huella bit a bit fija en Soria, Álava y Melilla, con semilla pública (D-50) y N fijos | `HuellaFija`: dos ejecuciones iguales y `huella_resultado` igual a `HUELLAS_FIJAS` (reglas, semillas, planes y composiciones de todos los candidatos). En CI, sobre fixtures sintéticos con generador determinista por semilla; con el motor real (GerryChain + entradas de la batería), `DDD_ACEPTACION_BATERIA=<carpeta>` compara dos ejecuciones | activo |
| b | Todo ganador pasa el certificador independiente (núcleo único, R-NUCLEO y atomicidad M04) y el contrato | `GanadorCertificado`: `herramientas.certificador_exacto.juzgar` = PASS, sin violaciones, K distritos; en Soria hay núcleo cerrado (R-NUCLEO no trivial) | activo |
| c | Nunca peor que el canónico en los 71 | `NuncaPeorQueElCanonico` lee `docs/ESTUDIOS/T132_BATERIA_MOTOR/COMPETIDOR.csv` (no recalcula): 71 filas, validación PASS, ninguna «empeora» y (fuera de tolerancia, desvío máx.) ≤ canónico | activo |
| d | El certificador rechaza planes adversos | `CasosAdversos`: distrito discontinuo (R-CONTIG), fuera de techo (R-POB-TECHO) y de suelo (R-POB-SUELO), municipio partido de más (R-MUN-MIXTOS), distrito que cruza provincia (R-PROV) | activo |
| e | Mismo mapa con id viejo y nuevo (D-60) | `MismoMapaIdViejoYNuevo`: falla si se ejecuta; marcado `skip` hasta el corte 5.0.0 (`CORTE_5_0_0.md`) | pendiente |

## Mantenimiento
- Cambiar el núcleo de reglas, la semilla, N o la función de calidad cambia las huellas: regenerar `HUELLAS_FIJAS` es una
  decisión consciente y va en la PR con su motivo.
- Tras una nueva batería, sustituir `COMPETIDOR.csv`; el test (c) debe seguir verde.
- Al llegar el corte 5.0.0, implementar (e) y quitar el `skip`.
- Límite conocido: (a) con el motor real no corre en CI (necesita GerryChain y las entradas reconstruidas); la huella del
  motor real queda fuera de la suite hasta que haya entradas fijas versionadas.
