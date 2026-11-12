# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-10
# ANTERIOR: ninguna (fichero nuevo)
"""T-148: la tabla maestra AUT/NAC cuadra con el INE (fuente con sha256), el catálogo y territorios/."""
import csv, hashlib, html, re, unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TABLA = ROOT / "configuracion" / "notacion_territorial.csv"
INE = ROOT / "fuentes" / "ine_codigos_territoriales_2026-11-10"
# sha256 de las páginas del INE descargadas el 2026-11-10 (literal fijado a mano, no recalculado).
SHA_INE = {
    "cod_ccaa.htm": "7eef080756423405e404a18ae279e7daad3b325ea5b613cff14f277f8e942851",
    "cod_provincia.htm": "5129d5ae9739a7822f3f8d421db2463d5c2fba9ff5e061ff1de16c046d999178",
    "cod_ccaa_provincia.htm": "de7cdc23b28756ac65687019cbef20d97f068e71d1b1fe2d30ce2836c36e5249",
}
OTRAS_LENGUAS = {
    "Araba", "Bizkaia", "Gipuzkoa", "Girona", "Lleida", "Ourense", "Alacant", "Castelló", "València",
    "Illes", "Balears", "Comunitat", "Euskadi", "Catalunya", "Galiza", "A Coruña", "Nafarroa",
}


def _tabla():
    lineas = [l for l in TABLA.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lineas))


def _ine(nombre):
    t = (INE / nombre).read_text(encoding="latin-1")
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        c = [html.unescape(re.sub(r"<[^>]*>", "", x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        if c and re.fullmatch(r"\d\d", c[0]):
            out.append(c)
    return out


class NotacionTerritorial(unittest.TestCase):
    def test_fuente_ine_con_sha256(self):
        for n, sha in SHA_INE.items():
            self.assertEqual(hashlib.sha256((INE / n).read_bytes()).hexdigest(), sha, n)

    def test_19_aut_y_52_nac_con_codigos_del_ine(self):
        filas = _tabla()
        aut = {f["codigo_ine"]: f for f in filas if f["ambito"] == "AUT"}
        nac = {f["codigo_ine"]: f for f in filas if f["ambito"] == "NAC"}
        self.assertEqual((len(aut), len(nac), len(filas)), (19, 52, 71))
        self.assertEqual(sorted(aut), [f"{i:02d}" for i in range(1, 20)])
        self.assertEqual(sorted(nac), [f"{i:02d}" for i in range(1, 53)])
        for f in filas:
            self.assertEqual(f["codigo"], f["ambito"] + f["codigo_ine"])
        # Independiente del código: literales del INE.
        self.assertEqual({c[0]: c[1] for c in _ine("cod_ccaa.htm")}, {k: v["literal_ine"] for k, v in aut.items()})
        self.assertEqual({c[0]: c[1] for c in _ine("cod_provincia.htm")}, {k: v["literal_ine"] for k, v in nac.items()})
        # Ceuta y Melilla en los dos universos.
        self.assertEqual((aut["18"]["nombre_es"], aut["19"]["nombre_es"]), ("Ceuta", "Melilla"))
        self.assertEqual((nac["51"]["nombre_es"], nac["52"]["nombre_es"]), ("Ceuta", "Melilla"))

    def test_nombres_solo_en_espanol(self):
        esperado = {"NAC01": "Álava", "NAC15": "La Coruña", "NAC17": "Gerona", "NAC20": "Guipúzcoa",
                    "NAC25": "Lérida", "NAC32": "Orense", "NAC48": "Vizcaya", "NAC07": "Baleares",
                    "NAC03": "Alicante", "NAC12": "Castellón", "NAC46": "Valencia", "AUT10": "Comunidad Valenciana"}
        por = {f["codigo"]: f for f in _tabla()}
        for k, v in esperado.items():
            self.assertEqual(por[k]["nombre_es"], v)
        for f in por.values():
            n = f["nombre_es"]
            self.assertNotIn("/", n)
            self.assertFalse(OTRAS_LENGUAS & set(re.split(r"[\s,]+", n)), n)
            self.assertNotIn("A Coruña", n)

    def test_correspondencia_con_catalogo_y_territorios(self):
        cat = yaml.safe_load((ROOT / "configuracion" / "catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
        por = {f["codigo"]: f for f in _tabla()}
        for t in cat["territories"]:
            f = por["AUT" + t["autonomous_community_code_ine"]]
            self.assertEqual((f["codigo"].lower(), f["nombre_es"]), (t["territory_id"], t["name"]))  # T-220: id nuevo
        nac = [t for t in cat["pilot_territories"] if not t["territory_id"].startswith("congreso350_")]
        self.assertEqual(len(nac), 52)
        for t in nac:
            f = por["NAC" + t["province_codes"][0]]
            self.assertEqual(f["codigo"].lower(), t["territory_id"])  # T-220: id nuevo
            self.assertEqual("Congreso " + f["nombre_es"], t["name"])
            self.assertEqual(t["pilot_code"], "C" + f["codigo_ine"])
        ids = [f["codigo"].lower() for f in por.values()]  # T-220: carpetas con el id nuevo
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertTrue((ROOT / "territorios" / i).is_dir(), i)


if __name__ == "__main__":
    unittest.main()
