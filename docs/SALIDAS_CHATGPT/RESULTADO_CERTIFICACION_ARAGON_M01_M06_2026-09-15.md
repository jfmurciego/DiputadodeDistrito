# Resultado de certificación Aragón M01–M06 — 2026-09-15

## 1. Resultado ejecutivo

**PASS.** Aragón queda certificado de M01 a M06 con la topología depurada que exige una frontera compartida mínima de **1 metro**. El run territorial canónico de esta certificación es **GitHub Actions `34960965537`**, ejecutado sobre el commit **`5e151b38e686daa9c1c552741be6f0e638d599c6`** y concluido en `SUCCESS`.

El nuevo baseline conserva las **1.463 secciones**, **1.364.621 habitantes**, **K=67**, el reparto provincial **Huesca 11 / Teruel 7 / Zaragoza 49**, `hard=0`, `fuera_12=0`, contigüidad completa por grafo, provincia única por distrito, disciplina municipal y conservación exacta del universo M01→M06.

La topología reconstruida y certificada contiene exactamente **1.463 nodos y 4.063 aristas**, sin nodos aislados. El `maxdev` real de M06 es **`0.11820424865218981`**. Siguiendo la convención histórica del repositorio, el nuevo trinquete se fija a 12 decimales en **`0.118204248652`**, manteniendo la tolerancia técnica `+1e-9` de la prueba de regresión.

El anterior trinquete **`0.099299365905`** deja de ser canónico porque fue obtenido sobre el grafo anterior, que admitía contactos puramente puntuales. Al exigir `min_shared_border_m=1.0` cambia el conjunto de adyacencias y, por tanto, el espacio de soluciones territoriales admisibles. No es metodológicamente válido exigir al nuevo grafo el óptimo de un espacio topológico distinto.

No se ha ejecutado ni promovido **Aragón-10** ni **Aragón-50**.

## 2. HEAD y runs relevantes

- HEAD de partida indicado al abrir esta intervención: `ea6b305640af34f700e1954315f66314b1219035`.
- Primer intento de certificación: run `34959925108`, sobre `d4d6da38b07ee5a668c533a4b8501d6ad6a116c1`, **FAIL antes de M01** por `permission denied` al ejecutar `/app/procedimiento.sh` dentro del contenedor. Este run no aporta conclusión territorial.
- Corrección del arranque del workflow: commit `9846b0e29b7de10878b7b947d9529a029883758e`; CI `Pruebas DDD — R015` run `34960497443`, `SUCCESS`.
- HEAD ejecutado por la certificación válida: `5e151b38e686daa9c1c552741be6f0e638d599c6`.
- Run territorial canónico: `34960965537`, `SUCCESS`.
- Preservación legacy de configuración Aragón 7.12.0: commit `f4b5460f14febce8cdcf05a2ca1db7af67e9199c`.
- Preservación legacy de regresión Aragón 1.5.0: commit `cf2dcd0e47fc17d8e82f08d887fd8c44cfc02b57`.
- Configuración Aragón promovida a 7.13.0 con nuevo baseline: commit `565e03b6368762440b82ee959c452fb5b87c2341`.
- Trinquete de regresión actualizado: commit `bd99d9c0a1b5dc921884f6d3fdb1924ed3c2f946`; CI run `34961886871`, `SUCCESS`.
- Precisión documental del valor canónico a 12 decimales: commit `0761814336bfc9e551e9aa4346b5ea15bdcc8713`; CI run `34962033632`, `SUCCESS`.
- HEAD funcional inmediatamente anterior a crear este informe: `0761814336bfc9e551e9aa4346b5ea15bdcc8713`.

El commit que contiene este propio informe se obtiene después de ese último HEAD y, por definición, no puede autorreferenciarse dentro de su propio contenido sin crear una cadena recursiva de commits.

## 3. Certificación M01→M06

| Módulo | Evidencia | Resultado |
|---|---|---|
| M01 | `rows=1463`, `missing_population=0` | PASS |
| M02 | `edges=4063`, `geometric=4063`, `bridges=0`, `predicate=touches`, CRS `EPSG:25830`, `min_shared_border_m=1.0` | PASS |
| M03 | `nodes=1463`, `edges=4063`, `isolated=0`, `provincias_bad=0`, `municipios_bad=0` | PASS |
| M04 | K=67; cuotas `{'22':11,'44':7,'50':49}`; `hard=0`; `outside_tol=0`; min=18.237; max=22.775 | PASS |
| M05 | `hard=0`; `fuera_12=0`; `max_rel_dev≈0.1182`; `greedy=0`; `anneal=0`; `changed_units=0` | PASS |
| M06 | K=67; 1.463 secciones; población=1.364.621; `fuera_12=0` | PASS |

### M04

