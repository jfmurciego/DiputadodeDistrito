# T-418 · Doble vuelta desde R2 (opción nueva de P70 Archivo) — diseño corto

VERSIÓN: 1.1.0 · FECHA: 2026-11-19 · ESTADO: propuesta, con las 4 decisiones aprobadas por el Planificador y la revisión de #923 · ANTERIOR: 1.0.0 (misma PR, sin fusionar)

Objetivo (D-178/D-179, prioridad V4): sin regenerar, calcular dv_base, dv_A y dv_B de los 52 territorios del Congreso (`nac`) a partir de lo que
ya está en R2 y dejar los datos que lee la V4 (T-413 §5). Solo lectura sobre git; solo escribe objetos nuevos en R2. No lanza ni publica.

## 1. Opción en el botón (D-129/D-130)
Una acción más en `accion` de `p70-archivo.yml` (una familia, opciones dentro): **«P75 Doble vuelta desde R2»**. Sin entradas nuevas:
`territorios` (vacío = los 52 `nac`) y `eleccion` (vacío = 2023-07), que ya existen. Los 19 `aut` quedan fuera (tabla de bloques solo de generales).
Job nuevo `doble_vuelta_r2`, un solo job que recorre los territorios en serie (≈ 85 MB en total; sin matriz). Grupo de concurrencia
`archivar-artefactos-r2` (único escritor en R2). Permisos `contents: read`; sin entorno `produccion` (no borra nada).

## 2. Por territorio
0. **Territorios**: los del Congreso por el resolutor (`territorio_ids.ambito == NAC`, nunca por prefijo). Un `aut` o un id desconocido en `territorios` se rechaza.
1. **Run vigente**: `resultados_ligeros.vigente_por_eleccion(canonical_m08, <fecha de la elección>, ambito=NAC)`: el run mayor DE ESA ELECCIÓN (un run de 2026, mayor, no cuenta).
   El registro del visor trae cada territorio con su id nuevo (`nacNN`) y con el legacy (`congreso_*`) y las claves de R2 (`<carpeta>/<run>/ddd-minimo-<run>-M08.zip`) llevan
   el legacy: se localiza el paquete **por run** en `archivo_r2.json`. Carpeta y run son los del archivista, no propios.
2. Baja `ddd-minimo-<run>-M08.zip` de R2 y comprueba su sha256 contra `archivo_r2.json`; si no coincide, el territorio queda `SHA_DISTINTO`. Si el M08 vigente no está en R2:
   `SIN_PAQUETE_EN_R2` (falla el territorio, consta en el informe y el job sale en rojo, pero el resto sigue).
3. Informa de si trae `…_m07_resultados_partido.csv`. Sin él: `SIN_CSV_M07`, no se calcula (nunca reconstruir votos) y se lista para **regenerarlo en cuanto P75 lo diga**.
4. La elección la fija la entrada (`eleccion`, por defecto 2023-07): el paquete no lleva el YAML de parámetros que la nombra. Guarda: si más del 5 % de los votos no casa con el alias
   (`COBERTURA_BAJA`), no se calcula y se avisa de elección distinta o alias incompleto.
5. Ejecuta `doble_vuelta.py --alias … --detalle …` (+ `doble_vuelta_cobertura.py`) con la tabla de bloques y el alias de `main`.
6. Sube la salida a R2 con **objetos nuevos**: nada se sobrescribe ni se borra.

## 3. Salidas (siempre claves nuevas, con el run de P75)
- `<carpeta>/<run>/ddd-doble-vuelta-<run>-p75-<run_p75>.zip` (`doble_vuelta.csv`, `detalle.csv`, `cobertura.json`, `manifiesto.json`) y
  `doble_vuelta/<AAAA-MM>/<run_p75>/INFORME.json` (una fila por territorio: run, sha256 de entrada y salida, `trae_m07`, % sin casar, estado, clave). `run_p75` = `GITHUB_RUN_ID`.
  La V4 lee el informe del último run de P75; cada ejecución deja el suyo.
- Resumen del job (tabla) y artefacto del run (14 días) con el mismo informe.
- Criterio de hecho: 52/52 calculados o los restos listados uno a uno con causa.
- **Territorios sin el CSV de M07**: se regeneran EN CUANTO P75 diga cuáles son, con la 00 «Generar desde fuente» (no se espera al 29-11; la prioridad es la V4 y el propietario
  firma el lanzamiento). Si son más de 5, se avisa al Coordinador antes.

## 4. Archivos compartidos y pruebas
`.github/workflows/p70-archivo.yml` (turno exclusivo; copia 1.0.0 en `legacy/workflows/`), `tests/test_t368_p70_equivalencia.py` (fija las opciones de P70:
se amplía con la nueva) y la descripción del input `territorios`; las demás acciones no cambian (fixture congelado, no `legacy/`: en CI no está). Nuevos: `herramientas/p75_doble_vuelta_r2.py` (núcleo sin red con el cliente de
`archivar_artefactos_r2.py` inyectable) y `tests/test_t418_p75.py` con R2 simulado: sha256 distinto, paquete sin CSV, elección distinta, éxito, determinismo.
No toca `modulos/`, `doble_vuelta.py` ni el visor. PR única `no-automerge`.
**Puerta del workflow**: job `doble_vuelta_r2` con `contents: read`, `queue: max` en el grupo `archivar-artefactos-r2` (un solo escritor en R2), `timeout-minutes: 90`, las credenciales R2
(`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID`, `R2_BUCKET`) en el `env` del PASO como el resto de jobs y SIN credenciales nuevas; las entradas llegan por `env`, no
interpoladas en el script.

## 5. Decisiones (aprobadas por el Planificador: «ok a T-418 con las 4»)
1. **Registro**: solo R2 (`INFORME.json` por ejecución); el publicador P40 de la V4 deja el sha256 en git. 2. **Numeración**: `district_id` interno (0..K-1); convierte el publicador.
3. **Detalle**: el de #907. 4. **Sin CSV de M07**: regenerar solo esos, ya (00 «Generar desde fuente»), sin esperar al 29-11; si son más de 5, avisar antes.
