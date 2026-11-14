# Autorización: poda de releases antiguas (T-285)

- Frase literal del propietario (chat del Operador, 2026-11-14): «Autorizo borrar las releases antiguas que no son de mapas (borradores de ensembles y cyl-m06-checkpoint-temp).»
- Alcance: 33 borradores `ensemble-*` y `cyl-m06-checkpoint-temp` (34; `poda_releases_2026-11-14/lista.tsv`, 1,51 GB).
- Retenidas (referenciadas en `publicaciones_visor.json` y `catalogo_procedencia.json`): `ensemble-congreso-la-rioja-cccc4a1e8df2`, `ensemble-congreso-salamanca-2b68dd0a396a`, `ensemble-congreso-sevilla-9987893f2689`. Pendiente de decisión del propietario.
- Fuera de la frase: `almacen-m06-*` (6) y `viewer-*` (2) borradores; `mapa-*` y `fuente-infoelectoral-02202307`.
- Ejecución: el proxy de la sesión cloud devuelve 403 al DELETE de releases. La ejecuta el propietario con `poda_releases_2026-11-14/borrar_releases.sh`.
