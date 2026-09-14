# Continuidad — Castilla y León

**Versión:** 2.0.0  
**Fecha:** 2026-09-11  
**Estado:** CYL-05 cerrado; M07 bloqueado únicamente por falta de fuente electoral territorial validada  
**Anterior:** `legacy/memoria/CONTINUIDAD_CASTILLA_Y_LEON_v1.0.0.md`

## 1. Mandato vigente

Continuar `jfmurciego/DiputadodeDistrito` sobre `main`, con un único motor común y sin crear repositorio, rama permanente ni copia de módulos para Castilla y León. GitHub es la fuente de verdad y el plano de ejecución; el chat se usa para arquitectura, diagnóstico y decisiones.

Castilla y León ya no es una implantación por iniciar. Es la **segunda implantación territorial validada del motor DDD hasta M06**.

## 2. Referencias que deben leerse al abrir un nuevo hilo

1. `README.md`.
2. `docs/ESTADO_MAESTRO_PROYECTO.md`.
3. este documento.
4. `docs/EJECUCIONES/2026-09-11_CYL04_CYL05.md`.
5. `docs/ARQUITECTURA_MULTI_TERRITORIO.md`.
6. `docs/CONTRATO_TERRITORIO.md`.
7. `docs/MODULOS/README.md` y M01–M08.
8. `docs/POLITICA_DE_VERSIONES.md`.

No reconstruir el estado desde conversaciones si estos documentos y GitHub Actions ya lo contienen.

## 3. Estado territorial Castilla y León

Configuración activa: `territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml`, versión 0.9.0, estado `candidate_m06` en el momento de CYL-05.

Datos estructurales certificados:
- 3.506 secciones censales;
- población total 2025: 2.401.221;
- 9 provincias;
- K=82;
- reparto Hamilton: Ávila 6, Burgos 12, León 15, Palencia 6, Salamanca 11, Segovia 5, Soria 3, Valladolid 18, Zamora 6;
- 10.399 aristas territoriales en M03, de las que 7 son pasarelas topológicas explícitas;
- 0 provincias desconectadas;
- 0 municipios desconectados tras las pasarelas auditadas.

## 4. CYL-04 — M05 validado

Referencia: commit `1549011cc56c56f3403e11902437228731e7d8ee`.
Workflow: `Optimización DDD — territorio`.
Run: `34619174991`.
Resultado: **SUCCESS**.

Resultado M05:
- K=82;
- `hard=0`;
- `fuera_12=0`;
- máximo desvío relativo = 0,1198;
- contigüidad = 82/82;
- cuotas provinciales intactas;
- unidades M04 preservadas;
- núcleos urbanos cerrados preservados.

La resolución del último outlier no requirió modificar M05. M04 v7.4.8 expuso una micro-unidad residual fronteriza transferible en Ávila; M05 existente pudo entonces resolver la solución.

## 5. Lecciones M04 que forman parte del motor

### 5.1 Cierre urbano con factibilidad provincial
Un núcleo urbano cerrado no se valida únicamente porque él mismo caiga dentro de ±12 %. Tras el cierre, la masa provincial restante debe poder distribuirse entre los distritos abiertos dentro de la banda objetivo.

### 5.2 Residuo abierto debe ser realmente móvil
Un residuo municipal marcado como abierto puede quedar inmóvil si ocupa un distrito completo como una sola `ddd_unit_id`. Cuando esa atomicidad bloquea la factibilidad posterior, M04 puede exponer la mínima micro-unidad fronteriza transferible cuya extracción conserva la conectividad del residuo.

### 5.3 Responsabilidad correcta
M04 define granularidad y factibilidad estructural; M05 optimiza. No se amplía el recocido para compensar una unidad mal definida por M04.

## 6. CYL-05 — M06 validado

Workflow: `Consolidación DDD — territorio`.
Run: `34620163650`.
Resultado: **SUCCESS**.
Artifact: `castilla-y-leon-CYL05-34620163650`, ID `10271783303`, SHA-256 `958d2eace53a6439a68fd92df17356c1ad87a7c4a5ec6bff8021adcadc0e1495`.

M06 v7.1.0 certificó:
- identidad exacta `CUSEC_KEY → district_id` entre M05 y M06;
- 3.506 secciones;
- 82 distritos;
- población 2.401.221 en resumen, catálogo y composición;
- `fuera_12=0`;
- provincia única por distrito;
- métricas geométricas válidas;
- catálogo distrital de 82 filas;
- composición territorial de 3.506 filas.

Productos M06:
- resumen poblacional;
- catálogo distrital auditable;
- composición exacta por sección;
- GeoJSON de secciones;
- GeoJSON disuelto de distritos.

M06 no cambia `district_id`; materializa y audita la solución M05.

## 7. M07 — estado real

M07 **no está bloqueado por ingeniería**. Está bloqueado por fuente de datos.

El repositorio contiene actualmente una fuente electoral seccional explícita: `inputs/rtve_aragon_2026_secciones.json`, correspondiente a Aragón. No existe en el repositorio una fuente electoral validada de Castilla y León que pueda usarse honestamente para M07.

No reutilizar, extrapolar ni adaptar silenciosamente los datos de Aragón. Para abrir CYL-06/M07 se requiere incorporar una fuente electoral territorial adecuada, con origen, elección, nivel de detalle, claves de sección/mesa y checksum documentados.

Hasta entonces, **Castilla y León está correctamente cerrado en M06**.

## 8. Aragón sigue siendo regresión protegida

Baseline Aragón: GitHub Run #9 `34599224954`, 67 distritos, 1.463 secciones, 1.364.621 habitantes, Huesca 11 / Teruel 7 / Zaragoza 49, `fuera_12=0`, máximo desvío 9,930 %.

M06 v7.1.0 debe superar una regresión específica de compatibilidad sobre el YAML histórico Aragón antes de declararse baseline general. Workflow creado: `.github/workflows/regresion-m06-aragon.yml`.

## 9. Siguiente orden de trabajo

1. Cerrar la regresión M06 de Aragón.
2. Si pasa, declarar M06 v7.1.0 baseline multi-territorio y registrar el hito.
3. Actualizar Estado Maestro con CYL-05 cerrado.
4. Mantener M07 CYL bloqueado hasta disponer de una fuente electoral válida.
5. Preparar el tercer territorio para medir cuánto trabajo queda realmente específico de cada implantación; Extremadura es el candidato previsto.
6. Mantener separada la auditoría fina R017 de Aragón.

## 10. Reglas de ingeniería

- Todo cambio de fichero versionado conserva el predecesor exacto en `legacy/`.
- Las cabeceras documentan versión, nombre, función, cambios, motivo y anterior.
- Los logs pesados y resultados de ejecución permanecen en GitHub/Actions, no en el chat.
- Los cambios comunes deben mantener regresión Aragón y Castilla y León.
- No introducir excepciones territoriales hardcodeadas si existe una formulación general.
- No usar resultados electorales para construir la geometría.
- No avanzar un módulo si su dependencia de datos no está satisfecha.
