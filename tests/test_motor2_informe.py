#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · informe por territorio de la competición (solo stdlib)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competicion import EntradaTerritorio, competir  # noqa: E402
from ddd_motor2.informe import escribir  # noqa: E402
from tests.test_motor2_competicion import Fijo  # noqa: E402


class Informe(unittest.TestCase):
    def test_json_y_md(self):
        tmp = Path(tempfile.mkdtemp())
        pob = {"A": 95, "B": 105, "C": 110, "D": 90}
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(pob))}
        grafo = tmp / "grafo.json"
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        from tests.test_motor2_competicion import CFG
        e = EntradaTerritorio("prueba", CFG, grafo)
        canon = Fijo("canonico", {None: {"A": "1", "B": "1", "C": "1", "D": "2"}}, pob)  # 310/90: inválido
        gc = Fijo("gerrychain", {7: {"A": "1", "B": "1", "C": "2", "D": "2"}, 8: None}, pob)
        r = competir(e, canon, gc, [7, 8], tmp / "out")
        fj, fm = escribir(r, tmp / "inf")
        d = json.loads(fj.read_text(encoding="utf-8"))
        self.assertEqual(d["ganador"], "gerrychain-s7")
        self.assertTrue(d["mejora_al_canonico"])
        self.assertIn("violaciones_duras", d["motivo_frente_al_canonico"])
        self.assertEqual([c["id"] for c in d["candidatos"]], ["gerrychain-s7", "canonico", "gerrychain-s8"])
        md = fm.read_text(encoding="utf-8")
        self.assertIn("Ganador: **gerrychain-s7**", md)
        self.assertIn("R-POB-TECHO", md)
        self.assertEqual(md.count("\n| "), 4)  # cabecera + 3 candidatos


if __name__ == "__main__":
    unittest.main()
