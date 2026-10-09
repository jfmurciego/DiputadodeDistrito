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

## 2026-09-11 — R014 — M05 v7.3.0, escape de mínimo local

**Problema:** Run #7 dejó un único distrito fuera de ±12 %: distrito 56 de Zaragoza con 31.563 habitantes. M05 v7.2.0 aceptó 0 movimientos.

**Auditoría:** la reproducción sobre artefactos exactos M03/M04 demuestra 642 relaciones dirigidas únicas candidatas en el estado inicial. El bloqueo no está en `candidates()`: los movimientos que descargan el distrito 56 manteniendo contigüidad crean temporalmente un segundo distrito fuera de ±12 %, mientras que movimientos pequeños que mejorarían inmediatamente la población rompen contigüidad. La estrategia greedy estrictamente monótona queda atrapada en un mínimo local.

**Cambio funcional:** se conserva `modulos/05_optimizar_distritos.py` v7.2.0 en `legacy/modulo05/05_optimizar_distritos_v7.2.0.py` y se publica **M05 v7.3.0 — Escape determinista de mínimos locales**. La búsqueda pasa a tener una fase greedy determinista y una fase de recocido simulado reproducible que solo se activa si queda desequilibrio fino y solo opera en las provincias afectadas.

**Invariantes:** el recocido no puede violar suelo/techo, provincia, contigüidad, unidad `ddd_unit_id` ni cierre `ddd_closed_urban`. La función objetivo canónica no se rebaja: la salida siempre restaura la mejor solución encontrada según la comparación lexicográfica original.

**Configuración:** `configuracion/aragon_2025.yaml` pasa de v7.4.0 a **v7.5.0**, preservando la anterior en `legacy/configuracion/aragon_2025_v7.4.0.yaml`. Se parametrizan límites de greedy/recocido, semilla, pesos de energía, penalización de churn y temperaturas.

**Prueba diagnóstica:** contra los artefactos exactos del Run #7 se obtiene 67 distritos, 1.463 secciones, 1.364.621 habitantes, cuotas 11/7/49, `hard=0`, `fuera_12=0`, máximo desvío ≈11,943 %, min=18.345, max=22.800, 0 desconectados, 0 cruces provinciales y 0 violaciones municipales.

**Estado:** candidato. La prueba local no constituye aceptación. R014 solo se promociona tras una nueva ejecución GitHub Actions desde `main` que confirme todos los PASS y los outputs M01–M08.
