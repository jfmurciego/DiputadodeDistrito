# Auditoría consolidada y plan de acción — Fase 1

**Fecha de corte:** 2026-09-12  
**Repositorio:** `jfmurciego/DiputadodeDistrito`  
**Rama / HEAD:** `main` / `fde28250ae532836e548c5ff2f8855542fea3709`  
**Alcance cerrado:** Aragón → Castilla y León → Extremadura. No avanzar a otros territorios hasta superar todas las puertas de esta fase.  
**Fuentes cruzadas:** estado y continuidad del repositorio; auditoría, valoración, tareas y parche aportados por Claude.

## Veredicto de estado

El motor tiene dos resultados territorialmente válidos (Aragón y Castilla y León) y una tercera implantación todavía experimental (Extremadura). El riesgo inmediato no es el algoritmo de Aragón, cuyo baseline fue recomputado externamente, sino la falta de garantías automáticas y de evidencia durable.

Los hallazgos de Claude siguen vigentes en `main`:

- La regresión de Aragón no se dispara al cambiar M01–M05 ni `ddd_core/**`, y admite degradación hasta 12 % frente al baseline de 9,9299365905 %.
- No existe regresión automática M01–M06 de Castilla y León.
- Los tests llamados de regresión leen evidencia almacenada; no reejecutan el motor.
- Los resultados canónicos de Castilla y León y Extremadura no están materializados en el repositorio.
- Extremadura declara solo M01–M03 en su YAML; K, atomicidad y límites se inyectan en workflows experimentales.
- Persisten defaults territoriales silenciosos en código común.
- Aragón conserva dos YAML desincronizados y carece de un `territory_contract` completo.
- Hay 45 workflows activos, con duplicación y sin clasificación operativa completa.

Por tanto, la expansión territorial queda congelada. Los trabajos ya hechos fuera de Fase 1 se conservan, pero no se ejecutan ni se amplían.

## Plan de acción secuencial

Cada puerta se acepta únicamente con un run de GitHub Actions. Si falla, se detiene la fase y se registra el diagnóstico; no se relajan umbrales.

### Puerta 1 — Blindar y reverificar Aragón

1. Aplicar `01_regresion_aragon_paths_y_trinquete.diff`.
2. Lanzar inmediatamente la regresión M01–M06.
3. Exigir: 67 distritos, 1.463 secciones, 1.364.621 habitantes, cuotas 11/7/49, `hard PASS`, `fuera_12=0` y `maxdev <= 0.099299365905 + 1e-9`.
4. Si el valor cambia, detenerse y comparar M02–M06 y `ddd_core/` contra el manifiesto del run canónico `34599224954`; no mover el trinquete.

**Cierre:** run SUCCESS y evidencia publicada. Hasta entonces, Aragón está validado históricamente pero no reverificado contra el código actual.

### Puerta 2 — Crear la segunda regresión real

1. Crear `regresion-m06-castilla-y-leon.yml` con los mismos disparadores comunes de Aragón.
2. Ejecutar M01–M06 y exigir: 82 distritos, 3.506 secciones, 2.401.221 habitantes, cuotas provinciales declaradas, contigüidad completa, `hard PASS` y `fuera_12=0`.
3. Registrar el `maxdev` real del primer run SUCCESS como trinquete en un commit posterior.
4. Materializar el run canónico de CyL bajo `territorios/castilla_y_leon/resultados/ejecuciones/`, incluyendo manifiesto, validación y recomputación independiente de invariantes.

**Cierre:** regresión automática SUCCESS, trinquete fijado y evidencia durable completa.

### Puerta 3 — Hacer explícito el contrato común

Ejecutar esta puerta solo cuando Aragón y CyL estén verdes.

1. Implementar un único cargador de límites duros que falle si falta cualquier ratio territorial; eliminar defaults silenciosos en `ddd_core/`, `modulos/` y `herramientas/`.
2. Completar `territory_contract` de Aragón y justificar o revisar su atomicidad 1,75.
3. Consolidar Aragón en un único YAML canónico bajo `territorios/aragon/config/` y actualizar todos los consumidores.
4. Renombrar los tests estáticos como pruebas de integridad de evidencia y documentar que las regresiones reales son los workflows.
5. Ejecutar ambas regresiones sin variación numérica.

**Cierre:** Aragón y CyL mantienen exactamente sus baselines y toda configuración obligatoria falla de forma explícita si está incompleta.

### Puerta 4 — Consolidar Extremadura

1. Elevar al YAML canónico K=65, reparto 41/24, atomicidad y los ratios realmente adoptados; documentar la razón de cualquier diferencia frente a Aragón/CyL.
2. Sustituir diccionarios completos incrustados en workflows por lectura del YAML y sobreescrituras mínimas, explícitas y registradas para experimentos.
3. Materializar el baseline c020 y la evidencia EXT-19 con manifiestos honestos; marcar cualquier reconstrucción a posteriori.
4. Consolidar o descartar formalmente el relevo EXT-19. Continuar solo con operadores generales; no introducir excepciones ocultas.
5. Promover Extremadura únicamente si un run M01–M06 logra 65 distritos, reparto 41/24, contigüidad completa, `hard PASS` y tolerancia objetivo completa. Si no, dejarla formalmente como experimental con el mejor resultado y el bloqueo reproducible.

**Cierre:** contrato reproducible y evidencia durable; resultado promovido o descarte experimental explícito.

### Puerta 5 — Limpieza operativa de Fase 1

1. Clasificar workflows como `activo`, `experimental` o `congelado`; sacar de `.github/workflows/` los experimentos cerrados después de preservar su evidencia.
2. Añadir una prueba sintética rápida M01–M06 para cambios comunes; mantener Aragón y CyL como regresiones pesadas.
3. Generar el estado factual desde manifiestos y validaciones, y reducir los documentos manuales de estado a una única fuente canónica más decisiones fechadas.
4. Ejecutar CI global y las regresiones de Aragón/CyL; verificar que no queda trabajo activo de territorios posteriores.

**Cierre de Fase 1:** todas las puertas anteriores en verde, Extremadura resuelta o descartada formalmente y documentación sincronizada. Solo entonces se retoma Andalucía.

## Orden de ejecución propuesto

| Lote | Contenido | Regla de parada |
|---|---|---|
| F1.1 | Parche y reverificación Aragón | Cualquier divergencia del baseline |
| F1.2 | Regresión y evidencia CyL | Cualquier invariante territorial fallido |
| F1.3 | Configuración estricta, YAML Aragón y nombres de tests | Variación numérica en Aragón o CyL |
| F1.4 | Contrato, evidencia y cierre Extremadura | Excepción oculta o contrato no reproducible |
| F1.5 | Limpieza de workflows, test sintético y estado generado | CI o regresiones no verdes |

## Fuera de alcance

Andalucía, Cataluña, Madrid, restantes comunidades, archipiélagos, Ceuta/Melilla y M07–M08 quedan expresamente fuera de esta pasada. Tampoco se resuelve aquí el anclaje jurídico del 12 % ni la incorporación de compacidad a la función objetivo; se registran como decisiones de producto posteriores al cierre técnico de Fase 1.
