# N08 — preflight sobre diagnóstico topológico nacional real
Versión 1.3.0; nombre puerta Congreso N08; fecha 2026-10-12; alcance diagnóstico sin piloto; estado BLOCKED.
Anterior: legacy/n08/N08_PREFLIGHT_v1.2.0.md.
Cambio/motivo: añadir acreditación focalizada Cantabria sobre #251, sin reconstruir producto nacional. Base 29502ea86325102b00737023232f5020cfea3061.

N06 y K=407 permanecen aprobados. Fuentes INE 2025/2025 y sus hashes intactos: 36.554 secciones, 49.128.297 habitantes, 52 cuotas desde población acreditada. generation_authorized=false. No piloto, 00 ni M01–M08 productivos.

## A. Preparación topológica nacional

| Requisito | Estado | Evidencia/límite |
|---|---|---|
| Identidad, join, población, cuotas y CRS | PASS | ZIP protegido y WKB idénticos a #241; CUSEC exacto; atributos originales, EPSG:25830; INVENTARIO_52.csv y manifest |
| Cobertura diagnóstica 52/52 | PASS | 52 checkpoints completos y reproducibles, sin omitir componentes o secciones aisladas |
| Grafo de frontera física justificada | PASS | 99.597 aristas, frontera lineal >0 y overlap=0, hashes de contacto; sin autorreferencias/duplicadas/interprovinciales; auditor independiente recomputa todos los contactos |
| Separación físico/operativo | PASS | Ninguna pasarela; grafo operativo idéntico al seccional raw; multipartes no se acreditan como tránsito físico |
| Inventario de componentes y municipios | PASS | 77 componentes seccionales, 397 de partes poligonales, 538 municipios discontinuos; miembros, poblaciones y CUSEC sin desagregación conservados |
| Integridad topológica completa | BLOCKED | 498 pares de solapamiento intraprovincial y 7 interprovinciales; no existe política aprobada para repararlos/admitirlos |
| Huecos y dominio provincial independiente | NOT_EVIDENCED | Cantabria: 28/28 contrastados: Campoo comunal, Lastrilla/Cezura palentinos y 25 microvacíos de origen no acreditado; dominio exacto 2025 pendiente por discrepancia temporal/precisión IGN. No acredita otras 51 unidades |
| Política nacional de contigüidad/excepciones | BLOCKED | Islas/enclaves/discontinuidades siguen pendientes; sensibilidad de frontera/redondeo no constituye aprobación |

## B. Factibilidad del primer piloto (Cantabria)

| Requisito | Estado | Evidencia/límite |
|---|---|---|
| Entradas y grafo Cantabria | PASS | 458 secciones, 593.623 habitantes, K=5, 1.208 aristas; auditoría geométrica independiente PASS |
| Naturaleza administrativa de Valle y población | PASS | BOE/BOC enclave cántabro; IGN independiente; INE Nomenclátor 2025 = 249 y única sección 3910101001 conciliada; sin identidad geométrica exacta entre ediciones |
| Naturaleza insular Santa Marina y la Torre | PASS | IGN/RCC, topónimos, BOE/ayuntamientos corroboran dos islas; identidad exacta 2025 no acreditada |
| Laredo, población por partes y contigüidad electoral | BLOCKED | Laredo contexto intermareal probable, PNOA 2023, identidad jurídica precisa NOT_EVIDENCED; tres secciones con 3.382 habitantes sin reparto certificado; excepciones Valle/islas NOT_APPROVED. Cinco componentes no prueban partición viable |
| Contraste de 28 vacíos y 30 solapamientos | PASS | Inventario 28/28 y 30/30 reproducido; naturaleza de tres grandes corroborada; 25 microvacíos de origen no acreditado, sin reparación |
| Admisión de precisión y dominio exacto 2025 | BLOCKED | Población Campoo y política de precisión pendientes; no se equiparan recintos IGN 2026 a límites exactos INE 2025 |
| Disciplina municipal y unidad mínima | BLOCKED | Cinco municipios discontinuos por partes; política de corte/indivisibilidad y unidad mínima no aprobadas |
| Límites poblacionales internos | BLOCKED | Seis opciones cuantificadas; propuesta única ±15% sobre P_i/K_i pendiente de aprobación. Cantabria: 100.915,91–136.533,29; enclave249 impide suelo ordinario bajo contigüidad estricta sin excepción acreditada |
| M01–M03, interfaces diagnóstico | PASS | Lectura/join reales y pruebas funciones reales/sintéticas; grafo nacional auditado; no extrapolar a producción |
| M04–M06, consumo/resultado nacional | BLOCKED | Validadores de entrada/salida y pruebas sintéticas aisladas; sin partición real ni política aprobada; no se acredita factibilidad/ejecución productiva |

## C. Autorización de ejecución productiva

BLOCKED. El encargo autoriza diagnóstico, validadores, pruebas, revisión y PR borrador. No autoriza piloto ni generación; las decisiones pendientes conservan su estado contractual. PASS de A no implica PASS de B ni de C. No declarar N08 READY.

Expediente completo: docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/. Los componentes de partes con población no asignable llevan NOT_EVIDENCED, nunca cero. El manifest original del constructor clasifica B inicialmente NOT_EVIDENCED; este preflight posterior lo clasifica BLOCKED tras el análisis nominal y de límites.

Siguiente acción técnica precisa: obtener deslinde RCC/DPMT aplicable a Laredo 3903503001:p0000 y certificación agregada de 2025 por partes/Campoo, vinculados a hashes originales. Obtener decisiones nominales de excepciones, unidad mínima, disciplina municipal, precisión y límites; implementar registro/guardas nacionales M04–M06 y probar sintéticamente antes de solicitar autorización separada de ensayo. Expediente nuevo: docs/ESTUDIOS/N08_CANTABRIA_ACREDITACION_20261012/. No modifica compatibilidad ni estados de las otras 51 unidades.
