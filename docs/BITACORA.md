# Bitácora de progreso

**Versión:** 2.12.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.11.0.md`

## R001–R011 — Base reproducible y outputs auditables
Se recupera y profesionaliza el procedimiento; se formalizan M01–M08, caché territorial, fuentes congeladas, validación, manifiestos, ejecución GitHub y publicación completa de outputs por módulo.

## Run #5 — 34584775443
R011 demuestra auditabilidad, pero la auditoría posterior descubre una validación territorial incompleta: 13 distritos interprovinciales y 30 municipios fragmentados. No es referencia territorial.

## R012 — Provincia dura y disciplina municipal
Reglas estructurales vigentes: 67 distritos; Huesca 11 / Teruel 7 / Zaragoza 49; provincia infranqueable; municipio íntegro mientras quepa bajo techo; municipio sobredimensionado particionado internamente en bloques conexos; distritos urbanos completos exclusivamente municipales y solo residual mezclable; contigüidad estricta; suelo 0,80 y techo 1,75; objetivo fino ±12%.

Configuración v7.4.0. Validación v1.3.0. M05 v7.2.0.

## Run #6 — 34587157452
FAIL detectado por M05: distrito 52 desconectado. Auditoría del producto M04 demuestra que M04 ya lo entregaba con 15 componentes. Causa raíz: el particionador preservaba cada bloque extraído pero no la conectividad del residuo municipal.

Expediente: `docs/EJECUCIONES/GITHUB_RUN_0006_2026-09-11.md`.

## M04 v7.3.0
Se preserva v7.2.1. Se introduce partición municipal balanceada y conexa, ensamblaje rural conexo, eliminación de fallback no adyacente y autovalidación dentro de M04. Comprobación sobre artefactos reales del Run #6: 67; 11/7/49; 0 cruces; 0 desconectados; 0 bajo suelo; 0 sobre techo; 1 distrito fuera de ±12% (31.563 habitantes en Zaragoza). Pendiente ratificación por GitHub.

## R013 documental — Continuidad y puerta de entrada
Se revisa la documentación para impedir pérdida de contexto entre conversaciones:
- `README.md` pasa a v3.0.0 y se convierte en puerta de entrada real al proyecto;
- se crea `docs/CONTINUIDAD_NUEVO_CHAT.md` como protocolo canónico de handoff;
- los antiguos `docs/MEMORIA_DEL_PROYECTO.md` y `docs/MEMORIA_PROYECTO.md`, que contenían estados R001/R005 ya falsos, se retiran como fuentes canónicas y sus contenidos se preservan en `legacy/memoria/`;
- se establece como fuente vigente `docs/ESTADO_MAESTRO_PROYECTO.md` + bitácora + continuidad + última ronda/ejecución.

## Reglas permanentes
Un informe nunca sustituye al producto. Una ejecución de IA no sustituye a GitHub reproducible. Corregir el primer módulo que rompe el contrato, no parchear módulos posteriores. Toda versión nueva preserva legacy, documenta el cambio y solo se promociona si mantiene las restricciones ya aceptadas.