La ruta primaria heredada se ejecuta y el núcleo 7.4.6 activa el fallback determinista ya aprobado cuando es necesario. En el run certificado se registra **`fallbacks=1` y `accepted=1`**. El wrapper canónico es M04 **7.6.1**. La solución resultante cumple `hard=0` y `outside_tol=0` sin reintroducir contactos puntuales, sin crear puentes y sin relajar suelo, techo, K ni provincias.

### M05

M05 recibe ya una solución dentro de tolerancia y no necesita alterar la asignación: `changed_units=0`, sin movimientos greedy ni de recocido aceptados. Por tanto, el resultado M04 permanece territorialmente idéntico en M05.

### M06

M06 consolida exactamente las mismas 1.463 asignaciones sección→distrito. La identidad de asignaciones **M04 = M05 = M06** ha sido comprobada sección a sección. Los ZIP no son byte-idénticos porque cada producto tiene su propia serialización/archivo; la identidad certificada es la del universo y la asignación territorial.

## 4. Población y nuevo maxdev

Target regional: **20.367,4776119403** habitantes por distrito.

- Distrito con menor población: **52**, **18.237** habitantes, desviación relativa **`-0.10460193709462193`** (-10,4601937095 %).
- Distrito con mayor población y peor desviación absoluta: **49**, **22.775** habitantes, desviación relativa **`+0.11820424865218981`** (+11,8204248652 %).
- `hard=0`.
- `fuera_12=0`.
- `maxdev` real M06: **`0.11820424865218981`**.
- trinquete canónico almacenado: **`0.118204248652`**.

El redondeo a 12 decimales mantiene la misma convención con la que estaba expresado el trinquete R016 `0.099299365905`.

## 5. Universo, provincias, municipios y contigüidad

### Universo

- M01: 1.463 secciones.
- M04: 1.463 secciones asignadas.
- M05: 1.463 secciones asignadas.
- M06: 1.463 secciones consolidadas.
- Población total M06: **1.364.621**, coincidente con el universo preparado.
- No hay pérdidas, duplicados ni reasignaciones ocultas entre M04, M05 y M06.

### Provincias

Todos los distritos contienen una única provincia. Reparto final exacto:

- Huesca (`22`): **11** distritos.
- Teruel (`44`): **7** distritos.
- Zaragoza (`50`): **49** distritos.

No existe ningún cruce provincial.

### Disciplina municipal

Solo aparecen divididos los tres municipios cuya población excede el techo duro aproximado de 35.643 habitantes:

- **Huesca**: 55.033 habitantes, 3 distritos; exactamente un distrito residual mixto.
- **Teruel**: 36.521 habitantes, 2 distritos; exactamente un distrito residual mixto.
- **Zaragoza**: 699.007 habitantes, 34 distritos; cero distritos mixtos.

Ningún municipio que cabe bajo el techo duro ha sido dividido. Se cumplen las reglas de cardinalidad municipal y `max_mixed_districts_per_split_municipality=1`.

### Contigüidad por grafo

Se reconstruyó independientemente la adyacencia con la semántica activa de M02 —`touches`, CRS `EPSG:25830`, frontera compartida mínima de 1 metro— y se obtuvieron exactamente **4.063 aristas**, sin aislados. Los **67/67 distritos** inducen un único componente conectado en ese grafo.

Por tanto, la contigüidad por grafo queda certificada bajo la nueva topología.

## 6. Identidad y hashes de productos

Artefacto GitHub Actions del run `34960965537`:

- nombre: `ddd-production-34960965537-1`
- tamaño: **14.038.770 bytes**
- digest del artefacto: **`sha256:fa6225c22e0045772a7928e70cc30b670fc24b282e75558724a5cd233ded4892`**

SHA-256 registrados en `MANIFIESTO_EJECUCION.json`:

| Producto | SHA-256 |
|---|---|
| `aragon_2025_m04_informe.json` | `0b9bfb40899da5997486c4a52bc264d85941bea633d00aee46c2cb54fe86597e` |
| `aragon_2025_m04_semillas.geojson.zip` | `321d6d630851f2f7c0b5033da3c34ed86c1d443c99377b1368c43cca29f6c454` |
| `aragon_2025_m05_distritos_optimizados.geojson.zip` | `effa814003fb9fb9f8fd88991cbbdd090928848d5c2b098040d5f9ec47a3195b` |
| `aragon_2025_m05_informe.json` | `a9a857bca444aa8bbf24b86fb3f8f7026d95223d4de0efa388b621f8ab8b93f8` |
| `aragon_2025_m06_catalogo_distritos.csv` | `ce3aba59e6340790cbb864da0cdc94a23f6179f79c84a4f5cd978286d56f2193` |
| `aragon_2025_m06_composicion_distritos.csv` | `b3928cd2595077f24f74c6b2fec0a03120113edc377dac002765080a4c219c3d` |
| `aragon_2025_m06_distritos.geojson.zip` | `2e56a6e92cef704dc51bda9ceedd780e92d3ff7f8232a5bc68e56fe2194c6e62` |
| `aragon_2025_m06_resumen_distritos.csv` | `f2dbbb5d54b65d8b584d7740921b39328f2fcf88c70a8018bafa971743409c30` |
| `aragon_2025_m06_secciones.geojson.zip` | `822bda83e7a8762f6bf0292074f7ab4775630a2b29bd3ad01d57fdb98d2a45b3` |

