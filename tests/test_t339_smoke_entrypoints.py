"""T-339: smoke de carga de TODOS los entrypoints que invocan procedimiento.sh y los workflows.

Cada ``python X.py`` / ``python -m X`` (lista derivada del repo) se ejecuta con ``--help`` en un subproceso limpio y
por ruta, como en CI, con el PYTHONPATH que fije su workflow. Solo falla por errores de carga (import, atributo,
nombre, sintaxis, sys.modules): es lo que T-338 (#808) no vio porque el proceso de test ya tenía módulos cargados.
"""
import os
import re
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUENTES = [ROOT / "procedimiento.sh", *sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
PATRON = re.compile(r"\bpython3? (?:-m ([A-Za-z_][\w.]*)|([\w./-]+\.py))")
# Módulos de la biblioteca estándar o de pip que los workflows invocan con -m: no son código del repo.
EXCLUIDOS = {"pip": "pip, no es código del repo", "py_compile": "stdlib", "unittest": "stdlib; ya es la propia suite"}
ERRORES_CARGA = re.compile(r"(ModuleNotFoundError|ImportError|AttributeError|NameError|SyntaxError|TypeError): ")
MODULO_AUSENTE = re.compile(r"ModuleNotFoundError: No module named '([\w.]+)'")
DECLARA_ARGS = re.compile(r"argparse|parse_args|sys\.argv")
# Entrypoints sin argparse/parse_args/sys.argv: --help ejecutaría su cuerpo (efectos secundarios). No se ejecutan;
# cada uno debe figurar aquí con su motivo (si aparece uno nuevo sin listar, el test falla y obliga a decidir).
SIN_ARGS_NO_EJECUTADOS = {}
# Entrypoints con args pero que no responden a --help con código 0 (motivo obligatorio).
HELP_RC_DISTINTO_DE_0 = {
    "ddd_core/territorio_ids.py": "CLI mínima con sys.argv: --help imprime el uso y sale con 64 (sin efectos)",
}
TIMEOUT_S = 180


def _es_del_repo(modulo):
    top = modulo.split(".")[0]
    return (ROOT / top).is_dir() or (ROOT / f"{top}.py").is_file() or any(
        (ROOT / d / f"{top}.py").is_file() for d in ("herramientas", "ddd_core", "modulos"))


def entrypoints():
    """{ruta relativa del fichero: (argumentos de python, {fuentes que lo invocan})}"""
    res = {}
    for fuente in FUENTES:
        texto = fuente.read_text(encoding="utf-8", errors="replace")
        for modulo, ruta in PATRON.findall(texto):
            if modulo:
                if modulo in EXCLUIDOS:
                    continue
                fichero = modulo.replace(".", "/") + ".py"
                args = ["-m", modulo]
            else:
                fichero, args = ruta, [ruta]
            if not (ROOT / fichero).is_file():
                continue
            res.setdefault(fichero, (args, set()))[1].add(fuente)
    return res


def _entorno(fuentes):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")}
    # Como el workflow: solo se añade PYTHONPATH si TODAS las fuentes que lo invocan lo fijan.
    if all("PYTHONPATH" in f.read_text(encoding="utf-8", errors="replace") for f in fuentes):
        env["PYTHONPATH"] = str(ROOT)
    return env


def _git_estado():
    return subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout


def _probar(item):
    """-> (fichero, tipo, detalle) con tipo en OK | FALLO | SKIP | TIMEOUT"""
    fichero, (args, fuentes) = item
    try:
        r = subprocess.run([sys.executable, *args, "--help"], cwd=ROOT, env=_entorno(fuentes),
                           capture_output=True, text=True, timeout=TIMEOUT_S, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return fichero, "TIMEOUT", f"más de {TIMEOUT_S} s"
    ultima = (r.stderr.strip().splitlines() or [""])[-1][:200]
    ausente = MODULO_AUSENTE.search(r.stderr)
    if ausente and not _es_del_repo(ausente.group(1)):
        return fichero, "SKIP", f"dependencia de terceros ausente: {ausente.group(1)}"
    if "Traceback" in r.stderr and ERRORES_CARGA.search(r.stderr):
        return fichero, "FALLO", ultima
    if r.returncode != 0 and fichero not in HELP_RC_DISTINTO_DE_0:
        return fichero, "FALLO", f"rc={r.returncode}: {ultima}"
    return fichero, "OK", ""


class SmokeEntrypoints(unittest.TestCase):
    def test_hay_entrypoints(self):
        self.assertGreater(len(entrypoints()), 50)

    def test_sin_args_listados_con_motivo(self):
        sin = {f for f in entrypoints() if not DECLARA_ARGS.search((ROOT / f).read_text(encoding="utf-8", errors="replace"))}
        self.assertEqual(sin, set(SIN_ARGS_NO_EJECUTADOS), "entrypoints sin argparse/sys.argv: añádelos con motivo a SIN_ARGS_NO_EJECUTADOS")

    def test_help_por_ruta_en_subproceso_limpio(self):
        items = [(f, v) for f, v in sorted(entrypoints().items()) if f not in SIN_ARGS_NO_EJECUTADOS]
        antes = _git_estado()
        with ThreadPoolExecutor(max_workers=4) as pool:
            resultados = list(pool.map(_probar, items))
        malos = [f"{f} [{t}]: {d}" for f, t, d in resultados if t in ("FALLO", "TIMEOUT")]
        saltados = [f"{f}: {d}" for f, t, d in resultados if t == "SKIP"]
        if saltados:
            print("\nSKIP (dependencias de terceros ausentes):\n  " + "\n  ".join(saltados), file=sys.stderr)
        self.assertEqual(malos, [], "entrypoints que no cargan:\n" + "\n".join(malos))
        self.assertEqual(_git_estado(), antes, "el smoke --help no debe dejar ficheros nuevos ni modificados en el repo")

    def test_validar_fuentes_reanudacion_aut11_llega_a_la_puerta(self):
        # Como procedimiento.sh:85 con params reales y un paquete sin manifiesto: llega al cargador de ids y falla
        # por la puerta esperada, nunca por el cargador (T-338).
        import tempfile
        with tempfile.TemporaryDirectory() as paquete:
            r = subprocess.run([sys.executable, "herramientas/validar_fuentes_reanudacion.py",
                                "--params", "territorios/aut11/config/aut11_2025.yaml",
                                "--package", paquete, "--root-dir", "."],
                               cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Fuentes BLOQUEADAS", r.stderr)
        self.assertNotIn("__dict__", r.stderr)

    def test_preflight_electoral_aut11_rechaza_el_id_viejo(self):
        # T-349: como el P12 (preflight_preparacion_fuente --kind electoral) con el catálogo real: el paquete registrado
        # de Extremadura lleva el id viejo, no se reutiliza (sin run_id) y el resolutor lo informa.
        r = subprocess.run([sys.executable, "-m", "herramientas.preflight_preparacion_fuente", "--root-dir", ".",
                            "--kind", "electoral", "--territory", "aut11", "--edition", "2025"],
                           cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stderr)
        import json
        datos = json.loads(r.stdout)
        self.assertFalse(datos["registered"])
        self.assertEqual(datos.get("rejected_reason"), "ID_NO_CANONICO")
        self.assertIsNone(datos["run_id"])


if __name__ == "__main__":
    unittest.main()
