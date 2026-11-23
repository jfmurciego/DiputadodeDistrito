#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Poda de R2 con lista aprobada (T-145): verifica cada clave y su copia, y solo entonces borra.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Poda de R2 con lista aprobada
FECHA: 2026-11-23
ESTADO: candidato
CAMBIOS: 1.2.0 (T-443, D-188/D-198, paso 6 del §c de docs/ESTUDIOS/T435_ESTRUCTURA_R2/DISENO.md): (a) protección del árbol nuevo: ninguna fila
  de la lista puede ser de `fuentes/`, `interno/` o `mapas/` (`CLAVE_PROTEGIDA`), ni de `arc-e/` salvo `arc-e/paquetes-p10/<package_sha256>.zip`. (b) Esas
  filas de paquete P10 solo se borran si CADA paquete citado (por territorio y edición de `configuracion/catalogo_preparacion.yaml`: el
  `generation_state` de su contrato, o la evidencia del catálogo si el contrato no lo trae) tiene su copia por edición `fuentes/por-territorio/<ámbito>/<territorio>/<edición>/paquete.zip` comprobada por sha256
  (manifiesto de la carpeta con huella = package_sha256 y sha256 del zip igual al metadato de R2); si falta una, ninguna fila de paquete se borra
  (`ARC_E_P10_SIN_COPIA_POR_EDICION`). Una fila de paquete citado debe traer esa copia como `copia_clave`; uno no citado (D-178), sin copia.
  (c) Lista con claves nuevas: la copia que se conserva puede estar en `interno/estados/…` (territorio = el de su entrada en
  orchestracion/archivo_r2.json). (d) M01/M02/M03/M03U: el paquete P10 del territorio vale en la ruta por edición o en `arc-e/` (lectura con doble ruta).
  Sin borrar nada: simulación por defecto como antes.
CAMBIOS: 1.1.0 (T-304): la protección de M01/M02/M03/M03U pasa de ``bateria/entradas/<t>/`` (retirada en T-303) al paquete P10 de la fuente del
  territorio, ``arc-e/paquetes-p10/<package_sha256>.zip`` (package_sha256 del contrato), que debe existir en R2 con sha256. Lista y reglas de borrado no cambian.
CAMBIOS: 1.0.0: fichero nuevo (T-145; la copia ha de ser del mismo territorio).
MOTIVO: R2 tiene 28 GB frente a 10 GB gratuitos; el propietario aprobó la lista docs/ESTUDIOS/T145_PODA_R2/ola1_borrar.csv
  (234 claves). El borrado en R2 es irreversible: esta herramienta no borra nada fuera de esa lista.
ANTERIOR: legacy/herramientas/podar_r2_v1.1.0_20261123.py
QUÉ HACE: lee la lista (el sha256 del fichero debe ser el fijado en la entrada), y por cada fila comprueba (1) que la clave es un
  ``ddd-state-<run>-M0x.zip``, (2) que R2 la tiene con el sha256 de la lista y el manifiesto la anota igual, (3) que la copia que
  conserva existe en R2 y en el manifiesto con su sha256 y que no está en la propia lista, y (4) para M01/M02/M03/M03U, que
  el territorio tiene su paquete P10 de la fuente ``arc-e/paquetes-p10/<package_sha256>.zip`` en R2 con metadato sha256 (T-304). Simulación por defecto: informa
  de todo y no borra. Con ``--ejecutar``: si algún desajuste, no borra nada; si no hay, borra una a una, comprueba que desaparece, quita la
  entrada del manifiesto y se detiene al primer error. Informe JSON de lo borrado.
