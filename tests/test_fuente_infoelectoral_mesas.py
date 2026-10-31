"""Versión 1.0.0; 2026-10-30; candidato. Conversor del ZIP oficial Infoelectoral por mesa.
Origen: nuevo, sin predecesor. Los registros siguen el ancho fijo real de 02202307_MESA.zip (Huesca).
"""
from __future__ import annotations

import csv
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas.fuente_infoelectoral_mesas import convert, resolve  # noqa: E402

PREFIX = "02202307"
# Registro 09 real de la mesa 1 de Huesca (municipio 001): censo 225, 176 votos a candidaturas.
REAL_09 = "022023071022200101001 U00002250000225000000000000000000098000012300000000000000000017600000000000000S"


def r09(mun: str, dis: str, sec: str, mesa: str, census: int, blank: int, null: int, cand: int) -> str:
    head = f"{PREFIX}10222{mun}{dis}{sec:<4}{mesa}"
    body = f"{census:07d}{census:07d}{0:07d}{0:07d}{0:07d}{0:07d}{blank:07d}{null:07d}{cand:07d}"
    return (head + body).ljust(100, "0") + "S"


def r10(mun: str, dis: str, sec: str, mesa: str, party: str, votes: int) -> str:
    return f"{PREFIX}10222{mun}{dis}{sec:<4}{mesa}{party}{votes:07d}"


def r03(party: str, siglas: str) -> str:
    return f"{PREFIX}{party}{siglas:<50}{siglas:<150}"


class InfoelectoralConversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _zip(self, records09, records10):
        path = self.root / "mesas.zip"
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("09022307.DAT", "\r\n".join(records09).encode("iso-8859-1"))
            zf.writestr("10022307.DAT", "\r\n".join(records10).encode("iso-8859-1"))
            zf.writestr("03022307.DAT", "\r\n".join([r03("000001", "FO"), r03("000002", "PSOE")]).encode("iso-8859-1"))
        return path

    def _contract(self, path, **expected):
        base = {"ccaa": "02", "sections": 2, "polling_stations": 3, "parties": 2, "candidate_votes": 30,
                "blank_votes": 2, "null_votes": 1, "voters": 33, "cera_records": 1}
        base.update(expected)
        return {"election_id": "demo", "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "election_prefix": PREFIX, "province": "22",
                "files": {"mesas": "09022307.DAT", "candidaturas_mesa": "10022307.DAT", "candidaturas": "03022307.DAT"},
                "expected": base}

    def _fixture(self):
        records09 = [r09("001", "01", "001", "A", 100, 1, 1, 10), r09("001", "01", "001", "B", 100, 1, 0, 12),
                     r09("002", "01", "002", "U", 50, 0, 0, 8), r09("999", "09", "001", "U", 900, 4, 11, 943)]
        records10 = [r10("001", "01", "001", "A", "000001", 4), r10("001", "01", "001", "A", "000002", 6),
                     r10("001", "01", "001", "B", "000002", 12), r10("002", "01", "002", "U", "000001", 8),
                     r10("999", "09", "001", "U", "000002", 943)]
        return records09, records10

    def test_real_record_layout_parses(self):
        self.assertEqual(101, len(REAL_09))
        self.assertEqual(REAL_09[:18], r09("001", "01", "001", "U", 225, 0, 0, 176)[:18])
        self.assertEqual(REAL_09[18:23], "001 U")
        self.assertEqual(int(REAL_09[79:86]), 176)

    def test_mesas_aggregate_to_cusec_and_cera_is_excluded(self):
        path = self._zip(*self._fixture())
        out = self.root / "mesas.csv"
        summary = convert(path, self._contract(path), out)
        self.assertEqual(3, summary["polling_stations"])
        self.assertEqual(2, summary["sections"])
        self.assertEqual({"records": 1, "blank_votes": 4, "null_votes": 11, "candidate_votes": 943}, summary["cera_excluded"])
        rows = list(csv.DictReader(out.open(encoding="utf-8")))
        cusecs = {r["codigo_provincia"] + r["codigo_municipio"] + r["codigo_distrito"] + r["codigo_seccion"] for r in rows}
        self.assertEqual({"2200101001", "2200201002"}, cusecs)
        self.assertEqual(30, sum(int(r["votos"]) for r in rows))
        self.assertEqual({"FO", "PSOE"}, {r["partido"] for r in rows})

    def test_totals_must_match_contract(self):
        path = self._zip(*self._fixture())
        with self.assertRaisesRegex(ValueError, "candidate_votes"):
            convert(path, self._contract(path, candidate_votes=31, voters=34), self.root / "x.csv")

    def test_party_votes_must_match_mesa_total(self):
        records09, records10 = self._fixture()
        records10[0] = r10("001", "01", "001", "A", "000001", 5)
        path = self._zip(records09, records10)
        with self.assertRaisesRegex(ValueError, "mesas con votos"):
            convert(path, self._contract(path), self.root / "x.csv")

    def test_zip_fingerprint_is_enforced(self):
        path = self._zip(*self._fixture())
        contract = self._contract(path)
        contract["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            convert(path, contract, self.root / "x.csv")


class HuescaContractTests(unittest.TestCase):
    def test_huesca_contract_reconciles_official_totals_minus_cera(self):
        contract = resolve(election_id="congreso_huesca_2023-07-23", territory_id="congreso_huesca",
                           election_date="2023-07-23", root_dir=ROOT)
        self.assertEqual("e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8", contract["source_sha256"])
        self.assertEqual(117735, contract["expected"]["candidate_votes"])
        self.assertEqual(120190, contract["expected"]["voters"])


if __name__ == "__main__":
    unittest.main()
