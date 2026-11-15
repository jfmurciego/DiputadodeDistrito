# Traspaso del Operador (15-11, ~11:45 Europe/Madrid)

- Saliente: session_01KQDtFqw1LBgGn6nCuxP8Yx. Relevo decidido por el Planificador porque el contexto está alto.
- No hay nada en vuelo:
  - el vigilante de T-349 está parado;
  - no queda ningún run lanzado por mí en curso.

## Campaña activa: `2026-11-15_deslinde11-r4`
- Ficha: `docs/autorizaciones/2026-11-15_deslinde11-r4.md`.
- Estado: PARADA, con **reanudación condicionada**.
- Frase literal del propietario (15-11, ~11:12): «Reanuda la campaña 2026-11-15_deslinde11-r4 desde el piloto aut11 cuando el arreglo T-349 esté en main con la CI en verde.»
- T-349 es el arreglo para que un paquete electoral con id no canónico no se reutilice y se prepare de nuevo.
  - El 15-11 a las ~11:40 aún NO estaba en `main`.
  - Ojo: «Plan 1.0.50 … cola T-342 a T-349» (#817) no es T-349.
- Al cumplirse la condición:
  1. La base de la congelación pasa al commit que contiene T-349 en el que pruebas-plataforma está en verde. Anótalo en la ficha.
  2. Repite la P00 del piloto aut11 con:
     - `territory_id=11 Extremadura`, `data_edition=2025`;
     - `execution_mode=Generar desde fuente territorial acreditada`;
     - `optimization_algorithm=Canónico`, `motor=motor2`;
     - `publication_mode=territorial_only`, `publish_result=false`, `cadena_electoral=true`.

     Usa el P10 r4 43691914540, ya verificado y archivado (43694583130). No rehagas el P10 ni el archivo.
  3. Si la cadena entera sale bien (territorial, «Activación de Legislatura» y la 00 electoral «Reutilizar» del bot), siguen los pasos 1, 2 y 4 de la ficha para los otros 70. El paso 5 (P50) solo tras #765 (D-111).

### Antecedentes del piloto
- Intento 1, 43694989383: defecto del cargador de `territorio_ids` (lo arregló T-338, #808).
- Intento 2:
  - territorial 43698495438: CERTIFIED, con el M06 en R2;
  - Activación 43701739818: success, pero hizo REUSE de `ddd-electoral-package-extremadura-2025-42720735134`;
  - electoral 43701871746: la puerta 03→04 quedó BLOQUEADO con `PAQUETE_ELECTORAL: territorio o edición no coincide`.
- Ese defecto afecta a los 71: todos los paquetes electorales registrados son anteriores al renombrado.

## Reglas del propietario añadidas hoy (vía Planificador)
- Toda PARADA, fallo no transitorio o fin de tanda se avisa **al momento** al Planificador (session_01KQDtFsURitLodmiR3KkgF3) con `send_message`, en una línea: qué, run y causa. También los éxitos de tanda.
- Antes de cada lanzamiento, comprueba las entradas contra la ficha.
- Al terminar cada run, mira su conclusión y el resumen PREPARÓ/ADQUIERE/REUTILIZÓ de cada fase.
- Nada de paradas falsas: si dudas, lee el log del paso antes de parar.

## Scripts (`docs/autorizaciones/operador_r4_scripts/`; en el original las rutas apuntan a la scratchpad del saliente: ajústalas)
- `r4.sh`:
  - encadena el piloto (P10 → verificación → archivo → P00 con cadena) y luego las tandas de P10 de 10 filas, el archivado y las P00 en tandas de 5;
  - es reanudable por marcas `ok_*` y `since_*`;
  - lee la base de la congelación del fichero `base`;
  - con `STOP_AFTER_PILOTO=1` sale tras el piloto, para poder avisar.
- `verif.sh <run_p10> <id>`:
  - criterio válido: en el log de «Preparar fuentes territoriales», el `ddd-source-execution` tiene `decision=ACQUIRE`, `restored_from_checkpoint=false`, `acquired_at` de la r4 y el artefacto es `ddd-source-package-<id>-2025-<run>`;
  - resultados ya verificados: `verif_r4.txt`.
- `tanda_multi.sh <filas>`:
  - despacha las P00 y espera las cadenas (P00 y Activación) creadas desde `SINCE`;
  - corta en cuanto termina un run que no es success.
- `p10.sh`, `archivar.sh` y `mapa_ids.py`: P10 por filas, archivo P10 → R2 (`bateria-motor.yml`) y mapa de etiqueta a id canónico.
- `espera_t349.sh`: vigilante de la condición. Solo fija `base`; no lanza.
- Ficheros de resultados en `docs/autorizaciones/`:
  - `p10_r4_resultado.tsv` y `p10_r4_paquetes.tsv`;
  - `archivo_p10_r4_resultado.tsv`;
  - `regeneracion_r4_intento2.tsv` y `regeneracion_r4_intento1.tsv`.

  `regeneracion_r4_resultado.tsv` no existe ahora: se crea al lanzar la P00. Si queda una fila de un intento anterior, `tanda_multi.sh` la salta.

## Lecciones (paradas falsas y vigilantes)
1. `REGISTERED_RUN_ID`/`REGISTERED_ARTIFACT_NAME` del P10 es el candidato consultado, no una reutilización. Lo que vale es el JSON `ddd-source-execution` (decisión y `restored_from_checkpoint`) y la línea «Fuentes del P10: ADQUIERE…» del resumen.
2. Un vigilante que busca «T-NNN» con `git log --grep` coge commits del plan que solo nombran la tarea. Busca el título que empieza por `T-NNN:` y comprueba el diff.
3. Esperar a que no quede ninguna 00 en curso antes de mirar resultados retrasa el aviso de un fallo hasta una hora. Corta al primer run terminado que no sea success.
4. La CI de main: mira 100 runs y descarta los cancelados (los empujes de robot se cancelan entre sí); con 10 hubo una falsa «main en rojo».
5. Antes de repetir una P00, aparta del TSV de resultados la fila del intento anterior y la marca `since_*`. Si no, la tanda se salta o recoge el run viejo.
6. Desde la nube no se pueden bajar artefactos ni borrar releases (proxy): no se puede comparar el sha256 del crudo de un paquete. Sí se leen los logs de jobs y los commits de robot (huellas materializadas en `territorios/<id>/config/<id>_2025.yaml`).
7. Al propietario no se le piden comandos: está en Windows y le ha costado varios fallos.
