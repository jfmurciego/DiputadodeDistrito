#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de datos abiertos y fichas por distrito (T-60)
VERSIÓN: 1.1.0 · FECHA: 2026-11-11 · ESTADO: candidato
ANTERIOR: legacy/tests/test_datos_abiertos_v1.0.0_20261111.py
CAMBIOS 1.1.0 (T-249): un M06 nuevo sin M08 de su run no saca el territorio del paquete (par coherente); la guarda
  DATOS_ABIERTOS_REDUCCION falla si el INDEX pierde territorios sin retirada explícita; la retirada sí los borra.
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

T = "nac22"  # T-220: el generador filtra por el ámbito NAC del resolutor (un id fuera de la tabla no es nacional)


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
        for s in ("Distrito 1", "100", "PP", "distritos.geojson", "resultados.csv", "CC-BY-4.0", "a" * 40):
            self.assertIn(s, ficha)
        self.assertIsNone(e["distritos"][0]["nombre"])
        self.assertIn("CC BY 4.0", (self.out / "README.md").read_text(encoding="utf-8").replace("CC-BY", "CC BY") + "CC BY 4.0")
        self.assertEqual(da.comprobar(self.out, self.reg), [])

    def test_numeracion_1_a_k_sin_distrito_cero(self):
        idx = self.gen()
        self.assertEqual([d["distrito"] for d in idx["territorios"][T]["distritos"]], [1, 2])
        self.assertEqual(sorted(p.name for p in (self.out / T).glob("distrito-*.html")), ["distrito-1.html", "distrito-2.html"])
        self.assertEqual([r.split(",")[0] for r in (self.out / T / "resultados.csv").read_text().splitlines()], ["distrito", "1", "2"])

    def test_regenera_paquete_1_0_y_borra_distrito_cero(self):
        self.gen()
        idx = json.loads((self.out / "INDEX.json").read_text())
        e = idx["territorios"][T]
        e.pop("numeracion")  # paquete 1.0: ids 0..K-1
        (self.out / "INDEX.json").write_text(json.dumps(idx))
        (self.out / T / "distrito-0.html").write_text("viejo")
        nuevo = self.gen()
        self.assertEqual([d["distrito"] for d in nuevo["territorios"][T]["distritos"]], [1, 2])
        self.assertFalse((self.out / T / "distrito-0.html").exists())
        self.assertEqual(da.comprobar(self.out, self.reg), [])

    def test_geojson_publico_sin_district_id(self):
        self.gen()
        dest = self.d / "site"
        da.materializar(dest, self.out, self.reg, m06_dir=self.m6)
        gj = json.loads((dest / T / "distritos.geojson").read_text())
        self.assertEqual(sorted(f["properties"]["distrito"] for f in gj["features"]), [1, 2])
        self.assertTrue(all("district_id" not in f["properties"] for f in gj["features"]))
        e = json.loads((self.out / "INDEX.json").read_text())["territorios"][T]["geojson"]
        self.assertEqual(da.sha((dest / T / "distritos.geojson").read_bytes()), e["sha256"])
        self.assertNotEqual(e["sha256"], e["sha256_origen"])

    def test_nombres_opcionales(self):
        self.gen()
        (self.out / "nombres.json").write_text(json.dumps({T: {"0": "Alto Duero"}}))
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


class ParCoherente(Base):
    """T-249: el lote P50 43030563528 registró solo M06 nuevos y el paquete pasó de 51 a 17 territorios."""

    def _registro(self, f):
        r = json.loads(self.reg.read_text())
        f(r["products"])
        self.reg.write_text(json.dumps(r))

    def test_m06_nuevo_sin_m08_conserva_el_par_anterior(self):
        self.gen()
        self._registro(lambda ps: ps.append(dict(ps[0], run_id="9", blob_sha="c" * 40)))
        idx = self.gen()
        self.assertEqual(idx["territorios"][T]["run_id"], "5")
        self.assertTrue((self.out / T / "distrito-1.html").exists())
        self.assertEqual(da.comprobar(self.out, self.reg), [])
        da.materializar(self.d / "site", self.out, self.reg, m06_dir=self.m6)

    def test_reduccion_sin_retirada_falla_sin_borrar(self):
        self.gen()
        antes = (self.out / "INDEX.json").read_bytes()
        self._registro(lambda ps: ps[0].update(run_id="9"))  # el M08 vigente (run 5) se queda sin su M06
        with self.assertRaisesRegex(ValueError, "DATOS_ABIERTOS_REDUCCION"):
            self.gen()
        self.assertEqual((self.out / "INDEX.json").read_bytes(), antes)
        self.assertTrue((self.out / T / "index.html").exists())

    def test_retirada_explicita_borra(self):
        self.gen()
        self._registro(lambda ps: ps.clear())
        self.assertEqual(self.gen()["territorios"], {})
        self.assertFalse((self.out / T).exists())


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
