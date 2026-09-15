# Ensembles territoriales con GerryChain

**Versión:** 1.1.0 — 2026-09-15

GerryChain/ReCom es un motor M05 alternativo. M01–M05 producen una partición
inicial válida y M06–M08 siguen consumiendo el campo `district_id`. El motor
canónico continúa siendo el predeterminado.

## Contrato y reproducibilidad

La unión M03–M05 se realiza exclusivamente por `M03.nodes[].id` y
`M05.CUSEC_KEY`. `ddd_unit_id` es una unidad atómica y puede repetirse. Cada
plan deriva semillas explícitas del territorio, la huella SHA-256 de M03/M05 y
la tabla comarcal, el perfil y el ordinal.

Son puertas duras: universo de secciones, K, límites de población, provincia y
reparto provincial, atomicidad, disciplina municipal, distritos urbanos
cerrados y contigüidad. La comarca es un objetivo ponderado y se informa con
fragmentación, retención de población y entropía. La forma se mide sobre la
geometría real con Polsby–Popper; el número de aristas cortadas se conserva
como señal secundaria, no como sustituto geométrico.

Antes de crear la matriz, una puerta independiente vuelve a medir cada arista
en `EPSG:25830`, excluye contactos exclusivamente puntuales y comprueba la
contigüidad del territorio y de todos los distritos. Aragón exige al menos un
metro de frontera compartida. Una base inválida bloquea el lote completo antes
de iniciar sus cinco perfiles.

## Operación

La única entrada humana es **Operación territorial DDD — M01 a M08**. La
operación **Generar alternativas GerryChain** llama al workflow reutilizable en
tres fases:

1. `synthetic`: pruebas unitarias, integración real de ReCom y lote sintético.
2. `aragon_10`: prepara M01–M05 una sola vez, valida la topología métrica y
   ejecuta dos alternativas por
   cada uno de los cinco perfiles.
3. `aragon_50`: exige además `PROMOVER_ARAGON_50`; esta confirmación declara
   que el piloto de 10 terminó completo y que su coste y publicación fueron
   revisados.

Los resultados no se incorporan al repositorio. Se publican como artefacto y
como release borrador. La página solo se despliega cuando todas las
alternativas cumplen las restricciones. Un lote parcial conserva la matriz de
reintento y puede diagnosticarse sin publicar una galería incompleta.

El entorno se instala desde `requirements-ensemble.lock`, separado del
`requirements.lock` canónico para no modificar las dependencias de producción.

## Primera ejecución autorizada

En GitHub Actions, abrir **Operación territorial DDD — M01 a M08** y seleccionar:

- territorio: **Aragón**;
- operación: **Generar alternativas GerryChain**;
- fase: **Piloto Aragón — 10 alternativas**;
- autorización: `EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION`.

El piloto genera diez candidatos, conserva resultados reanudables en una
release borrador y solo publica la galería si los diez superan todas las puertas.
No usar `aragon_50` hasta revisar duración, memoria, formas y retención comarcal
del piloto.
