import csv
import json
from pathlib import Path

from herramientas.generar_nombres_distrito import build_names


ROOT = Path(__file__).resolve().parents[1]


def test_nombres_publicados_son_completos_unicos_y_recomputables():
    config = json.loads((ROOT / "configuracion/nombres_distrito.json").read_text(encoding="utf-8"))
    with (ROOT / config["output_csv"]).open(encoding="utf-8", newline="") as source:
        published = list(csv.DictReader(source))
    expected = []
    for territory, relative in sorted(config["territories"].items()):
        expected.extend(build_names(territory, ROOT / relative, config["dominant_municipality_threshold"]))
    expected.sort(key=lambda row: (row["territory"], row["district_id"]))
    assert len(published) == len(expected) == 214
    assert len({row["district_name"] for row in published}) == 214
    assert [row["district_name"] for row in published] == [row["district_name"] for row in expected]


def test_informe_prueba_ausencia_de_datos_partidistas():
    report = json.loads((ROOT / "resultados/fase1/NOMBRES_DISTRITO_INFORME.json").read_text(encoding="utf-8"))
    assert report["districts"] == 214
    assert report["unique_names"] == 214
    assert report["partisan_fields_used"] == []
