# Auditoría de estado — Diputado de Distrito

**Fecha de corte:** 2026-09-12 09:30 UTC  
**Repositorio:** `jfmurciego/DiputadodeDistrito`  
**Rama auditada:** `main`  
**HEAD auditado:** `95978c75ec45400c4f475f71276989a9cdc311fd`  
**Naturaleza:** auditoría documental, estructural y de ejecuciones GitHub Actions; no reejecuta localmente el procesamiento GIS.

## 1. Veredicto ejecutivo

El repositorio está operativo, reproducible y ya funciona como motor multi-territorio. Aragón y Castilla y León tienen implantaciones validadas hasta M06. Extremadura ha validado M01–M03 y dispone de una solución M04/M05 técnicamente factible, pero todavía no cerrada dentro de tolerancia. Andalucía tiene M01–M03 validados y su primer ensayo M04 falló por cuatro distritos fuera de restricciones duras. Cataluña completó realmente CAT-01/M01–M03, aunque la documentación de continuidad todavía lo presenta como “en ejecución”.

El principal riesgo actual no es de ejecución sino de **desalineación documental**: `PROMPT_CONTINUIDAD_TERRITORIOS.md` es más reciente que `ESTADO_MAESTRO_PROYECTO.md` y `BITACORA.md`, pero incluso aquel quedó desactualizado respecto a los runs de Andalucía y Cataluña ejecutados después.

## 2. Estado técnico verificado

### Repositorio y gobernanza

- Rama permanente: únicamente `main`.
- `main` no está protegida.
- HEAD: `95978c75ec45400c4f475f71276989a9cdc311fd`.
- Última CI global: **Pruebas DDD — R015 #262**, run `34685861034`, SUCCESS.
- La suite verificó cabeceras/versionado/legacy y regresión territorial.
- Existen estructuras activas para código común, territorios, documentación, resultados, workflows y `legacy/`.
- La política de conservar versiones anteriores se está aplicando materialmente en configuraciones, workflows, módulos, documentación y pruebas.

### Aragón — referencia principal

**Estado:** validado y protegido como baseline funcional.

- Run canónico: `34599224954` / R016.
- 67 distritos; 1.463 secciones; 1.364.621 habitantes.
- Reparto provincial: Huesca 11 / Teruel 7 / Zaragoza 49.
- Restricciones duras: PASS.
- `fuera_12=0`; máximo desvío 9,930 %.
- M06 materializado; M07–M08 funcionales.
- Pendiente legítimo: auditoría territorial fina, sin reabrir por inercia la optimización poblacional.

### Castilla y León — segunda implantación validada

**Estado:** validada hasta M06.

- Run M05: `34619174991`, SUCCESS.
- 82 distritos; 3.506 secciones; 2.401.221 habitantes.
- Restricciones duras: PASS.
- `fuera_12=0`; máximo desvío aproximado 11,98 %.
- M06: catálogo de 82 distritos y composición de 3.506 secciones.
- M07 bloqueado exclusivamente por falta de fuente electoral territorial validada.

### Extremadura — generalización M04/M05

**Estado:** M01–M03 cerrados; M04/M05 aún experimental.

- 964 secciones; 1.053.345 habitantes.
- M03: 964 nodos, 2.607 aristas, 0 aislados, 0 provincias o municipios desconectados.
- K=65; reparto 41 Badajoz / 24 Cáceres.
- Baseline c020: `hard=0`.
- EXT-19, run `34652238246`, SUCCESS técnico.
- El run confirmó un relevo 2×2 válido que reduce los outliers de 2 a 1, pero ese movimiento fue diagnosticado, no consolidado como nueva solución canónica.
- La solución vigente sigue sin cierre de tolerancia: no debe declararse territorio validado.

### Andalucía — prueba de escalabilidad

**Estado:** M01–M03 cerrados; M04 no factible con la configuración ensayada.

