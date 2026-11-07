"""T-56: el sitio publicado incluye el hemiciclo nacional y el dashboard lo enlaza con ruta relativa."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"


def paso(nombre):
    d = yaml.safe_load(PUB.read_text(encoding="utf-8"))
    for job in d["jobs"].values():
        for s in job.get("steps") or []:
            if s.get("name") == nombre:
                return s["run"]
    raise AssertionError(nombre)


class HemicicloEnElSitio(unittest.TestCase):
    def test_el_publicador_copia_y_comprueba_el_hemiciclo(self):
        pre = paso("Preparar dependencias y materializador verificable")
        self.assertIn("test -f dashboard/hemiciclo.html", pre)
        self.assertIn("dashboard/hemiciclo.json", pre)
        build = paso("Construir sitio candidato completo")
        self.assertIn("cp dashboard/hemiciclo.html dashboard/hemiciclo.json /tmp/site-candidate/dashboard/", build)
        self.assertLess(build.index("cp -R publicado/dashboard/."), build.index("cp dashboard/hemiciclo.html"))
        self.assertLess(build.index("cp dashboard/hemiciclo.html"), build.index("preparar_visor_ejecucion.py"))

    def test_construccion_local_contiene_el_hemiciclo_y_el_enlace_resuelve(self):
        build = paso("Construir sitio candidato completo")
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site-candidate"
            # Los pasos de copia del publicador, sobre un directorio temporal (sin el materializador del registro).
            copias = "\n".join(l for l in build.splitlines() if l.strip().startswith(("rm -rf /tmp/site-candidate", "cp ", "grep -q")))
            script = "set -euo pipefail\n" + copias.replace("/tmp/site-candidate", str(site))
            subprocess.run(["bash", "-c", script], cwd=ROOT, check=True)
            dash = site / "dashboard"
            for f in ("index.html", "hemiciclo.html", "hemiciclo.json", "status.json"):
                self.assertTrue((dash / f).is_file(), f)
            html = (dash / "index.html").read_text(encoding="utf-8")
            href = re.search(r'<a href="([^"]+)">Hemiciclo nacional</a>', html).group(1)
            base = "https://jfmurciego.github.io/DiputadodeDistrito/dashboard/"
            destino = urljoin(base, href)
            self.assertEqual(destino, base + "hemiciclo.html")
            self.assertTrue((dash / destino[len(base):]).is_file())
            # hemiciclo.html carga hemiciclo.json de su misma carpeta
            self.assertIn('||"hemiciclo.json"', (dash / "hemiciclo.html").read_text(encoding="utf-8"))
            json.loads((dash / "hemiciclo.json").read_text(encoding="utf-8"))

    def test_indices_fuente_y_publicado_iguales(self):
        a = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
        self.assertEqual(a, (ROOT / "publicado/dashboard/index.html").read_text(encoding="utf-8"))
        self.assertIn('<a href="hemiciclo.html">Hemiciclo nacional</a>', a)


if __name__ == "__main__":
    unittest.main()
