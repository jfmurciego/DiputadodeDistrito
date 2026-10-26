# F10 — Recibos electorales de Asturias y Galicia

**Versión:** 1.1.0 — **Fecha:** 2026-10-26 — **Estado:** candidato para revisión
**Alcance:** preservar y validar los paquetes electorales de Asturias 2023 y Galicia 2024 asociados a la edición de preparación 2025, y enlazar sus recibos a artefactos reales de CI.
**Predecesor:** `legacy/docs/AUDITORIAS/F10_RECIBOS_ELECTORALES_ASTURIAS_GALICIA_20261026/README_v1.0.0_20261026.md`; expediente local `F10-20261026-acreditacion`.
**Cambios:** registra los recibos canónicos emitidos tras validar los artefactos CI.
**Motivo:** enlazar el catálogo y el consumidor F10 a paquetes preservados con digest y run reales, sin alterar puertas F10.

## Paquetes preservados

| Territorio | Elección | Fuente declarada | SHA-256 del resultado normalizado | Estado del validador |
|---|---|---|---|---|
| Principado de Asturias | `asturias_jgpa_2023`, 2023-05-28 | GIPEYOP, espejo auditable permitido por la declaración; no es un editor oficial | `f82dc1299c97da1d6857ddc7e05cefe34e0b931d8e131608f5c2c998a533cce9` | `READY_PACKAGE` |
| Galicia | `galicia_parlamento_2024`, 2024-02-18 | Xunta de Galicia, cuatro descargas provinciales oficiales | `7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96` | `READY_PACKAGE` |

El original XLSX de Asturias se preserva en `originales/principado_de_asturias/asturias_2023_mesas_verified_mirror.xlsx`, SHA-256 `4799a86b0689d1de91a5b81778df2e8a1e5093afd6b8da6bd7f8656fbc65f950` (461027 bytes). El paquete Galicia incluye sus cuatro originales CSV y registra cada SHA en su manifiesto.

La validación `READY_PACKAGE` acredita compatibilidad del paquete con el contrato y sus hashes de payload. No acredita crosswalk territorial 2025→elección ni transforma el estado electoral de F10. Los artefactos de CI generados por el workflow identifican un run real y se usarán como entrada del emisor común `promover_catalogo_operacional.py`; el digest se verificará desde la metadata real de Actions antes de emitir cada recibo.

## Recibos emitidos

El workflow de PR `40389705458` validó cada paquete antes de subirlo. Se cotejaron nombre, run, digest, estado no expirado y HEAD del artefacto en la metadata de GitHub Actions. El emisor común `promover_catalogo_operacional.py` generó estos recibos y actualizó exclusivamente las referencias electorales del catálogo:

| Territorio | Recibo | Elección | Run | Artefacto | SHA-256 del artefacto | Identidad electoral |
|---|---|---|---:|---|---|---|
| Principado de Asturias | `territorios/principado_de_asturias/evidencia/fuentes_electorales/2025/29fb6a23b9c2e9fa3f3c393c34b90c868983302ea5d8767f7be5d472fbd6536c/40389705458/receipt.json` | `asturias_jgpa_2023` | `40389705458` | `ddd-electoral-package-principado_de_asturias-2025-40389705458` | `85e2d198db4216120dfacd46a6f5681dcf24f62ac8e68aacd634575f5e5eb037` | `29fb6a23b9c2e9fa3f3c393c34b90c868983302ea5d8767f7be5d472fbd6536c` |
| Galicia | `territorios/galicia/evidencia/fuentes_electorales/2025/af07c8d3bce5a45f63afd1c5d5eca0423a7713f71b4fbbb6c812f2509f51f230/40389705458/receipt.json` | `galicia_parlamento_2024` | `40389705458` | `ddd-electoral-package-galicia-2025-40389705458` | `58b1d99c27cce39a55129484d9d2a3f8ebcd5748bb3a063c813440bc209e60e2` | `af07c8d3bce5a45f63afd1c5d5eca0423a7713f71b4fbbb6c812f2509f51f230` |

El consumidor canónico conserva los recuentos electorales y conjuntos previos, porque ambos territorios ya tenían identidad temporal admisible. No se ejecutó incorporación electoral, producción ni generación.
