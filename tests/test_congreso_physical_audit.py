"""Physical-contact semantics: only positive linear borders form graph edges."""
import unittest

try:
    from shapely.geometry import box
    from herramientas.auditar_contiguedad_piloto_congreso import classify_contact, _polygon_parts
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


if __name__ == "__main__":
    unittest.main()
