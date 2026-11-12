"""Versión 1.0.0; 2026-11-02; candidato. T-27 fase (a): escenarios no canónicos en el registro del visor."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas import registro_publicaciones_visor as reg
from herramientas.preparar_visor_ejecucion import _decorate_and_sort, add_registered_product

ROOT = Path(__file__).resolve().parents[1]
REPO = "jfmurciego/DiputadodeDistrito"


def entry(kind, ident, **extra):
    blob = hashlib.sha1(ident.encode()).hexdigest()
    base = {"id": ident, "asset_type": "territorial_product", "source_type": "repository_blob", "repository": REPO,
            "blob_sha": blob, "immutable_location": f"github-git-blob://{REPO}/{blob}",
            "territory_id": "nac37", "sha256": hashlib.sha256(ident.encode()).hexdigest(), "kind": kind,
            "run_id": 111, "expected_districts": 1, "label": ident}
    base.update(extra)
    return base


def scenario(kind="scenario_m06", ident="s6", scenario_id="gerrychain-50-111", **extra):
    fields = {"scenario_id": scenario_id, "strategy": "GerryChain 50", "scenario_kind": "alternative", **extra}
    return entry(kind, ident, **fields)


def registry(*products):
    return {"schema": reg.SCHEMA, "products": list(products), "ensembles": []}


class RegistroEscenariosTests(unittest.TestCase):
    def test_par_de_escenario_valido_y_canonicos_intactos(self):
        reg.validate_registry(registry(entry("canonical_m06", "c6"), entry("canonical_m08", "c8"),
                                       scenario(), scenario("scenario_m08", "s8")))
        reg.validate_registry(json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8")))

    def test_campos_obligatorios_del_escenario(self):
        for broken in (scenario(scenario_id=""), scenario(strategy="Otra"), scenario(strategy=None),
                       {**scenario(), "scenario_kind": "canonical"}, {**scenario(), "canonical": True}):
            with self.assertRaises(ValueError):
                reg.validate_registry(registry(broken))

    def test_m08_exige_el_m06_del_mismo_escenario(self):
        with self.assertRaisesRegex(ValueError, "sin scenario_m06"):
            reg.validate_registry(registry(scenario("scenario_m08", "s8")))
        with self.assertRaisesRegex(ValueError, "sin scenario_m06"):
            reg.validate_registry(registry(scenario(), scenario("scenario_m08", "s8", scenario_id="otro")))

    def test_un_solo_canonical_true_por_territorio_y_familia(self):
        reg.validate_registry(registry(entry("canonical_m06", "c6", canonical=True), entry("canonical_m06", "d6", run_id=2),
                                       entry("canonical_m08", "c8", canonical=True)))
        with self.assertRaisesRegex(ValueError, "más de una entrada canonical=true"):
            reg.validate_registry(registry(entry("canonical_m06", "c6", canonical=True),
                                           entry("canonical_m06", "d6", run_id=2, canonical=True)))
        with self.assertRaises(ValueError):
            reg.validate_registry(registry(entry("canonical_m06", "c6", canonical=False)))

    def test_identidad_de_escenario_por_scenario_id_y_solo_adicion(self):
        a, b = scenario(), scenario(ident="t6", scenario_id="gerrychain-50-222", run_id=222)
        reg.validate_registry(registry(a, b))  # mismo run no hace falta: la identidad es el scenario_id
        with self.assertRaisesRegex(ValueError, "duplicada"):
            reg.validate_registry(registry(a, scenario(ident="u6")))
        r = registry(entry("canonical_m06", "c6"))
        reg.upsert_entry(r, scenario())
        reg.upsert_entry(r, scenario("scenario_m08", "s8"))
        self.assertEqual({e["kind"] for e in r["products"]}, {"canonical_m06", "scenario_m06", "scenario_m08"})

    def test_el_visor_materializa_y_ordena_los_escenarios(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            site, mat = root / "site", root / "mat"
            payload = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"district_id": 1},
                 "geometry": {"type": "Polygon", "coordinates": [[[-5.6, 40.9], [-5.5, 40.9], [-5.5, 41.0], [-5.6, 40.9]]]}}]}
            results = []
            for e in (scenario(), entry("canonical_m06", "c6"), scenario("scenario_m08", "s8")):
                (mat / e["id"]).mkdir(parents=True)
                with zipfile.ZipFile(mat / e["id"] / "asset", "w") as z:
                    z.writestr("x.geojson", json.dumps(payload))
                add_registered_product(e, ROOT, mat, site, results)
            sc = next(r for r in results if r["kind"] == "scenario_m06")
            self.assertEqual((sc["strategy"], sc["scenario_id"]), ("GerryChain 50", "gerrychain-50-111"))
            self.assertEqual(sc["viewer_path"], "data/results/congreso_salamanca/scenario-gerrychain-50-111/m06.geojson")
            ordered = [r["kind"] for r in _decorate_and_sort(copy.deepcopy(results), ROOT)]
            self.assertLess(ordered.index("canonical_m06"), ordered.index("scenario_m08"))
            self.assertLess(ordered.index("scenario_m08"), ordered.index("scenario_m06"))


if __name__ == "__main__":
    unittest.main()
