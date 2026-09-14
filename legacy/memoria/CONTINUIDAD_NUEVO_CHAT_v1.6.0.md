# Continuidad del proyecto en un nuevo chat

**Versión:** 1.6.0
**Fecha de corte:** 2026-09-11
**Anterior:** `legacy/memoria/CONTINUIDAD_NUEVO_CHAT_v1.5.0.md`

## Fuente de verdad

El repositorio `jfmurciego/DiputadodeDistrito` manda sobre cualquier recuerdo del chat. Leer: `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, este documento, `docs/BITACORA.md`, arquitectura, contratos M01–M08, última ronda/ejecución, configuración, workflows, tests y código afectado. Los antiguos `docs/MEMORIA*` están retirados.

## Arquitectura y reglas

M01 base territorial+población → M02 adyacencias → M03 grafo → M04 construcción inicial → M05 optimización → M06 consolidación → M07 agregación electoral → M08 producto final.

Aragón: 67 distritos; 1.463 secciones; 1.364.621 habitantes; provincia 11/7/49; contigüidad estricta; suelo 0,80×target; techo 1,75×target; objetivo ±12 %; municipio pequeño indivisible; municipio sobredimensionado particionado de forma conexa con solo residual mezclable; resultados electorales fuera del algoritmo geométrico.

## Referencia territorial — Run #9 / R016

GitHub Run #9 **`34599224954` — SUCCESS** sobre `f9ca44ff005043f630fce39334d34726d8bf55c5`.

M05 v7.4.0 parte del mismo estado que Run #8 y alcanza la misma primera solución factible en la iteración 9.038, con `max_rel_dev=0.119431695687`. En vez de detenerse, continúa 10.962 iteraciones más y termina con `max_rel_dev=0.099299365905` y error cuadrático `0.161271162560`.

Validación final: 67 distritos, 1.463 secciones, 1.364.621 habitantes, Huesca 11 / Teruel 7 / Zaragoza 49, 0 desconectados, 0 cruces provinciales, 0 violaciones municipales, 0 bajo suelo, 0 sobre techo y **0 fuera de ±12 %**.

R016 queda **CERRADO Y PROMOCIONADO**. Run #9 sustituye a Run #8 como baseline territorial.

## Qué cambió respecto de Run #8

Solo cambian 12 distritos y todos están en Zaragoza. El peor distrito de Zaragoza baja de 11,943 % a 9,140 %. Huesca y Teruel permanecen exactamente iguales. El máximo global final pasa a ser el distrito 0 de Huesca, con -9,930 %.

## Ingeniería y auditoría

R015 sigue siendo la puerta general de regresión, gobernanza y determinismo. R016 añade pruebas específicas de refinamiento y una regresión del baseline Run #9.

Toda sustitución versionada conserva primero el predecesor inmediato en `legacy/`. La copia histórica se conserva literalmente, incluso si tiene whitespace o defectos cosméticos. Si una versión anterior no fue recuperada, se registra en `docs/DEUDA_HISTORICA_LEGACY.md`; nunca se fabrica.

La promoción de un ejecutable ya probado no obliga a reescribirlo solo para cambiar una etiqueta de estado: eso alteraría el blob probado. El estado de promoción se registra en Estado Maestro y en el expediente del run.

`main` es la única rama permanente y actualmente la única rama existente. Si se crea una rama técnica temporal, debe eliminarse tras su integración.

## Orden para continuar

1. Confirmar HEAD de `main` y último run de pruebas.
2. Leer esta continuidad, Estado Maestro y el último expediente de ejecución.
3. Definir un objetivo funcional concreto para la siguiente ronda.
4. Conservar predecesores y versionar cualquier fichero que se cambie.
5. Exigir CI verde y nuevo run territorial cuando cambie comportamiento.

**Siguiente paso:** decidir el objetivo de R017. El cuello poblacional ya no está en Zaragoza: el máximo global es Huesca (-9,930 %), seguido de Teruel (-9,822 %) y Zaragoza (+9,140 %). No se debe seguir optimizando por inercia sin decidir antes qué calidad territorial se quiere mejorar.
