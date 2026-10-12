# A2 — M05 v7.8.4: búsqueda autónoma experimental opt-in

## Alcance del cambio

Actualiza el contrato documental M05 a v1.4.3 para identificar el wrapper activo v7.8.4 y preservar como predecesor v1.4.2 en `legacy/`. La estrategia autónoma se describe como experimental y privada; no modifica ni activa el comportamiento predeterminado.

Integra `private_annealing` con aceptación atómica y validación oficial. R1
reconstruye estados y poblaciones desde las asignaciones finales; R2 dirige al
staging las salidas configurables de M06, incluido su diagnóstico, y preserva
productos anteriores ante rechazo, timeout o error. El reparador vigente y sus
valores predeterminados no cambian. La estrategia requiere `enabled: true` y
`strategy: private_annealing`; permanece desactivada por defecto.

La configuración experimental validada fue seed `4629`, `max_seconds: 150`,
`max_candidates: 800000`. Esos límites corresponden a los ensayos, no son defaults
ni un SLA. C-01 emite `UNSUPPORTED` cuando se solicita auditar `private_annealing`,
porque el auditor no varía su semilla anidada y no puede certificar su robustez.

## Evidencia autónoma Madrid — runs 12 y 13

Ambos runs usaron entradas, contrato, configuración normalizada y semilla
idénticos. Encontraron candidata en el intento 627.431 y produjeron la misma
asignación canónica SHA-256
`ebc2590a4d60851d803bf6548189f89ca55d2f0970304e1c4ccf8150ff8f15f9`. La salida
tiene `hard=0`, K=135, 4.479 secciones y 6.871.903 habitantes; conserva las 90
unidades urbanas congeladas y declara 23 distritos fuera de tolerancia blanda.
M06 oficial v7.2.2, `validar_ejecucion.py` y auditoría geométrica pasan en ambos
runs: 130 PASS, cinco excepciones justificadas y cero bloqueos. Los hashes ZIP
de M05/M06 difieren entre runs por empaquetado; la asignación canónica coincide.

Identidades de entrada:

- ZIP exterior del artefacto M05 original: `artifact-11353290857.zip`, SHA-256
  `6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c`.
- Checkpoint M05 interno usado por ambos runs:
  `519ba8ab03c6089ee2a269bbeddcd40081645bcaf802e0922350c4fcf37f38c6`.
- Grafo M03: `34ac24c2be4ec810caff0d8170f54dfdf00b79fd575b1e80f8f362143c8152ec`.
- Contrato Madrid: `8e2b2d7f705a95a2c9ec92afbfedbd259d68e4fcc1e526136f3da0c91a0ea6de`.
- Configuración normalizada común: `220de01562029206d8ca5489c51879c9beca308a6df892972e3ab89ba0f86ec7`.
- `params.yaml` run 12: `f01a5ec2be8754dab1c526c4a163b0ed6a883ee61b1dca2d6600467f7099b5a7`.
- `params.yaml` run 13: `97186cf2a4b735afef2915ca45c0d28135e0f98824f1d883ed50e8f73a646f08`.

Hashes de ejecución verificables:

- `m05_private_annealing.py`: `d873a1762542367e92b17c0ffb5be87ac7b8b16716b6a60814fefe25d9934b2d`.
- Wrapper M05: `e9d20d223dd1f884ec974832095b553395b2324b562ef743a678b742dc9ef958`.
- M06 v7.2.2: `16e61eeb6bc455756c91a1a26aa92cdc5ec8bf2a0a5974f51ee215b6fff21864`.
- `validar_ejecucion.py`: `36328723b2be93b6c22c2079c5cb8dd17e77eb94e5c172ee234726888349d0e4`.
- Auditor geométrico: `45b263e53ac93578d90e31bcab7212550f414d465181bcc2cb3e49c89027e463`.
- Reportes M05 run 12 / 13: `71732a3256a29e58d48d2ed7ae996513ecea16317441de35c1f0f044ba585baa` / `b9737ee8fe1f715de8e983284a8e2300b83ca1be1942d90e47a0634dd4d2fdd5`.
- Logs M06 run 12 / 13: `ac03559a4bb181a60266fee1e30d14d44bdbe47ad88a1e4c1889eef79208bc58` / `6ba5adb6b0e5f54bd653618fdbcb309671e5aeaac63a5b3d73b834ab6498ca36`.
- Validador run 12 / 13 (mismo log):
  `806b0bf4b34167fbf4d2b30a8f393c43d93c383b0f3cf45a2024aa01dcf560ec`.
- Auditoría geométrica run 12 / 13:
  `58dbdd34f6ce1a40e9078dc2d419573caa5de692720bbf2eb4d11a39f667fec2` /
  `4a34a950835e1de00a57d1cadca124afd6feb05c94265bf4227faf7779f10304`.

El manifiesto completo del expediente persistente tiene SHA-256
`152348a4b50451842b5b2b6be7675ee53b19209cec150a6f6e01757efeb13d7b`; su lista
`SHA256SUMS.txt` tiene SHA-256
`b8b0e02464197859d69cac064796d5e7c56b793c67303fbc0eb28ad2f007fb64`. Los bytes,
logs, parámetros, productos y dictámenes se conservan fuera de Git en
`/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/artefactos/A2_V784_DIAGNOSTICO_TIEMPO_20261012/`; no se incluyen los productos geográficos
voluminosos en el diff.

## R1/R2, regresiones y revisiones

R1/R2 recibieron PASS acotado de código y pruebas dirigidas en la revisión del
paquete `DDD_A2_CORRECCION_R1_R2_REVISION_CHAT.zip`; el dictamen completo
`reference/prior_review/REVIEW_FINAL.md` tiene SHA-256
`b4b8ca89c9dcb01047f89afd169131ffa4d6c35d7067b7f1b5a830d365302d4f`. Ese
`REVIEW_NO_GO` era por los runs 10/11 sin candidata; los runs 12/13 posteriores
resolvieron esa puerta. El dictamen independiente de ejecución de runs 12/13,
`DICTAMEN_REVISOR_EJECUCION.md`, tiene SHA-256
`44f7cc415b4d8bd60345cb8dd7b4573573c7a3ea52b54bfcdb3804eae36cad08` y es PASS
acotado.

Sobre el candidato funcional original pasaron 48 pruebas M05/M06 y 61 M04/
contratos. Sus logs tienen SHA-256 `a9cd2fe33ee8bccda5460a25be428c0469fb2c90be4579004e5642d80e69a32b` y
`60630b1332ab29400e2c8a20e9724729ea28b97c64a75ff78084a86b5dd31d84`. En esta
base de integración también pasan las pruebas dirigidas de C-01, annealing,
coherencia R1, staging y rollback (resultado de esta rama en el expediente
local). La PR solicita CI y revisión del HEAD final.

## Límites

**A2 es experimental y opt-in. No activa Madrid en producción, no certifica
Madrid ni el Motor Nacional, no habilita A3 y no supone certificación nacional.**
No cambian contratos, K, tolerancias ni parámetros predeterminados. No se declara
Madrid certificado ni se promueve una asignación productiva.