USO: python herramientas/podar_r2.py --sha256-lista <sha> [--ejecutar] [--informe ruta.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import archivar_artefactos_r2 as ar  # noqa: E402
import rutas_r2  # noqa: E402

LISTA = "docs/ESTUDIOS/T145_PODA_R2/ola1_borrar.csv"
_ESTADO = re.compile(r"^[a-z0-9_]+/\d+/ddd-state-\d+-(M0\d[A-Z]?)\.zip$")
_P10 = re.compile(r"^arc-e/paquetes-p10/([0-9a-f]{64})\.zip$")
_ETAPAS_BATERIA = {"M01", "M02", "M03", "M03U"}
PROTEGIDAS = ("fuentes/", "interno/", "mapas/")  # árbol nuevo (D-188): nunca se poda con esta herramienta
CATALOGO = "configuracion/catalogo_preparacion.yaml"


def sha256_fichero(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer_lista(ruta: Path, sha_esperado: str) -> list[dict]:
    real = sha256_fichero(ruta)
    if real != sha_esperado.strip().lower():
        raise ValueError(f"LISTA_NO_APROBADA: sha256 de la lista {real} != fijado {sha_esperado}")
    with ruta.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    claves = [f["clave"] for f in filas]
    if len(set(claves)) != len(claves):
        raise ValueError("LISTA_INVALIDA: claves duplicadas")
    for f in filas:
        if f["clave"].startswith(PROTEGIDAS):
            raise ValueError(f"CLAVE_PROTEGIDA: {f['clave']} ({', '.join(PROTEGIDAS)} no se podan)")
        if not (_ESTADO.match(f["clave"]) or _P10.match(f["clave"])):
            raise ValueError(f"LISTA_INVALIDA: {f['clave']} no es un estado ddd-state-* ni un paquete arc-e/paquetes-p10/<sha256>.zip")
    return filas


def paquetes_citados(root: Path = ROOT) -> list[dict]:
    """Paquetes P10 citados: por cada territorio y edición del catálogo, el `generation_state` de su contrato (o, sin él, la evidencia del catálogo): {territorio, edicion,
    package_sha256, clave} con la clave por edición (None si el territorio no tiene ruta nueva: cuenta como copia ausente)."""
    import yaml
    cat = yaml.safe_load((root / CATALOGO).read_text(encoding="utf-8")) or {}
    out, vistos = [], set()
    for t in cat.get("territories") or []:
        tid = t.get("territory_id")
        for ed, e in sorted((t.get("editions") or {}).items()):
            # el del contrato (`generation_state`), que es el que archiva `bateria_motor archivar-p10`; sin él, el de la evidencia del catálogo
            contrato = root / str((e or {}).get("contract_path") or "")
            h = None
            if (e or {}).get("contract_path") and contrato.is_file():
                h = ((yaml.safe_load(contrato.read_text(encoding="utf-8")) or {}).get("generation_state") or {}).get("package_sha256")
            hs = [h or ((e or {}).get("preparation_evidence") or {}).get("package_sha256")]
            for h in hs:
                if not h or (tid, str(ed), h) in vistos:
                    continue
                vistos.add((tid, str(ed), h))
                try:
                    clave = rutas_r2.ruta_paquete_p10(tid, str(ed))
                except (rutas_r2.RutaInvalida, KeyError, ValueError):
                    clave = None
                out.append({"territorio": tid, "edicion": str(ed), "package_sha256": h, "clave": clave})
    return out


def copia_por_edicion_ok(c: dict, sha: Callable[[str], Optional[str]], leer_json: Callable[[str], Optional[dict]]) -> bool:
    """La copia por edición existe y es la del paquete citado: manifiesto con huella = package_sha256 y sha256 del zip = metadato de R2."""
    if not c.get("clave"):
        return False
    man = leer_json(rutas_r2.ruta_manifiesto(c["clave"])) or {}
    esperado = ((man.get("ficheros") or {}).get("paquete.zip") or {}).get("sha256")
    return man.get("huella") == c["package_sha256"] and bool(esperado) and sha(c["clave"]) == esperado


def _territorio_copia(ck: str, arts: dict) -> str:
    """Territorio de la copia: la carpeta de la clave vieja o el de su entrada del índice (árbol nuevo, sin territorio en la ruta)."""
    return str((arts.get(ck) or {}).get("territorio") or "") if rutas_r2.es_nueva(ck) else ck.split("/")[0]


def verificar_p10(filas: list[dict], sha: Callable[[str], Optional[str]], citados: list[dict],
                  leer_json: Callable[[str], Optional[dict]]) -> list[dict]:
    """Filas `arc-e/paquetes-p10/`: solo si TODAS las copias por edición de los paquetes citados están (D-198); fila citada → su copia por edición."""
    filas = [f for f in filas if _P10.match(f["clave"])]
    if not filas:
        return []
    faltan = [c for c in citados if not copia_por_edicion_ok(c, sha, leer_json)]
    if faltan:
        detalle = ", ".join(f"{c['territorio']}/{c['edicion']}" for c in faltan[:8])
        return [{"clave": f["clave"], "error": "ARC_E_P10_SIN_COPIA_POR_EDICION", "detalle": f"{len(faltan)} sin copia: {detalle}"} for f in filas]
    por_sha: dict[str, set] = {}
    for c in citados:
        por_sha.setdefault(c["package_sha256"], set()).add(c["clave"])
    fallos = []
    for f in filas:
        k, ck = f["clave"], (f.get("copia_clave") or "")
        pkg = _P10.match(k).group(1)
        err = None
        if sha(k) != f["sha256"]:
            err = "SHA_R2_DISTINTO"
        elif pkg in por_sha and ck not in por_sha[pkg]:
            err = "P10_CITADO_SIN_SU_COPIA"  # la copia que se conserva es la de su edición
        elif pkg in por_sha and sha(ck) != f["copia_sha256"]:
            err = "COPIA_SHA_R2_DISTINTO"
        elif pkg not in por_sha and ck:
            err = "P10_NO_CITADO_CON_COPIA"
        if err:
            fallos.append({"clave": k, "error": err})
    return fallos


def verificar(filas: list[dict], man: dict, sha: Callable[[str], Optional[str]],
              tiene_entrada: Callable[[str], bool], citados: Optional[list[dict]] = None,
              leer_json: Optional[Callable[[str], Optional[dict]]] = None) -> list[dict]:
    """Devuelve la lista de desajustes (vacía = todo verificado). Solo lectura."""
    arts, claves = man["artefactos"], {f["clave"] for f in filas}
    fallos = []
    if any(_P10.match(f["clave"]) for f in filas):
        if citados is None or leer_json is None:
            fallos += [{"clave": f["clave"], "error": "ARC_E_P10_SIN_COPIA_POR_EDICION"} for f in filas if _P10.match(f["clave"])]
        else:
            fallos += verificar_p10(filas, sha, citados, leer_json)
    for f in filas:
        if _P10.match(f["clave"]):
            continue
        k, h, ck, ch = f["clave"], f["sha256"], f["copia_clave"], f["copia_sha256"]
        err = None
        etapa = _ESTADO.match(k).group(1)
        if ck in claves:
            err = "COPIA_EN_LA_LISTA"
        elif ck.startswith(PROTEGIDAS) and not ck.startswith("interno/estados/"):
            err = "COPIA_FUERA_DE_INTERNO_ESTADOS"
        elif _territorio_copia(ck, arts) != f["territorio"] or k.split("/")[0] != f["territorio"]:
            err = "COPIA_DE_OTRO_TERRITORIO"
        elif arts.get(k, {}).get("sha256") != h:
            err = "MANIFIESTO_DISTINTO"
        elif sha(k) != h:
            err = "SHA_R2_DISTINTO"
        elif arts.get(ck, {}).get("sha256") != ch:
            err = "COPIA_MANIFIESTO_DISTINTO"
        elif sha(ck) != ch:
            err = "COPIA_SHA_R2_DISTINTO"
        elif etapa in _ETAPAS_BATERIA and not tiene_entrada(f["territorio"]):
            err = "SIN_ENTRADA_MINIMA_BATERIA"
        if err:
            fallos.append({"clave": k, "error": err})
    return fallos


def podar(filas: list[dict], ruta_man: Path, sha, tiene_entrada, borrar, ejecutar: bool, citados: Optional[list[dict]] = None,
          leer_json: Optional[Callable[[str], Optional[dict]]] = None) -> dict:
    man = ar.cargar_manifiesto(ruta_man)
    fallos = verificar(filas, man, sha, tiene_entrada, citados, leer_json)
    informe = {"ejecutar": ejecutar, "claves": len(filas), "bytes_lista": sum(int(f["tamano_bytes"]) for f in filas),
               "desajustes": fallos, "borradas": [], "error": None,
               "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if fallos or not ejecutar:
        return informe
    try:
        for f in filas:
            k = f["clave"]
            borrar(k)
            if sha(k) is not None:
                raise RuntimeError(f"BORRADO_NO_EFECTIVO {k}")
            man["artefactos"].pop(k, None)
            informe["borradas"].append({"clave": k, "tamano_bytes": int(f["tamano_bytes"]), "sha256": f["sha256"],
                                        "copia_clave": f["copia_clave"], "copia_sha256": f["copia_sha256"]})
    except Exception as exc:  # noqa: BLE001 - se detiene al primer error y deja constancia
        informe["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        ar.guardar_manifiesto(ruta_man, man)
    informe["bytes_borrados"] = sum(b["tamano_bytes"] for b in informe["borradas"])
    return informe


def claves_paquete_p10(territorio: str, root: Path = ROOT) -> list[str]:
    """Donde vale el paquete P10 del territorio (T-443): la ruta por edición del catálogo (`default_edition`) y la de `arc-e/` por package_sha256."""
    vieja = clave_paquete_p10(territorio, root)
    nueva = None
    try:
        import yaml
        ed = str((yaml.safe_load((root / CATALOGO).read_text(encoding="utf-8")) or {}).get("default_edition") or "")
        nueva = rutas_r2.ruta_paquete_p10(territorio, ed)
    except (OSError, rutas_r2.RutaInvalida, KeyError, ValueError):
        nueva = None
    return rutas_r2.candidatas(nueva, vieja) if vieja else []


def clave_paquete_p10(territorio: str, root: Path = ROOT) -> Optional[str]:
    """Clave R2 del paquete P10 de la fuente del territorio (id viejo o nuevo): ``arc-e/paquetes-p10/<package_sha256>.zip``; None sin contrato
    o sin package_sha256."""
    import yaml
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ddd_core.territorio_ids import carpeta_de, resolver_id
    nuevo = resolver_id(territorio)
    ruta = root / "territorios" / carpeta_de(root, nuevo) / "config" / f"{nuevo}_2025.yaml"
    if not ruta.is_file():
        return None
    h = ((yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}).get("generation_state") or {}).get("package_sha256")
    return f"arc-e/paquetes-p10/{h}.zip" if h else None


def clientes_r2(bucket: str, cuenta: str):
    sha, _ = ar.r2_cliente(bucket, cuenta)
    ep = f"https://{cuenta}.r2.cloudflarestorage.com"

    def tiene_entrada(territorio: str) -> bool:
        return any(sha(k) for k in claves_paquete_p10(territorio))

    def leer_json(k: str) -> Optional[dict]:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "o.json"
            p = subprocess.run(["aws", "s3", "cp", f"s3://{bucket}/{k}", str(dest), "--endpoint-url", ep, "--only-show-errors"],
                               capture_output=True, text=True)
            if p.returncode != 0:
                if re.search(r"404|NoSuchKey|Not Found|does not exist", p.stderr or ""):
                    return None
                raise subprocess.CalledProcessError(p.returncode, "s3 cp", stderr=p.stderr)
            try:
                return json.loads(dest.read_text(encoding="utf-8"))
            except ValueError:
                return None

    def borrar(k: str) -> None:
        ar.con_reintentos(lambda: subprocess.run(
            ["aws", "s3", "rm", f"s3://{bucket}/{k}", "--endpoint-url", ep, "--only-show-errors"], check=True),
            f"R2 borrado {k}")

    return sha, tiene_entrada, borrar, leer_json


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    ap.add_argument("--sha256-lista", required=True, help="sha256 aprobado de la lista CSV")
    ap.add_argument("--ejecutar", action="store_true", help="borra de verdad; sin él, solo simula")
    ap.add_argument("--informe", help="ruta del informe JSON")
    a = ap.parse_args(argv)
    root = Path(a.root_dir)
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::Faltan R2_BUCKET o R2_ACCOUNT_ID.")
        return 1
    try:
        filas = leer_lista(root / LISTA, a.sha256_lista)
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    sha, tiene_entrada, borrar, leer_json = clientes_r2(bucket, cuenta)
    citados = paquetes_citados(root) if any(_P10.match(f["clave"]) for f in filas) else None
    inf = podar(filas, root / ar.MANIFIESTO, sha, tiene_entrada, borrar, a.ejecutar, citados, leer_json)
    texto = json.dumps(inf, ensure_ascii=False, indent=2, sort_keys=True)
    if a.informe:
        Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
        Path(a.informe).write_text(texto + "\n", encoding="utf-8")
    print(texto)
    for d in inf["desajustes"]:
        print(f"::error::{d['error']} {d['clave']}")
    if inf["error"]:
        print(f"::error::PODA_DETENIDA {inf['error']}")
    return 1 if inf["desajustes"] or inf["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
