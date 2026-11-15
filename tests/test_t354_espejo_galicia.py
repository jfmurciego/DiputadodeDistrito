"""T-354: espejo en R2 (ARC-E) de las 4 fuentes de mesas de Galicia; la 03 las lee del espejo con la misma huella que la fuente oficial."""
import hashlib
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest import mock

import yaml

from herramientas import fuente_r2 as f
from herramientas.comprobar_fuente_electoral_oficial import check_declaration

ROOT = Path(__file__).resolve().parents[1]
DECL = ROOT / "territorios/aut12/config/elecciones/galicia_parlamento_vigente.yaml"
CSV = b"mesa;censo;votos\n01;100;50\n"


def _decl():
    return yaml.safe_load(DECL.read_text(encoding="utf-8"))


class Resp:
    status = 200

    def __init__(self, data):
        self._d = data
        self.headers = Message()
        self.headers["Content-Type"] = "text/csv"

    def read(self, n=-1):
        return self._d if n < 0 else self._d[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class EspejoGalicia(unittest.TestCase):
    def test_indice_trae_las_4_fuentes_de_la_declaracion(self):
        d = _decl()
        idx = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]
        for s in d["sources"]:
            nombre = f"{d['election_id']}_{s['id']}.csv"
            self.assertIn(nombre, idx)
            self.assertEqual(idx[nombre]["origen_url"], s["url"])
        self.assertEqual(d["territory_id"], "aut12")

    def test_entrada_pendiente_no_se_usa(self):
        with mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            self.assertIsNone(f.traer("galicia_parlamento_2024_lugo_mesas.csv", cp=mock.Mock(side_effect=AssertionError)))
            self.assertEqual(f.bajar("galicia_parlamento_2024_lugo_mesas.csv", Path("x")), 3)

    def test_la_03_lee_del_espejo_sin_red_y_con_la_misma_huella(self):
        d = _decl()
        def opener(request, timeout=0):
            raise AssertionError("no debe ir a la Xunta")
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as td2:
            r_esp = check_declaration(d, td, opener=opener, espejo=lambda n: CSV)
            r_of = check_declaration(d, td2, opener=lambda req, timeout=0: Resp(CSV), espejo=lambda n: None)
        for r, origen in ((r_esp, "r2_mirror"), (r_of, None)):
            self.assertEqual(r["decision"], "READY")
            self.assertEqual(len(r["selected_sources"]), 4)
            self.assertTrue(all(x.get("origin") == origen for x in r["selected_sources"]))
        self.assertEqual([x["sha256"] for x in r_esp["selected_sources"]], [x["sha256"] for x in r_of["selected_sources"]])
        self.assertEqual(r_esp["selected_sources"][0]["sha256"], hashlib.sha256(CSV).hexdigest())

    def test_espejo_pide_el_nombre_election_source(self):
        d = _decl()
        pedidos = []
        with tempfile.TemporaryDirectory() as td:
            check_declaration(d, td, opener=lambda req, timeout=0: Resp(CSV), espejo=lambda n: pedidos.append(n))
        self.assertEqual(pedidos, [f"{d['election_id']}_{s['id']}.csv" for s in d["sources"]])

    def test_espejo_con_huella_distinta_cae_a_la_oficial(self):
        datos = b"otro"
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            idx = Path(td) / "i.json"
            idx.write_text(json.dumps({"fuentes": {"x.csv": {"clave": "k", "sha256": "0" * 64}}}))
            self.assertIsNone(f.traer("x.csv", cp=lambda o, d, e=None: Path(d).write_bytes(datos), indice=idx))

    def test_traer_devuelve_bytes_verificados(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            idx = Path(td) / "i.json"
            idx.write_text(json.dumps({"fuentes": {"x.csv": {"clave": "k", "sha256": hashlib.sha256(CSV).hexdigest()}}}))
            self.assertEqual(f.traer("x.csv", cp=lambda o, d, e=None: Path(d).write_bytes(CSV), indice=idx), CSV)


if __name__ == "__main__":
    unittest.main()
