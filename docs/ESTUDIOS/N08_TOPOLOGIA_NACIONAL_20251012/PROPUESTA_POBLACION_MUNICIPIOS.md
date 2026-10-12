# Propuesta única, pendiente del propietario
Versión1.0.0; fecha2026-10-12; alcance análisis de seis opciones reales; estado NOT_APPROVED; origen nuevo.

Recomendación: mantener 120.000 como referencia institucional para K; utilizar P_i/K_i como centro operativo provincial y tolerancia ordinaria ±15%, preservando Soria/Ceuta/Melilla como excepciones poblacionales expresas. No crea nuevas excepciones provinciales. Fronteras provinciales duras. La indivisibilidad municipal absoluta debe descartarse como regla general: preservar municipios contiguos cuando quepan y sean compatibles con equilibrio; permitir subdivisión necesaria por secciones oficiales en municipios grandes o cuando equilibrio/conectividad lo exijan, minimizando cortes municipales como objetivo secundario. Toda sección multipartes necesita tratamiento acreditado específico antes de usarla como unidad atómica. Nunca inferir pasarelas ni población de partes por área.

Las seis alternativas comparan ±10/15/20% alrededor de referencia fija y promedio provincial. El centro provincial evita incompatibilidades aritméticas impuestas por el redondeo de K, sin sustituir la regla aprobada. ±15% es una propuesta intermedia: datos y casos afectados expuestos para decisión; no se atribuye optimalidad ni factibilidad suficiente. Municipios por encima del techo exigirían varios distritos si se adoptase ese límite; los listados nominales con población y mínimo de distritos aparecen en FACTIBILIDAD_OPCIONES.json. Las aristas/anomalías, los componentes diminutos y secciones desconectadas no se resuelven ampliando tolerancias.

| Centro | Tolerancia | Media provincial fuera del intervalo | Provincias con bloqueo de componentes | Provincias incompatibles con municipio indivisible | Municipios > techo | Secciones > techo |
| --- | --- | --- | --- | --- | --- | --- |
| reference_120000 | 1/10 | 05,16,19,21,32,34,40,44,47,49 | 24 | 33 | 51 | 0 |
| reference_120000 | 3/20 | 05,16,19,32,34,40,49 | 22 | 33 | 51 | 0 |
| reference_120000 | 1/5 | 05,34,40,49 | 19 | 31 | 47 | 0 |
| provincial_mean | 1/10 | ninguna | 16 | 33 | 53 | 0 |
| provincial_mean | 3/20 | ninguna | 16 | 31 | 48 | 0 |
| provincial_mean | 1/5 | ninguna | 16 | 31 | 46 | 0 |

Límites se calculan con fracciones exactas: por cada componente ceil(P/cap)≤k_c≤floor(P/floor), con al menos una plaza y k_c≤n_secciones; luego sum(min)≤K_i≤sum(max). Componentes de cero población también requieren cobertura, de modo que no se omiten. Las excepciones poblacionales no dispensan contigüidad ni eliminan componentes físicos.

Falta aprobación expresa del propietario sobre centro y tolerancia, unidad mínima, regla de cortes municipales y tratamiento nominal de discontinuidades. Esta recomendación sigue el mandato de representación directa del proyecto, no los350 escaños ni Hamilton; no constituye dictamen jurídico de viabilidad constitucional o legislativa. No altera decisiones actuales ni configura el motor productivo.
