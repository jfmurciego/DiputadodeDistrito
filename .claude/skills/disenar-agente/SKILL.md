---
name: disenar-agente
description: Diseña o revisa un agente, subagente o skill de DDD con el criterio del sistema más pequeño que cumple. Úsala cuando se proponga crear un agente nuevo, convertir un procedimiento en skill o subagente, o revisar uno existente.
---

# Diseñar un agente

Destilado del metaagente v1.0 (`docs/ARQUITECTURA/referencias/META_AGENTE_ARQUITECTO_CONSTRUCTOR_v1.0.md`,
secciones 7, 9, 25, 29E y 30) y de FRAMEWORK §6-§8. No cargarlo entero.

1. ¿Hace falta? Mecánico → CI/hook/script. Procedimiento que el chat necesita → skill. Trabajo acotado de solo
   lectura → subagente (`.claude/agents/`, salida JSON). Largo con decisiones → chat con rol.
2. Ficha: misión · exclusiones · entrada y salida · herramientas · autoridad (qué puede escribir o lanzar) ·
   criterio de aceptación · recursos (modelo, tope) · recuperación.
3. Delegación autocontenida: el encargo lleva objetivo, entorno, autorización, éxito, restricciones y baseline;
   el subagente no depende del contexto del chat.
4. Estados de tarea: PENDING, READY, RUNNING, REVIEW, WAITING_APPROVAL, BLOCKED, COMPLETED, FAILED. Efectos externos:
   PREPARED, AUTHORIZED, IN_FLIGHT, CONFIRMED, UNKNOWN; si es UNKNOWN, reconciliar antes de reintentar.
5. Resultado de calidad: PASS, PASS_WITH_EXCEPTIONS, FAIL, BLOCKED. Aprobación ligada al HEAD o digest exacto.
6. Quien construye no certifica: la verificación la hace otro contexto con el diff y la especificación.
7. Madurez declarada con evidencia: diseñado → implementado → probado → verificado.
8. Evals: no está listo hasta cazar los defectos históricos (FRAMEWORK §9, ADV-01..16 de la auditoría V2) sobre el
   diff original.
9. Humano en lo irreversible: lanzar, fusionar y publicar nunca son efecto colateral de un plan.

No adoptar: controladores con leases, almacenes de eventos ni prompts maestros residentes (coste fijo por chat).
