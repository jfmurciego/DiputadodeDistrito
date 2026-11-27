<!--
PROYECTO: Diputado de Distrito
VERSIÓN: 0.1.0
NOMBRE DE VERSIÓN: Investigación T-509 · ámbito 06b · laboratorio del banco, nac27–nac52 (esqueleto)
FECHA: 2026-11-28
ESTADO: DOCUMENTO DE TRABAJO de la investigación T-509 (en curso). No es el plan; no autoriza lanzar ni publicar nada
CAMBIOS: 0.1.0 — esqueleto y plan de medida
MOTIVO: orden del propietario (28-11), protocolo `PROTOCOLO.md`, ámbito 06b del anexo A
ANTERIOR: ninguna (fichero nuevo)
-->

# 06b · Laboratorio del banco: Deslinde 1.2 frente a GerryChain y al exacto, nac27–nac52

Sesión `session_01KQDtFrNwYVBHjQWqaQkvim`. Motor de `main` (9e630d11, Deslinde 1.2). Sesión cloud, 4 núcleos, 15 GB.
No se ha lanzado ni publicado nada.

## Estado (se actualiza en cada empuje)
- 23:44Z · entorno instalado (`requirements.lock` + `requirements-banco-motor.lock`), seccionados 2023 y 2024 del INE
  bajados y verificados (7a15e700…, df931fa0…), entradas de Lugo generadas (32 s). Resto de entradas en curso.

## Tramo y orden (de menor a mayor K)
| Territorio | K | Estado |
|---|---|---|
| Palencia (nac34), Segovia (nac40), Soria (nac42), Teruel (nac44), Zamora (nac49), Ceuta (nac51), Melilla (nac52) | 1 | Trivial: un solo distrito, no hay nada que optimizar |
| Lugo (nac27), Orense (nac32), Salamanca (nac37) | 3 | pendiente |
| Valladolid (nac47) | 4 | pendiente (repite el piloto con el motor 1.2) |
| Cantabria (nac39) | 5 | pendiente |
| Navarra (nac31), Toledo (nac45) | 6 | pendiente |
| Tarragona (nac43) | 7 | pendiente |
| Asturias (nac33), Pontevedra (nac36), Zaragoza (nac50) | 8 | pendiente |
| Santa Cruz de Tenerife (nac38) | 9 | pendiente |
| Las Palmas (nac35), Vizcaya (nac48) | 10 | pendiente |
| Murcia (nac30) | 13 | pendiente |
| Málaga (nac29) | 15 | pendiente |
| Sevilla (nac41) | 16 | pendiente (repite el piloto con el motor 1.2) |
| Valencia (nac46) | 23 | pendiente |
| Madrid (nac28) | 59 | No se adquiere en la nube (FALLO_ADQUISICION): fuera |

## Método (el del piloto T-465, `docs/ESTUDIOS/T465_BANCO_PILOTO/DISENO.md`)
- Entradas: `bateria_motor.py entradas --desde-fuente --seccionado shapefile`.
- Deslinde: `python -m ddd_motor2.competir` (D8, cadenas por defecto), motor de `main`.
- Exacto: `optimo_d8.py` de T-296 (CP-SAT, 4 hilos), con tope de 10 minutos por territorio.
- GerryChain puro: `gerrychain_puro.py` del piloto, 10⁴ pasos, semillas públicas 1..10.
- Los tres se juzgan con la misma `Natural.clave("D8")` y los mismos átomos.

## Tabla final
Pendiente (se rellena con `docs/ESTUDIOS/T509_LAB_BANCO/nac_b/resultados/`).

## Hallazgos
Pendiente.
