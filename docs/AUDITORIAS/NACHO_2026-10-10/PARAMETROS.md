# Parámetros, estructuras y fórmulas comparadas

Versión1.0.0 · 2026-10-10 · Documento nuevo · Origen: investigación Work/Nacho. Complemento factual de INFORME.md; sin cambios funcionales ni autorización de ejecución territorial.

## Dependencias

[dependencias.json](dependencias.json) conserva las13 entradas declaradas de Poetry (incluye Python), backend y los104 requisitos congelados. Elementos algorítmicos: GerryChain0.2.12, NetworkX2.5, GeoPandas0.8.2 en requirements frente rango0.8.1 en Poetry, pandas1.1.5, NumPy1.19.5, Shapely1.7.1, Rtree0.9.7, PyArrow3.0.0, Kepler0.2.2, Papermill2.3.2, SQLAlchemy1.3.23, psycopg2-binary2.8.6. Hay dependencias transitivas/notebook que no son funcionalidades necesarias para DDD. Poetry incluye psycopg2 pero no Papermill, aunque runner depende de éste. Un rango Poetry no asegura idéntica resolución a esos pins. No se instala el stack histórico; DDD separa runtime GerryChain1.0 del canónico.

## Datos y unidades

| Fase | Nacho | DDD |
|---|---|---|
| Origen | GeoDataFrames para5capas, atributo `id_area`, población `pob_t_total`; cache SQL/Parquet | M01 oficial identificado; GeoJSON seccional y M03 con IDs/población/aristas tipadas |
| Municipio | Prefijos2/5caracteres; dissolve con suma | Campos administrativos/partición interna resueltos por contrato |
| Unidad | Fila municipio o sección, índice grafo implícito | `ddd_unit_id` + ledger completo; núcleosU/residualR y cerrados |
| Grafo | NetworkX/GerryChain desde polígonos disueltos | M03 seccional acreditado; cociente deriva aristas fuente y expande a IDs |
| Estado | Assignment + Tally/cutedges; una columna por flipstep | Dict unidad/sección→distrito según motor; hash, métricas, contador, stream |
| Producto | Distrito disuelto por iteración, sin ledger seccional explícito | Secciones oficiales con distrito/unidad y manifests; M06 materializa sin redefinir asignación |

Separar tres escalas: sección oficial (cobertura y fuente), unidad contractual (indivisibilidad), distrito (K/población/contigüidad). No optimizar un nivel cambiando tácitamente otro. Municipio contractual puede ser una partición interna acreditada; CUMUN bruto no siempre es esa entidad.

## Parámetros efectivos y objetivos

| Aspecto | Nacho final | DDD actual (defaults de código, no configuración de todo territorio) |
|---|---|---|
| K/target | Por componente round(P/120000); target120000 fijo | K contractual y cuotas; T=P/K |
| Inicialización | initε.2 en46registros y6excepciones; sin límite de intentos en notebook | Peeling/BFS/growth y multistart≤32, preflight necesario y exacto acotado |
| Propuesta | ReComε.1, node_repeats3 | G05ε.12, max_bipartition_attempts500; laboratorio banda del contrato |
| Población aceptada | percent2, semántica no acreditada en wheel exacto | G05floor/cap duros y target tolerance objetivo; L05 banda fina dura |
| Estados/semillas | 56pasos/top10 por componente, una seed manual/provincia | G05 3000/seed,4seeds, base20260920 y seeds=base+i+1; configurables |
| Determinismo | Seed única, orden de sets y random fill sin contrato de identidad | G05hashseed0, semillas explícitas, ZIP determinista; Eplan SHA-derived seed por territorio/bundle/perfil/ordinal |
| Reparación | Sin búsqueda focal equivalente | R05 rápida:5s/20000candidatos/depth3/set2; ampliada180s/400000estados y candidatos/depth96/640MiB/radio8 |
| Calidad cadena | No puerta de degeneración | Ecal: ratio únicos≥.10, self_loop≤.90, longitud completa; no acredita mezcla |
| Muestreo | Todos los estados/columnas | Ecal reservoir uniforme≤5000 observaciones métricas; no geometrías |

