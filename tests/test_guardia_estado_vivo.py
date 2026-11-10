#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: guardia contra tests que fijan el estado vivo del ciclo de preparación (T-147)
VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: el bot reescribe catálogo y contratos de territorios en cada preparación; un test sobre el repositorio vivo
  no puede exigir `generation_ready` o `source_prepared_pending_pre_m04` con assertEqual/==. Debe usar
  `tests._estados_vivos.ESTADOS_PREPARADO` (assertIn) o una fixture fija (`tests/_raiz_congelada.py`, tmpdir).
"""
import re
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ESTADOS = ("generation_ready", "source_prepared_pending_pre_m04")
FIJA = re.compile(r"assertEqual\([^\n]*\[[\"']status[\"']\][^\n]*[\"'](?:%s)[\"']|"
                  r"[\"']status[\"']\]\s*==\s*[\"'](?:%s)[\"']" % ("|".join(ESTADOS), "|".join(ESTADOS)))
# Ficheros cuyo contrato/catálogo es una fixture en tmpdir (no el estado vivo); revisados en T-147.
FIXTURE_EN_TMPDIR = {
    "test_materializar_conserva_cabecera.py",
    "test_pre_m04_persistencia_concurrente.py",
    "test_resolved_source_contract_consumers.py",
    "test_temporal_source_preflight_contract.py",
}


class GuardiaEstadoVivo(unittest.TestCase):
    def test_ningun_test_fija_el_estado_del_ciclo_sobre_el_repositorio_vivo(self):
        malos = []
        for f in sorted(TESTS.glob("test_*.py")):
            if f.name == Path(__file__).name or f.name in FIXTURE_EN_TMPDIR:
                continue
            for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if FIJA.search(linea):
                    malos.append(f"{f.name}:{n}: {linea.strip()[:100]}")
        self.assertEqual(malos, [], "usa ESTADOS_PREPARADO (assertIn) o una fixture fija")

    def test_la_guardia_detecta_el_patron(self):
        self.assertTrue(FIJA.search('self.assertEqual(row["status"], "generation_ready")'))
        self.assertTrue(FIJA.search('self.assertEqual(c["meta"]["status"], "source_prepared_pending_pre_m04")'))
        self.assertFalse(FIJA.search('self.assertIn(row["status"], ESTADOS_PREPARADO)'))


if __name__ == "__main__":
    unittest.main()
