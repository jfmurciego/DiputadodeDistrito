"""Physical-contact semantics: only positive linear borders form graph edges."""
import unittest

try:
    from shapely.geometry import box
    from herramientas.auditar_contiguedad_piloto_congreso import (
        classify_contact, _polygon_parts, _topology_polygon_part_ids,
    )
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False


@unittest.skipUnless(HAS_SHAPELY, "Shapely geospatial runtime unavailable")
class PhysicalAuditTests(unittest.TestCase):
    def test_positive_shared_border_is_linear_edge(self):
        result = classify_contact(box(0, 0, 1, 1), box(1, 0, 2, 1))
        self.assertEqual(result["kind"], "LINEAR")
        self.assertEqual(result["shared_border_m"], 1)

    def test_point_contact_is_not_an_edge(self):
        result = classify_contact(box(0, 0, 1, 1), box(1, 1, 2, 2))
        self.assertEqual(result["kind"], "POINT")
        self.assertEqual(result["shared_border_m"], 0)

    def test_positive_area_overlap_is_reported_and_not_an_edge(self):
        result = classify_contact(box(0, 0, 2, 2), box(1, 1, 3, 3))
        self.assertEqual(result["kind"], "OVERLAP")
        self.assertEqual(result["overlap_area_m2"], 1)
        self.assertEqual(result["shared_border_m"], 0)

    def test_multipolygon_parts_remain_independent(self):
        from shapely.geometry import MultiPolygon
        self.assertEqual(len(_polygon_parts(MultiPolygon([box(0, 0, 1, 1), box(3, 0, 4, 1)]))), 2)

    def test_polygon_part_inventory_is_not_component_representative_count(self):
        topology = {
            "nodes": [{"CUSEC": "2405001001", "physical_part_components": ["2400101001:p0000"]}],
            "polygon_part_components": [{
                "id": "2400101001:p0000",
                "parts": ["2405001001:p0000", "2405001001:p0001"],
            }],
        }
        self.assertEqual(
            _topology_polygon_part_ids(topology)["2405001001"],
            ["2405001001:p0000", "2405001001:p0001"],
        )

    def test_duplicate_polygon_part_identity_is_rejected(self):
        topology = {"polygon_part_components": [
            {"parts": ["2405001001:p0000"]},
            {"parts": ["2405001001:p0000"]},
        ]}
        with self.assertRaisesRegex(ValueError, "TOPOLOGY_POLYGON_PART_ID_INVALID"):
            _topology_polygon_part_ids(topology)


if __name__ == "__main__":
    unittest.main()
