# Registro de cambios DDD

Registro cronológico acumulativo. No se reescriben entradas antiguas.

## 2026-09-11 — Ronda R001 — Profesionalización y recuperación

**Objetivo:** convertir el código recuperado de Aragón en un procedimiento reproducible, auditable y ejecutable por su autor en GitHub.

**Decisiones:**
- Terminología oficial: Procedimiento DDD → Módulos → Ejecuciones → Rondas.
- Se define arquitectura de ocho módulos con contratos y justificación de separación.
- Se adopta versionado SemVer y conservación obligatoria en `legacy/` además de Git.
- GitHub pasa a ser entorno de referencia verificable; una ejecución local del asistente no constituye aceptación.
- Se introduce contenedor, dependencias fijadas, workflow manual, checksums y validación dura.
- Se corrigen defectos de cableado recuperados: referencia inexistente a step7b, clave YAML duplicada y ruta de salida de la unión final.
- Módulo 1 se rediseña para filtrado temprano de Aragón y lectura por chunks del CSV nacional, evitando cargar fuentes nacionales completas en RAM.
- Se corrige normalización de CUSEC para el formato oficial de `65034.csv`: primer bloque exacto de diez dígitos.
- La contigüidad se valida sobre el grafo de adyacencias; `MultiPolygon` no se usa como prueba de desconexión.

**Ejecución de recuperación observada:** 1.463 secciones; 67 distritos; población 1.364.621; 67/67 distritos conectados en grafo. Restricción poblacional: FAIL, con 30 distritos bajo 0,80×target y 7 sobre 1,75×target; mínimo 3.451; máximo 37.042; target 20.367,48.

**Estado de la ronda:** infraestructura en construcción; baseline territorial recuperado y diagnosticado; optimizador todavía no aceptable.

## 2026-09-11 — Mantenimiento operativo — Workflow v2.7.1

**Objetivo:** eliminar el error de presentación observado en el Run #7 sin mezclarlo con cambios del algoritmo territorial.

**Cambio:** se conserva `.github/workflows/procedimiento-ddd.yml` v2.7.0 en `legacy/workflows/procedimiento-ddd_v2.7.0.yml` y se publica v2.7.1. El texto Markdown del README generado deja de envolver `PRODUCTOS.json` con backticks dentro de un heredoc no protegido.

**Causa:** el shell interpretaba los backticks como sustitución de comandos y emitía `PRODUCTOS.json: command not found` durante la publicación de resultados.

**Impacto:** exclusivamente operativo/documental. No cambian M01-M08, configuración, fuentes, restricciones territoriales, función objetivo, outputs de los módulos ni reglas R012.
