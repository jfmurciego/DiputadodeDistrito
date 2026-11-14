"""Versión 1.0.0 — T-310: los visores no cargan recursos de terceros y sirven maplibre-gl fijado con sha256/SRI. Fecha: 2026-11-14.
Estado: prueba. Anterior: ninguno (fichero nuevo).
"""
import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISOR = ROOT / "visor"
VENDOR = VISOR / "vendor" / "maplibre-gl" / "5.7.0"
EXT = re.compile(r"^(https?:)?//", re.I)
# Lista blanca de recursos estáticos: vacía. Los <a> de navegación no cuentan.
TAGS = re.compile(r"<(script|link|img|source|iframe|embed|object|video|audio|input)\b[^>]*>", re.I)
ATTR = re.compile(r"\b(?:src|href|data|poster|srcset)\s*=\s*[\"']([^\"']+)[\"']", re.I)
CSS_REF = re.compile(r"(?:@import\s+(?:url\()?|url\()\s*[\"']?((?:https?:)?//[^\"')\s]+)", re.I)
# Cargas dinámicas en JS aún no resueltas (decisión del propietario pendiente; ver registro T-310).
DINAMICAS_PENDIENTES = {"https://tile.openstreetmap.org/", "https://static.cloudflareinsights.com/"}


def _publicados(exts):
    return [p for p in VISOR.rglob("*") if p.suffix in exts and "vendor" not in p.parts]


class SinTerceros(unittest.TestCase):
    def test_html_sin_recursos_externos(self):
        mal = []
        for p in _publicados({".html"}):
            for m in TAGS.finditer(p.read_text(encoding="utf-8")):
                tag = m.group(0)
                if tag.lower().startswith("<link") and "stylesheet" not in tag.lower() and "icon" not in tag.lower() \
                        and "preload" not in tag.lower() and "preconnect" not in tag.lower():
                    continue
                for u in ATTR.findall(tag):
                    if EXT.match(u):
                        mal.append((str(p.relative_to(ROOT)), u))
        self.assertEqual(mal, [])

    def test_css_sin_recursos_externos(self):
        mal = [(str(p.relative_to(ROOT)), u) for p in _publicados({".css"})
               for u in CSS_REF.findall(p.read_text(encoding="utf-8"))]
        mal += [(str(p.relative_to(ROOT)), u) for p in VENDOR.glob("*.css")
                for u in CSS_REF.findall(p.read_text(encoding="utf-8"))]
        self.assertEqual(mal, [])

    def test_js_sin_cargas_externas_salvo_pendientes(self):
        mal = []
        for p in _publicados({".js"}):
            for u in re.findall(r"[\"'`](https?://[^\"'`\s]+)", p.read_text(encoding="utf-8")):
                if not any(u.startswith(d) for d in DINAMICAS_PENDIENTES) and \
                        re.search(r"tiles|src\s*=|\.src|import\(", u) is not None:
                    mal.append((str(p.relative_to(ROOT)), u))
        self.assertEqual(mal, [])

    def test_ningun_visor_usa_unpkg(self):
        for p in list(_publicados({".html", ".js", ".css"})) + [ROOT / "ddd_ensemble" / "gallery.py"]:
            self.assertNotIn("unpkg.com", p.read_text(encoding="utf-8"), p)

    def test_vendor_coincide_con_procedencia(self):
        d = json.loads((VENDOR / "PROCEDENCIA.json").read_text(encoding="utf-8"))
        self.assertEqual(d["version"], "5.7.0")
        for nombre, info in d["ficheros"].items():
            datos = (VENDOR / nombre).read_bytes()
            self.assertEqual(hashlib.sha256(datos).hexdigest(), info["sha256"], nombre)
            self.assertEqual(len(datos), info["bytes"], nombre)
        for nombre, sri in d["sri_sha384"].items():
            dig = base64.b64encode(hashlib.sha384((VENDOR / nombre).read_bytes()).digest()).decode()
            self.assertEqual(sri, "sha384-" + dig)

    def test_html_usa_vendor_con_integrity(self):
        d = json.loads((VENDOR / "PROCEDENCIA.json").read_text(encoding="utf-8"))
        for p in _publicados({".html"}):
            h = p.read_text(encoding="utf-8")
            if "maplibre-gl" not in h:
                continue
            for nombre, sri in d["sri_sha384"].items():
                self.assertRegex(h, r'vendor/maplibre-gl/5\.7\.0/%s"[^>]*integrity="%s"' % (re.escape(nombre), re.escape(sri)), p)


if __name__ == "__main__":
    unittest.main()
