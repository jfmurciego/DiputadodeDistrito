# Deuda histórica de `legacy/` — auditoría 2026-09-11

## Alcance
Este documento registra huecos heredados de la recuperación inicial. No crea versiones retrospectivas ni altera código funcional. Su objetivo es impedir que una cabecera dé por disponible una copia que no existe.

## Huecos verificados

| Fichero activo | Referencia histórica declarada | Estado |
|---|---|---|
| `modulos/01_preparar_base_territorial.py` v7.0.3 | `legacy/2026-09-11_modulo01_v7.0.2/01_preparar_base_territorial.py` | no materializada en el árbol vigente |
| `modulos/06_consolidar_distritos.py` v7.0.0 | `legacy/recuperado_2026-09-11_v6/` | no materializada en el árbol vigente |
| `modulos/07_agregar_resultados_electorales.py` v7.0.0 | `legacy/recuperado_2026-09-11_v6/scripts/ddd_step7_aggregate_election_results_v6_1_params.py` | no materializada en el árbol vigente |
| `modulos/08_integrar_resultados.py` v7.0.1 | `legacy/2026-09-11_modulo08_v7.0.0/08_integrar_resultados.py` | no materializada en el árbol vigente |

M02 y M03 sí apuntan a antecedentes existentes en `legacy/2026-09-11_github_pre_modulos/`.

## Regla desde política v1.1.0
Una ruta inexistente no puede presentarse como versión conservada. Cuando el contenido histórico no pueda recuperarse con certeza, la siguiente revisión de cabecera debe sustituir esa referencia por `PREDECESOR HISTÓRICO NO RECUPERADO` o `ORIGEN: baseline recuperado`, sin inventar contenido.

## Qué no se hace aquí
No se modifica M01/M06/M07/M08 únicamente para cambiar una cabecera inmediatamente después de Run #8, porque eso produciría un nuevo HEAD ejecutable distinto del commit recién validado. Esa normalización será una ronda de mantenimiento no funcional, seguida de su propia verificación.

## Otros gaps de ingeniería
- No existe todavía una suite unitaria completa visible; la aceptación actual se basa en GitHub Actions y validaciones integradas.
- Deben auditarse de forma sistemática las cabeceras de scripts auxiliares y herramientas para determinar cuáles están dentro del alcance obligatorio de la política.
- Las ramas `infra/fuentes-reproducibles*` son históricas/no canónicas y se conservan hasta decisión explícita sobre su eliminación.

Estos gaps son deuda explícita; no invalidan Run #8, pero tampoco se consideran resueltos hasta su cierre documentado.
