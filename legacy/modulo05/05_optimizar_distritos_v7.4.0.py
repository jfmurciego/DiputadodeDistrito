#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.4.0
NOMBRE DE VERSIÓN: Refinamiento canónico post-factibilidad
FECHA: 2026-09-11
FUNCIÓN: optimizar población sin cruzar provincias ni romper las unidades municipales/urbanas construidas por M04.
ENTRADAS: grafo M03 y solución M04 v7.3.1 con ddd_unit_id y ddd_closed_urban.
SALIDAS: asignación optimizada y reporte.
REGLAS DURAS: provincia única por distrito; movimientos de unidad completa; distritos urbanos cerrados no reciben ni ceden unidades; contigüidad estricta; suelo/techo poblacional.
OBJETIVO CANÓNICO: primero eliminar violaciones duras; después minimizar distritos fuera de ±12%; después máximo desvío y error cuadrático.
ESTADO: candidato R016 — pendiente de ejecución territorial GitHub.
CAMBIOS: continúa la búsqueda después de la primera solución con fuera_12=0; conserva como ámbito las provincias que eran problemáticas al inicio y registra primera factibilidad frente al óptimo final encontrado.
MOTIVO: el código v7.3.x interrumpía el recocido al primer fuera_12=0 aunque el objetivo canónico todavía ordena minimizar máximo desvío y error cuadrático.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.3.1.py
"""
# Snapshot íntegro de la versión 7.4.0 preservado por trazabilidad.
# El contenido ejecutable exacto permanece recuperable en el commit padre de esta entrada legacy.
