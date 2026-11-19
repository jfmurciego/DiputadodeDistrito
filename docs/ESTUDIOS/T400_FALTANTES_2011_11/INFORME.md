# T-400 (b) · Qué falta en 2011-11 (provincias no OK)

Estado: 38 de 52 materializadas (#883, #886, #893). Mediciones con `contrato_2011_11.json` y la cadena local de nac35 (rama `t400-puente-la-graciosa-2011`).

| Prov. | Estado | Causa | Acción propuesta |
|---|---|---|---|
| 35 Las Palmas | materializa con la PR de T-400 (M01-M03 OK); M04 falla | (1) `province_districts={'35': 8}` en el yaml de la época; M04 reparte por partición insular (35-C01/C02/G01). (2) Fuerteventura 35-C02: 102.810 hab. < suelo 115.523 (K=1); `validation.population_floor_exempt_partitions` vacío | P1 y P2 |
| 07 Baleares (`nac07`) | M04 «need=8 > unidades abiertas=0» | Misma causa (1): cuota por partición (07-C01/C02/G01) ausente. No reproducida con 2011 (probable) | P1 (+ P2 si alguna isla queda bajo el suelo) |
| 38 Santa Cruz | materializada, M04 sin probar | Misma estructura (38-C01/G01): fallará igual (probable) | P1 |
| 08 Barcelona | BLOQUEADA_SIN_DATO | Sección 0804703001 sin población en ningún año (0,39 %) | P3 |
| 36 Pontevedra | BLOQUEADA_SIN_DATO | Sección 3605901003 sin población en ningún año (2,64 %) | P3 |
| 51 Ceuta | BLOQUEADA_RELLENO | 1,69 % estimada (> 1 %, D-161); sin total municipal oficial para ajustar | P3 |
| 03, 24, 27, 32, 33 | APARTADA_VOTOS | Votos fuera del seccionado 2012 > 0,1 % (máx. 0,54 %; 5.752 votos) | P4 |

## Preguntas para el propietario
1. **Reparto de K por partición insular en el histórico (07, 35, 38).** Hamilton con la población de la época entre las particiones del contrato base, como en 2025 (nac35 2011: 6/1/1). Es mecánico y no cambia suelo, techo ni K. **Recomiendo sí**, en una PR sobre `contrato_historico_epoca.py`.
2. **Suelo de Fuerteventura 2011 (nac35).** Exención de suelo de 35-C02 (0,76 de la media, una isla = un distrito, como Lanzarote en 2026). **Recomiendo sí**, con motivo y huella declarados; alternativa: dejar nac35 apartada.
3. **Total municipal del Padrón 2011 (`29005.csv`, ya acreditado) como ajuste de las secciones sin dato.** Cuadra por residuo municipal 0804703001, 3605901003 y Ceuta (municipio único), y deja solo lo no cuadrado como «estimada». **Recomiendo sí**: desbloquea 08, 36 y probablemente 51 sin excluir población.
4. **Provincias APARTADA_VOTOS (D-158).** **Recomiendo mantenerlas apartadas**; la alternativa es subir el tope de la puerta de votos de 2011 a 0,6 % (cambia D-70).
