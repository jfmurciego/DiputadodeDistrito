"""Asegura que el límite histórico no omita contactos del índice espacial."""
import importlib.util
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ddd_m02_candidate_completeness", ROOT / "modulos" / "02_construir_adyacencias.py"
)
M02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M02)
OLD_SPEC = importlib.util.spec_from_file_location(
    "ddd_m02_candidate_completeness_v732",
    ROOT / "legacy" / "modulo02" / "02_construir_adyacencias_v7.3.2.py",
)
OLD_M02 = importlib.util.module_from_spec(OLD_SPEC)
if OLD_SPEC is None or OLD_SPEC.loader is None:
    raise ImportError("No se pudo cargar el predecesor M02 v7.3.2")
OLD_SPEC.loader.exec_module(OLD_M02)


def _fixture():
    features = []
    for side, x0 in (("L", 0), ("R", 100)):
        holes = []
        fragments = []
        for ix in range(7):
            for iy in range(8):
                cx, cy = x0 + 32 + ix * 5, 30 + iy * 5
                holes.append(
                    [
                        (cx - 1.4, cy - 1.4),
                        (cx + 1.4, cy - 1.4),
                        (cx + 1.4, cy + 1.4),
                        (cx - 1.4, cy + 1.4),
                        (cx - 1.4, cy - 1.4),
                    ]
                )
                fragments.append(
                    (
                        f"{side}F{ix:02d}{iy:02d}",
                        Polygon(
                            [
                                (cx - 0.5, cy - 0.5),
                                (cx + 0.5, cy - 0.5),
                                (cx + 0.5, cy + 0.5),
                                (cx - 0.5, cy + 0.5),
                            ]
                        ),
                    )
                )
        outer = (
            [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
            if side == "L"
            else [(100, 0), (200, 0), (200, 100), (100, 100), (100, 0)]
        )
        features.append((f"{side}BIG", Polygon(outer, holes=holes)))
        features.extend(fragments)
    return gpd.GeoDataFrame(
        {"CUSEC_KEY": [key for key, _ in features]},
        geometry=[geom for _, geom in features],
        crs="EPSG:3035",
    )


def _edges(gdf, max_candidates, module=M02):
    return sorted(
        module.iter_edges(
            gdf,
            "CUSEC_KEY",
            "contact",
            1.0,
            1.0,
            0.0,
            0.0,
            max_candidates,
            0,
            "EPSG:3035",
        )
    )


def test_candidate_limit_does_not_drop_far_centroid_shared_boundary():
    gdf = _fixture()

    before = _edges(gdf, 50, OLD_M02)
    capped = _edges(gdf, 50)
    exhaustive = _edges(gdf, 0)

    assert ("LBIG", "RBIG") not in before
    assert ("LBIG", "RBIG") in exhaustive
    assert capped == exhaustive
    assert _edges(gdf, 50) == capped
