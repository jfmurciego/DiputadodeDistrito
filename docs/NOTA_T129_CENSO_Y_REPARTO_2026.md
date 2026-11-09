# T-129 — Censo/población para las generales de 2026 (nota técnica)

Fecha: 2026-11-09 · Solo documentación; no toca motor, huellas ni contratos.

## Fuentes (con sha256)
- RD 806/2026 (BOE-A-2026-20742), XML descargado de boe.es: `5e1ae58f61d1031e085a1e60d1cccd86dd28d72639dd4d2b0ffded9ae5cb565e`.
  El texto solo cita el art. 162 LOREG y da el reparto en el anexo; **no indica la cifra de población usada**.
- `configuracion/escanos_oficiales_congreso_2026.csv`: `9c9b48c1dcefe1aac327aa0211fc5f7c57130f83e5929dab25cbac352d182b8f` (transcribe el anexo).
- Población provincial INE a 1-1-2025 (52 filas, 49.128.297 hab.): `docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json`,
  `6a5f16d1bf354bebb1d05ad0f9afc350d8dc1c7ea251aac3ce6002e392b16a7c`.
- No verificado: INE (servicios.ine.es) y la LOREG consolidada no son accesibles desde esta sesión (proxy). Lo marcado «(sin fuente local)» queda por acreditar.

## Qué censo aplica
- El reparto de diputados (art. 162 LOREG) se hace por **población de derecho** de cada provincia (2 por provincia, 1 Ceuta y 1 Melilla, 248 por resto mayor), no por censo electoral. El censo electoral (CER, mayores de 18; CERA, residentes ausentes) no interviene en el reparto (sin fuente local: texto del art. 162, BOE-A-1985-11672).
- El CER/CERA sí importa para participación y para el cuadre de resultados de Interior (los contratos ya llevan `cera_records`); no condiciona el trazado de distritos, que usa población por sección.
- Cifras INE a 1-1-2026: el repo registra «población 2026 no publicada» (`configuracion/preparacion_legislatura_vigente.yaml`, cabecera 1.1.2). Los 407 distritos usan padrón 1-1-2025 con decisión F10-20261012-PAIR-2025.

## Prueba con el padrón 2025
Reparto del art. 162 recalculado con la población 1-1-2025 (cuota = 48.957.663/248 = 197.410):
- Coincide con el anexo en 48 de 50 provincias, **incluidas Madrid 38 y Cádiz 8**.
- Difiere en 2: Ciudad Real (calculado 4, oficial 5) y Santa Cruz de Tenerife (calculado 8, oficial 7). El último escaño se decide por un resto de 100.269 (Tenerife) frente a 100.028 (Ciudad Real): **241 habitantes**. El RD, por tanto, usa una cifra distinta de la de 1-1-2025 (probablemente otra fecha o revisión; sin fuente local).

## Efecto estimado
- Escaños: Madrid = 2 + 36 cuotas enteras (36,036); margen sobre el entero ≈ 7.100 hab. (0,1 %). Cádiz = 2 + 6 (6,39); su resto (76.960) queda a ≈ 23.000 hab. de ganar el escaño extra; sin el 9.º de 2023. Ambos coinciden con el RD; la sensibilidad de Madrid es mínima, la de Ciudad Real/Tenerife es crítica.
- Distritos: suelo/techo son relativos a la media de cada territorio (`population_floor_ratio` 0,80, techo según política) y los 407 se calcularon con 2025. Con 2026 el desplazamiento relativo entre secciones de un mismo territorio será de décimas de punto; no cabe cuantificarlo sin la tabla 65034 de 2026 (no publicada). Los distritos no se rehacen por esto; en un territorio con exención de suelo o margen justo (Baleares, Cádiz, Tenerife), reevaluar con `diagnostico/` cuando haya datos 2026.
- Votos: no hay efecto en los distritos publicados; la elección 2026 se incorpora por la vía M07 aceptada (secciones 2026 sin correspondencia = pérdida DDD).

## Qué falta para dejarlo listo y probado con 2023 (propuesta, sin implementar)
1. Test unitario del reparto art. 162 con población INE 1-1-2023 y `escanos_2023` del CSV como valor esperado (fuente independiente: RD 400/2023 y su sha256). Servirá de oráculo para 2026.
2. Acreditar la cifra de población del RD 2026 (comparar 1-1-2025, 1-1-2026 provisional, revisión) hasta reproducir Ciudad Real 5 / Tenerife 7; registrar fuente y sha256 en `elecciones_generales_2026.yaml`.
3. Cuando Interior publique: M07 por sección con el contrato de 2023 ya probado; verificar suma CER/CERA contra el total provincial como en `contratos_infoelectoral.yaml`.
4. Hallazgo para el Planificador (motor): ninguno; el K de DDD (N06) no depende de los escaños.

## Reproducir
```
python3 -I - <<'P'
import json
rows=json.load(open('docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json'))['rows']
pop={r['province_code']:r['population'] for r in rows if r['province_code'] not in('51','52')}
q=sum(pop.values())/248
s={k:2+int(v//q) for k,v in pop.items()}
for k in sorted(pop,key=lambda k:-(pop[k]%q))[:350-2-sum(s.values())]: s[k]+=1
print(s['28'],s['11'],s['13'],s['38'])   # 38 8 4 8
P
```
