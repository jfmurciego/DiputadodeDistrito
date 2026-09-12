# Salida maestra de ChatGPT

**Versión:** 2.5.0  
**Fecha de corte:** 2026-09-12  
**Estado:** Fase 1 activa; expansión congelada  
**Anterior:** `legacy/salidas_chatgpt/SALIDA_MAESTRA_v2.4.0.md`  
**HEAD técnico auditado:** `e3cb917013c45af4b894e8f8207c79568c13e9b4`

## Último hito
`HITOS/2026-09-12_F104_CERRADO.md`

## Estado operativo
- F1.1 Aragón: cerrada y regresión verde.
- F1.2 Castilla y León: cerrada, evidencia durable y regresión verde.
- F1.3 contrato común: cerrada, YAML único Aragón y límites explícitos.
- F1.4 Extremadura: cerrada formalmente como `EXPERIMENTAL_BLOCKED`; M01-M06 reproducible, 2 outliers de ±10 %, sin promoción.
- F1.5: siguiente; limpieza operativa, smoke sintético y estado factual.
- Territorios posteriores: congelados.

## Evidencia
- `territorios/castilla_y_leon/resultados/ejecuciones/gh-34701897922-1/`
- `territorios/extremadura/resultados/ejecuciones/gh-34703213474-1/`
- `docs/AUDITORIAS/PLAN_ACCION_FASE1_ARAGON_CYL_EXTREMADURA_2026-09-12.md`

## Regla
No retomar Andalucía ni expansión hasta cerrar F1.5. Cálculo pesado exclusivamente en GitHub Actions.
