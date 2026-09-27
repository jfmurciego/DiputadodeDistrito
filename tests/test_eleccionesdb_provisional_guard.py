from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "herramientas/adaptador_eleccionesdb.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("ddd_eleccionesdb_guard", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class EleccionesDBProvisionalGuard(unittest.TestCase):
    def test_extremadura_provisional_is_not_promoted_as_verified_election(self):
        adapter = load_adapter()
        self.assertNotIn("extremadura_asamblea_2025-12-21", adapter.ELECTIONS)


if __name__ == "__main__":
    unittest.main()
