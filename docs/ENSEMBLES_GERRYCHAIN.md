# Ensembles territoriales con GerryChain

**Versión:** 1.0.0 — 2026-09-14

GerryChain/ReCom es un motor M05 alternativo. M01–M04 producen la misma base
canónica y M06–M08 siguen consumiendo el campo `district_id`. El motor canónico
continúa siendo el predeterminado.

## Contrato y reproducibilidad

La unión M03–M04 se realiza exclusivamente por `M03.nodes[].id` y
`M04.CUSEC_KEY`. `ddd_unit_id` es una unidad atómica y puede repetirse. Cada
plan deriva semillas explícitas del territorio, la huella SHA-256 de M03/M04 y
la tabla comarcal, el perfil y el ordinal.

Son puertas duras: universo de secciones, K, límites de población, provincia y
reparto provincial, atomicidad, disciplina municipal, distritos urbanos
cerrados y contigüidad. La comarca es un objetivo ponderado y se informa con
fragmentación, retención de población y entropía.

## Operación

La única entrada humana sigue siendo `picadora-territorial.yml`. La operación
`generar_alternativas_gerrychain` llama al workflow reutilizable en tres fases:

1. `synthetic`: pruebas unitarias, integración real de ReCom y lote sintético.
2. `aragon_10`: prepara M01–M04 una sola vez y ejecuta dos alternativas por
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
