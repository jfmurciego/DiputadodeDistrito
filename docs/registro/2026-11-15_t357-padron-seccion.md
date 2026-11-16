## 2026-11-15 — T-357 — Población por sección censal 2011-2020 y casado con seccionado y votos

Causa: D-125 (opción A para el histórico) exige saber qué población por sección existe. Cambio: estudio solo lectura en
`docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/` (INFORME.md, resultados.json, medir_casado.py) con URL, bytes y sha256 de las
descargas reales del INE (Censo 2011, Atlas tabla 30832 2015-2024, seccionados 2012/2015/2016/2019/2020) y el casado con los
votos del Observatorio. Pruebas: cifras reproducibles con `medir_casado.py`; 520 ficheros del Observatorio verificados contra
su manifiesto. Riesgos: ninguno (no toca motor, workflows ni contratos); sin padrón por sección anterior a 2015 salvo Censo 2011.
