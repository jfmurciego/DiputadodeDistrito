"""VERSIÓN: 1.0.0 · ANTERIOR: ninguna (fichero nuevo) · T-349.

Congela SIN TOCAR (`git show <BASE>:<ruta>`, byte a byte) el estado registrado de la r3 con id viejo que consume la cadena
de la r4 (Activación, 00, par, 03/04): configuración y los directorios de territorio de MUESTRA. No se ejecuta en los tests.
Uso, desde la raíz del repo: python tests/fixtures/t349_flujo/_generar_fixture.py
"""
import shutil
import subprocess
from pathlib import Path

BASE = "25dd77724e649257a6d2dfdfe65d40c9fd12a5ec"  # commit base de T-349 (estado real de la r3)
MUESTRA = ("aut11", "nac01", "aut01", "aut02", "aut05", "aut19", "aut08", "aut12")  # piloto aut11, un nac y otras autonómicas (docs/diagnostico/inventario_ids_no_canonicos.*)
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "raiz"


def _ls(prefix: str) -> list[str]:
    out = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, prefix], cwd=ROOT, text=True)
    return [p for p in out.splitlines() if p]


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    rutas = [p for p in _ls("configuracion/") if not p.startswith("configuracion/equivalencia_seccionado_")] + _ls("fuentes/")
    for t in MUESTRA:
        # Solo lo que leen los planificadores (config y evidencia); sin datos pesados (inputs/, resultados/).
        rutas += [p for p in _ls(f"territorios/{t}/") if p.split("/")[2] in ("config", "evidencia")]
    for rel in sorted(rutas):
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=ROOT))
    (OUT.parent / "BASE").write_text(BASE + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