- 6.029 secciones; 8.676.713 habitantes.
- M03: 6.029 nodos, 16.671 aristas, 0 aislados, 0 provincias o municipios desconectados.
- Ensayo AND-04: run `34661697111`, FAILURE.
- Causa verificada: M04 mantuvo 4 distritos fuera de suelo/techo; M05 no llegó a ejecutarse.
- No fue un fallo de infraestructura ni de fuentes.
- La documentación que indica “pendiente de recibir M04” está superada: M04 ya se ensayó y reveló una incompatibilidad de parametrización/particionado que debe resolverse de forma general.

### Cataluña — quinta implantación

**Estado:** CAT-01/M01–M03 ejecutado; contrato topológico todavía no cerrado.

- Run `34661723679`, SUCCESS.
- 5.143 secciones; 8.124.126 habitantes; 0 faltantes.
- M03: 5.143 nodos, 14.375 aristas y 1 aislado.
- Las auditorías de componentes provinciales y municipales estaban desactivadas en el baseline, por lo que el SUCCESS del workflow no equivale al cierre topológico.
- Siguiente puerta: identificar el aislado, activar auditorías provinciales/municipales, justificar cualquier pasarela y congelar cardinalidades antes de fijar K o abrir M04.

## 3. Hallazgos de gobernanza y trazabilidad

1. **Documentación canónica desincronizada.** `ESTADO_MAESTRO_PROYECTO.md` v2.1.0 todavía presenta CYL-05 como trabajo en curso y no recoge el estado real de Extremadura, Andalucía ni Cataluña.
2. **Bitácora incompleta respecto al HEAD.** `BITACORA.md` v2.21.0 llega a R020/Extremadura, pero no consolida AND-04 ni CAT-01.
3. **Prompt de continuidad parcialmente obsoleto.** Registra correctamente el orden territorial y los baselines de Aragón/Castilla y León, pero Andalucía ya ejecutó M04 y Cataluña ya terminó su baseline.
4. **CI global sana.** El último commit pasa R015 #262.
5. **Rama sin protección.** Es coherente con el modelo de una sola rama acordado, pero permite modificar `main` sin una puerta remota obligatoria; debe constar como riesgo aceptado o corregirse explícitamente.
6. **Proliferación de workflows experimentales.** Los numerosos workflows EXT-* ofrecen trazabilidad, pero conviene clasificarlos como activos, experimentales congelados o legacy para reducir ambigüedad operativa.
7. **Outputs no siempre canónicos.** Varios ensayos publican artefactos de Actions sin materializarlos como baseline dentro de `resultados/`; debe mantenerse clara la distinción entre evidencia experimental y resultado aceptado.

## 4. Orden operativo recomendado

1. Actualizar Estado Maestro, Bitácora y continuidades territoriales con AND-04 y CAT-01.
2. Cerrar CAT-02: auditoría del aislado y componentes, sin fijar todavía K.
3. Consolidar o descartar formalmente el relevo EXT-19 antes de seguir ampliando operadores.
4. Diagnosticar en M04 la inviabilidad andaluza; barrido territorial propio, sin heredar ciegamente c020.
5. Mantener Aragón como regresión principal y Castilla y León como segunda regresión en todo cambio común.
6. Clasificar workflows experimentales y mover a `legacy/workflows/` los ya cerrados cuando su evidencia esté documentada.

## 5. Estado global resumido

| Territorio | M01–M03 | M04–M05 | M06 | M07–M08 | Estado |
|---|---:|---:|---:|---:|---|
| Aragón | Validado | Validado | Validado | Funcional | Baseline principal |
| Castilla y León | Validado | Validado | Validado | Bloqueado por fuente electoral | Segunda implantación |
| Extremadura | Validado | Experimental; 1 outlier potencial tras relevo | Pendiente | Pendiente | Generalización |
| Andalucía | Validado | M04 falló con 4 hard outliers | Pendiente | Pendiente | Escalabilidad |
| Cataluña | Ejecutado; topología no cerrada | Pendiente | Pendiente | Pendiente | Baseline inicial |

## 6. Criterio de cierre de esta auditoría

La auditoría queda cerrada sobre el HEAD indicado. Cualquier commit o run posterior exige una nueva fecha de corte. No se ha modificado código, configuración, workflows, outputs ni documentación canónica; únicamente se añade este informe.
