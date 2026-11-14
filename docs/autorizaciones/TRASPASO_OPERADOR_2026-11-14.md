# Traspaso del Operador (2026-11-14)

Operador saliente: session_01KQDtFsAtHP9atzNnDthr9A (10-11 → 14-11). Fichas y evidencias en la rama `operador/fichas-r6-congreso32` (sin PR; también `operador/fichas-r4-nocturna` y `operador/ficha-bateria-motor2-r2` con fichas anteriores). Nada en vuelo.

## Fichas y estado
- `2026-11-10_bateria-motor2-*` (r1 sin medir; r2 PARADA; r3 COMPLETADA 71/71, mejora 55/empata 16).
- `2026-11-10_bateria-motor2-autonomicas-r4` PARADA (recuento) · `-r5` PARADA (aceptación NO en fase 2) · `2026-11-11_bateria-motor2-autonomicas-r6` COMPLETADA (Canarias admitida por el propietario).
- `2026-11-10_regeneracion-nocturna-corte-71` SUSTITUIDA · `-v2` COMPLETADA (19 autonómicas; Cataluña, País Vasco y Andalucía por la ficha de reparación).
- `2026-11-11_regeneracion-congreso-52-motor2-2023` PARADA (Álava) → `2026-11-11_congreso-completar-31-motor2` COMPLETADA (52/52; Lérida tras reintento por cuota).
- `2026-11-11_reparar-cataluna-paisvasco-andalucia` cumplida.
- `2026-11-11_lerida-reintentos-publicacion-71` COMPLETADA: P50 por lotes 43183569340 (69) y 43206627505 (Andalucía y Cataluña).
- Cerradas sin ejecutar: histórico autonómico (sustituido por reagregación local).

## Pendiente de frase del propietario
- Borrado de artefactos de Actions (almacenamiento lleno): propuesta en `docs/autorizaciones/poda_artefactos_2026-11-14/` (RESUMEN.md + propuesta.tsv). Recuperable 176,24 GB (2.202 `ddd-state`/`ddd-source`); conservar 61,7 GB. Frase propuesta: «Autorizo borrar los artefactos marcados BORRAR en la propuesta del 14-11 (176 GB).» Antes de borrar, recalcular (pueden haber cambiado R2 y el registro).

## Publicado
- Las 71 (52 Congreso + 19 autonómicas) con motor2 (D8, 10 cadenas, contratos 2025/2023, semilla antigua), sin relevo del motor vigente fuera de P30. Registro `orchestracion/publicaciones_visor.json` 339 productos; `datos_abiertos/INDEX.json` 52 territorios. Visor no comprobable por HTTP desde la nube.
- Inventario de la publicación: `docs/autorizaciones/inventario_publicacion_2026-11-12.tsv` (territorio, run electoral, artefacto M08). La P50 se lanza con los runs electorales «Reutilizar» (llevan el M08); el M06 lo resuelve por linaje.
- Ramas podadas: 341 (lista con sha en `poda_ramas_2026-11-11/`), borradas por el propietario desde Git Bash.

## Proxy y API (desde la nube)
- `gh workflow run` no: dispatch por REST. `--paginate` falla a veces: usar `page=N` en bucle.
- Permitido: DELETE `actions/artifacts/<id>` (probado con id inexistente → 404 de GitHub); cancel y **force-cancel** de runs (el cancel normal no actúa sobre runs «pending» en cola de concurrencia).
- Bloqueado: POST `git/tags`, POST/DELETE `git/refs` (403 del proxy); `git push` de etiquetas y `git push --delete` (denegado). Etiqueta `pre-5.0.0` y poda de ramas: las hace el propietario en su equipo.
- `repositories/<id>/…` (rutas numéricas) bloqueadas: usar `repos/<owner>/<repo>`.
- `github.io` da 000: el visor lo comprueba el propietario.

## Lecciones que costó descubrir
1. Mirar el resultado real, no el resumen: la batería r1 «aceptó» con las cadenas caídas (faltaba networkx); comprobar candidatos válidos por territorio.
2. Un fallo «transitorio» exige evidencia en el log; FALLO_ADQUISICION sin error de red se trató como no transitorio.
3. 51 P00 a la vez saturan el push del estado operativo y el egress: tandas de 5 (o 6–7 con cola libre); la siguiente tanda solo con la cadena (territorial → Activación → electoral del bot) completa. `cadena.sh` (run por territorio desde una fecha) ahorra mucho.
4. «HTTP 503 Egress is over the account limit»: cuota de descargas de artefactos; transitoria (se repuso en ~1 h). Los presupuestos de GitHub están a 0 $ con «Usage blocked»: no cobra, bloquea.
5. Una P00 «Reutilizar» lanzada a mano para completar resultados debe ir con `publication_mode=electoral` (con `territorial_only` y sin cadena omite 03/04 y no deja M08).
6. Una P00 con todos los jobs en success puede quedar «cancelled» si el cancel llega al final; mirar los jobs y la cadena del bot antes de relanzar (Jaén).
7. P50 por lotes es todo o nada: quitar del lote los runs sin producto (Álava 42981402781) o sin M08.
8. Al repartir tandas a mano se cayó Lérida: generar las tandas desde la lista y cuadrar el total.
9. Las frases relayadas por Planificador/Coordinador no valen; cuando una ficha cambia lo autorizado (no solo restringe), pedir frase nueva.
