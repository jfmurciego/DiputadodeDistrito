"""Web sola al fusionar: monta el sitio de R2 vigente con la V4 de `main` y lo deja listo para `publicar_sitio_r2.py` (T-430, D-194 P7, paso 3c).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-194 (pregunta 7 de REDISENO_R2): al fusionar una PR que solo toca la web (`visor/v4/`), publicarla sin datos y sin P40 completa.
QUÉ HACE (sin calcular nada ni tocar datos):
  (1) lee el índice del sitio `_sitio/actual.json` del bucket del sitio (lo escribe P40); sin índice no monta nada y sale 0 (la primera
      publicación del sitio en R2 es de P40, que monta el sitio entero);
  (2) baja el sitio (`aws s3 sync`, sin `_sitio/`), exige el sha256 de CADA fichero del índice y quita lo que no está en él;
  (3) quita lo que es de la V4 (todo `v4/` y, en la raíz, cada nombre de primer nivel de `visor/v4/` de antes o de ahora, `--previos`);
  (4) pone la V4 de ahora como la deja P40 (`preparar_portada_v4.py`): `visor/v4/` sin lo de `NO_PUBLICAR.txt` en la raíz y `v4/` con
      una redirección por página;
  (5) comprueba que siguen la portada V4, la V1, la V2, la V3 y la documentación.
  Nombres de la V4 que pisarían otra parte del sitio (`RESERVADOS`) abortan sin montar. Los árboles de datos ni se bajan ni se suben
  (no están en el bucket del sitio). El borrado y su tope son los de `publicar_sitio_r2.py`, que publica después el montaje.
USO: python herramientas/web_fusion_r2.py --destino D [--previos n1,n2,…] [--raiz .] [--bucket B]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from herramientas.preparar_portada_v4 import MARCA_V4, REDIRECCION, destino_en_raiz
from herramientas.publicar_datos_web import R2, DatosWebError, _aws, sha256
from herramientas.publicar_sitio_r2 import INDICE, clave_valida

RAIZ = Path(__file__).resolve().parents[1]
RESERVADOS = {"v1", "v2", "v3", "v4", "docs", "dashboard", "nacional", "congreso", "datos", "data", "_sitio"}
OBLIGATORIOS = ("index.html", "v1/index.html", "v2/index.html", "v3/index.html", "docs/index.html")


class R2Bajada(R2):
    def bajar(self, destino: Path) -> None:
        r = _aws(["sync", f"s3://{self.bucket}/", str(destino), "--exclude", "_sitio/*"])
        if r.returncode != 0:
            raise DatosWebError(f"R2_BAJADA: {r.stderr.strip()[:300]}")


def no_publicar(v4: Path) -> set[str]:
    out = set()
    for linea in (v4 / "NO_PUBLICAR.txt").read_text(encoding="utf-8").splitlines():
        f = linea.strip()
        if f and not f.startswith("#") and ".." not in f and not f.startswith("/"):
            out.add(f)
    return out


def ficheros_v4(v4: Path) -> dict[str, Path]:
    fuera = no_publicar(v4)
    out = {}
    for p in sorted(v4.rglob("*")):
        rel = p.relative_to(v4).as_posix()
        if p.is_file() and not any(rel == f or rel.startswith(f + "/") for f in fuera):
            out[rel] = p
    return out


def montar(destino: Path, r2, raiz: Path = RAIZ, previos: set[str] = frozenset()) -> int:
    indice_b = r2.leer(INDICE)
    if indice_b is None:
        print(f"[web_fusion] sin {INDICE} en el bucket del sitio: la primera publicación del sitio en R2 es de P40; no se monta nada")
        return 0
    indice = json.loads(indice_b).get("ficheros") or {}
    if not indice:
        raise DatosWebError("INDICE_VACIO: el índice del sitio no lista ficheros; no se monta nada")
    v4 = raiz / "visor" / "v4"
    nuevos = ficheros_v4(v4)
    nombres = {r.split("/", 1)[0] for r in nuevos} | set(previos)
    choques = sorted(nombres & RESERVADOS)
    if choques:
        raise DatosWebError(f"V4_PISA_EL_SITIO: {', '.join(choques)}; no se monta nada")
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    r2.bajar(destino)
    malos = [k for k, h in indice.items() if not clave_valida(k) or not (destino / k).is_file() or sha256((destino / k).read_bytes()) != h]
    if malos:
        raise DatosWebError(f"SITIO_R2_NO_CASA: {len(malos)} ficheros del índice faltan o no casan (p. ej. {malos[0]}); no se monta nada")
    for p in sorted(destino.rglob("*"), reverse=True):  # lo que no está en el índice (huérfanos de un borrado a medias) no entra
        rel = p.relative_to(destino).as_posix()
        if p.is_file() and rel not in indice:
            p.unlink()
        elif p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    for k in indice:  # lo que es de la V4 (de antes o de ahora)
        if k.startswith("v4/") or k.split("/", 1)[0] in nombres:
            (destino / k).unlink()
    for rel, p in nuevos.items():
        (destino / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, destino / rel)
    for rel in sorted(r for r in nuevos if r.endswith(".html")):
        d = destino / "v4" / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(REDIRECCION.format(destino=destino_en_raiz(Path(rel))), encoding="utf-8")
    faltan = [f for f in OBLIGATORIOS if not (destino / f).is_file()]
    if faltan:
        raise DatosWebError(f"SITIO_INCOMPLETO: faltan {', '.join(faltan)}; no se publica")
    if MARCA_V4 not in (destino / "index.html").read_text(encoding="utf-8"):
        raise DatosWebError("SIN_PORTADA_V4: la raíz montada no es la portada de la V4; no se publica")
    n = sum(1 for p in destino.rglob("*") if p.is_file())
    print(f"[web_fusion] montado {destino}: {n} ficheros ({len(nuevos)} de la V4)")
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destino", type=Path, required=True)
    ap.add_argument("--previos", default="", help="nombres de primer nivel de visor/v4/ antes de la fusión, separados por comas")
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    ap.add_argument("--bucket", default=os.environ.get("R2_SITIO_BUCKET", ""))
    a = ap.parse_args(argv)
    if not a.bucket:
        print("[web_fusion] sin R2_SITIO_BUCKET: no se monta nada")
        return 0
    previos = {n.strip() for n in a.previos.split(",") if n.strip()}
    malos = sorted(n for n in previos if "/" in n or n in (".", ".."))
    if malos:
        print(f"[web_fusion] PREVIOS_NO_VALIDOS: {malos}", file=sys.stderr)
        return 2
    try:
        montar(a.destino, R2Bajada(a.bucket), a.raiz, previos)
    except DatosWebError as e:
        print(f"[web_fusion] {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
