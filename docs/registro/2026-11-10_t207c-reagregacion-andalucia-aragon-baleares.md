## 2026-11-10 — T-207c — Histórico autonómico reagregado: Andalucía, Aragón y Baleares (12 elecciones)

- Causa: con la composición canónica de T-207 las 12 elecciones estaban PENDIENTE_DE_REAGREGAR; el Planificador autorizó la reagregación local.
- Cambio: `herramientas/reagregacion_autonomicas.py` 1.1.0 (sin tocar) en local con Observatorio (sha256 en cada MANIFEST), seccionados INE históricos y seccionado 2025/padrón 65034. Resultado en `datos/resultados/historico/autonomicas/{andalucia,aragon,illes_balears}/` (CSV por distrito y partido, MANIFEST, rotación). `siglas_sin_homologar.json` regenerado; COBERTURA y RESUMEN de T-176 actualizados; textos con «Baleares».
- Resultado: 12/12 cuadran (≤0,5 %, D-17): defecto frente al total 0; pérdida de voto máxima 0,37 % (Andalucía 2026, 15.425 votos), Aragón 2026 0,09 %, el resto 0. Baleares con `aproximado_en_distrito` (secciones de 2025 asignadas por geometría). Aragón 2011 y 2015 siguen en hueco (solo municipio). Total: 54/75 elecciones, 11/17 comunidades.
- Pruebas: cuadre exacto de la propia herramienta (Σ distritos + perdido = Σ fuente) y `GovernanceHeaders`. Sin efecto en M04/M05 ni huellas; no requiere 00.