SHA-256 de la configuración utilizada por el run: **`6fe966fe64f733b584078630dfd8c5fc1fa6aebf2a32e6581781d249b89a9370`**.

Los productos de preparación M01–M03 se materializan en `.cache` y no quedaron incluidos en el artefacto de ejecución subido por este workflow; sus métricas están demostradas por los logs del run, pero no se atribuyen aquí hashes de fichero que el artefacto no contiene.

## 7. Sustitución del baseline y del trinquete

### Valor antiguo

`0.099299365905` era el maxdev canónico de R016 / Run #9, obtenido sobre el grafo anterior. La regresión activa de Aragón lo utilizaba como trinquete duro.

### Razón de obsolescencia

Con `min_shared_border_m=1.0` se eliminan aristas que representaban exclusivamente contactos puntuales o fronteras inferiores al mínimo métrico. Esto cambia la conectividad disponible para construir y optimizar los distritos. El resultado anterior puede seguir siendo un dato histórico válido, pero **no es un límite de regresión comparable para el nuevo grafo**.

No se ha relajado la tolerancia política/metodológica de ±12 %. El nuevo `maxdev` de 11,8204 % sigue dentro de ella. Lo que cambia es únicamente el baseline técnico de regresión para una topología diferente.

### Nuevo valor

- maxdev real observado: `0.11820424865218981`.
- trinquete canónico: **`0.118204248652`**.
- tolerancia numérica de comparación: `+1e-9`, igual que en el mecanismo anterior.

## 8. Ficheros modificados y preservación legacy

Se han realizado exclusivamente los cambios necesarios para fijar el baseline y conservar sus predecesores:

- `legacy/configuracion/aragon_2025_v7.12.0.yaml` — copia exacta de la configuración sustituida.
- `territorios/aragon/config/aragon_2025.yaml` — versión 7.13.0, baseline M01–M06 con topología métrica certificada y nuevo maxdev.
- `legacy/workflows/regresion-m06-aragon_v1.5.0.yml` — copia exacta del workflow de regresión sustituido.
- `.github/workflows/regresion-m06-aragon.yml` — versión 1.6.0, trinquete actualizado a `0.118204248652`.
- `docs/SALIDAS_CHATGPT/RESULTADO_CERTIFICACION_ARAGON_M01_M06_2026-09-15.md` — este informe de cierre.

Antes de cada escritura se releyó el estado del fichero objetivo. Durante la intervención otras sesiones avanzaron `main`; cuando ocurrió, se volvió a tomar el HEAD y el SHA del fichero afectado antes de escribir. No se sobrescribió ninguna modificación concurrente del mismo fichero.

## 9. Fallos e incidencias

El único fallo operativo previo a la certificación fue el run `34959925108`: el bind mount del checkout sobre `/app` ocultaba el `procedimiento.sh` de la imagen al que se había aplicado `chmod +x`, y el contenedor intentaba ejecutar directamente una copia sin permiso ejecutable. El workflow se corrigió para invocar el script mediante `/bin/bash`. La CI de esa corrección quedó verde antes de lanzar la certificación válida.

Ese primer run abortó antes de M01 y, por tanto, no constituye una ejecución territorial fallida ni evidencia contra M01–M06.

## 10. Límites respetados

En esta certificación no se ha modificado:

- `ddd_ensemble/**`;
- código GerryChain;
- `docs/ESTADO_MAESTRO_PROYECTO.md`;
- BITACORA;
- `REGISTRO_DE_CAMBIOS.md`;
- Google Drive;
- nomenclatura pública de workflows.

No se ha ejecutado **Aragón-10** ni **Aragón-50**.

## 11. Punto exacto de reenganche

**Baseline territorial canónico de reenganche:**

- territorio: Aragón 2025;
- run: **`34960965537`**;
- configuración: **`territorios/aragon/config/aragon_2025.yaml` v7.13.0**;
- topología: `touches` + `min_shared_border_m=1.0`;
- grafo: **1.463 nodos / 4.063 aristas / 0 aislados**;
- K: **67**;
- reparto: **11 / 7 / 49**;
- `hard=0`;
- `fuera_12=0`;
- nuevo trinquete: **`0.118204248652`**.

La tarea de certificación M01→M06 queda cerrada en este punto. Cualquier cambio futuro en la topología, en M01–M06 o en el contrato territorial deberá reentrar por una nueva certificación M01→M06 contra este baseline. Este cierre **no autoriza ni implica** ejecutar o promover Aragón-10 o Aragón-50.
