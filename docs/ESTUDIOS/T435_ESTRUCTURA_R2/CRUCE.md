# T-435 — Cruce clave a clave de R2 (propuesta)

VERSIÓN: 1.0.0 · FECHA: 2026-11-21 · ESTADO: propuesta, solo lectura · ANTERIOR: ninguna (fichero nuevo)

Completa `DISENO.md` (árbol y reglas de nombres aprobados el 20-11). Fuente: CSV del P74 del run 44871986746 (job 136748336941,
impreso en el log por T-437): **2.042 objetos, 16.466.793.928 bytes (16,47 GB)**. El cruce completo es `CRUCE_claves.csv`
(clave actual, bytes, acción, ruta nueva, motivo; una fila por objeto, suma igual al total del P74).
**No se mueve ni se borra nada.** «Borrar» es «candidata a borrar»: ningún borrado antes del 29-11 ni antes de regenerar, copiar y
verificar, y siempre con frase de campaña D-52 del propietario (D-176/D-178).

## Resumen por grupo y acción

| Grupo actual | Acción propuesta | Objetos | Tamaño |
|---|---|---:|---:|
| `arc-e/paquetes-p10` | mover a `fuentes/por-territorio/…/paquete.zip` (paquete del contrato vigente) | 120 | 9.288 MB |
| `arc-e/paquetes-p10` | **borrar**: versión anterior (solo figura en la evidencia de un territorio, no en su contrato vigente) | 22 | 1.818 MB |
| `arc-e/fuentes/ine` | mover a `fuentes/ine/<año>/` | 19 | 1.548 MB |
| `arc-e/fuentes/nazioenbehatokia` | mover a `fuentes/gobierno-vasco/…` (sin sha12) | 625 | 214 MB |
| `arc-e/fuentes/interior`, `xunta` | mover a `fuentes/interior/2023/`, `fuentes/xunta/2024/` | 5 | 5 MB |
| `arc-p/m06` | mover a `interno/almacen-m06/` tras regenerar (T-416) | 51 | 1.112 MB |
| 19 carpetas de comunidad con nombre antiguo | **borrar** tras regenerar (D-61, D-178) | 209 | 1.983 MB |
| ídem, `principado_de_asturias/40132061626` (única copia de su M08) | conservar hasta publicar (excepción T-416) | 1 | 10 MB |
| 52 `congreso_*` | **borrar** tras regenerar | 516 | 138 MB |
| 52 `nacNN` | doble vuelta fijada → `mapas/nacionales/congreso-2023/<provincia>/`; último run por tipo → `interno/estados/` tras regenerar; resto **borrar** | 52 · 208 · 56 | 0,2 · 55 · 4,5 MB |
| 19 `autNN` | ídem con `mapas/autonomicas/<comunidad>-<año>/` | 15 · 76 · 20 | 0,3 · 79 · 8 MB |
| 3 `congreso350_*` | mover a `interno/competicion/` (T-416: conservar) | 12 | 4 MB |
| `bateria` | **borrar** (retirada en T-303) | 19 | 49 MB |
| `videos` | mover al bucket público de vídeos (D-175/D-178); el marcador `videos/` se borra | 1 · 1 | 152 MB · 0 |
| `doble_vuelta` | los dos informes fijados en `doble_vuelta_publicada.json` → dentro de `mapas/`; los otros 2, **borrar** | 2 · 2 | ~0 |
| `campanas` (9, 2,5 KB) | **decidir**: el run es su clave natural | 9 | ~0 |
| `connection-tests` | **borrar** | 1 | ~0 |

Totales por acción: mover 850 (11,06 GB) · mover tras regenerar 335 (1,25 GB) · borrar 121 (1,88 GB) · borrar tras regenerar 725
(2,12 GB) · conservar hasta publicar 1 · vídeo 1 (0,15 GB) · decidir 9.

## Hallazgos que cambian decisiones

1. **No baja de 10 GB.** Aun borrando todo lo marcado (1,88 + 2,12 GB) y sacando el vídeo (0,15 GB), quedan unos **12,3 GB**: los
   120 paquetes P10 vigentes pesan 9,29 GB y las fuentes INE 1,55 GB (una sola tabla, `30832_…csv`, son 446 MB). La estructura
   nueva ordena; el límite gratuito exige otra decisión (comprimir/recortar paquetes P10, o asumir el coste: unos 0,03 USD/mes por
   cada 2 GB sobre el límite, a 0,015 USD/GB·mes).
2. **22 paquetes P10 antiguos (1,82 GB)** no son el paquete de ningún contrato vigente. D-178 conservó `arc-e` entero «sin listado de 2.º nivel»; este listado lo da. **Decidido el 21-11 (propietario, vía Planificador): se borran junto con la limpieza posterior al 29-11 (D-178)**; siguen marcados «borrar» en `CRUCE_claves.csv` y sujetos a D-52.
3. **Colisión de nombres entre ámbitos.** `aut13` (Madrid) y `nac28` (Madrid), `aut14`/`nac30`, `aut06`/`nac39`… comparten
   nombre en español. Por eso, fuera de `mapas/` (que ya separa ámbito), las carpetas llevan ámbito: `fuentes/por-territorio/{nacionales,autonomicas}/<territorio>/` e
   `interno/estados/{nacionales,autonomicas}/<territorio>/`. **Decidido el 21-11: vale.**
4. **Duplicados:** los 57 del P74 anterior son 2 grupos de tipos: 5 pares de Nazioen Behatokia (mismo ETAG; al quitar el sha12
   del nombre colisionan y se guarda uno) y 52 pares de doble vuelta de `nacNN` (p75 superados; se conserva el fijado).
5. Ceuta y Melilla (`aut18`, `aut19`) no tienen autonómica vigente en `calendario_autonomicas.csv`: su carpeta `mapas/autonomicas/<comunidad>-<año>/` queda con año por fijar.

## Reglas aplicadas (reproducibles)

- **Vigente de un territorio** = `package_sha256` de `territorios/<t>/config/<t>_2025.yaml`. Un paquete P10 que solo aparece en
  `territorios/*/evidencia/` es «versión anterior»; el que no aparece en el repositorio, «sin referencia».
- **Doble vuelta vigente** = run p75 fijado en `configuracion/doble_vuelta_publicada.json` (hoy 44575597009-1 y, autonómicas,
  44747623035-1); los demás p75 son duplicados superados.
- **Último run de su tipo** (`ddd-audit`, `ddd-audit-electoral`, `ddd-minimo-M06/M08`, `ddd-state-…`) por territorio `nacNN`/`autNN`: el de
  mayor id; los anteriores, «solo vigente» → borrar.
- **Año de las fuentes INE:** el del nombre del fichero (`seccionado_<año>`); 2 objetos sin año (`AAAA` en `CRUCE_claves.csv`) se fijan con el manifiesto de fuentes.
- **Nazioen Behatokia:** se quita el sufijo `_<sha12>` del nombre; la carpeta pasa a `gobierno-vasco` (el nombre en euskera sale de la ruta).
- `<año>` de las autonómicas = año de la elección con `vigente=si` en `calendario_autonomicas.csv`.

## Límites

- El mapa de «mover» fija la ruta; el sha12 del nombre y el run pasan al `manifiesto.json` de cada carpeta (§a de `DISENO.md`).
- El cruce es de solo lectura sobre el P74; el módulo de rutas (§c, paso 1) debe regenerarlo y compararlo con este CSV.
- Antes de cualquier borrado: sha256 de cada clave nueva, el manifiesto actualizado y `publicaciones_visor.json` sin citas a R2 (T-416).
