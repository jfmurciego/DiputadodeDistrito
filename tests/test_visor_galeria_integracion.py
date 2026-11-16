"""Versión 1.0.0 — T-325: integración de la galería territorial en V3 (portada, gobernanza y prueba de comportamiento en Node).
Fecha: 2026-11-15. Estado: candidato. Anterior: ninguna (fichero nuevo).
La prueba de comportamiento (tests/test_visor_galeria.js) se ejecuta si hay Node; sin Node se omite (la CI de unittest no trae Node; falta añadirla al paso Node de pruebas-plataforma.yml).
"""
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "visor" / "v3"


class Portada(HTMLParser):
    def __init__(self):
        super().__init__()
        self.orden, self.galeria, self.scripts = [], {}, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id") == "territory-gallery":
            self.galeria = {"tag": tag, "hidden": "hidden" in a, "label": a.get("aria-labelledby")}
            self.orden.append("galeria")
        if "model-cards" in (a.get("class") or ""):
            self.orden.append("modelos")
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])


class Integracion(unittest.TestCase):
    def test_portada_con_galeria_antes_de_los_indicadores_y_script_propio(self):
        p = Portada()
        p.feed((V3 / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(p.orden, ["galeria", "modelos"])
        self.assertEqual(p.galeria, {"tag": "section", "hidden": True, "label": "gallery-title"})
        self.assertLess(p.scripts.index("../v2/galeria/galeria.js"), p.scripts.index("v3.js"))
        self.assertTrue(all(not re.match(r"^(https?:)?//", s) for s in p.scripts if "maplibre" not in s or s.startswith("../")))

    def test_el_workflow_congelado_publica_la_galeria(self):
        """El workflow copia visor/v2/ entero con cp -R: la galería viaja con él sin tocar el workflow."""
        wf = (ROOT / ".github" / "workflows" / "_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        self.assertIn("cp -R visor/v2/. /tmp/site-candidate/v2/", wf)
        self.assertTrue((ROOT / "visor" / "v2" / "galeria" / "galeria.js").is_file())

    def test_cabeceras_y_copias_legacy(self):
        for rel in ("visor/v3/v3.js", "visor/v3/v3.css", "visor/v3/index.html", "visor/v2/galeria/galeria.js"):
            txt = (ROOT / rel).read_text(encoding="utf-8")[:3000]
            self.assertRegex(txt, r"VERSIÓN: ?\d+\.\d+\.\d+", rel)
            m = re.search(r"ANTERIOR: (\S+?)(?:\s*-->|\s|$)", txt)
            self.assertIsNotNone(m, rel)
            # legacy/ no entra en la imagen de CI (.dockerignore): la copia se comprueba donde existe el árbol.
            if not m.group(1).startswith("ninguna") and (ROOT / "legacy").is_dir():
                self.assertTrue((ROOT / m.group(1)).is_file(), f"{rel}: falta {m.group(1)}")

    @unittest.skipUnless(shutil.which("node"), "sin Node en este entorno; ver la PR (hay que añadirla a pruebas-plataforma.yml)")
    def test_comportamiento_en_node(self):
        r = subprocess.run(["node", str(ROOT / "tests" / "test_visor_galeria.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
