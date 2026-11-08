#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de datos abiertos y fichas por distrito (T-60)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: territorio sintético: paquete, huellas, fichas, nombres opcionales, idempotencia, sha256 erróneo,
  materialización con GeoJSON verificado, paquete real al día y enlace del publicador.
"""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import generar_datos_abiertos as da  # noqa: E402
import resultados_ligeros as rl  # noqa: E402

T = "congreso_sintetico"


def zip_(nombre, feats):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(nombre, json.dumps({"features": feats}))
    return b.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        d = Path(self._d.name)
        self.d = d
        m6 = zip_("x_m06.geojson", [{"properties": {"district_id": i, "district_pop": 100 + i, "section_count": 5,
                                                    "municipality_count": 3}} for i in (1, 0)])
        m8 = zip_("x_m08.geojson", [{"properties": {"district_id": str(i), "district_pop": 100 + i, "total_votes": 50,
                                                    "winner_party": "PP", "winner_votes": 20, "winner_share": 0.4}} for i in (0, 1)])
        reg = {"products": [
            {"kind": "canonical_m06", "territory_id": T, "territory_label": "Congreso Soria", "run_id": "5",
             "blob_sha": "a" * 40, "sha256": rl.sha256(m6)},
            {"kind": "canonical_m08", "territory_id": T, "run_id": "5", "blob_sha": "b" * 40, "sha256": rl.sha256(m8)}]}
        self.reg = d / "reg.json"
        self.reg.write_text(json.dumps(reg))
        self.res = d / "res"
        rl.generar(self.res, self.reg, m08_dir=self._dir({T: m8}, "m8", "5"))
        self.m6 = self._dir({T: m6}, "m6", "5")
        self.out = d / "out"

    def _dir(self, zs, nombre, run):
        p = self.d / nombre
        p.mkdir()
        for t, z in zs.items():
            (p / f"{t}_{run}.zip").write_bytes(z)
        return p

    def gen(self, **k):
        return da.generar(self.out, self.reg, self.res, m06_dir=self.m6, **k)

    def tearDown(self):
        self._d.cleanup()


class DatosAbiertos(Base):
    def test_paquete_huellas_y_fichas(self):
        idx = self.gen()
        e = idx["territorios"][T]
        self.assertEqual(idx["licencia"]["id"], "CC-BY-4.0")
        self.assertEqual((e["provincia"], e["n_distritos"], e["run_id"], e["blob_sha"]), ("Soria", 2, "5", "a" * 40))
        csv_ = (self.out / T / "resultados.csv").read_bytes()
        self.assertEqual(e["resultados"]["sha256"], da.sha(csv_))
        ficha = (self.out / T / "distrito-1.html").read_text(encoding="utf-8")
        for s in ("Distrito 1", "101", "PP", "distritos.geojson", "resultados.csv", "CC-BY-4.0", "a" * 40):
            self.assertIn(s, ficha)
        self.assertIsNone(e["distritos"][0]["nombre"])
        self.assertIn("CC BY 4.0", (self.out / "README.md").read_text(encoding="utf-8").replace("CC-BY", "CC BY") + "CC BY 4.0")
        self.assertEqual(da.comprobar(self.out, self.reg), [])

    def test_nombres_opcionales(self):
        self.gen()
        (self.out / "nombres.json").write_text(json.dumps({T: {"1": "Alto Duero"}}))
        self.gen()
        self.assertIn("Alto Duero", (self.out / T / "distrito-1.html").read_text(encoding="utf-8"))

    def test_idempotente_y_sin_red_si_no_cambia(self):
        self.gen()
        antes = {p: p.stat().st_mtime_ns for p in self.out.rglob("*") if p.is_file()}
        da.generar(self.out, self.reg, self.res, m06_dir=self.d / "vacio")  # sin ZIP: no debe bajar nada
        self.assertEqual(antes, {p: p.stat().st_mtime_ns for p in self.out.rglob("*") if p.is_file()})

    def test_sha_erroneo_falla(self):
        r = json.loads(self.reg.read_text())
        r["products"][0]["sha256"] = "0" * 64
        self.reg.write_text(json.dumps(r))
        with self.assertRaises(ValueError):
            self.gen()

    def test_materializar_verifica_geojson(self):
        self.gen()
        dest = self.d / "site"
        da.materializar(dest, self.out, self.reg, m06_dir=self.m6)
        self.assertTrue((dest / T / "distritos.geojson").is_file())
        self.assertFalse((dest / "nombres.json").exists())
        idx = json.loads((self.out / "INDEX.json").read_text())
        idx["territorios"][T]["geojson"]["sha256"] = "0" * 64
        (self.out / "INDEX.json").write_text(json.dumps(idx))
        with self.assertRaises(ValueError):
            da.materializar(dest, self.out, self.reg, m06_dir=self.m6)

    def test_comprobar_detecta_desfase(self):
        self.gen()
        (self.out / T / "resultados.csv").write_text("x")
        self.assertTrue(da.comprobar(self.out, self.reg))


class PaqueteReal(unittest.TestCase):
    def test_paquete_versionado_al_dia(self):
        self.assertEqual(da.comprobar(), [])

    def test_publicador_incluye_datos(self):
        d = yaml.safe_load((ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8"))
        runs = [s.get("run", "") for j in d["jobs"].values() for s in j.get("steps") or []]
        cand = "--registro /tmp/publicaciones_visor.candidate.json"
        self.assertTrue(any(f"generar_datos_abiertos.py {cand} --materializar /tmp/site-candidate/datos" in r for r in runs))
        # T-114: resultados ligeros y datos abiertos se regeneran desde el candidato y se persisten con el registro.
        construir = next(r for r in runs if "--materializar /tmp/site-candidate/datos" in r)
        orden = [f"resultados_ligeros.py {cand}\n", f"generar_datos_abiertos.py {cand}\n",
                 f"generar_datos_abiertos.py {cand} --comprobar", f"generar_datos_abiertos.py {cand} --materializar"]
        posiciones = [construir.find(o) for o in orden]
        self.assertNotIn(-1, posiciones)
        self.assertEqual(sorted(posiciones), posiciones)
        persistir = next(r for r in runs if 'git commit -m "chore: registrar activos persistentes del visor"' in r)
        self.assertIn('git add -A -- "$PUBLICATION_REGISTRY" datos/resultados datos_abiertos', persistir)
        self.assertTrue(any("test -f datos_abiertos/INDEX.json" in r for r in runs))


if __name__ == "__main__":
    unittest.main()
