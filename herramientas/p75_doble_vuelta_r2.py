#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P75 Doble vuelta desde R2: calcula dv_base, dv_A y dv_B de cada territorio a partir del ddd-minimo-<run>-M08 archivado (T-418).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-178/D-179: la V4 sale sin regenerar los territorios publicados. El paquete mínimo M08 de R2 lleva (por construcción, `_m0[678]_`) la
  tabla de votos por partido y distrito de M07; esta herramienta la lee y calcula la doble vuelta con `doble_vuelta.py` y el alias de partidos.
QUÉ HACE: por territorio (por defecto los del Congreso, ámbito NAC, con M08 vigente DE LA ELECCIÓN en orchestracion/publicaciones_visor.json; un `aut` se rechaza): (1) localiza `ddd-minimo-<run>-M08` en
  orchestracion/archivo_r2.json, lo baja de R2 y comprueba su sha256 (herramientas/restaurar_estado_r2.py); (2) informa de si trae
  `*_m07_resultados_partido.csv` (sin él no se calcula: nunca se reconstruyen votos); (3) mide la cobertura del alias sobre esos ids (un % alto de votos sin
  casar = elección distinta de la pedida o alias incompleto) y calcula `doble_vuelta.csv`, `detalle.csv`, `cobertura.json` y `manifiesto.json`;
  (4) sube `<carpeta>/<run>/ddd-doble-vuelta-<run>-p75-<run_p75>.zip` a R2 (ZIP determinista; carpeta y run son los del archivista, no propios) y, al final,
  `doble_vuelta/<AAAA-MM>/<run_p75>/INFORME.json` con una fila por territorio: cada ejecución sube objetos nuevos y no sobrescribe ni borra nada.
  Sale 0 si todos los territorios quedan OK; 1 si alguno no (el informe se sube igualmente). Sin `--sin-subir` necesita R2_BUCKET, R2_ACCOUNT_ID y AWS_*.
  `district_id` va tal como lo escribe M07 (0..K-1); la numeración pública la aplica el publicador (T-135).
USO: python herramientas/p75_doble_vuelta_r2.py [--territorios nac01,nac02] [--eleccion 2023-07] [--salida DIR] [--sin-subir]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archivar_artefactos_r2 as ar  # noqa: E402
import doble_vuelta as dv  # noqa: E402
import doble_vuelta_cobertura as cob  # noqa: E402
import fuente_r2  # noqa: E402
import p70_resolver as pr  # noqa: E402
import restaurar_estado_r2 as rr  # noqa: E402
import resultados_ligeros as rl  # noqa: E402
from ddd_core import territorio_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUBLICACIONES = Path("orchestracion/publicaciones_visor.json")
ARCHIVO = Path("orchestracion/archivo_r2.json")
ALIAS = Path("configuracion/alias_partidos_generales.csv")
ELECCION_DEFECTO = "2023-07"
CSV_M07 = "_m07_resultados_partido.csv"
UMBRAL_SIN_CASAR = 5.0  # % de votos sin casar a partir del cual se avisa de elección o alias incorrectos
_FECHA_ZIP = (2020, 1, 1, 0, 0, 0)


