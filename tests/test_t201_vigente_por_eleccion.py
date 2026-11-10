# -*- coding: utf-8 -*-
"""T-201: la vigente se elige por (territorio, elección), nunca por el run_id mayor entre elecciones.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Prueba obligatoria: registrar entradas 2026 SIMULADAS (run_id mayores) no cambia lo que muestran resultados ligeros,
datos abiertos, hemiciclo y legislatura vigente para 2023. Los valores esperados son literales.
"""
import copy
import io
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402
import generar_datos_abiertos as da  # noqa: E402
import generar_hemiciclo as gh  # noqa: E402
import legislatura_vigente as lv  # noqa: E402
import resultados_ligeros as rl  # noqa: E402

E26 = {"election_date": "2026-11-29", "election_id": "congreso_soria_2026-11-29"}


def m08(ganadores):
    feats = [{"properties": {"district_id": str(i), "district_pop": 1000 + i, "total_votes": 500,
                             "winner_party": g, "winner_votes": 200, "winner_share": 0.4}} for i, g in enumerate(ganadores)]
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x_m08_distritos_resultados.geojson", json.dumps({"features": feats}))
    return b.getvalue()


def prod(kind, t, run, datos=b"", **extra):
    e = {"kind": kind, "territory_id": t, "run_id": str(run), "blob_sha": f"b{kind[-3:]}{run}",
         "sha256": rl.sha256(datos), "canonical": True}
    e.update(extra)
    return e


class VigentePorEleccion(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.zips = self.d / "zips"
        self.zips.mkdir()
        z23, z26 = m08(["PP", "PSOE"]), m08(["VOX", "VOX"])
        (self.zips / "congreso_soria_20.zip").write_bytes(z23)
        (self.zips / "congreso_soria_900.zip").write_bytes(z26)
        (self.zips / "congreso_teruel_901.zip").write_bytes(z26)
        self.p23 = [prod("canonical_m08", "congreso_soria", 20, z23), prod("canonical_m06", "congreso_soria", 20, z23)]
        self.p26 = [prod("canonical_m08", "congreso_soria", 900, z26, **E26), prod("canonical_m06", "congreso_soria", 900, z26, **E26),
                    prod("canonical_m08", "congreso_teruel", 901, z26, election_date="2026-11-29"),
                    prod("canonical_m06", "congreso_teruel", 901, z26, election_date="2026-11-29")]

    def reg(self, nombre, products):
        r = self.d / nombre
        r.write_text(json.dumps({"products": products}))
        return r

    def test_resultados_ligeros_y_datos_abiertos_no_cambian(self):
        solo, mixto = self.reg("a.json", self.p23), self.reg("b.json", self.p23 + self.p26)
        a = rl.generar(self.d / "oa", solo, m08_dir=self.zips)
        b = rl.generar(self.d / "ob", mixto, m08_dir=self.zips)
        self.assertEqual(a, b)
        self.assertEqual(sorted(b["territorios"]), ["congreso_soria"])
        self.assertEqual(b["territorios"]["congreso_soria"]["run_id"], "20")
        self.assertEqual((self.d / "oa/congreso_soria.csv").read_bytes(), (self.d / "ob/congreso_soria.csv").read_bytes())
        self.assertEqual(rl.vigentes(mixto, "2026-11-29")["congreso_soria"]["run_id"], "900")
        self.assertEqual(sorted(rl.vigentes(mixto, "2026-11-29")), ["congreso_soria", "congreso_teruel"])
        self.assertEqual({t: p["run_id"] for t, p in da.vigentes_m06(mixto).items()}, {"congreso_soria": "20"})
        self.assertEqual(da.vigentes_m06(mixto), da.vigentes_m06(solo))
        self.assertEqual(da.vigentes_m06(mixto, "2026-11-29")["congreso_teruel"]["run_id"], "901")

    def test_hemiciclo_no_cambia(self):
        solo, mixto = self.reg("a.json", self.p23), self.reg("b.json", self.p23 + self.p26)
        res = []
        for r in (solo, mixto):
            gh.REGISTRO_VISOR = r
            res.append(gh.cargar_m08(self.d / "c", self.zips))
        self.assertEqual(res[0], res[1])
        self.assertEqual(list(res[1][0].values()), [["PP", "PSOE"]])
        gh.REGISTRO_VISOR = mixto
        g26, r26 = gh.cargar_m08(self.d / "c", self.zips, "2026-11-29")
        self.assertEqual(sorted(r26.values()), ["900", "901"])
        gh.REGISTRO_VISOR = ROOT / "orchestracion/publicaciones_visor.json"

    def test_legislatura_vigente(self):
        today = date(2026, 11, 10)
        v23, v26 = {"products": self.p23}, {"products": self.p23 + self.p26}
        self.assertEqual(lv.territory_state(self.d, "congreso_soria", v26, today),
                         lv.territory_state(self.d, "congreso_soria", v23, today))
        self.assertEqual(lv.territory_state(self.d, "congreso_soria", v26, today), {"estado": "PUBLICADO", "run_id": "20"})
        self.assertEqual(lv.territory_state(self.d, "congreso_teruel", v26, today)["estado"], "TERRITORIAL_CERTIFICADO")
        self.assertEqual(lv.territory_state(self.d, "congreso_teruel", v26, today, "2026-11-29"),
                         {"estado": "PUBLICADO", "run_id": "901"})

    def test_identidad_incluye_la_eleccion(self):
        a = {"territory_id": "t", "kind": "scenario_m08", "scenario_id": "s1"}
        b = dict(a, election_date="2026-11-29")
        self.assertNotEqual(rpv.identity_key(a), rpv.identity_key(b))
        self.assertEqual(rpv.identity_key(a), ("t", "scenario_m08", "s1", "2023-07-23"))

    def test_m06_reutilizado_solo_dentro_de_la_misma_eleccion(self):
        loc = "github-git-blob://o/r/" + "a" * 40
        viejo = {"territory_id": "t", "kind": "canonical_m06", "run_id": "1", "immutable_location": loc}
        reg = {"products": [viejo]}
        mismo = dict(viejo, run_id="2")
        otra = dict(viejo, run_id="2", election_date="2026-11-29")
        self.assertTrue(rpv._already_registered_reused_m06(reg, mismo))
        self.assertFalse(rpv._already_registered_reused_m06(reg, otra))

    def test_constante_unica(self):
        self.assertEqual(rl.ELECCION_POR_DEFECTO, rpv.ELECCION_POR_DEFECTO)

    def test_registro_real_sin_cambios(self):
        reg = json.loads((ROOT / "orchestracion/publicaciones_visor.json").read_text("utf-8"))
        antes = copy.deepcopy(reg)
        mixto = self.reg("real.json", reg["products"] + self.p26)
        solo = self.reg("real0.json", reg["products"])
        self.assertEqual(rl.vigentes(solo), rl.vigentes(mixto))
        self.assertEqual(da.vigentes_m06(solo), da.vigentes_m06(mixto))
        self.assertEqual(reg, antes)


if __name__ == "__main__":
    unittest.main()
