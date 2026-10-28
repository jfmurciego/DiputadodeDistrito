# Ensayo PV-CUT-01 — resolución incremental de cortes de conectividad

- Hipótesis: el MILP relajado ya encuentra asignaciones poblacionalmente factibles en dos movimientos; cortes de conectividad separados iterativamente pueden excluir sus componentes desconectados con menos variables que el flujo multicommodity anterior y hallar una asignación final conectada.
- Entrada autenticada: checkpoint M04 de run `37458584767`, ZIP SHA-256 `56979163e7b14ead11682e194277cc3b96ed54c8db3c62fe7857de8952d8a83d`; grafo operativo M03 SHA-256 `8d3f19d66bb718a772ca75c36c18165b547c26a6a67f7ba10afa5213f2a2b316`. El inventario local con 146 archivos y los tres ZIP oficiales ha sido verificado íntegramente contra su manifiesto.
- Modelo: mismo conjunto de variables y restricciones poblacionales, provinciales, municipales, indivisibilidad y congelación del ensayo 07. Cada componente desconectado hallado en una solución se corta mediante la desigualdad válida `sum(x[u,d], u in S) - sum(x[v,d], v in frontera(S)) <= |S|-1`. Cada candidata solo es éxito si los 75 distritos son conexos en el grafo M03.
- Diferencia respecto de ensayos cerrados: no agrega flujos de conectividad a priori; agrega cortes válidos iterativamente y vuelve a optimizar el mismo objetivo de minimizar unidades reasignadas. No reutiliza secuencia manual ni búsqueda determinista anterior.
- Presupuesto total preregistrado: máximo 120 s wall, 100.000 nodos acumulados de solver, 12 resoluciones; memoria virtual máxima del proceso 6 GiB. No se amplía tras fallo.
- Éxito: asignación conectada con `hard=0`, K=75, conservación del universo/población, provincias, municipios, unidades indivisibles y congelación intactos. De existir, se conserva como candidata experimental; no se promueve ni valida M06 productivo en este ensayo.
- Parada: candidata admisible, presupuesto agotado, modelo infeasible o máximo de iteraciones. Un resultado negativo es acotado y no prueba infactibilidad global.
- Código del ensayo: `pv_iterative_connectivity_cuts.py`; SHA-256 se registra en `result.json` junto con las entradas y versiones.

## Enmienda preregistrada antes de la corrida corregida

La primera implementación del script terminó en 120 s, pero una revisión posterior encontró que el conjunto `allowed` fijaba distritos totalmente congelados y no unidades congeladas individuales en distritos mixtos. Se preserva su reporte como `result_pre_fix_invalid.json`, explícitamente invalidado y no admisible. Se corrigió el conjunto permitido y se añadió una aserción de pinning para cada unidad congelada. La corrida siguiente repite una sola vez PV-CUT-01 con el mismo presupuesto (120 s / 100.000 nodos / 12 resoluciones / 6 GiB); es necesaria para validar la corrección de implementación, no una ampliación del presupuesto.
