# N08 — preflight sobre diagnóstico topológico nacional real
Versión 1.2.0; nombre puerta Congreso N08; fecha 2026-10-12; alcance diagnóstico sin piloto; estado BLOCKED.
Anterior: legacy/n08/N08_PREFLIGHT_v1.1.0.md.
Cambio/motivo: sustituir ausencia de diagnóstico por resultados 52/52 ejecutados, auditados y con bloqueos nominales. Base b583c52128daa85c14de9def0c9a3cb7d5f5e92e.

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
| Huecos y dominio provincial independiente | NOT_EVIDENCED | Vacíos encerrados medidos y registrados; sin límite independiente que permita clasificarlos como agua/enclave/déficit y comprobar cobertura exterior |
| Política nacional de contigüidad/excepciones | BLOCKED | Islas/enclaves/discontinuidades siguen pendientes; sensibilidad de frontera/redondeo no constituye aprobación |

## B. Factibilidad del primer piloto (Cantabria)

| Requisito | Estado | Evidencia/límite |
|---|---|---|
| Entradas y grafo Cantabria | PASS | 458 secciones, 593.623 habitantes, K=5, 1.208 aristas; auditoría geométrica independiente PASS |
| Contigüidad y población de todos los componentes | BLOCKED | Valle de Villaverde: componente de 249 habitantes; tres secciones Laredo/Ribamontán al Mar/Santander repartidas entre partes sin población desagregada; cinco componentes físicos no prueban cinco distritos viables |
| Disciplina municipal y unidad mínima | BLOCKED | Cinco municipios discontinuos por partes; política de corte/indivisibilidad y unidad mínima no aprobadas |
| Límites poblacionales internos | BLOCKED | Seis opciones cuantificadas; propuesta única ±15% sobre P_i/K_i pendiente de aprobación. Cantabria: 100.915,91–136.533,29; enclave249 impide suelo ordinario bajo contigüidad estricta sin excepción acreditada |
| M01–M03, interfaces diagnóstico | PASS | Lectura/join reales y pruebas funciones reales/sintéticas; grafo nacional auditado; no extrapolar a producción |
| M04–M06, consumo/resultado nacional | BLOCKED | Validadores de entrada/salida y pruebas sintéticas aisladas; sin partición real ni política aprobada; no se acredita factibilidad/ejecución productiva |

## C. Autorización de ejecución productiva

BLOCKED. El encargo autoriza diagnóstico, validadores, pruebas, revisión y PR borrador. No autoriza piloto ni generación; las decisiones pendientes conservan su estado contractual. PASS de A no implica PASS de B ni de C. No declarar N08 READY.

Expediente completo: docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/. Los componentes de partes con población no asignable llevan NOT_EVIDENCED, nunca cero. El manifest original del constructor clasifica B inicialmente NOT_EVIDENCED; este preflight posterior lo clasifica BLOCKED tras el análisis nominal y de límites.

Siguiente acción técnica precisa: cerrar registro acreditado del enclave y partes de Cantabria, contrastar vacíos/dominio y política de precisión sin alterar originales; obtener decisiones explícitas de contigüidad/excepciones, unidad mínima, disciplina municipal y límites. Después, integrar las guardas nacionales M04–M06 y solicitar autorización separada de ensayo.
