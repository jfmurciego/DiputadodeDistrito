"""
Nombre: Regresión M02 de reproyección valenciana
Versión: 1.0.0
Fecha: 2026-10-19
Alcance: prueba de dos pares de contacto del original INE 2025
Estado: candidato
Cambios/motivo: impedir que EPSG:3035 oculte contactos fuente bajo el umbral de solape
Anterior: no existe; nueva regresión con geometrías oficiales protegidas
"""
import importlib.util
from pathlib import Path
import unittest

import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "territorios/comunidad_valenciana/config/comunidad_valenciana_2025.yaml"
FIXTURE = ROOT / "tests/fixtures/f10_valencia_m02_native_crs/source_touch_pairs_2025.geojson"
SPEC = importlib.util.spec_from_file_location("m02_valencia", ROOT / "modulos/02_construir_adyacencias.py")
M02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M02)
PAIRS = {
    ("4616401004", "4620701007"),
    ("4619401013", "4624404012"),
}


class ValenciaM02NativeCrsTests(unittest.TestCase):
    def test_config_preserves_contract_and_uses_metric_crs(self):
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        m02 = config["modulos"]["modulo_02_construir_adyacencias"]
        self.assertEqual(m02["working_crs"], "EPSG:25830")
        self.assertEqual(m02["max_precision_overlap_area_m2"], 1.0)
        self.assertEqual(m02["min_shared_border_m"], 1.0)
        self.assertEqual(m02["buffer_m"], 0.0)
        self.assertEqual(m02["simplify_m"], 0.0)
        self.assertEqual(config["meta"]["source_section_year"], 2025)
        self.assertEqual(config["meta"]["source_population_year"], 2025)

    def test_source_contacts_are_admitted_without_projected_overlap(self):
        gdf = gpd.read_file(FIXTURE)
        self.assertEqual(gdf.crs.to_epsg(), 4326)
        self.assertEqual(set(gdf["CUSEC_KEY"]), {x for pair in PAIRS for x in pair})
        original = gdf.set_index("CUSEC_KEY")
        for left, right in PAIRS:
            a, b = original.loc[left].geometry, original.loc[right].geometry
            self.assertTrue(a.touches(b))
            self.assertGreater(a.boundary.intersection(b.boundary).length, 0.0)
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        m02 = config["modulos"]["modulo_02_construir_adyacencias"]

        def edges(crs):
            return set(M02.iter_edges(
                gdf,
                m02["id_field"],
                m02["predicate"],
                float(m02["min_shared_border_m"]),
                float(m02["max_precision_overlap_area_m2"]),
                float(m02["buffer_m"]),
                float(m02["simplify_m"]),
                int(m02["max_candidates"]),
                0,
                crs,
            ))

        self.assertEqual(edges("EPSG:3035"), set())
        self.assertEqual(edges(m02["working_crs"]), PAIRS)

        metric = gdf.to_crs(m02["working_crs"]).set_index("CUSEC_KEY")
        for left, right in PAIRS:
            a, b = metric.loc[left].geometry, metric.loc[right].geometry
            self.assertTrue(a.intersects(b))
            self.assertGreaterEqual(a.boundary.intersection(b.boundary).length, 1.0)
            self.assertLessEqual(a.intersection(b).area, 1.0)


if __name__ == "__main__":
    unittest.main()
