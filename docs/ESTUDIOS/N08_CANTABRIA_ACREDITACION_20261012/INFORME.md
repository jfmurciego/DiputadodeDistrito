# N08 — acreditación territorial de Cantabria
Versión 1.0.0; fecha 2026-10-12; alcance acreditación diagnóstica Cantabria; estado candidato BLOCKED. Cambio: evidencia externa puntual. Motivo: cierre de incertidumbres N08; origen: #251 y fuentes oficiales independientes; sin predecesor.

Base exacta `29502ea86325102b00737023232f5020cfea3061`; rama temporal `codex/n08-cantabria-acreditacion`. Se conservan 458 secciones, 102 municipios, 593.623 habitantes, K=5, 1.208 aristas, dos componentes seccionales y cinco componentes de partes. K nacional=407; `generation_authorized=false`.

Valle de Villaverde es una discontinuidad administrativa legítima, acreditada por BOE/BOC, cartografía independiente IGN y población municipal INE 2025 = 249. Santa Marina y la Torre son islas corroboradas; sus poblaciones parciales permanecen NOT_EVIDENCED. Laredo presenta un banco litoral compatible con entorno intermareal en PNOA 2023; su identidad administrativa precisa y la causa de discrepancia con IGN siguen NOT_EVIDENCED. No se atribuyen habitantes cero a ninguna parte.

Los 28 vacíos se inventarían sin cambios geométricos: territorio comunal Campoo y Cabuérniga (68,700278km²), enclaves palentinos Lastrilla (5,036683km²) y Cezura (1,689797km²), y 25 microvacíos (0,030500414m²). La naturaleza administrativa de los tres mayores está corroborada; sus límites exactos2025 no. Los 25 menores son discrepancias reales del producto bruto, con origen no acreditado: 23 quedan cubiertos al analizar precisión0,0001 m y dos conservan residuos. No hay reparación ni política de admisión aprobada.

Los 30 solapamientos suman por parejas0,096292374m²; son demasiado pequeños para explicar los grandes dominios administrativos omitidos. SOLAPAMIENTOS_30.csv registra cada par, hash, sensibilidad y distancia al vacío más próximo. La proximidad no prueba causalidad. No se convierten en aristas.

A: preparación diagnóstica PASS; integridad/dominio exactos BLOCKED/NOT_EVIDENCED. B: factibilidad del piloto BLOCKED; no existe partición demostrada. C: producción BLOCKED. Este expediente elimina la incertidumbre sobre naturaleza de Valle, dos islas y tres grandes vacíos; quedan población por partes, Laredo, precisión cartográfica y decisiones contractuales. No se declara N08 READY.

Reproducir con `python herramientas/acreditar_cantabria_n08.py --parts-dir <partes-protegidas-INE 2025> --output <directorio-nuevo>`. Entorno registrado en REPRODUCCION_INDEPENDIENTE.md. Sólo se extrae Cantabria del ZIP protegido para el contraste; no se reconstruye el producto nacional ni se alteran sus 55 artefactos. GEOMETRIAS.json.gz contiene únicamente las siete partes nominales y los 28 vacíos necesarios para reproducir sus identificadores originales, sin duplicar las 458 geometrías completas.

Evidencia individual: RESULTADOS.json, VACIOS_28.csv, MULTIPARTES.md, VALLE_DE_VILLAVERDE.md, FACTIBILIDAD.md. Procedencia: FUENTES.json y recibos originales. Decisiones literales: DECISIONES_PENDIENTES.md. Las fuentes cartográficas puntuales PNOA/MTN son evidencia de diagnóstico, sin publicación de mapas de distritos.
