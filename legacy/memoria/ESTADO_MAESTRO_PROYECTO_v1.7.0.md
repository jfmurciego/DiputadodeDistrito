# Estado maestro del proyecto — Diputado de Distrito

**Versión:** 1.7.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/ESTADO_MAESTRO_PROYECTO_v1.6.0.md`

## 1. Regla de arranque
Leer este documento; `docs/BITACORA.md`; arquitectura; contratos `docs/MODULOS/`; configuración; última ronda; última ejecución; workflow.

## 2. Reglas duras Aragón — R012
1. 67 distritos exactos.
2. Contigüidad estricta por grafo.
3. Conservación de 1.463 secciones y población.
4. Suelo 0,80×target y techo 1,75×target.
5. Provincia como frontera dura.
6. Reparto provincial exacto: Huesca 11, Teruel 7, Zaragoza 49.
7. Municipio que cabe bajo el techo duro: indivisible.
8. Municipio sobredimensionado: partición interna en bloques conexos.
9. Todos sus distritos salvo como máximo el residual deben ser exclusivamente municipales.
10. Solo el residual urbano puede completarse con municipios menores adyacentes de la misma provincia.
11. Resultados electorales nunca condicionan la geometría.

## 3. Estatus de ejecuciones
Run #5 `34584775443`: referencia de auditabilidad R011, no referencia territorial R012.

Run #6 `34587157452`: FAILURE. M04 terminó, M05 rechazó el distrito 52 por desconexión. La auditoría del artefacto M04 demostró que el distrito 52 ya contenía 15 componentes. Expediente: `docs/EJECUCIONES/GITHUB_RUN_0006_2026-09-11.md`.

## 4. Causa raíz Run #6
El algoritmo M04 extraía bloques urbanos conexos, pero no obligaba al residuo del municipio a permanecer conexo. En Zaragoza se generó un residuo fragmentado que posteriormente fue tratado como una sola unidad territorial. M05 actuó correctamente como guardia.

## 5. Implementación vigente
Configuración `configuracion/aragon_2025.yaml` v7.4.0. Validación `herramientas/validar_ejecucion.py` v1.3.0.

### M04 v7.3.0 — Partición balanceada conexa por provincia
- construye cada provincia de forma independiente;
- municipio íntegro mientras su población sea <= techo duro;
- municipio sobredimensionado: partición híbrida conexa + reparación local poblacional;
- el residual urbano se elige por contacto exterior; los demás bloques son cerrados;
- unidades rurales se agrupan mediante partición conexa y reparación local;
- no existe fallback que asigne una unidad a un distrito no adyacente;
- antes de exportar, M04 comprueba cardinalidad 67, cuotas 11/7/49, provincia única, contigüidad y suelo/techo.

Versión anterior preservada en `legacy/modulo04/04_generar_semillas_v7.2.1.py`.

### M05 v7.2.0
- optimiza únicamente dentro del espacio territorial protegido por M04;
- mueve unidades completas;
- no cruza provincias;
- preserva contigüidad de donante y receptor;
- prioriza hard constraints, luego ±12%, máximo desvío y error cuadrático.

## 6. Verificación previa a nueva ejecución
M04 v7.3.0 fue reproducido sobre los artefactos reales M01/M03 del Run #6. Resultado local:
- 67 distritos;
- Huesca 11, Teruel 7, Zaragoza 49;
- cero cruces provinciales;
- cero distritos desconectados;
- cero distritos bajo suelo o sobre techo;
- los municipios no sobredimensionados permanecen atómicos;
- un único distrito rural de Zaragoza queda fuera de ±12%, con 31.563 habitantes.

Esto convierte el próximo run en prueba de aceptación real del nuevo M04 y, si M04 pasa, en prueba de capacidad de M05 para resolver el último desajuste fino sin romper las reglas duras.

## 7. Outputs
R011 permanece vigente: M01-M08 deben exponer productos completos. M04/M05 deben seguir publicando asignaciones auditables con provincia, municipio, `ddd_unit_id`, `ddd_closed_urban`, población y distrito.

## 8. Siguiente acción exacta
Ejecutar workflow en modo `iterativo`. No se acepta un PASS si la validación detecta cualquier cruce provincial, desconexión o fragmentación municipal inválida. Si el run supera M04 pero falla después, auditar M05 exclusivamente; no volver a alterar M04 sin evidencia de un defecto propio.
