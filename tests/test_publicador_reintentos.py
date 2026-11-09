# -*- coding: utf-8 -*-
"""T-124: reintentos de gh api en .ddd-publication/materializar_registro.sh (de _reutilizable-publicar-sitio.yml).

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Extrae `gh_retry` del workflow y lo ejecuta en bash con un `gh` falso que cuenta las llamadas.
"""
import re
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github/workflows/_reutilizable-publicar-sitio.yml"


def _funcion() -> str:
    m = re.search(r"# --- reintentos \(T-124\) ---\n(.*?)# --- fin reintentos ---", WORKFLOW.read_text("utf-8"), re.S)
    assert m, "falta gh_retry en el workflow"
    return textwrap.dedent(m.group(1))


class Reintentos(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def _correr(self, respuestas):
        """respuestas: lista de (codigo, stderr, stdout) por intento. Devuelve (rc, nº de llamadas, salida del fichero)."""
        (self.tmp / "bin").mkdir()
        for i, (rc, err, out) in enumerate(respuestas, 1):
            (self.tmp / f"r{i}").write_text(f"{rc}\n{err}\n{out}")
        gh = self.tmp / "bin" / "gh"
        gh.write_text(f"""#!/usr/bin/env bash
n=$(( $(cat {self.tmp}/n 2>/dev/null || echo 0) + 1 )); echo $n > {self.tmp}/n
f={self.tmp}/r$n; [[ -f $f ]] || f={self.tmp}/r{len(respuestas)}
rc="$(sed -n 1p $f)"; err="$(sed -n 2p $f)"; out="$(sed -n 3p $f)"
[[ -n "$err" ]] && echo "$err" >&2
[[ -n "$out" ]] && echo "$out"
exit $rc
""")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        script = self.tmp / "t.sh"
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + _funcion() + f'\ngh_retry {self.tmp}/salida gh api repos/x/y\n')
        r = subprocess.run(["bash", str(script)], env={"PATH": f"{self.tmp}/bin:/usr/bin:/bin", "DDD_REINTENTO_BASE": "0"},
                           capture_output=True, text=True, timeout=30)
        n = int((self.tmp / "n").read_text())
        salida = (self.tmp / "salida").read_text().strip() if (self.tmp / "salida").exists() else None
        return r, n, salida

    def test_504_dos_veces_y_luego_ok(self):
        r, n, salida = self._correr([(1, "gh: Gateway Timeout (HTTP 504)", ""), (1, "gh: Bad Gateway (HTTP 502)", ""), (0, "", "OK")])
        self.assertEqual((r.returncode, n, salida), (0, 3, "OK"))
        self.assertEqual(r.stdout.count("::warning::"), 2)

    def test_reset_de_conexion_se_reintenta(self):
        r, n, salida = self._correr([(1, "read tcp: connection reset by peer", ""), (0, "", "OK")])
        self.assertEqual((r.returncode, n, salida), (0, 2, "OK"))

    def test_404_no_se_reintenta(self):
        r, n, _ = self._correr([(1, "gh: Not Found (HTTP 404)", "")])
        self.assertEqual((r.returncode, n), (1, 1))
        self.assertIn("HTTP 404", r.stderr)

    def test_403_y_422_no_se_reintentan(self):
        for err in ("gh: Forbidden (HTTP 403)", "gh: Unprocessable Entity (HTTP 422)"):
            with self.subTest(err=err):
                shutil.rmtree(self.tmp / "bin", ignore_errors=True)
                (self.tmp / "n").unlink(missing_ok=True)
                r, n, _ = self._correr([(1, err, "")])
                self.assertEqual((r.returncode, n), (1, 1))

    def test_tres_intentos_y_falla(self):
        r, n, _ = self._correr([(1, "gh: Service Unavailable (HTTP 503)", "")])
        self.assertEqual((r.returncode, n), (1, 3))
        self.assertIn("HTTP 503", r.stderr)

    def test_las_dos_descargas_usan_gh_retry(self):
        t = WORKFLOW.read_text("utf-8")
        self.assertIn('gh_retry "$target/$id/asset" gh api', t)
        self.assertIn('gh_retry "$target/$id/blob.json" gh api', t)
        self.assertNotRegex(t, r'\n\s+gh api [^\n]*> "\$target/\$id/(asset|blob\.json)"')


if __name__ == "__main__":
    unittest.main()
