"""Versión 1.0.0 — T-325: el catálogo de la galería territorial V3 se comprueba contra los ficheros reales (no contra el texto del código).
Fecha: 2026-11-15. Estado: candidato. Anterior: ninguna (fichero nuevo).
Cubre: cobertura de las 52 provincias y 19 comunidades, existencia y sha256 de cada imagen, licencias libres permitidas con su URL,
atribución visible, enlaces solo a Commons/Creative Commons, tamaño total acotado y que el validador falle de verdad ante datos malos.
"""
import copy
import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
GAL = ROOT / "visor" / "v2" / "galeria"
LIC = re.compile(r"^(CC BY(-SA)? [1-4]\.\d( [a-z]{2})?|CC0 1\.0|CC0|Public domain)$")
LIC_URL = re.compile(r"^https://creativecommons\.org/(licenses/(by|by-sa)/[1-4]\.\d(/[a-z]{2})?|publicdomain/(zero/1\.0|mark/1\.0))(/deed\.[a-z]+|/)?$")
ORIGEN = re.compile(r"^https://commons\.wikimedia\.org/wiki/File:[^\s\"'<>]+$")
MAX_TOTAL = 4 * 1024 * 1024
MAX_IMG = 250 * 1024
N_PROVINCIAS, N_COMUNIDADES = 52, 19  # literales: provincias INE + Ceuta y Melilla; 17 comunidades + 2 ciudades autónomas


def webp_ancho(data):
    """Ancho de un WebP con pérdida (VP8); None si es otro subformato."""
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("no es WebP")
    if data[12:16] == b"VP8 ":
        return int.from_bytes(data[26:28], "little") & 0x3FFF
    return None


def validar(cat, carpeta, provincias, comunidades):
    """Devuelve la lista de defectos de un catálogo con sus imágenes en `carpeta`."""
    mal = []
    imgs = {i["id"]: i for i in cat.get("imagenes", [])}
    if len(imgs) != len(cat.get("imagenes", [])):
        mal.append("ids repetidos")
    total = 0
    for i in imgs.values():
        f = carpeta / i["archivo"]
        if not re.fullmatch(r"img/[a-z0-9\-]+\.webp", i["archivo"]):
            mal.append(f"{i['id']}: ruta no local o no webp")
            continue
        if not f.is_file():
            mal.append(f"{i['id']}: falta el fichero")
            continue
        data = f.read_bytes()
        total += len(data)
        if hashlib.sha256(data).hexdigest() != i.get("sha256"):
            mal.append(f"{i['id']}: sha256 no coincide")
        if len(data) != i.get("bytes") or len(data) > MAX_IMG:
            mal.append(f"{i['id']}: tamaño")
        try:
            w = webp_ancho(data)
            if w is not None and (w > 800 or w != i.get("ancho")):
                mal.append(f"{i['id']}: ancho {w}")
        except ValueError:
            mal.append(f"{i['id']}: no es WebP")
        if not LIC.match(i.get("licencia", "")):
            mal.append(f"{i['id']}: licencia no permitida {i.get('licencia')!r}")
        if not LIC_URL.match(i.get("licencia_url", "")):
            mal.append(f"{i['id']}: URL de licencia")
        elif ("BY-SA" in i["licencia"]) != ("/by-sa/" in i["licencia_url"]):
            mal.append(f"{i['id']}: licencia y URL no casan")
        if not ORIGEN.match(i.get("origen_url", "")):
            mal.append(f"{i['id']}: URL de origen")
        elif unquote(i["origen_url"].rsplit("File:", 1)[1]).replace("_", " ") != i.get("titulo_commons", "").replace("_", " "):
            mal.append(f"{i['id']}: título y URL de origen no casan")
        if not i.get("autor", "").strip() or re.search(r"[<>]", i["autor"]):
            mal.append(f"{i['id']}: autor vacío o con marcado")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", i.get("comprobado", "")):
            mal.append(f"{i['id']}: sin fecha de comprobación")
        if not i.get("descripcion", "").strip():
            mal.append(f"{i['id']}: sin descripción para el alt")
    if total > MAX_TOTAL:
        mal.append(f"tamaño total {total}")
    terr = cat.get("territorios", {})
    for cod in provincias:
        if terr.get("provincia:" + cod) not in imgs:
            mal.append("provincia sin imagen " + cod)
    for cod in comunidades:
        if terr.get("comunidad:" + cod) not in imgs:
            mal.append("comunidad sin imagen " + cod)
    if set(terr) - {"provincia:" + c for c in provincias} - {"comunidad:" + c for c in comunidades}:
        mal.append("claves de territorio desconocidas")
    if set(imgs) - set(terr.values()):
        mal.append("imágenes huérfanas: " + ",".join(sorted(set(imgs) - set(terr.values()))))
    return mal


def _cods(nombre):
    d = json.loads((ROOT / "visor" / "v2" / "datos" / nombre).read_text(encoding="utf-8"))
    return [f["properties"]["cod"] for f in d["features"]]


class CatalogoReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = json.loads((GAL / "catalogo.json").read_text(encoding="utf-8"))
        cls.prov, cls.com = _cods("provincias.json"), _cods("comunidades.json")

    def test_cabecera_de_gobernanza(self):
        for k, v in (("version", "1.0.0"), ("anterior", "ninguna (fichero nuevo)"), ("tarea", "T-325")):
            self.assertEqual(self.cat[k], v)
        self.assertTrue(self.cat["fecha"] and self.cat["estado"])

    def test_cobertura_esperada_con_literales(self):
        self.assertEqual((len(self.prov), len(self.com)), (N_PROVINCIAS, N_COMUNIDADES))

    def test_catalogo_valido_contra_los_ficheros(self):
        self.assertEqual(validar(self.cat, GAL, self.prov, self.com), [])

    def test_solo_licencias_libres_y_atribucion(self):
        familias = {re.match(r"CC BY-SA|CC BY|CC0", i["licencia"]).group(0) for i in self.cat["imagenes"]}
        self.assertTrue(familias <= {"CC BY", "CC BY-SA", "CC0"}, familias)
        self.assertTrue(all(i["autor"].strip() for i in self.cat["imagenes"]))

    def test_sin_nombres_de_ids_antiguos_ni_lenguas_regionales(self):
        # Topónimos solo en español: las descripciones no usan las formas en otra lengua de las capitales con nombre castellano.
        prohibidas = re.compile(r"\b(Girona|Lleida|Donostia|Ourense|A Coruña|Gasteiz|Castelló|Palma de Mallorca\b.*Illes|Eivissa)\b")
        malas = [i["descripcion"] for i in self.cat["imagenes"] if prohibidas.search(i["descripcion"])]
        self.assertEqual(malas, [])

    def test_ninguna_url_de_imagen_es_externa(self):
        for i in self.cat["imagenes"]:
            self.assertFalse(re.match(r"^(https?:)?//", i["archivo"]), i["id"])


class ValidadorFalla(unittest.TestCase):
    """El validador de verdad detecta datos malos: se aplica a copias deterioradas."""

    @classmethod
    def setUpClass(cls):
        cls.cat = json.loads((GAL / "catalogo.json").read_text(encoding="utf-8"))
        cls.prov, cls.com = _cods("provincias.json"), _cods("comunidades.json")

    def _con(self, mutar, tocar_fichero=None):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            shutil.copytree(GAL / "img", tmp / "img")
            cat = copy.deepcopy(self.cat)
            mutar(cat)
            if tocar_fichero:
                tocar_fichero(tmp)
            return validar(cat, tmp, self.prov, self.com)

    def test_copia_intacta_es_valida(self):
        self.assertEqual(self._con(lambda c: None), [])

    def test_licencia_no_libre(self):
        def m(c): c["imagenes"][0]["licencia"] = "CC BY-NC 4.0"
        self.assertTrue(any("licencia" in x for x in self._con(m)))

    def test_licencia_sin_url(self):
        def m(c): c["imagenes"][1]["licencia_url"] = "http://creativecommons.org/licenses/by-nd/2.0/"
        self.assertTrue(any("URL de licencia" in x for x in self._con(m)))

    def test_sha256_alterado(self):
        def m(c): c["imagenes"][2]["sha256"] = "0" * 64
        self.assertTrue(any("sha256" in x for x in self._con(m)))

    def test_fichero_modificado(self):
        def t(tmp):
            f = tmp / "img" / "prov-04.webp"
            d = bytearray(f.read_bytes())
            d[len(d) // 2] ^= 0xFF
            f.write_bytes(bytes(d))
        self.assertTrue(any("prov-04" in x for x in self._con(lambda c: None, t)))

    def test_fichero_ausente(self):
        self.assertTrue(any("falta el fichero" in x for x in self._con(lambda c: None, lambda tmp: (tmp / "img" / "prov-05.webp").unlink())))

    def test_autor_con_marcado(self):
        def m(c): c["imagenes"][3]["autor"] = "<img src=x onerror=alert(1)>"
        self.assertTrue(any("autor" in x for x in self._con(m)))

    def test_origen_externo_no_commons(self):
        def m(c): c["imagenes"][4]["origen_url"] = "https://example.org/wiki/File:X.jpg"
        self.assertTrue(any("origen" in x for x in self._con(m)))

    def test_ruta_de_imagen_externa(self):
        def m(c): c["imagenes"][5]["archivo"] = "https://upload.wikimedia.org/x.webp"
        self.assertTrue(any("ruta" in x for x in self._con(m)))

    def test_provincia_sin_imagen(self):
        def m(c): del c["territorios"]["provincia:28"]
        self.assertTrue(any("provincia sin imagen 28" in x for x in self._con(m)))

    def test_imagen_huerfana(self):
        def m(c): c["territorios"].pop("comunidad:01")
        out = self._con(m)
        self.assertTrue(any("comunidad sin imagen 01" in x for x in out))


if __name__ == "__main__":
    unittest.main()
