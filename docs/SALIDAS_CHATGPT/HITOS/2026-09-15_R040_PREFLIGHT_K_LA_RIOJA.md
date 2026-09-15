# R040 preflight — decisión ex ante de K para La Rioja

**Fecha:** 2026-09-15
**Estado:** contrato preparado; ejecución R040 no autorizada
**Territorio:** La Rioja
**Ejecuciones territoriales:** ninguna

## Decisión

Se fija **K=33** antes de M04 con `k_source: norma`.

La fuente normativa es la Ley 3/1991, de 21 de marzo, de Elecciones a la Diputación General de La Rioja. Su artículo 19 fija en 33 el número de diputados. El Estatuto de Autonomía establece que la ley electoral debe fijar el tamaño del Parlamento entre 32 y 40 miembros y que la circunscripción es la Comunidad Autónoma.

Fuentes oficiales consultadas el 2026-09-15:

- BOE, Ley 3/1991: https://www.boe.es/buscar/act.php?id=BOE-A-1991-7743
- BOE, Estatuto de Autonomía de La Rioja: https://www.boe.es/buscar/act.php?id=BOE-A-1982-15030

## Justificación metodológica

DDD conserva para esta prueba el tamaño legal vigente de la cámara que se pretende representar mediante distritos uninominales. La decisión es institucional y previa a cualquier geometría, optimización o resultado electoral. No se ha comparado K=33 con ningún otro K.

La Rioja es una comunidad uniprovincial. Mantener `district_apportionment: hamilton` no introduce una decisión adicional: el reparto es trivial, provincia 26 = 33 distritos. La frontera provincial tampoco reduce el espacio regional porque coincide con el territorio completo.

Se adopta el perfil común R036 `0.80 / 1.75 / 0.12` sin excepción. R022/R023 aportan el bootstrap previo: 343 secciones, 326.803 habitantes y cero pasarelas topológicas.

## Falsabilidad

Este cambio sólo prepara el contrato `production_m01_m06`. No ejecuta M01–M06 ni autoriza R040. Cuando exista autorización expresa, La Rioja deberá recorrer la cadena común sin modificar `.github/workflows/`, `modulos/` ni `ddd_core`. Si falla, el fallo se registra como hallazgo de R040; no se introduce código específico para convertirlo en PASS.
