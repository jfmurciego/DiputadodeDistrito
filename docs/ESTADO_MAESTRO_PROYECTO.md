# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.5.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.4.0.md`

## 1. Regla de arranque
Leer este documento; `docs/BITACORA.md`; arquitectura; contratos `docs/MODULOS/`; configuración; última ronda; última ejecución; workflow.

## 2. Objetivo
Procedimiento de Distritación DDD reproducible, auditable y generalizable. Aragón primero; después Castilla y León, Extremadura y España completa por configuración/datos, sin forks del motor.

## 3. Arquitectura
M01 secciones+población; M02 adyacencias; M03 grafo; M04 construcción inicial; M05 optimización; M06 consolidación; M07 agregación electoral; M08 producto final. M01-M03 son preparación reutilizable; M04-M06 núcleo territorial; M07-M08 capa electoral desacoplada.

## 4. Reglas duras Aragón — R012
1. 67 distritos exactos.
2. Contigüidad estricta por grafo.
3. Conservación exacta de secciones y población.
4. Suelo 0,80×target y techo 1,75×target.
5. **Provincia como frontera dura:** ningún distrito puede cruzar provincia.
6. Reparto provincial por Hamilton sobre población 2025: **Huesca 11, Teruel 7, Zaragoza 49**.
7. **Disciplina municipal:** un municipio que cabe en un distrito no se fragmenta.
8. Municipio grande: mínimo `ceil(P/cap)` y máximo `ceil(P/target)` distritos; como máximo uno de ellos puede ser mixto con otros municipios.
9. Para municipios divididos, se forman primero distritos internos al municipio; únicamente el residual puede completarse con municipios menores adyacentes de la misma provincia.
10. CUSEC único/no nulo; determinismo; resultados electorales no condicionan geometría.

## 5. Población provincial 2025
- Huesca: 230.087.
- Teruel: 136.091.
- Zaragoza: 998.443.
- Aragón: 1.364.621.
- Target global: 20.367,48.

## 6. Estatus del Run #5
GitHub Run #5 `34584775443` continúa siendo evidencia válida de R011 —outputs completos y reproducibles— y demuestra 67 distritos, 0 bajo suelo, 0 sobre techo y 0 desconectados bajo la puerta antigua.

**No es una referencia territorial aceptable bajo R012.** La auditoría encontró 13 distritos interprovinciales y fragmentación municipal incompatible con la nueva regla. Se reclasifica como PASS técnico bajo validación territorial incompleta.

## 7. R012
Documento canónico: `docs/RONDAS/R012_2026-09-11_provincia_y_disciplina_municipal.md`.

Configuración vigente: `configuracion/aragon_2025.yaml` v7.4.0.
Validación vigente: `herramientas/validar_ejecucion.py` v1.3.0.

La puerta de calidad ahora falla por:
- cualquier distrito interprovincial;
- cardinalidad provincial distinta de 11/7/49;
- municipio repartido entre más distritos de los permitidos;
- más de un distrito mixto para un municipio dividido;
además de las puertas ya existentes de contigüidad, cardinalidad y población.

## 8. Rediseño M04
M04 deja de ser un semillado global libre sobre las 1.463 secciones.

Secuencia objetivo:
1. separar el territorio por provincia;
2. calcular las unidades municipales/urbanas atómicas;
3. mantener íntegro todo municipio que cabe en un distrito;
4. para municipios grandes, construir unidades internas conectadas; los distritos urbanos se llenan primero dentro del municipio;
5. solo el residual urbano puede absorber municipios menores adyacentes;
6. ensamblar 11/7/49 distritos contiguos dentro de las tres provincias.

M05 no debe reparar errores estructurales creados por M04: M04 debe entregar ya una solución válida territorialmente.

## 9. Rediseño M05 multiobjetivo
Los movimientos incompatibles con provincia, contigüidad o disciplina municipal son inválidos y no entran en la función objetivo.

Dentro del espacio válido, prioridad lexicográfica:
1. número de distritos fuera de ±12%;
2. magnitud total que excede ±12%;
3. fragmentación municipal evitable;
4. distritos mixtos asociados a municipios divididos;
5. máximo desvío poblacional;
6. error cuadrático global;
7. posteriormente compacidad, superficie y coherencia comarcal con fuentes formalizadas.

## 10. Outputs y auditoría
R011 sigue vigente: cada módulo debe exponer el producto completo que produce. Tablas/JSON auditables se guardan en Git; geometrías pesadas en artefactos M01-M08 con SHA-256 registrado.

## 11. Siguiente acción exacta
Implementar una nueva versión de M04 que construya por provincia y sobre unidades municipales/urbanas atómicas; después adaptar M05 para mover unidades completas y nunca secciones que rompan la disciplina municipal. No lanzar una nueva ejecución de aceptación hasta que ambos módulos implementen R012, porque la nueva validación correctamente convertiría la solución antigua en FAIL.
