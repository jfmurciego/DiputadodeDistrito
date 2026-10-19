# F10 — Auditoría documental de acreditación de Comunidad Valenciana (19-10-2026)

**Estado:** revisión documental completada; **admisibilidad territorial F10 = BLOCKED**; **sin promoción**, sin ejecución M04–M06 y sin modificación de contratos.

## Hechos comprobados en main

1. La matriz F10 `docs/AUDITORIAS/F10_CIERRE_TERRITORIAL_20261012/matriz_nacional_19.json` identifica Comunidad Valenciana como `territorial_acquisition=BLOCKED`, `territorial_admissibility=BLOCKED`, `electoral_admissibility=ADMISSIBLE` y `joint_admissibility=BLOCKED`. Esta fila se refiere a la pareja histórica **2023/2023**, no a la preparación territorial 2025.
2. El contrato `configuracion/preparacion_legislatura_vigente.yaml` fija elección `comunidad_valenciana_corts_2023` de 28/05/2023, `population_required_year=2023`, `section_required_year=2023`, `population_selected_year=2023` y `section_selected_year=2023`. La acción consignada es `ACQUIRE_WRONG_YEAR` para el paquete 2025.
3. **Existe un recibo 2025 auténtico versionado**, en `territorios/comunidad_valenciana/evidencia/fuentes_territoriales/2025/f50c038b9e79935c6fc0327df0d4f40d0315dbae70bff5215c32ce4b48e2cd28/38091132175/receipt.json`, con `run_id=38091132175`, `package_sha256=76ffdfc3c11291b7578560cd31b9eeab2e9b8aedc06bdfbd6c763590d6f969d9`, fuente 2025/2025 y `territorial_identity_sha256=f50c038b9e79935c6fc0327df0d4f40d0315dbae70bff5215c32ce4b48e2cd28`. **No acredita la pareja electoral territorial 2023/2023**.
4. El catálogo `configuracion/catalogo_preparacion.yaml` aún conserva `preparation_evidence.run_id=36273981926` y no registra el recibo 38091132175 como evidencia independiente. No sustituir el linaje histórico ni sobrescribir la preparación existente de manera automática.
5. La PR #277, fusionada como `868d0d6ce374f25169d96af1e43d123af3f645b0`, deja `working_crs=EPSG:25830` y los años de fuente 2025 explícitos en `territorios/comunidad_valenciana/config/comunidad_valenciana_2025.yaml`. La evidencia M01–M03 contenida en `docs/AUDITORIAS/F10_VALENCIA_M02_REPROYECCION_20261019/` usa 3515 CUSEC, población 5425182 y el paquete 2025. **No es un recibo 2023 ni una promoción F10**.
6. El expediente de 2023 `docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/CIERRE_UNIVERSO_Y_BLOQUEO_GEOMETRICO.md` acredita la procedencia del INE 2023, su población y los cuatro casos de normalización geométrica; registra dos intersecciones superiores al máximo de 1 m² bajo **EPSG:3035**: `4617201001/4619401008` y `4617201001/4619401013`. La matriz histórica detalla 46 secciones sin observación poblacional; **ausente no equivale a cero**. Como el CRS de la configuración de 2025 cambió posteriormente a EPSG:25830, esas magnitudes geométricas antiguas **no se deben dar por inalteradas** sin repetir el chequeo acotado sobre los originales 2023 y el contrato realmente aplicable. No modificar geometría, tolerancias ni fechas por inferencia.

## Resultado exigible a Fuentes Oficiales

- **Recepción 2025:** localizada y trazable; el recibo existe. No declararla pendiente de creación.
- **Objeto de cierre F10:** pareja oficial 2023/2023 de población y seccionado, con origen y bytes conservados, recibo o acreditación equivalente admitida por el consumidor F10, cobertura e identidad exactas, evaluación topológica del consumidor con CRS justificado y validación de la edición temporal. En caso de defecto persistente, preservar `BLOCKED` con pares e identificadores exactos.
- **Dependencia del frente Autonómico:** cualquier prueba operativa M01–M06, resolución funcional del contrato topológico y emisión de producto territorial. Fuentes verifica procedencia/recibo/admisibilidad, no ejecuta generación.
- **Siguiente comprobación de Fuentes:** contrastar el expediente protegido 2023 con el recibo/candidato del catálogo y reevaluar exclusivamente los dos pares geométricos bajo el CRS vigente que sea legítimo para 2023. Si no aparece acreditación completa y válida, mantener `BLOCKED` y entregar hallazgos a Autonómico/Work.
- **Gobierno:** ninguna evidencia descrita autoriza cambiar `territorial_acquisition` a `CLOSED`, marcar `joint_admissibility=PASS`, generar o publicar.

**Alcance de esta revisión:** lectura del repositorio, documentos y pruebas de CI existentes. No se afirma haber recalculado las geometrías originales 2023 ni ejecutado un nuevo consumidor canónico en esta auditoría.

## Evidencia acotada comprobable en CI

`tests/test_f10_valencia_2023_fuente_crs.py` valida sobre los tres CUSEC originales WFS 2023 conservados en GitHub que `4617201001` toca a `4619401008` y `4619401013` en CRS fuente EPSG:25830 sin solapamiento interior; en la reproyección independiente a EPSG:3035 se excede 1 m². Esto acredita **únicamente estos dos pares en ese fichero WFS**, no el universo provincial completo ni la identidad de los ZIP protegidos locales.

El universo 2023 publicado en `universo_2023.json` registra 3503 filas poblacionales numéricas para 3503 secciones geométricas, identidad exacta y cero blancos *en la tabla seleccionada*. Las 46 filas originales en blanco se excluyeron de esa selección: **no equivale a atribuirles población cero**. La falta actual es de **admisión integral del paquete histórico exacto y recibo canónico**, no una demostración de que esas 3503 observaciones seleccionadas carezcan de población.

No se ha materializado en esta sesión el conjunto completo de originales del almacén Mac ni recalculado su SHA. Hasta verificar esos bytes y la edición 2023/2023, el consumidor F10 debe mantener el bloqueo.
