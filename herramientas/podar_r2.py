#!/usr/bin/env python3
"""Poda de R2: calcula (y, con lista aprobada, ejecuta) el borrado de artefactos archivados fuera de la política de retención.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Poda de R2 bajo 10 GB
FECHA: 2026-11-07
ESTADO: candidato
QUÉ HACE: lee orchestracion/archivo_r2.json y orchestracion/publicaciones_visor.json y aplica la política de
  docs/POLITICA_RETENCION_R2.md: por territorio se conserva el run vigente (y, si hay uno más nuevo y al menos igual de completo sin publicar, ese también) y de cada uno solo el producto final;
  las auditorías pequeñas (< 1 MB) se conservan siempre. Calcula lista de borrado, tamaño borrado y tamaño final.
  Por defecto SIMULA (no toca R2 ni el manifiesto). El borrado real exige --borrar, una lista aprobada
  (--lista) y su sha256 (--sha256); rechaza cualquier clave que la política hoy conserve o que no esté en el manifiesto.
  --comprobar-limite falla (1) si la suma del manifiesto supera 9 GB.
CAMBIOS: 1.0.0: fichero nuevo (T-76).
MOTIVO: el propietario no quiere pagar R2: capa gratuita de 10 GB y el archivo ocupaba ~28 GB.
ANTERIOR: ninguna (fichero nuevo)
Uso:
  python herramientas/podar_r2.py [--root-dir .] [--conservar-m06] [--salida lista.json]      (simulación)
  python herramientas/podar_r2.py --comprobar-limite
  python herramientas/podar_r2.py --borrar --lista lista.json --sha256 <huella>               (borrado real)
Entorno (solo --borrar): R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_*.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFIESTO = "orchestracion/archivo_r2.json"
VISOR = "orchestracion/publicaciones_visor.json"
LIMITE_BYTES = 9 * 10**9
AUDITORIA_MAX = 10**6
_ETAPA = re.compile(r"-M(\d+)(U?)$")


def _archivista():
    spec = importlib.util.spec_from_file_location("archivar_artefactos_r2", Path(__file__).with_name("archivar_artefactos_r2.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def etapa(nombre: str) -> int:
    """Número de etapa M0x de un «ddd-state-<run>-M0x»; 0 si no es un estado."""
    if not nombre.startswith("ddd-state-"):
        return 0
    m = _ETAPA.search(nombre)
    return int(m.group(1)) if m and not m.group(2) else 0


def huella_lista(claves) -> str:
    return hashlib.sha256("\n".join(sorted(claves)).encode("utf-8")).hexdigest()


def run_vigente(runs: dict[str, dict], publicados: dict[str, int]) -> str:
    """Run vigente: el publicado en el visor (prioriza M08 y el mayor id) si está archivado; si no, el mayor run
    archivado con la etapa más avanzada."""
    pub = [r for r in publicados if r in runs]
    if pub:
        return max(pub, key=lambda r: (publicados[r], int(r)))
    return max(runs, key=lambda r: (max(runs[r]["etapas"], default=0), int(r)))


def publicados_visor(visor: dict) -> dict[str, dict[str, int]]:
    """territorio → {run: rango} con rango 2 si hay canonical_m08, 1 si solo canonical_m06."""
    out: dict[str, dict[str, int]] = {}
    for p in visor.get("products", []):
        run, terr = str(p.get("run_id") or ""), p.get("territory_id")
        if not run.isdigit() or not terr:
            continue
        rango = {"canonical_m08": 2, "canonical_m06": 1}.get(p.get("kind"))
        if rango:
            d = out.setdefault(terr, {})
            d[run] = max(d.get(run, 0), rango)
    return out


def calcular(manifiesto: dict, visor: dict, conservar_m06: bool = False) -> dict:
    """Política pura: devuelve claves a conservar/borrar, tamaños y avisos."""
    entradas = manifiesto.get("artefactos", {})
    pub = publicados_visor(visor)
    por_terr: dict[str, dict[str, dict]] = {}
    for k, e in entradas.items():
        r = por_terr.setdefault(e["territorio"], {}).setdefault(str(e["run_id"]), {"claves": [], "etapas": set()})
        r["claves"].append(k)
        n = etapa(e["artefacto"])
        if n:
            r["etapas"].add(n)
    conservar: set[str] = set()
    avisos: list[str] = []
    vigentes: dict[str, str] = {}
    for terr, runs in sorted(por_terr.items()):
        vig = run_vigente(runs, pub.get(terr, {}))
        vigentes[terr] = vig
        if terr in pub and vig not in pub[terr]:
            avisos.append(f"{terr}: el run publicado no está archivado; vigente = {vig} (último con etapa más avanzada)")
        mas_nuevo = max(runs, key=int)
        if vig != mas_nuevo and max(runs[mas_nuevo]["etapas"], default=0) >= max(runs[vig]["etapas"], default=0):
            avisos.append(f"{terr}: hay un run archivado más nuevo ({mas_nuevo}) que el vigente ({vig}); se conserva también")
        mantener = [vig]
        if mas_nuevo != vig and max(runs[mas_nuevo]["etapas"], default=0) >= max(runs[vig]["etapas"], default=0):
            mantener.append(mas_nuevo)  # un run más nuevo y al menos igual de completo aún no se ha publicado: no se pierde
        for run in mantener:
            final = max(runs[run]["etapas"], default=0)
            for k in runs[run]["claves"]:
                n = etapa(entradas[k]["artefacto"])
                if n and (n == final or (conservar_m06 and n == 6)):
                    conservar.add(k)
    for k, e in entradas.items():
        if not etapa(e["artefacto"]) and e["tamano_bytes"] < AUDITORIA_MAX:
            conservar.add(k)
    borrar = sorted(set(entradas) - conservar)
    tam = lambda ks: sum(entradas[k]["tamano_bytes"] for k in ks)
    return {
        "conservar": sorted(conservar),
        "borrar": borrar,
        "bytes_total": tam(entradas),
        "bytes_borrar": tam(borrar),
        "bytes_final": tam(conservar),
        "vigentes": vigentes,
        "avisos": avisos,
    }


def superar_limite(manifiesto: dict, limite: int = LIMITE_BYTES) -> tuple[bool, int]:
    total = sum(e["tamano_bytes"] for e in manifiesto.get("artefactos", {}).values())
    return total > limite, total


def lista_json(plan: dict) -> dict:
    return {
        "schema": "ddd.poda-r2/1.0",
        "sha256": huella_lista(plan["borrar"]),
        "bytes_borrar": plan["bytes_borrar"],
        "bytes_final": plan["bytes_final"],
        "claves": plan["borrar"],
    }


def verificar_lista(lista: dict, sha_esperado: str, plan: dict, manifiesto: dict) -> list[str]:
    """Errores que impiden el borrado real (vacío = aprobada y coherente con la política actual)."""
    errores = []
    claves = lista.get("claves", [])
    real = huella_lista(claves)
    if real != sha_esperado:
        errores.append(f"la huella de la lista ({real}) no coincide con la aprobada ({sha_esperado})")
    if lista.get("sha256") != real:
        errores.append("el campo sha256 de la lista no coincide con su contenido")
    ent = manifiesto.get("artefactos", {})
    for k in claves:
        if k not in ent:
            errores.append(f"{k}: no está en el manifiesto")
        elif k in set(plan["conservar"]):
            errores.append(f"{k}: la política actual lo conserva")
    return errores


def r2_borrar(bucket: str, cuenta: str):
    con_reintentos = _archivista().con_reintentos
    ep = f"https://{cuenta}.r2.cloudflarestorage.com"

    def _rm(k: str) -> None:
        subprocess.run(["aws", "s3", "rm", f"s3://{bucket}/{k}", "--endpoint-url", ep, "--only-show-errors"], check=True)

    return lambda k: con_reintentos(lambda: _rm(k), f"R2 borrar {k}")


def borrar(claves: list[str], manifiesto: dict, rm) -> dict:
    """Borra en R2 y retira del manifiesto solo lo borrado; los fallos se informan y se conserva su entrada."""
    res = {"borrados": [], "errores": []}
    for k in claves:
        try:
            rm(k)
        except Exception as exc:  # noqa: BLE001
            res["errores"].append(f"{k}: {exc}")
            continue
        manifiesto["artefactos"].pop(k, None)
        res["borrados"].append(k)
    return res


def _gb(n: int) -> str:
    return f"{n / 1e9:.2f} GB"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    ap.add_argument("--conservar-m06", action="store_true", help="conserva también el M06 del run vigente (zip no acumulativos)")
    ap.add_argument("--salida", help="escribe aquí la lista de borrado (para aprobar)")
    ap.add_argument("--comprobar-limite", action="store_true", help="falla si el manifiesto suma más de 9 GB")
    ap.add_argument("--borrar", action="store_true", help="borrado real (exige --lista y --sha256)")
    ap.add_argument("--lista")
    ap.add_argument("--sha256")
    a = ap.parse_args(argv)
    root = Path(a.root_dir)
    arc = _archivista()
    man = arc.cargar_manifiesto(root / MANIFIESTO)
    if a.comprobar_limite:
        excede, total = superar_limite(man)
        print(f"R2: {_gb(total)} archivados (límite {_gb(LIMITE_BYTES)})")
        if excede:
            print(f"::error::El archivo R2 supera {_gb(LIMITE_BYTES)}: lanza la poda (podar-r2.yml) con la lista aprobada.")
        return 1 if excede else 0
    visor = json.loads((root / VISOR).read_text(encoding="utf-8")) if (root / VISOR).is_file() else {}
    plan = calcular(man, visor, a.conservar_m06)
    if not a.borrar:
        if a.salida:
            Path(a.salida).write_text(json.dumps(lista_json(plan), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for av in plan["avisos"]:
            print(f"aviso: {av}")
        print(f"SIMULACIÓN: borrar {len(plan['borrar'])} de {len(man['artefactos'])} artefactos, {_gb(plan['bytes_borrar'])}; "
              f"final {_gb(plan['bytes_final'])}; huella {huella_lista(plan['borrar'])}")
        return 0
    if not a.lista or not a.sha256:
        print("::error::--borrar exige --lista y --sha256.")
        return 1
    lista = json.loads(Path(a.lista).read_text(encoding="utf-8"))
    errores = verificar_lista(lista, a.sha256, plan, man)
    if errores:
        for e in errores:
            print(f"::error::{e}")
        return 1
    import os
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::Faltan R2_BUCKET o R2_ACCOUNT_ID.")
        return 1
    res = borrar(lista["claves"], man, r2_borrar(bucket, cuenta))
    arc.guardar_manifiesto(root / MANIFIESTO, man)
    _, total = superar_limite(man)
    print(json.dumps({"borrados": len(res["borrados"]), "errores": res["errores"], "final_bytes": total}, ensure_ascii=False))
    for e in res["errores"]:
        print(f"::error::{e}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
