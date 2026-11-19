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
3. **Total municipal del Padrón 2011 (`29005.csv`): NO sirve** (corrección del 19-11 tras medirlo; mi recomendación anterior era errónea). El Padrón es de 1-ene-2011 y la tabla de secciones del Censo de 1-nov-2011: en 398 municipios > 20.000 hab. la suma de secciones difiere de −22 % a +3,3 % (media −1,2 %). Residuos resultantes: 08047 (0804703001) = 126 hab. (una sección típica, ~1.000-2.500), 36059 (3605901003) = 250 hab., Ceuta = −819 (negativo: sin ajuste posible). Aplicarlo inventaría poblaciones. Opciones: (a) fuente del total municipal del **Censo** 2011 (1-nov-2011) con sha256: no está acreditada; (b) excluir las secciones sin dato declarando su población (como D-153) y que decida la puerta de votos; (c) mantener BLOQUEADA. **Recomiendo (a) si la tabla municipal del Censo está en el INE; si no, (c).** No implementado.
5. **38 Santa Cruz (nuevo).** 38-G01 = 115.715 hab. < suelo 120.634 (0,81 de la media; K=7): requiere exención de suelo y la política de nac38 no la gobierna. Misma figura que Fuerteventura (P2): **recomiendo sí**, exención de 38-G01 declarada; mientras tanto la provincia falla cerrado (#934).
4. **Provincias APARTADA_VOTOS (D-158).** **Recomiendo mantenerlas apartadas**; la alternativa es subir el tope de la puerta de votos de 2011 a 0,6 % (cambia D-70).
