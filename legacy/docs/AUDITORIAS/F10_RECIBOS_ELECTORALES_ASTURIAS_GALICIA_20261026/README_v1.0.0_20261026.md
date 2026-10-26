# F10 — Recibos electorales de Asturias y Galicia

**Versión:** 1.0.0 — **Fecha:** 2026-10-26 — **Estado:** candidato para revisión
**Alcance:** preservar y validar los paquetes electorales de Asturias 2023 y Galicia 2024 asociados a la edición de preparación 2025, y enlazar sus recibos a artefactos reales de CI.
**Predecesor:** expediente local `F10-20261026-acreditacion`; paquetes conservados en el almacén protegido.
**Cambios:** añade los paquetes validados, el original de Asturias disponible y el flujo de validación/subida con identidad de run.
**Motivo:** materializar recibos con `run_id` y digest emitidos por Actions, sin inventar metadatos ni alterar puertas F10.

## Paquetes preservados

| Territorio | Elección | Fuente declarada | SHA-256 del resultado normalizado | Estado del validador |
|---|---|---|---|---|
| Principado de Asturias | `asturias_jgpa_2023`, 2023-05-28 | GIPEYOP, espejo auditable permitido por la declaración; no es un editor oficial | `f82dc1299c97da1d6857ddc7e05cefe34e0b931d8e131608f5c2c998a533cce9` | `READY_PACKAGE` |
| Galicia | `galicia_parlamento_2024`, 2024-02-18 | Xunta de Galicia, cuatro descargas provinciales oficiales | `7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96` | `READY_PACKAGE` |

El original XLSX de Asturias se preserva en `originales/principado_de_asturias/asturias_2023_mesas_verified_mirror.xlsx`, SHA-256 `4799a86b0689d1de91a5b81778df2e8a1e5093afd6b8da6bd7f8656fbc65f950` (461027 bytes). El paquete Galicia incluye sus cuatro originales CSV y registra cada SHA en su manifiesto.

La validación `READY_PACKAGE` acredita compatibilidad del paquete con el contrato y sus hashes de payload. No acredita crosswalk territorial 2025→elección ni transforma el estado electoral de F10. Los artefactos de CI generados por el workflow identifican un run real y se usarán como entrada del emisor común `promover_catalogo_operacional.py`; el digest se verificará desde la metadata real de Actions antes de emitir cada recibo.
