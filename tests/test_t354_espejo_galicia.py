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

    def test_huellas_del_propietario_casan_con_los_4_ids_de_la_declaracion(self):
        # literales independientes: huellas medidas por el propietario (Windows, HTTP 200) el 2026-11-15
        esperado = {
            "a_coruna_mesas": (126382, "b763e5648136b80d805378532bd03dfe49025b063c9c17a1b6b1f365148735d1"),
            "lugo_mesas": (42842, "89afa88e7e9e7c7fee09402e98c4abddbfec635c80ea2dc56d37f63e515931b0"),
            "ourense_mesas": (45226, "9e7992fc0665cf485aff13f621470b6cfe73ed814dfcd0627622c197fc1a050d"),
            "pontevedra_mesas": (109012, "aa5be16cb0702ca2315dc0c08c437e296b8dcbf35efe45610818daf01eb8233d"),
        }
        d = _decl()
        self.assertEqual({s["id"] for s in d["sources"]}, set(esperado))
        for sid, (n, sha) in esperado.items():
            e = f.ficha(f"{d['election_id']}_{sid}.csv")
            self.assertEqual((e["bytes"], e["sha256"]), (n, sha))
            self.assertRegex(e["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(e["clave"], f"arc-e/fuentes/xunta/{d['election_id']}_{sid}_{sha[:12]}.csv")

    def test_traer_es_fail_closed_con_la_huella_del_indice(self):
        nombre = "galicia_parlamento_2024_lugo_mesas.csv"
        with mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            self.assertIsNone(f.traer(nombre, cp=lambda o, dst, e=None: Path(dst).write_bytes(b"otra cosa")))
            self.assertEqual(f.bajar(nombre, Path(tempfile.mkdtemp()) / "x", cp=lambda o, dst, e=None: Path(dst).write_bytes(b"otra cosa")), 53)

    def test_entrada_pendiente_no_se_usa(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            idx = Path(td) / "i.json"
            idx.write_text(json.dumps({"fuentes": {"p.csv": {"clave": None, "sha256": None}}}))
            self.assertIsNone(f.traer("p.csv", cp=mock.Mock(side_effect=AssertionError), indice=idx))
            self.assertEqual(f.bajar("p.csv", Path(td) / "x", indice=idx), 3)

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

    def test_espejo_roto_cae_a_la_oficial(self):
        def roto(n):
            raise ImportError("fuente_r2")
        with tempfile.TemporaryDirectory() as td:
            r = check_declaration(_decl(), td, opener=lambda req, timeout=0: Resp(CSV), espejo=roto)
        self.assertEqual(r["decision"], "READY")
        self.assertTrue(all(x.get("origin") is None for x in r["selected_sources"]))

    def test_integrado_espejo_no_verificado_cae_a_la_oficial(self):
        # traer() real: huella del índice distinta de los bytes, y entrada con sha256 null: nunca se mezclan bytes sin verificar
        basura = b"mesa;censo;votos\n99;1;1\n"
        d = _decl()
        for sha in ("0" * 64, None):
            with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as td2, mock.patch.dict("os.environ", {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
                idx = Path(td) / "i.json"
                idx.write_text(json.dumps({"fuentes": {f"{d['election_id']}_{s['id']}.csv": {"clave": "k", "sha256": sha} for s in d["sources"]}}))
                espejo = lambda n: f.traer(n, cp=lambda o, dst, e=None: Path(dst).write_bytes(basura), indice=idx)
                r = check_declaration(d, td2, opener=lambda req, timeout=0: Resp(CSV), espejo=espejo)
            self.assertEqual(r["decision"], "READY")
            self.assertTrue(all(x.get("origin") is None and x["sha256"] == hashlib.sha256(CSV).hexdigest() for x in r["selected_sources"]))

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
