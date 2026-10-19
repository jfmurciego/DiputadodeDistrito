<!--
Nombre: Benchmarks territoriales de integración de M02 v7.3.3
Versión: 1.0.0
Fecha: 2026-10-19
Alcance: verificar la implementación M02 integrada selectivamente sobre main
Estado: evidencia experimental reproducible
Cambios/motivo: registrar comparación exacta de aristas con checkpoints históricos
Anterior: no aplica; primera edición de esta evidencia
-->

# OPT-01 — benchmark territorial sobre el candidato de integración

## Identidad

- Base del candidato: `48688c939a46d6be23078f2a1dfa1da286dd23c0` (AUTO-01 sobre `main` `21a4a150eb14f1abecd5d798b159d84a71df1f4a`).
- Código ensayado `modulos/02_construir_adyacencias.py`: SHA-256 `7e588c5454620bbca18d27ed49c670f6740a20aa40031bae128716c40bc6a42f`; coincide con el código territorial revisado en el expediente fuente.
- Pruebas M02, orquestación y consumidor Nacional: 62 passed, 12 subtests, 1 advertencia GeoJSON.
- Entorno del benchmark: Python 3.13.12; GeoPandas 1.1.2; Shapely 2.1.2; PyProj 3.7.2; Pyogrio 0.12.1.
- La memoria `ru_maxrss` se registra como bytes en macOS aunque el script histórico nombre el campo `max_rss_kb`.

## Resultados con artefactos auténticos

Para Cataluña y Murcia se comparó el conjunto completo de pares geométricos históricos con el producto de `iter_edges`, bajo `contact`, EPSG:3035, frontera compartida mínima de 1 m, solapamiento máximo de 1 m², buffer/simplificación 0. Se ejecutó el algoritmo nuevo con `max_candidates=0`, `50` y repetición; también v7.3.2 con ambos límites.

| Run / artifacts | Secciones y aristas | Resultado exacto | Tiempo observado |
|---|---:|---|---:|
| Cataluña `37453376100`, M01 `11408501059`, M02 `11407882609` | 5.117 / 14.315 | v7.3.3 (0, 50, repetición) coincide byte a byte con el histórico; 0 missing, extra o duplicados. SHA conjunto `0dc494dad59c9621d63db47a4fd36b03834840dcaf35a91e5d6ca537cdcb6576`. | 16,35–18,46 s por pasada |
| Murcia `37344628042`, M01 `11359368761`, M02 `11360262231` | 1.223 / 3.416 | v7.3.3 (0, 50, repetición) coincide; v7.3.2 con límite 50 omite `3001902001—3002202001` (3.415 aristas); v7.3.3 no pierde aristas. SHA nuevo/histórico `8ae16664ba47d29a5d03d953a4cbb3d21b8cd549d071654a803b08b0113f8b9a`. | v7.3.3 4,16–4,59 s; v7.3.2 cap 50 4,24 s |
| Aragón `34584775443`, M01/M02 artifacts `10193135816`/`10193136386` | 1.463 / 4.293 | Coincidencia exacta y determinista con el contrato histórico `touches`, EPSG:25830, min border 0 y cap 50. No acredita la configuración contractual actual de Aragón. | 4,15–5,04 s |

La configuración actual de Aragón tiene SHA-256 `4462020f0e90f4044ee763422227caf5c5469866541660c3bf26f28fc2527499`, distinta de la configuración histórica identificada en la evidencia fuente (`c5ffe01f3e4762088a735c2e4157b61b41a3ddb7e8717fd028611a4d8995af74`). Por eso Aragón se declara solo PASS del contrato histórico comparable. Las configuraciones actuales de Cataluña y Murcia coinciden con los hashes del expediente fuente.

Los artefactos exteriores M01/M02 contrastados: Cataluña `11408501059` SHA `1a2a5e6ddffc30a4b486f1951da8ffadda0c93d92b03e401317acb8cde759224`, `11407882609` SHA `dbbfd4a136138508f263bd1282514c5adccb45fd1d01491f2dc4a666e75a4e9f`; Murcia `11359368761` SHA `23227a2e0137c240dd7a84668e9da16e98954e5ba1bcf347b40b03a2a3135b96`, `11360262231` SHA `c00fe77814cf68b1ce9652786cd7315784e5deb0ad70dfcc46355988d9dc62ad`; Aragón `10193135816` SHA `d21c6f675c63e3abb7eb322ba35bcdf26cc980df7740b57786bcc73b2a8264bd`, `10193136386` SHA `c7e2dc716fbbf6f01ffa6d580990a2b9335c3275c9d6538c7777ea2b92d3ab40`.

Los resultados exhaustivos se conservan en `results/real-m02-results.json` (SHA-256 `ae45a3e4cfcb411f67151e7c397704cbd4c43b504238a189a60f4e660de741ca`) y `results/aragon-m02-results.json` (SHA-256 `f1fae98423192514a947e77bbe794abc5608c13c34018a7445a51ab875fdee04`). Memoria máxima observada para cada script en esta repetición: 200.142.848 bytes (Cataluña/Murcia) y 139.489.280 bytes (Aragón).

## Alcance

No se modificaron geometrías, fuentes ni tolerancias. Esto valida la enumeración M02 con estos checkpoints auténticos y contratos; no reacredita los otros territorios ni autoriza M03/M04 o generación. Los certificados vinculados al blob M02 anterior deben invalidarse/fallar cerrados hasta que haya evidencia compatible con el nuevo blob.
