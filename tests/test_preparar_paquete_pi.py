"""Pruebas del paquete de propiedad intelectual (T-281): determinismo, lista blanca, exclusiones y secretos."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.preparar_paquete_pi import main

# Construidos en tiempo de ejecución para que este fichero no contenga los patrones.
RUTA_PERSONAL = "/" + "Users" + "/alguien/proyecto"
TOKEN = "gh" + "p_" + "A" * 36

CODIGO_LARGO = "".join(f"X{i} = {i}\n" for i in range(800))  # ~11 páginas de código
FICHEROS = {
    "paquetes/deslinde/pyproject.toml": "[project]\nname = 'deslinde'\n",
    "paquetes/deslinde/README.md": "# Deslinde\n",
    "paquetes/deslinde/src/deslinde/__init__.py": '__version__ = "1.1.0"\n',
    "paquetes/deslinde/src/deslinde/a.py": "from ddd_core.x import f\nfrom deslinde import b\n",
    "paquetes/deslinde/src/deslinde/b.py": "def g():\n    return 1\n",
    "ddd_core/__init__.py": "",
    "ddd_core/x.py": "import ddd_core.y\ndef f():\n    return 2\n",
    "ddd_core/y.py": "Y = 3\n",
    "ddd_core/no_usado.py": "Z = 4\n",
    "ddd_motor2/viejo.py": "V = 1\n",
    "docs/ARQUITECTURA/DESLINDE_1_0.md": ("<!--\nVERSIÓN: 9.9.9\n-->\n# Deslinde\nTablas en `docs/ESTUDIOS/T64_*/c.csv`;"
                                         " estudio T-179 y T196; AUT17 no es un estudio.\n"),
    "docs/ARQUITECTURA/OTRO.md": "fuera\n",
    "docs/ESTUDIOS/T64_comarcas/c.csv": "a,b\n",
    "docs/ESTUDIOS/T64_comarcas.md": "comarcas\n",
    "docs/ESTUDIOS/T179_nat/informe.md": "estudio\n",
    "docs/ESTUDIOS/T179_nat/.env": "X=1\n",
    "docs/ESTUDIOS/T1790_otro/no.md": "no citado\n",
    "docs/ESTUDIOS/T196_bateria.md": "batería\n",
    "docs/ESTUDIOS/T17_otro/no.md": "no citado\n",
    "docs/ESTUDIOS/e1/informe.md": "no citado\n",
    "docs/registro_pi/DESCRIPCION.md": "<!--\nVERSIÓN: 1.0.0\n-->\n# Descripción\nAutor: [AUTOR].\n",
    "docs/registro_pi/NOTA_AUTORIA.md": "<!--\nVERSIÓN: 1.0.0\n-->\n# Nota\nAutor: [AUTOR]. Fecha: [FECHA]. D-68.\n",
    "CLAUDE.md": "memoria\n",
    ".claude/rules/r.md": "regla\n",
}
ESPERADOS = [
    "ddd_core/__init__.py", "ddd_core/x.py", "ddd_core/y.py",
    "docs/ARQUITECTURA/DESLINDE_1_0.md", "docs/ESTUDIOS/T179_nat/informe.md", "docs/ESTUDIOS/T196_bateria.md",
    "docs/ESTUDIOS/T64_comarcas.md", "docs/ESTUDIOS/T64_comarcas/c.csv",
    "paquetes/deslinde/README.md", "paquetes/deslinde/pyproject.toml",
    "paquetes/deslinde/src/deslinde/__init__.py", "paquetes/deslinde/src/deslinde/a.py",
    "paquetes/deslinde/src/deslinde/b.py",
]
SALIDAS = ("paquete_deslinde.zip", "COPIA_IDENTIFICATIVA.pdf", "NOTA_AUTORIA.pdf", "MANIFEST.json", "MANIFIESTO.txt",
           "SHA256SUMS", "README.md")


def _git(raiz: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(raiz), *args], check=True, capture_output=True, text=True).stdout


def _repo(tmp: Path, extra: dict[str, str] | None = None) -> Path:
    raiz = tmp / "repo"
    for rel, texto in {**FICHEROS, **(extra or {})}.items():
        p = raiz / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
    _git(raiz.parent, "init", "-q", str(raiz))
    _git(raiz, "add", "-A")
    env = ["-c", "user.name=t", "-c", "user.email=t@t.invalid"]
    subprocess.run(["git", "-C", str(raiz), *env, "commit", "-q", "-m", "x", "--date=2026-01-02T03:04:05Z"],
                   check=True, capture_output=True,
                   env={"GIT_COMMITTER_DATE": "2026-01-02T03:04:05Z", "PATH": "/usr/bin:/bin"})
    return raiz


class PaquetePI(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _generar(self, raiz: Path, nombre: str, *extra: str) -> int:
        return main(["--raiz", str(raiz), "--salida", str(self.tmp / nombre), *extra])

    def test_lista_blanca_y_exclusiones(self):
        raiz = _repo(self.tmp)
        self.assertEqual(self._generar(raiz, "s"), 0)
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual([f["ruta"] for f in m["ficheros"]], ESPERADOS)
        self.assertEqual(m["excluidos_por_politica"], ["docs/ESTUDIOS/T179_nat/.env"])
        self.assertEqual(sorted(m["estudios_citados"]), ["T179_nat", "T196_bateria.md", "T64_comarcas",
                                                         "T64_comarcas.md"])
        self.assertEqual((m["deslinde_version"], m["definicion_version"]), ("1.1.0", "9.9.9"))
        self.assertEqual(m["commit"], _git(raiz, "rev-parse", "HEAD").strip())
        y = next(f for f in m["ficheros"] if f["ruta"] == "ddd_core/y.py")
        self.assertEqual(y, {"ruta": "ddd_core/y.py", "bytes": 6, "sha256": hashlib.sha256(b"Y = 3\n").hexdigest()})

    def test_determinismo_zip_y_sha256(self):
        raiz = _repo(self.tmp)
        self.assertEqual(self._generar(raiz, "a"), 0)
        self.assertEqual(self._generar(raiz, "b"), 0)
        for nombre in SALIDAS:
            self.assertEqual((self.tmp / "a" / nombre).read_bytes(), (self.tmp / "b" / nombre).read_bytes(), nombre)
        datos = (self.tmp / "a/paquete_deslinde.zip").read_bytes()
        m = json.loads((self.tmp / "a/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(m["zip"]["sha256"], hashlib.sha256(datos).hexdigest())
        self.assertIn(f"{m['zip']['sha256']}  paquete_deslinde.zip", (self.tmp / "a/SHA256SUMS").read_text())
        pdf = (self.tmp / "a/COPIA_IDENTIFICATIVA.pdf").read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF\n"))
        texto = (self.tmp / "a/MANIFIESTO.txt").read_text(encoding="utf-8")
        for nombre in ("paquete_deslinde.zip", "COPIA_IDENTIFICATIVA.pdf", "NOTA_AUTORIA.pdf"):
            self.assertIn(f"{hashlib.sha256((self.tmp / 'a' / nombre).read_bytes()).hexdigest()}  {nombre}", texto)
        with zipfile.ZipFile(self.tmp / "a/paquete_deslinde.zip") as z:
            self.assertEqual(z.namelist(), ESPERADOS)
            self.assertEqual({i.date_time for i in z.infolist()}, {(1980, 1, 1, 0, 0, 0)})
            self.assertEqual(z.read("ddd_core/y.py"), b"Y = 3\n")

    def test_lee_del_commit_no_del_arbol_de_trabajo(self):
        raiz = _repo(self.tmp)
        (raiz / "ddd_core/y.py").write_text("Y = 999\n", encoding="utf-8")
        self.assertEqual(self._generar(raiz, "s", "--sin-zip"), 0)
        self.assertFalse((self.tmp / "s/paquete_deslinde.zip").exists())
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        y = next(f for f in m["ficheros"] if f["ruta"] == "ddd_core/y.py")
        self.assertEqual(y["sha256"], hashlib.sha256(b"Y = 3\n").hexdigest())

    def test_ruta_personal_se_incluye_con_aviso(self):
        raiz = _repo(self.tmp, {"docs/ESTUDIOS/T179_nat/log.txt": f"cwd={RUTA_PERSONAL}\n"})
        self.assertEqual(self._generar(raiz, "s"), 0)
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("docs/ESTUDIOS/T179_nat/log.txt", [f["ruta"] for f in m["ficheros"]])
        self.assertEqual(m["avisos"], [{"ruta": "docs/ESTUDIOS/T179_nat/log.txt", "tipo": "ruta_users"}])

    def test_falla_ante_secreto(self):
        for extra in ({"paquetes/deslinde/src/deslinde/c.py": f"T = '{TOKEN}'\n"},
                      {"docs/ESTUDIOS/T64_comarcas/k.txt": "-----BEGIN RSA " + "PRIVATE KEY-----\n"}):
            with self.subTest(extra=list(extra)):
                sub = self.tmp / list(extra)[0].replace("/", "_")
                sub.mkdir()
                raiz = _repo(sub, extra)
                self.assertEqual(main(["--raiz", str(raiz), "--salida", str(sub / "s")]), 2)
                self.assertFalse((sub / "s/MANIFEST.json").exists())

    def test_exclusion_explicita_queda_en_el_manifiesto(self):
        raiz = _repo(self.tmp, {"docs/ESTUDIOS/T179_nat/log.txt": f"cwd={RUTA_PERSONAL}\n"})
        self.assertEqual(self._generar(raiz, "s", "--excluir", "docs/ESTUDIOS/T179_nat/log.txt"), 0)
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(m["excluidos_explicitos"], ["docs/ESTUDIOS/T179_nat/log.txt"])
        self.assertNotIn("docs/ESTUDIOS/T179_nat/log.txt", [f["ruta"] for f in m["ficheros"]])
        self.assertEqual(self._generar(raiz, "t", "--excluir", "no/existe.txt"), 2)

    def test_autor_marcador_por_defecto_y_autor_dado(self):
        raiz = _repo(self.tmp)
        self.assertEqual(self._generar(raiz, "s"), 0)
        nota = (self.tmp / "s/NOTA_AUTORIA.pdf").read_bytes()
        self.assertIn(b"Autor: [AUTOR]. Fecha: 2026-01-02. D-68.", nota)
        self.assertIn(b"Autor: [AUTOR]", (self.tmp / "s/COPIA_IDENTIFICATIVA.pdf").read_bytes())
        self.assertEqual(self._generar(raiz, "t", "--autor", "Nombre Apellido", "--fecha", "2026-12-01"), 0)
        self.assertIn(b"Autor: Nombre Apellido. Fecha: 2026-12-01.", (self.tmp / "t/NOTA_AUTORIA.pdf").read_bytes())
        m = json.loads((self.tmp / "t/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertFalse(m["autor_es_marcador"])
        self.assertEqual(self._generar(raiz, "u", "--fecha", "1-12-2026"), 2)

    def test_extremos_omite_paginas_centrales_de_codigo(self):
        raiz = _repo(self.tmp, {"paquetes/deslinde/src/deslinde/largo.py": CODIGO_LARGO})
        self.assertEqual(self._generar(raiz, "todo"), 0)
        self.assertEqual(self._generar(raiz, "ext", "--extremos", "3"), 0)
        todo = json.loads((self.tmp / "todo/MANIFEST.json").read_text(encoding="utf-8"))["pdf"]
        ext = json.loads((self.tmp / "ext/MANIFEST.json").read_text(encoding="utf-8"))["pdf"]
        self.assertEqual(todo["paginas_codigo_omitidas"], 0)
        self.assertGreater(todo["paginas_codigo_total"], 6)
        self.assertEqual(ext["paginas_codigo_omitidas"], todo["paginas_codigo_total"] - 6)
        self.assertEqual(ext["paginas_total"], todo["paginas_total"] - ext["paginas_codigo_omitidas"] + 1)
        pdf = (self.tmp / "ext/COPIA_IDENTIFICATIVA.pdf").read_bytes()
        # Páginas de código por orden de ruta: pyproject, __init__, a, b y largo (la primera página de largo se omite).
        self.assertIn(b"name = 'deslinde'", pdf)
        self.assertIn(b"X799 = 799", pdf)
        self.assertNotIn(b"X0 = 0", pdf)
        self.assertNotIn(b"X400 = 400", pdf)


if __name__ == "__main__":
    unittest.main()