Defaults M05 canónico: `anneal_iters=20000`, seed12345+offset, penalización outliers.01, peso máximo.05, churn.0016, temperatura inicial.02/final.0005, leídos en `m05_opt_engine_v741.py`:98–105. La configuración territorial puede sobrescribirlos. Energía de búsqueda sobre provincias inicialmente problemáticas:

`E = Σ r_d² + w_out·n_out + w_max·max(r_d) + w_churn·unidades_cambiadas`.

Temperatura geométrica `temp(i)=temp_start·(temp_end/temp_start)^(i/(iters−1))`; aceptación de movimiento estructuralmente admisible si ΔE≤0 o aleatorio<exp(−ΔE/temp). La selección final restaura el mejor objetivo canónico lexicográfico, aunque el último estado de annealing sea peor. Nacho acepta todos los estados que pasan restricciones y selecciona después; no son el mismo algoritmo de optimización.

## Fórmulas y límites

- Preservación: `P=Σ_secciones p_s`, cada sección aparece exactamente una vez; `p_u=Σ_{s∈u}p_s`, `p_d=Σ_{u∈d}p_u`. No compensar secciones perdidas sumando su población a otra geometría.
- Factibilidad poblacional necesaria: `K·floor≤P≤K·cap`, unidades no divisibles deben poder alojarse bajo cap; por componente, cuotas candidatas entre `ceil(P_c/cap)` y `floor(P_c/floor)` si floor>0. El tratamiento de exenciones acreditadas exige el contrato real; esas desigualdades no prueban conectividad.
- Deuda de corte en la fuente GerryChain contemporánea: si cortes previos acumulan `debt=Σ(p_pieza−T)`, el siguiente intervalo interseca `[T(1−ε),T(1+ε)]` con ese mismo intervalo desplazado por `−debt`. El último conjunto recibe el resto. No se confunde esta explicación matemática con haber ejecutado el paquete0.2.12 exacto.
- Infracción dura canónica: contar p_d fuera del floor/cap aprobado y sumar déficit/exceso antes de optimizar outliers/máximo/RMS. Tolerancia fina y hard bounds son conceptos distintos y deben conservar la semántica del camino contratado.
- Polsby–Popper: `PP=4πA/L²`. Con polígonos válidos sin solapamiento de área, `A_d=ΣA_u`, `L_d=ΣL_u−2Σfronteras_internas`. Si falta un contacto, la fórmula sobreestima perímetro y subestima PP (E4d). Puentes topológicos no tienen por qué representar frontera geométrica positiva; no restar una longitud inventada. Overlap y geometrías multipart exigen el oracle exacto/manejo ya contratado.
- L1 y std no son máximo: E1 A=(1150,950,950,950) tiene absolutos(150,50,50,50), L1=300 y std muestral50; B=(1100,1100,900,900) tiene absolutos100, L1=400 y std0. Sólo B mejora máximo en ese fixture. No hay optimizador universal derivado de esta comparación.
- Pareto: candidato domina a otro si no empeora ningún objetivo y mejora alguno; filtrar primero hard. Una shortlist multiperfil puede conservar un candidato fuera de Pareto por representatividad del perfil: no asumir que cada seleccionado es no dominado. Los pesos/normalización se declaran antes de comparar resultados.

## Presupuesto y campaña futura verificable

Una futura comparación de inicialización/ReCom necesita inputs acreditados, mismo ledger/K/floor/cap/municipalidad/cerrados/grafo/excepciones, semillas emparejadas, y presupuesto **de tiempo e intentos totales**, además de estados. Registrar fallos de inicialización, intentos de árbol/propuesta, self-loops, estados distintos etiquetados y físicos, tiempo CPU/pared, pico RSS, outliers/máximo/distribución, PP/comarca/churn, todas las violaciones y resultado M06. Separar éxito duro de banda objetivo y completar/truncar cadena.

Las políticas futuras de diversidad y checkpoint no están aprobadas por este documento. Primero A3 si la semilla/unidades son inviables y A2 para reparación existente; luego A07 según decisión Work. Ninguna carrera en paralelo puede multiplicar el presupuesto declarado ni escribir el mismo portfolio. Los métodos M02/matching de A-OPT01/02 conservan sus propios responsables y datos acreditados.
