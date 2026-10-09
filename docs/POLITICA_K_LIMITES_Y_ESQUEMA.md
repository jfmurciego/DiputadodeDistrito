# Política de K, límites y esquema territorial

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** vigente — R036  
**Anterior:** ninguno — documento nuevo

## Decisión

R036 convierte la definición del problema en contrato auditable antes del cálculo. No modifica distritos, algoritmos ni productos certificados.

1. El catálogo nacional registra el estado del territorio y la decisión de K.
2. El YAML territorial repite K como parámetro ejecutable.
3. La puerta de admisión exige coincidencia exacta entre catálogo, contrato, M04, M06 y validación.
4. Todo K declara origen y justificación. `historico_no_registrado` es una declaración honesta de deuda, no una fórmula reutilizable.
5. El contrato general de límites es `0.80 / 1.75 / 0.12`.
6. Toda excepción declara motivo, evidencia y fecha antes de ejecutar; nunca se corrigen umbrales después de ver una salida.
7. `bootstrap_m01_m03` observa datos y topología; `production_m01_m06` exige el contrato completo y es el único nivel ejecutable por la línea de producción.

## Aplicación a lo existente

- Aragón: K=67 se conserva como baseline certificado; el origen no quedó registrado. Usa el perfil general.
- Castilla y León: K=82 conserva el tamaño de la XII Legislatura autonómica y usa Hamilton para igualdad poblacional provincial. Usa el perfil general.
- Extremadura: K=65 y sus límites históricos quedan identificados como experimento bloqueado. La formalización no promociona, recalcula ni convierte la excepción en precedente.

## Regla para nuevos territorios

Antes de M04 debe existir una decisión de K independiente del resultado. El orden preferente es: norma aplicable; fórmula nacional publicada; decisión propia motivada. La selección no puede basarse en cuál K produce el mapa políticamente o geométricamente más conveniente. La neutralidad electoral se verifica después y nunca alimenta M04–M06.

## Control ejecutable

`herramientas/validar_contrato_territorial.py` llama a `ddd_core.territory_contract` y rechaza esquema ambiguo, catálogo incoherente, K sin procedencia, límites excepcionales sin expediente o cadena M01–M06 incompleta. La validación no ejecuta módulos territoriales.
