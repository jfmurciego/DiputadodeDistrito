from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd
import yaml

from herramientas.validar_fuentes_reanudacion import validate_resume_sources

ROOT = Path(__file__).resolve().parents[1]


class GaliciaLocalE2ERegressionTests(unittest.TestCase):
    def test_m01_detecta_punto_y_coma_en_csv_preparado(self):
        ns = {"__file__": str(ROOT / "modulos/01_preparar_base_territorial.py")}
        source = (ROOT / "modulos/01_preparar_base_territorial.py").read_text(encoding="utf-8")
        exec(compile(source.split("def load_cip", 1)[0], "m01-prefix", "exec"), ns)
        self.assertEqual(ns["_sniff_sep"]("A;B;C\n1;2;3\n"), ";")
        self.assertEqual(ns["_sniff_sep"]("A,B,C\n1,2,3\n"), ",")
        self.assertEqual(ns["_sniff_sep"]("A\tB\tC\n1\t2\t3\n"), "\t")

    def test_reanudacion_no_confunde_numero_de_fuentes_con_numero_de_secciones(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            declaration = root / "territorios/x/config/fuentes_oficiales.yaml"
            declaration.parent.mkdir(parents=True)
            declaration.write_text(yaml.safe_dump({
                "territory": {"id": "x", "edition": 2025},
                "coverage_checks": {"expected_sections": 2134},
            }), encoding="utf-8")

            package = root / "package"
            package.mkdir()
            bundle = package / "prepared_sources.zip"
            with zipfile.ZipFile(bundle, "w") as zf:
                zf.writestr("dummy.txt", "ok")
            import hashlib
            manifest = {
                "source_id": "prepared-territorial-sources:a,b",
                "territory_id": "x",
                "edition": 2025,
                "origin": "official",
                "path": bundle.name,
                "bytes": bundle.stat().st_size,
                "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
                "records": 2,
                "acquired_at": "2026-09-20T00:00:00Z",
            }
            (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            # validate_resume_sources obtiene territory_id del contrato principal.
            params = root / "territorios/x/config/params.yaml"
            params.write_text(yaml.safe_dump({"meta": {"territory_id": "x"}}), encoding="utf-8")
            result = validate_resume_sources(params=params, package=package, root_dir=root)
            self.assertEqual(result["decision"], "REUSE")
            self.assertEqual(result["records"], 2)

    def test_galicia_declara_pasarelas_y_cuotas_completas(self):
        cfg = yaml.safe_load((ROOT / "territorios/galicia/config/galicia_2025.yaml").read_text(encoding="utf-8"))
        bridges = cfg["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"]
        self.assertEqual([b["admin_scope"] for b in bridges], ["province:36", "municipality:36006"])
        self.assertEqual(cfg["validation"]["province_districts"], {"15": 31, "27": 9, "32": 9, "36": 26})
        self.assertEqual(sum(cfg["validation"]["province_districts"].values()), 75)
        self.assertNotIn("require_zero_outside_tolerance_after_m05", cfg["validation"])

    def test_m04_soporta_residuales_provinciales_desconectados(self):
        source = (ROOT / "ddd_core/m04_seed_engine_v745.py").read_text(encoding="utf-8")
        self.assertIn("Los núcleos cerrados pueden separar legítimamente el residual provincial", source)
        self.assertIn("if need not in states:", source)
        self.assertNotIn("unidades abiertas desconectadas provincia", source)

    def test_reparacion_no_abre_distritos_urbanos_cerrados(self):
        path = ROOT / "modulos/05_optimizar_distritos.py"
        source = path.read_text(encoding="utf-8")
        ns = {"__file__": str(path), "__name__": "ddd_m05_test"}
        exec(compile(source.replace('if __name__=="__main__": main()', ''), str(path), "exec"), ns)
        protect = ns["_protect_closed_urban_districts"]
        g = pd.DataFrame({
            "district_id": [1, 2, 2],
            "ddd_closed_urban": [True, False, False],
        }, index=["u1", "u2", "u3"])
        assignments = {"u1": 1, "u2": 2, "u3": 2}
        adj = {"u1": {"u2"}, "u2": {"u1", "u3"}, "u3": {"u2"}}
        protected, frozen_districts, frozen_units, baseline = protect(g, "district_id", assignments, adj)
        self.assertEqual(frozen_districts, {1})
        self.assertEqual(frozen_units, {"u1"})
        self.assertEqual(baseline, {"u1": 1})
        self.assertEqual(protected["u1"], set())
        self.assertEqual(protected["u2"], {"u3"})
        self.assertEqual(protected["u3"], {"u2"})


if __name__ == "__main__":
    unittest.main()
