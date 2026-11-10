# Municipales de España · nota de preparación (T-158)

Fecha de consulta: 2026-11-10. Estado: PREPARACIÓN; no hay motor, datos ni contrato.

## 1. Sistema vigente y norma (verificado)
Fuente: LOREG, BOE-A-1985-11672, XML consolidado de la API del BOE (sha256 en `README.md`).
- Art. 179.1: cada término municipal es una circunscripción; escala de concejales: hasta 100 residentes, 3; 101-250, 5;
  251-1.000, 7; 1.001-2.000, 9; 2.001-5.000, 11; 5.001-10.000, 13; 10.001-20.000, 17; 20.001-50.000, 21;
  50.001-100.000, 25; de 100.001 en adelante, uno más por cada 100.000 residentes o fracción, y uno más si el resultado es par.
  Versión vigente del apartado 1 por la LO 2/2011 (BOE-A-2011-1639).
- Art. 179.2: concejo abierto (alcalde por sistema mayoritario), fuera de la escala.
- Art. 180: reparto por el procedimiento del art. 163.1 (D'Hondt) con **barrera del 5 %** de los votos válidos de la circunscripción.
- Art. 184: municipios de hasta 250 habitantes sin concejo abierto: lista de 3 o 5 nombres y voto limitado a 2 o 4 candidatos (sistema de voto limitado, no por lista).
- Régimen especial de Canarias, Baleares (consejos insulares) y Navarra/País Vasco (normas propias para su régimen foral): NO VERIFICADO aquí.

## 2. Qué sería un «distrito uninominal»
Dentro de cada municipio, partir su territorio en tantos distritos como concejales (K = escala del art. 179) y elegir uno
por distrito. Solo tiene sentido práctico donde K ≥ 9 aprox. (municipios > 1.000 residentes); con 3-7 concejales el
distrito tendría menos de ~150-300 habitantes y una sección censal ya lo supera. Orden de magnitud con el censo: cientos de
municipios con ≥ 17 concejales (> 10.000 residentes). La cifra exacta de municipios por tramo debe salir de la tabla oficial de población, no de memoria.

## 3. Unidades mínimas y cartografía
- Unidad mínima natural: la sección censal del INE (ya usada en el contrato nacional: 36.554 secciones, ver
  `docs/ESTUDIOS/FUENTES_NACIONALES_INE_2025/ENTREGA.md`). Una sección tiene del orden de 1.000-2.500 electores, es decir,
  más que un distrito objetivo en municipios medianos (p. ej. 17 concejales y 15.000 residentes: ~880 por distrito).
  **Riesgo central:** la sección es demasiado gruesa para municipios de < ~30.000 habitantes; la atomicidad debería bajar a manzana/portal (cartografía callejera, no disponible aquí).
- Cartografía alcanzable: la del seccionado nacional ya en el repositorio. No alcanzables desde la nube: CNIG, Catastro y Sedes de ayuntamientos (NO VERIFICADO el estado de licencia; los datos del CNIG/IGN suelen ser CC BY 4.0 y los del INE reutilizables con cita, pero hay que confirmarlo en origen).

## 4. Población oficial
Cifras oficiales de población de cada municipio: Real Decreto anual de cifras de población (BOE) y Padrón (INE). El art. 179 habla de «residentes»: confirmar con el último RD de cifras oficiales cuál rige a la fecha de la convocatoria. Muestra de accesibilidad INE: tabla 2915 (`README.md`), no sirve como cifra oficial.

## 5. Resultados por mesa o sección y licencia
- Resultados municipales por mesa: Ministerio del Interior (Infoelectoral, descarga de ficheros por mesa), **no alcanzable desde la nube** (mismo bloqueo que ya consta en CLAUDE.md para las generales: rechaza runners y cloud); el espejo en release GitHub sólo existe para el Congreso 2023.
- Licencia: NO VERIFICADO (los datos de Interior se publican como información pública reutilizable; cita obligada y comprobación en origen).
- Hueco: la sección censal es la agregación de mesas; el cruce mesa→sección ya existe para Congreso (`equivalencia_secciones_congreso_2023`) y habría que rehacerlo para 2023-05 municipales.
- Hueco estructural: las listas municipales incluyen candidaturas locales sin sigla nacional; la homologación de siglas (D-20) no cubre las agrupaciones de electores.

## 6. Reglas del núcleo a parametrizar
- **Partición dura**: ámbito = término municipal (hoy provincia). Hay que impedir que un distrito cruce municipio.
- **K**: viene del art. 179 por tramo de población; no lo decide el motor. Municipios con K par/impar y la regla «uno más si par» solo afectan a > 100.000.
- **Techo/suelo**: el techo de ratio actual está pensado para distritos de ~100.000 hab.; en municipales hay que fijarlo por municipio.
- **Atomicidad**: sección censal como mínimo; en municipios donde una sección > población objetivo hace falta una unidad menor (ver §3).
- **Barrera del 5 %** y D'Hondt sólo importan para la comparación proporcional vs. uninominal, no para el trazado.
- Concejos abiertos y los < 250 habitantes: fuera de alcance.

## 7. Huecos y riesgos
1. Cartografía y resultados no alcanzables (tabla del README).
2. Sección censal demasiado gruesa (ver §3): puede invalidar el enfoque para la mayoría de municipios.
3. Multiplicidad: ~8.100 municipios; ejecutarlos todos con el motor actual (motor por territorio) exige otro modo de lanzamiento; solo un subconjunto (≥ 17 concejales) es viable.
4. Cambios de sección entre el seccionado y los resultados de 2023 (ya conocido en Congreso).
5. Regímenes forales (Navarra, País Vasco) y Canarias/Baleares sin verificar.

## 8. Esfuerzo (estimación)
Piloto de un municipio grande (p. ej. uno de > 100.000 hab.): 3-5 tareas (fuente de resultados por sección, contrato con partición dura municipal, política, prueba local). Escalar a todos los ≥ 17 concejales: 8-12 tareas más, dominadas por la adquisición de resultados y la unidad menor que la sección. Sin fuentes (hoy bloqueadas) no se puede empezar.
