# NAT-D-004 — Componentes físicos y K

**Resultado:** nueve unidades tienen más componentes poligonales que K; dos unidades (CPRO09 y CPRO34) tienen más componentes en el grafo seccional de frontera lineal que K. La tabla reproducible es `D04_COMPONENTES_MAYORES_QUE_K.csv` (SHA256 `6f6238c763e0bfb7d5b34ae05c557fc0b378449561eb1d7909f7933774097a1f`), derivada del lote 52/52 SHA256 `0595df6237b183c9f6499c16e28ff7da7331ab54d46f4f2a00f1c5564f10efc5`. Cada fila incluye SHA del informe y checkpoint provincial.

| CPRO | K | Componentes de partes | Componentes seccionales | M04 |
|---:|---:|---:|---:|---|
| 04 | 6 | 8 | 1 | PASS_NECESSARY_ONLY |
| 07 | 10 | 144 | 4 | PASS_NECESSARY_ONLY |
| 09 | 3 | 12 | 4 | BLOCKED |
| 15 | 9 | 21 | 1 | PASS_NECESSARY_ONLY |
| 17 | 7 | 71 | 2 | PASS_NECESSARY_ONLY |
| 27 | 3 | 9 | 1 | PASS_NECESSARY_ONLY |
| 30 | 13 | 25 | 1 | PASS_NECESSARY_ONLY |
| 34 | 1 | 6 | 3 | BLOCKED |
| 36 | 8 | 9 | 2 | PASS_NECESSARY_ONLY |

## Interpretación

Los componentes de partes poligonales no equivalen a componentes de distritos: una CUSEC multiparte conserva una sola identidad electoral y no crea una arista entre sus partes. El conteo `componentes_partes_fisicas > K` señala casos que requieren analizar qué partes pueden agruparse dentro de cada CUSEC y qué tratamiento excepcional de islas/discontinuidades puede ser necesario. No acredita por sí solo imposibilidad.

En CPRO09 (4 componentes seccionales, K=3) y CPRO34 (3 componentes seccionales, K=1), una partición de K grupos todos físicamente conectados no puede cubrir los componentes sin cruzar componentes o usar una excepción aprobada: cada grupo conectado queda contenido en un solo componente, así que serían necesarios al menos tantos distritos como componentes. El preflight expresa esta condición necesaria como M04 `BLOCKED` y conserva `feasibility_proven=false`. Los datos actuales no identifican ni autorizan una excepción individual; por ello no se declara imposibilidad general ni se conecta componente alguno artificialmente.

Todas las cifras proceden del preflight actual enlazado a la herramienta SHA registrada en el lote. No se generaron asignaciones territoriales ni se ejecutó generación.
