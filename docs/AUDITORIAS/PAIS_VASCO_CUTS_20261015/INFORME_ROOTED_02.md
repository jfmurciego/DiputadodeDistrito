# País Vasco — PV-CUT-02, cortes de conectividad con raíz

**Dictamen del ensayo:** `NEGATIVE_BOUNDED`; no hay candidata conectada ni base para declarar infactibilidad. Revisión independiente: `PASS_ACOTADO` para la validez de la formulación rooted y los controles examinados. El resultado queda limitado a este modelo y límite.

## Identidad y entrada

- M04 auténtico del run `37458584767`: artefacto SHA-256 `56979163e7b14ead11682e194277cc3b96ed54c8db3c62fe7857de8952d8a83d`.
- GeoJSON M04 usado por el modelo: SHA-256 `4a3d363de1c81381900eebecbc10c5ccc1e0beced11d1c385ca9d135978d7c13`.
- Grafo operativo M03: SHA-256 `8d3f19d66bb718a772ca75c36c18165b547c26a6a67f7ba10afa5213f2a2b316`.
- Dimensiones verificadas al cargar: 1.713 secciones, 281 unidades indivisibles, K=75, población 2.227.684, 694 aristas entre unidades, 29 unidades congeladas y 29 distritos enteramente congelados.
- Runtime: Python 3.11.14, NumPy 2.4.2, SciPy 1.17.0. Script final SHA-256 `b932f0472d6faac181691755f494b09eac3b5df457931ca01c5ab19e8d31a3a5`.

## Método y controles

Se reemplazó el corte sin raíz (PV-CUT-01) por una desigualdad condicionada a una raíz binaria exactamente seleccionada dentro de cada distrito: `x(S,d) - x(N(S),d) - |S| r(S,d) <= |S|-1`. Las raíces están limitadas por la asignación; toda unidad congelada está fijada a su distrito de entrada. El MILP preserva K, población total, floor/cap, provincia, unidades indivisibles y límites de partición municipal. Cada incumbent se audita contra el grafo M03; los desconectados reciben cortes y no pueden aceptarse.

Tres pruebas sintéticas de la desigualdad pasaron: corte de un componente desconectado no raíz, admisión de un distrito conectado igual al componente, y admisión cuando el componente tiene frontera asignada. `py_compile` pasó. La primera invocación del script abortó antes del solver (4,38 s) por consultar una variable raíz para un par unidad/distrito no admisible. Se restringió la consulta a variables existentes, quedó asentado en el preregistro y esa invocación no generó incumbent ni corte.

Presupuesto fijado antes de la búsqueda efectiva: 120 s de solver total, 100.000 nodos acumulados, máximo 12 resoluciones, 6 GiB de memoria virtual y supervisor wall de 130 s. No hubo reintentos ni extensión.

## Resultado

- Supervisor: 121,009 s; terminación normal del script (`returncode=0`), sin timeout del supervisor.
- Solver: 120,244 s wall; 140,681 s CPU de proceso; máximo RSS medido en 643.604.480 bytes; 49 nodos agregados; 10 resoluciones; 42 cortes.
- Las 10 resoluciones devolvieron incumbents, pero cada asignación mantenía distritos desconectados. En la última, 2 distritos tenían múltiples componentes; el solver alcanzó su límite durante la décima resolución.
- Todas las asignaciones de incumbents satisfacían las cotas poblacionales modeladas (`hard_violations={}`), pero no satisfacían conectividad. El último incumbent movía 5 unidades; no se promueve ni se valida como solución.
- No existe archivo de asignación candidata. No se ejecutaron M06, `validar_ejecucion.py` ni auditoría geométrica porque no hubo asignación conectada admisible.
- SHA-256 de `rooted_result.json`: ver `MANIFEST.json`. Supervisor: `rooted_supervisor.json`; hashes de stdout/stderr constan dentro.

La observación cuantitativa es que, al forzar sucesivamente los incumbents de mínimo movimiento a evitar componentes desconectados, la búsqueda produjo 42 cortes y llegó a incumbents de 5 movimientos sin conectar todo el mapa dentro del límite. Esto **no** dice que no exista solución: el solver no probó infactibilidad y el límite se agotó.

## Limitaciones y revisión

La salida JSON conserva el detalle de cada incumbent intermedio, pero ninguno es una candidata territorial; sus asignaciones no deben usarse para M05/M06. La revisión independiente de PV-CUT-01 encontró correctamente que su corte no enraizado podía excluir una partición válida; dicho ensayo no sustenta una conclusión algorítmica. Se solicitó revisión independiente de la formulación enraizada de PV-CUT-02. Hasta recibirla, esta nueva exploración es telemetría experimental con pruebas algebraicas locales, no método validado.

**Siguiente paso:** esperar dictamen sobre validez global de la desigualdad enraizada. No repetir este MILP ni incrementar el presupuesto. Si el corte se valida, el resultado sigue siendo `NEGATIVE_BOUNDED`; investigar otro mecanismo requeriría hipótesis y presupuesto preregistrados nuevos.