def r2_existe(bucket: str, cuenta: str):
    """existe(clave) → bool con `aws s3api head-object`: 404 = no existe; cualquier otro fallo se propaga (nunca se asume que no existe)."""
    ep = f"https://{cuenta}.r2.cloudflarestorage.com"

    def _una(k: str) -> bool:
        p = subprocess.run(["aws", "s3api", "head-object", "--bucket", bucket, "--key", k, "--endpoint-url", ep, "--output", "json"],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return True
        # solo el error estructurado de aws («An error occurred (404) when calling the HeadObject operation») o NoSuchKey; un «404» suelto en el
        # texto (endpoint, id de cuenta hexadecimal, fallo de conexión) NO es «no existe»
        if re.search(r"\(404\)|NoSuchKey", p.stderr or ""):
            return False
        raise subprocess.CalledProcessError(p.returncode, "head-object", stderr=p.stderr)

    return lambda k: ar.con_reintentos(lambda: _una(k), f"R2 head {k}")


def subir_nuevo(subir, existe, clave: str, ruta: Path, sha: str) -> None:
    """Sube SOLO si la clave no existe: nunca sobrescribe ni borra (si existe, FileExistsError y no se sube nada)."""
    if existe(clave):
        raise FileExistsError(f"P75_CLAVE_YA_EXISTE: {clave}")
    subir(clave, ruta, sha)


def run_p75_de_entorno(env=None) -> str:
    """Identifica la ejecución para las claves de R2: GITHUB_RUN_ID-GITHUB_RUN_ATTEMPT (un re-run conserva el run_id y cambia el intento)."""
    env = os.environ if env is None else env
    if env.get("GITHUB_RUN_ID"):
        return f"{env['GITHUB_RUN_ID']}-{env.get('GITHUB_RUN_ATTEMPT') or '1'}"
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def bloques_vigente(root: Path) -> Path:
    c = sorted((root / "configuracion").glob("bloques_partidos_*.csv"))
    if not c:
        raise FileNotFoundError("Sin configuracion/bloques_partidos_*.csv")
    return c[-1]


def territorios_con_m08(root: Path, pedidos: str = "", eleccion: str = ELECCION_DEFECTO) -> list[tuple[str, str]]:
    """(id nuevo, run) del canonical_m08 vigente DE LA ELECCIÓN de cada territorio del Congreso (ámbito NAC por el resolutor, T-220).

    Vacío = todos; si no, los códigos pedidos (coma, id nuevo o legacy). Un `aut` o un id desconocido se rechaza (la tabla de bloques es de las
    generales). El run se elige con `resultados_ligeros.vigente_por_eleccion` (nunca el mayor entre elecciones); el registro del visor trae cada
    territorio con su id nuevo y con el legacy, y la clave de R2 (`<carpeta>/<run>/ddd-minimo-<run>-M08.zip`) la pone el archivista con el legacy: se
    encuentra por run en `archivo_r2.json`."""
    fecha = pr.fecha_eleccion(root, eleccion)
    prods = json.loads((root / PUBLICACIONES).read_text(encoding="utf-8"))["products"]
    vig: dict[str, str] = {}
    for t, p in rl.vigente_por_eleccion(prods, "canonical_m08", fecha, ambito="NAC").items():
        nuevo = territorio_ids.resolver_id(t)
        if nuevo not in vig or int(p["run_id"]) > int(vig[nuevo]):
            vig[nuevo] = str(p["run_id"])
    if not pedidos.strip():
        return sorted(vig.items())
    out = []
    for c in [c.strip() for c in pedidos.split(",") if c.strip()]:
        try:
            nuevo = territorio_ids.resolver_id(c)
        except (territorio_ids.IdTerritorioDesconocido, territorio_ids.IdReservado) as exc:
            raise ValueError(f"P75_TERRITORIO_INVALIDO: «{c}» ({exc})") from exc
        if territorio_ids.ambito(nuevo) != "NAC":
            raise ValueError(f"P75_FUERA_DE_ALCANCE: {c} no es del Congreso (solo nac; los aut esperan a la tabla de bloques de las autonómicas)")
        if nuevo not in vig:
            raise ValueError(f"P75_SIN_M08_VIGENTE: {c} no tiene M08 vigente de {eleccion}")
        out.append((nuevo, vig[nuevo]))
    return out


def _zip_determinista(destino: Path, ficheros: list[Path]) -> None:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(ficheros, key=lambda p: p.name):
            i = zipfile.ZipInfo(f.name, _FECHA_ZIP)
            i.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(i, f.read_bytes())


def procesar(root: Path, territorio: str, run: str, eleccion: str, trabajo: Path, cp=fuente_r2._cp) -> dict:
    """Un territorio. Devuelve su fila del informe; deja el ZIP en `trabajo/<territorio>/` si estado == OK."""
    fila = {"territorio": territorio, "run": run, "estado": "ERROR", "trae_m07": None, "sin_casar_pct": None, "sin_bloque_pct": None,
            "sha256_paquete_entrada": None, "sha256_salida": None, "carpeta_r2": None}
    man = json.loads((root / ARCHIVO).read_text(encoding="utf-8"))
    hallado = rr.buscar(run, "M08", man)
    if not hallado:
        fila["estado"] = "SIN_PAQUETE_EN_R2"
        return fila
    clave, ent = hallado
    if not territorio_ids.mismo_territorio(clave.split("/")[0], territorio):  # la carpeta del archivista (legacy) debe ser la del territorio pedido
        fila["estado"] = "CARPETA_NO_ES_DEL_TERRITORIO"
        return fila
    fila["carpeta_r2"] = clave.rsplit("/", 2)[0]
    fila["sha256_paquete_entrada"] = ent.get("sha256")
    estado = trabajo / territorio / "estado"
    rc = rr.restaurar(run, estado, ("M08",), root / ARCHIVO, cp)
    if rc != 0:
        fila["estado"] = "SHA_DISTINTO" if rc == 53 else "SIN_PAQUETE_EN_R2"
        return fila
    csvs = sorted((estado / f"ddd-state-{run}-M08").rglob(f"*{CSV_M07}"))
    fila["trae_m07"] = bool(csvs)
    if not csvs:
        fila["estado"] = "SIN_CSV_M07"
        return fila
    if len(csvs) > 1:
        fila["estado"] = "VARIOS_CSV_M07"
        return fila
    salida = trabajo / territorio / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    bl, al = bloques_vigente(root), root / ALIAS
    for src in (csvs[0], bl, al):  # rutas relativas y estables en los manifiestos
        (salida / (src.name if src is not csvs[0] else "m07_resultados_partido.csv")).write_bytes(src.read_bytes())
    cwd = os.getcwd()
    try:
        os.chdir(salida)
        c = cob.cobertura("m07_resultados_partido.csv", bl.name, eleccion, al.name)
        Path("cobertura.json").write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        dv.generar("m07_resultados_partido.csv", bl.name, eleccion, "doble_vuelta.csv", "manifiesto.json", "detalle.csv", al.name)
    except Exception as exc:  # noqa: BLE001 - una causa por territorio, el resto sigue
        fila["estado"] = f"ERROR: {type(exc).__name__}: {str(exc)[:200]}"
        return fila
    finally:
        os.chdir(cwd)
    fila["sin_casar_pct"], fila["sin_bloque_pct"] = c["pct_sin_casar"], c["pct_sin_bloque"]
    if c["pct_sin_casar"] > UMBRAL_SIN_CASAR:
        fila["estado"] = "COBERTURA_BAJA"  # elección distinta de la pedida o alias incompleto
        return fila
    paquete = salida / f"ddd-doble-vuelta-{run}.zip"
    _zip_determinista(paquete, [salida / n for n in ("doble_vuelta.csv", "detalle.csv", "cobertura.json", "manifiesto.json")])
    fila["sha256_salida"] = hashlib.sha256(paquete.read_bytes()).hexdigest()
    fila["estado"] = "OK"
    return fila


def ejecutar(root: Path, pedidos: str, eleccion: str, trabajo: Path, cp=fuente_r2._cp, subir=None, run_p75: str = "local", existe=None) -> dict:
    """`run_p75` (GITHUB_RUN_ID) entra en las claves de R2 para no sobrescribir nada: cada ejecución sube objetos nuevos."""
    eleccion = cob.normalizar_eleccion(eleccion or ELECCION_DEFECTO)
    filas = []
    for t, run in territorios_con_m08(root, pedidos, eleccion):
        f = procesar(root, t, run, eleccion, trabajo, cp)
        if f["estado"] == "OK" and subir:
            clave = f"{f['carpeta_r2']}/{run}/ddd-doble-vuelta-{run}-p75-{run_p75}.zip"  # carpeta y run: los del archivista (no propios)
            try:
                subir_nuevo(subir, existe or (lambda k: False), clave, trabajo / t / "salida" / f"ddd-doble-vuelta-{run}.zip", f["sha256_salida"])
                f["clave_r2"] = clave
            except FileExistsError:
                f["estado"] = "CLAVE_YA_EXISTE"
        filas.append(f)
        print(f"[p75] {t} run {run}: {f['estado']}" + (f" (sin casar {f['sin_casar_pct']} %)" if f["sin_casar_pct"] is not None else ""), flush=True)
    informe = {"schema": "ddd.p75-informe/1.0", "eleccion": eleccion, "run_p75": run_p75,
               "entradas": {"bloques": {"ruta": str(bloques_vigente(root).relative_to(root)), "sha256": dv.sha256(bloques_vigente(root))},
                            "alias": {"ruta": str(ALIAS), "sha256": dv.sha256(root / ALIAS)}},
               "territorios": filas, "ok": sum(f["estado"] == "OK" for f in filas), "total": len(filas)}
    return informe


def lineas_para_log(inf: dict, sha_informe: str, clave_informe: str) -> list[str]:
    """Lo que hay que fijar en el repo para publicar: clave y sha256 del INFORME y, por territorio, el sha256 y la clave de su ZIP."""
    out = [f"INFORME_CLAVE={clave_informe}", f"INFORME_SHA256={sha_informe}"]
    out += [f"P75_ZIP territorio={f['territorio']} run={f['run']} sha256={f.get('sha256_salida')} clave={f.get('clave_r2')}" for f in inf["territorios"]]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--territorios", default="", help="códigos separados por comas (vacío = todos los nac)")
    ap.add_argument("--eleccion", default="", help="AAAA-MM (vacío = 2023-07)")
    ap.add_argument("--salida", default="", help="directorio donde dejar INFORME.json y los ZIP (por defecto, temporal)")
    ap.add_argument("--sin-subir", action="store_true")
    a = ap.parse_args(argv)
    subir = existe = None
    if not a.sin_subir:
        bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
        if not bucket or not cuenta:
            print("::error title=P75_SIN_CREDENCIALES::faltan R2_BUCKET/R2_ACCOUNT_ID")
            return 3
        _, subir = ar.r2_cliente(bucket, cuenta)
        existe = r2_existe(bucket, cuenta)
    with tempfile.TemporaryDirectory() as td:
        trabajo = Path(a.salida) if a.salida else Path(td)
        trabajo.mkdir(parents=True, exist_ok=True)
        run_p75 = run_p75_de_entorno()
        inf = ejecutar(ROOT, a.territorios, a.eleccion, trabajo, subir=subir, run_p75=run_p75, existe=existe)
        ruta = trabajo / "INFORME.json"
        ruta.write_text(json.dumps(inf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        clave_informe = f"doble_vuelta/{inf['eleccion']}/{run_p75}/INFORME.json"
        if subir:
            try:
                subir_nuevo(subir, existe, clave_informe, ruta, dv.sha256(ruta))
            except FileExistsError as exc:
                print(f"::error title=P75_CLAVE_YA_EXISTE::{exc}")
                return 1
        print("\n".join(lineas_para_log(inf, dv.sha256(ruta), clave_informe if subir else "(sin subir)")))
        malos = [f for f in inf["territorios"] if f["estado"] != "OK"]
        for f in malos:
            print(f"::warning title=P75_{f['estado'].split(':')[0]}::{f['territorio']} run {f['run']}")
        print(f"[p75] {inf['ok']}/{inf['total']} OK")
        return 0 if not malos else 1


if __name__ == "__main__":
    sys.exit(main())
