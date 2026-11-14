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

FICHEROS = {
    "ddd_motor2/__init__.py": "",
    "ddd_motor2/a.py": "from ddd_core.x import f\nfrom .b import g\nCMD = 'modulos/05_opt.py'\n",
    "ddd_motor2/b.py": "def g():\n    return 1\n",
    "ddd_core/__init__.py": "",
    "ddd_core/x.py": "import ddd_core.y\ndef f():\n    return 2\n",
    "ddd_core/y.py": "Y = 3\n",
    "ddd_core/no_usado.py": "Z = 4\n",
    "modulos/05_opt.py": "from ddd_core import y\n",
    "modulos/04_otro.py": "from ddd_core import no_usado\n",
    "docs/ARQUITECTURA/DESLINDE_1_0.md": "<!--\nVERSIÓN: 9.9.9\n-->\n# Deslinde\n",
    "docs/ARQUITECTURA/OTRO.md": "fuera\n",
    "docs/ESTUDIOS/e1/informe.md": "estudio\n",
    "docs/ESTUDIOS/e1/.env": "X=1\n",
    "docs/ESTUDIOS/e1/.claude/notas.md": "privado\n",
    "CLAUDE.md": "memoria\n",
    ".claude/rules/r.md": "regla\n",
}
ESPERADOS = [
    "ddd_core/__init__.py", "ddd_core/x.py", "ddd_core/y.py",
    "ddd_motor2/__init__.py", "ddd_motor2/a.py", "ddd_motor2/b.py",
    "docs/ARQUITECTURA/DESLINDE_1_0.md", "docs/ESTUDIOS/e1/informe.md", "modulos/05_opt.py",
]


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
        self.assertEqual(m["excluidos_por_politica"], ["docs/ESTUDIOS/e1/.claude/notas.md", "docs/ESTUDIOS/e1/.env"])
        self.assertEqual(m["deslinde_version"], "9.9.9")
        self.assertEqual(m["fecha_utc"], "2026-01-02T03:04:05Z")
        self.assertEqual(m["commit"], _git(raiz, "rev-parse", "HEAD").strip())
        y = next(f for f in m["ficheros"] if f["ruta"] == "ddd_core/y.py")
        self.assertEqual(y, {"ruta": "ddd_core/y.py", "bytes": 6, "sha256": hashlib.sha256(b"Y = 3\n").hexdigest()})

    def test_determinismo_zip_y_sha256(self):
        raiz = _repo(self.tmp)
        self.assertEqual(self._generar(raiz, "a"), 0)
        self.assertEqual(self._generar(raiz, "b"), 0)
        for nombre in ("paquete_deslinde.zip", "MANIFEST.json", "SHA256SUMS", "README.md"):
            self.assertEqual((self.tmp / "a" / nombre).read_bytes(), (self.tmp / "b" / nombre).read_bytes(), nombre)
        datos = (self.tmp / "a/paquete_deslinde.zip").read_bytes()
        m = json.loads((self.tmp / "a/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(m["zip"]["sha256"], hashlib.sha256(datos).hexdigest())
        self.assertIn(f"{m['zip']['sha256']}  paquete_deslinde.zip", (self.tmp / "a/SHA256SUMS").read_text())
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
        raiz = _repo(self.tmp, {"docs/ESTUDIOS/e1/log.txt": f"cwd={RUTA_PERSONAL}\n"})
        self.assertEqual(self._generar(raiz, "s"), 0)
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("docs/ESTUDIOS/e1/log.txt", [f["ruta"] for f in m["ficheros"]])
        self.assertEqual(m["avisos"], [{"ruta": "docs/ESTUDIOS/e1/log.txt", "tipo": "ruta_users"}])

    def test_falla_ante_secreto(self):
        for extra in ({"ddd_motor2/c.py": f"T = '{TOKEN}'\n"},
                      {"docs/ESTUDIOS/e1/k.txt": "-----BEGIN RSA " + "PRIVATE KEY-----\n"}):
            with self.subTest(extra=list(extra)):
                sub = self.tmp / list(extra)[0].replace("/", "_")
                sub.mkdir()
                raiz = _repo(sub, extra)
                self.assertEqual(main(["--raiz", str(raiz), "--salida", str(sub / "s")]), 2)
                self.assertFalse((sub / "s/MANIFEST.json").exists())

    def test_exclusion_explicita_queda_en_el_manifiesto(self):
        raiz = _repo(self.tmp, {"docs/ESTUDIOS/e1/log.txt": f"cwd={RUTA_PERSONAL}\n"})
        self.assertEqual(self._generar(raiz, "s", "--excluir", "docs/ESTUDIOS/e1/log.txt"), 0)
        m = json.loads((self.tmp / "s/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(m["excluidos_explicitos"], ["docs/ESTUDIOS/e1/log.txt"])
        self.assertNotIn("docs/ESTUDIOS/e1/log.txt", [f["ruta"] for f in m["ficheros"]])
        self.assertEqual(self._generar(raiz, "t", "--excluir", "no/existe.txt"), 2)


if __name__ == "__main__":
    unittest.main()
