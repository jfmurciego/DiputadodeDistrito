"""Contrato global de pasarelas topológicas en configuraciones territoriales activas."""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"u", "v", "admin_scope", "edge_type", "reason", "source"}


class TopologyBridgeContractTests(unittest.TestCase):
    def test_all_active_topology_bridges_are_fully_declarative_and_scope_matches_endpoints(self):
        checked = 0
        for path in sorted((ROOT / "territorios").glob("*/config/*_2025.yaml")):
            cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            bridges = (
                (cfg.get("modulos") or {})
                .get("modulo_02_construir_adyacencias", {})
                .get("topology_bridges", [])
                or []
            )
            for index, bridge in enumerate(bridges):
                checked += 1
                missing = sorted(k for k in REQUIRED if bridge.get(k) in (None, ""))
                self.assertEqual(
                    missing,
                    [],
                    f"{path}: topology_bridges[{index}] missing {missing}",
                )
                u, v = str(bridge["u"]), str(bridge["v"])
                scope = str(bridge["admin_scope"])
                if scope.startswith("province:"):
                    code = scope.split(":", 1)[1].zfill(2)
                    self.assertEqual(u[:2], code, f"{path}: u fuera de {scope}")
                    self.assertEqual(v[:2], code, f"{path}: v fuera de {scope}")
                elif scope.startswith("municipality:"):
                    code = scope.split(":", 1)[1]
                    self.assertEqual(u[:5], code, f"{path}: u fuera de {scope}")
                    self.assertEqual(v[:5], code, f"{path}: v fuera de {scope}")
                else:
                    self.fail(f"{path}: admin_scope no soportado: {scope}")
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
