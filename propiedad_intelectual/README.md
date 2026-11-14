# Paquete de propiedad intelectual de Deslinde

Instantánea del motor Deslinde (versión 1.0.1) tomada del commit `439af6a523b6fc52b7c28e87ad690510aff450fa` (2026-11-12T13:55:06Z UTC), generada por
`herramientas/preparar_paquete_pi.py` 1.0.0. Contiene 1128 ficheros (50407671 bytes): `ddd_motor2/`, los módulos que
ejecuta, el `ddd_core` que importan, `docs/ARQUITECTURA/DESLINDE_1_0.md` y `docs/ESTUDIOS/`.

Esta carpeta es privada: no entra en el repositorio público (`configuracion/exclusion_publicacion.txt`).
El envío al registro lo hace el propietario con su asesor.

## Verificar

1. `sha256sum -c SHA256SUMS` comprueba el ZIP y el manifiesto (si el ZIP está presente).
2. Cada fichero del ZIP tiene su tamaño y sha256 en `MANIFEST.json` (`ficheros`).
3. Reproducir: `python herramientas/preparar_paquete_pi.py --commit 439af6a523b6fc52b7c28e87ad690510aff450fa --excluir docs/ESTUDIOS/N06_DECISION_K_20261012/REGISTRO_PLAN.json --excluir docs/ESTUDIOS/N06_DECISION_K_20261012/pruebas_formalizacion_inicial.log --excluir docs/ESTUDIOS/N06_DECISION_K_20261012/vinculo_plan.json --excluir docs/ESTUDIOS/N06_INTEGRACION_INE_20261012/pruebas_90.log --excluir docs/ESTUDIOS/N08_CACERES_20261012/logs/ejecucion.txt --excluir docs/ESTUDIOS/T197_generales_2026/ensayo.py --excluir docs/ESTUDIOS/T211_ponderado_autonomicas/scripts/diag.py --excluir docs/ESTUDIOS/T211_ponderado_autonomicas/scripts/exentos.py --excluir docs/ESTUDIOS/T211_ponderado_autonomicas/scripts/resumen.py --excluir docs/ESTUDIOS/T211_ponderado_autonomicas/scripts/unid.py --excluir docs/ESTUDIOS/T217_vigente_piezas_finas/scripts/vig.py --excluir docs/ESTUDIOS/T225_CONGRESO_2025/RESUMEN.json --excluir docs/ESTUDIOS/T254_MEDICION_DESLINDE/resultados/auditoria_congreso_huesca.json --excluir docs/ESTUDIOS/T254_MEDICION_DESLINDE/resultados/auditoria_congreso_la_rioja.json --excluir docs/ESTUDIOS/T254_MEDICION_DESLINDE/resultados/auditoria_la_rioja.json` da los mismos bytes
   (ZIP sin compresión, orden por ruta, fecha fija 1980-01-01, permisos 0644).
