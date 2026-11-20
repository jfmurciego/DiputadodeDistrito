#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P75 Doble vuelta desde R2: calcula dv_base, dv_A y dv_B de cada territorio a partir del ddd-minimo-<run>-M08 archivado (T-418).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-20 · ESTADO: candidato
ANTERIOR: legacy/herramientas/p75_doble_vuelta_r2_v1.0.0_20261120.py
CAMBIOS: 1.1.0 (T-427, D-179/D-182/D-183): `--territorios aut` (o códigos aut): los 19 territorios autonómicos con su elección autonómica VIGENTE.
  El M08 de R2 de un aut lleva votos de las generales 2023-07 (no de la autonómica): se restaura igual (sha256) y se usa para comprobar el mapa
  (sus distritos deben ser EXACTAMENTE los del CSV de votos); los votos son los de la autonómica vigente reagregados a la composición del run M08
  vigente (datos/resultados/doble_vuelta_autonomicas/<aut>/<AAAAMM>/, `reagregacion_autonomicas.py --mapa-vigente` o T-426), con su MANIFEST
  (run_m08 y sha256 de la composición, que deben casar). Bloques y alias: los de las autonómicas filtrados por comunidad (`doble_vuelta --comunidad`).
  Ningún aut se calla: sin autonómicas (aut18, aut19) o fuera por decisión (aut11, D-183) → `NO_APLICA` con motivo (no cuenta como fallo);
  sin votos → `SIN_VOTOS_AUTONOMICOS` (fallo). Informe en `doble_vuelta/autonomicas/<run_p75>/INFORME.json`. nac y aut no se mezclan en una ejecución.
  Lo de los nac, idéntico. 1.0.0: fichero nuevo.
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
USO: python herramientas/p75_doble_vuelta_r2.py [--territorios nac01,nac02 | aut | aut01,aut02] [--eleccion 2023-07] [--salida DIR] [--sin-subir]
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
BLOQUES_AUT = Path("configuracion/bloques_partidos_autonomicas_2026-11-19.csv")
ALIAS_AUT = Path("configuracion/alias_partidos_autonomicas.csv")
VOTOS_AUT = Path("datos/resultados/doble_vuelta_autonomicas")
COMPOSICION_RUNS = Path("datos/composicion/MANIFEST_RUNS.json")
CALENDARIO = Path("configuracion/calendario_autonomicas.csv")
NO_APLICA = {"aut11": "fuera de la doble vuelta por decisión del propietario (D-183)",
             "aut18": "Ceuta no elige parlamento autonómico", "aut19": "Melilla no elige parlamento autonómico"}
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
            raise ValueError(f"P75_FUERA_DE_ALCANCE: {c} no es del Congreso (los aut van en su propia ejecución: `aut` o solo códigos aut)")
        if nuevo not in vig:
            raise ValueError(f"P75_SIN_M08_VIGENTE: {c} no tiene M08 vigente de {eleccion}")
        out.append((nuevo, vig[nuevo]))
    return out


def es_aut(pedidos: str) -> bool:
    """True si la ejecución es de los autonómicos (`aut`, o solo códigos aut); mezclar nac y aut se rechaza."""
    cs = [c.strip() for c in pedidos.split(",") if c.strip()]
    if [c.lower() for c in cs] == ["aut"]:
        return True
    amb = set()
    for c in cs:
        try:
            amb.add(territorio_ids.ambito(territorio_ids.resolver_id(c)))
        except (territorio_ids.IdTerritorioDesconocido, territorio_ids.IdReservado) as exc:
            raise ValueError(f"P75_TERRITORIO_INVALIDO: «{c}» ({exc})") from exc
    if len(amb) > 1:
        raise ValueError("P75_AMBITOS_MEZCLADOS: nac y aut van en ejecuciones distintas")
    return amb == {"AUT"}


def territorios_aut(root: Path, pedidos: str = "") -> list[tuple[str, str]]:
    """(aut, run) del canonical_m08 vigente (mapa de 2023-07) de TODOS los aut del registro (vacío o `aut`) o de los pedidos."""
    prods = json.loads((root / PUBLICACIONES).read_text(encoding="utf-8"))["products"]
    vig: dict[str, str] = {}
    for t, p in rl.vigente_por_eleccion(prods, "canonical_m08", pr.fecha_eleccion(root, ELECCION_DEFECTO), ambito="AUT").items():
        nuevo = territorio_ids.resolver_id(t)
        if nuevo not in vig or int(p["run_id"]) > int(vig[nuevo]):
            vig[nuevo] = str(p["run_id"])
    cs = [c.strip() for c in pedidos.split(",") if c.strip() and c.strip().lower() != "aut"]
    if not cs:
        return sorted(vig.items())
    out = []
    for c in cs:
        nuevo = territorio_ids.resolver_id(c)
        if nuevo not in vig:
            raise ValueError(f"P75_SIN_M08_VIGENTE: {c} no tiene M08 vigente")
        out.append((nuevo, vig[nuevo]))
    return out


def eleccion_vigente_aut(root: Path, aut: str) -> str | None:
    """AAAA-MM de la autonómica vigente del calendario (columna `vigente`), o None si la comunidad no tiene."""
    with open(root / CALENDARIO, encoding="utf-8", newline="") as f:
        v = [r["mes"] for r in csv.DictReader(f) if r["comunidad"] == aut and r.get("vigente") == "si"]
    if len(v) > 1:
        raise ValueError(f"P75_CALENDARIO_AMBIGUO: {aut} con {len(v)} elecciones vigentes")
    return v[0] if v else None


def _cobertura_aut(votos_csv: str, bloques: str, eleccion: str, alias: str, aut: str) -> dict:
    """Como doble_vuelta_cobertura.cobertura, con la tabla y el alias de la comunidad."""
    tabla = dv.cargar_tabla(bloques, eleccion, aut)
    por: dict[str, int] = {}
    for d in dv.aplicar_alias(dv.cargar_votos(votos_csv), dv.cargar_alias(alias, eleccion, aut)).values():
        for k, n in d.items():
            por[k] = por.get(k, 0) + n
    total = sum(por.values())
    sc = {k: n for k, n in por.items() if k not in tabla and n > 0}
    sb = sum(n for k, n in por.items() if k in tabla and not tabla[k])
    pct = lambda x: round(100 * x / total, 4) if total else 0.0  # noqa: E731
    return {"schema": "ddd.doble-vuelta-cobertura/1.0", "eleccion": eleccion, "comunidad": aut,
            "entradas": {"votos": {"ruta": votos_csv, "sha256": dv.sha256(votos_csv)}, "bloques": {"ruta": bloques, "sha256": dv.sha256(bloques)},
                         "alias": {"ruta": alias, "sha256": dv.sha256(alias)}},
            "votos_total": total, "votos_sin_casar": sum(sc.values()), "pct_sin_casar": pct(sum(sc.values())),
            "votos_sin_bloque": sb, "pct_sin_bloque": pct(sb),
            "partidos_sin_casar": [{"partido": k, "votos": n} for k, n in sorted(sc.items(), key=lambda a: (-a[1], a[0]))[:25]],
            "n_partidos_sin_casar": len(sc)}


def votos_aut(root: Path, aut: str, run: str, eleccion: str) -> tuple[Path | None, dict | None, str]:
    """(CSV distrito,partido,votos, MANIFEST, estado) de la autonómica vigente sobre el mapa del run M08; estado '' si vale."""
    carpeta = root / VOTOS_AUT / aut / eleccion.replace("-", "")
    csvp, manp = carpeta / f"{aut}_partidos.csv", carpeta / "MANIFEST.json"
    if not csvp.is_file() or not manp.is_file():
        return None, None, "SIN_VOTOS_AUTONOMICOS"
    man = json.loads(manp.read_text(encoding="utf-8"))
    fich = json.loads((root / COMPOSICION_RUNS).read_text(encoding="utf-8"))["ficheros"]
    ruta = str(man.get("composicion_ruta") or "")
    ent = fich.get(ruta.removeprefix("datos/composicion/"))
    sha_m = (man.get("fuentes") or {}).get("composicion") or man.get("composicion_sha256")
    if str(man.get("run_m08")) != run or not ent or str(ent.get("run_id")) != run or ent.get("territorio") != aut \
            or sha_m != ent.get("sha256_csv") or not (root / ruta).is_file() or dv.sha256(root / ruta) != sha_m:
        return None, man, "VOTOS_DE_OTRO_MAPA"
    if not (man.get("cuadre") or {}).get("ok"):
        return None, man, "CUADRE_NO_OK"
    return csvp, man, ""


def procesar_aut(root: Path, aut: str, run: str, trabajo: Path, cp=fuente_r2._cp) -> dict:
    """Un aut: misma fila que procesar() más `eleccion`, `motivo`, `aproximado_en_distrito` y `nivel` de los votos."""
    fila = {"territorio": aut, "run": run, "estado": "ERROR", "eleccion": None, "motivo": None, "trae_m07": None, "sin_casar_pct": None,
            "sin_bloque_pct": None, "aproximado_en_distrito": None, "nivel": None, "sha256_votos": None,
            "sha256_paquete_entrada": None, "sha256_salida": None, "carpeta_r2": None}
    if aut in NO_APLICA:
        fila.update(estado="NO_APLICA", motivo=NO_APLICA[aut])
        return fila
    ele = eleccion_vigente_aut(root, aut)
    if not ele:
        fila.update(estado="SIN_ELECCION_VIGENTE", motivo="sin elección autonómica vigente en configuracion/calendario_autonomicas.csv")
        return fila
    fila["eleccion"] = ele
    csvp, man, estado = votos_aut(root, aut, run, ele)
    if estado:
        fila.update(estado=estado, motivo={"SIN_VOTOS_AUTONOMICOS": f"sin {VOTOS_AUT}/{aut}/{ele.replace('-', '')}/ (votos por distrito del mapa vigente)",
                                           "VOTOS_DE_OTRO_MAPA": "los votos no son del mapa del run M08 vigente (run o sha256 de la composición)",
                                           "CUADRE_NO_OK": "el cuadre de votos de la reagregación no es correcto"}[estado])
        return fila
    c_ = man.get("cuadre") or {}
    fila.update(aproximado_en_distrito=bool(c_.get("aproximado_en_distrito")), nivel=c_.get("nivel"), sha256_votos=dv.sha256(csvp))
    man_r2 = json.loads((root / ARCHIVO).read_text(encoding="utf-8"))
    hallado = rr.buscar(run, "M08", man_r2)
    if not hallado:
        fila["estado"] = "SIN_PAQUETE_EN_R2"
        return fila
    clave, ent = hallado
    if not territorio_ids.mismo_territorio(clave.split("/")[0], aut):
        fila["estado"] = "CARPETA_NO_ES_DEL_TERRITORIO"
        return fila
    fila["carpeta_r2"], fila["sha256_paquete_entrada"] = clave.rsplit("/", 2)[0], ent.get("sha256")
    estado_dir = trabajo / aut / "estado"
    rc = rr.restaurar(run, estado_dir, ("M08",), root / ARCHIVO, cp)
    if rc != 0:
        fila["estado"] = "SHA_DISTINTO" if rc == 53 else "SIN_PAQUETE_EN_R2"
        return fila
    m07 = sorted((estado_dir / f"ddd-state-{run}-M08").rglob(f"*{CSV_M07}"))
    fila["trae_m07"] = bool(m07)
    if len(m07) != 1:
        fila["estado"] = "SIN_CSV_M07" if not m07 else "VARIOS_CSV_M07"
        return fila
    with open(m07[0], encoding="utf-8", newline="") as f:
        ids_mapa = {str(int(float(r["district_id"]))) for r in csv.DictReader(f)}
    salida = trabajo / aut / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    with open(csvp, encoding="utf-8", newline="") as f, open(salida / "votos_autonomica.csv", "w", encoding="utf-8", newline="") as g:
        w = csv.writer(g, lineterminator="\n")
        w.writerow(["district_id", "party", "votes"])
        ids_votos = set()
        for r in csv.DictReader(f):
            ids_votos.add(str(int(r["distrito"])))
            w.writerow([int(r["distrito"]), r["partido"], int(r["votos"])])
    if ids_votos != ids_mapa:
        fila.update(estado="DISTRITOS_NO_CASAN", motivo=f"distritos del M08 {len(ids_mapa)} y de los votos {len(ids_votos)} distintos")
        return fila
    bl, al = root / BLOQUES_AUT, root / ALIAS_AUT
    for src in (bl, al):
        (salida / src.name).write_bytes(src.read_bytes())
    cwd = os.getcwd()
    try:
        os.chdir(salida)
        c = _cobertura_aut("votos_autonomica.csv", bl.name, ele, al.name, aut)
        Path("cobertura.json").write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        dv.generar("votos_autonomica.csv", bl.name, ele, "doble_vuelta.csv", "manifiesto.json", "detalle.csv", al.name, aut)
    except Exception as exc:  # noqa: BLE001 - una causa por territorio, el resto sigue
        fila["estado"] = f"ERROR: {type(exc).__name__}: {str(exc)[:200]}"
        return fila
    finally:
        os.chdir(cwd)
    fila["sin_casar_pct"], fila["sin_bloque_pct"] = c["pct_sin_casar"], c["pct_sin_bloque"]
    if c["pct_sin_casar"] > UMBRAL_SIN_CASAR:
        fila["estado"] = "COBERTURA_BAJA"
        return fila
    paquete = salida / f"ddd-doble-vuelta-{run}.zip"
    _zip_determinista(paquete, [salida / n for n in ("doble_vuelta.csv", "detalle.csv", "cobertura.json", "manifiesto.json")])
    fila["sha256_salida"] = hashlib.sha256(paquete.read_bytes()).hexdigest()
    fila["estado"] = "OK"
    return fila


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
    aut = es_aut(pedidos)
    eleccion = "autonomicas" if aut else cob.normalizar_eleccion(eleccion or ELECCION_DEFECTO)
    filas = []
    for t, run in (territorios_aut(root, pedidos) if aut else territorios_con_m08(root, pedidos, eleccion)):
        f = procesar_aut(root, t, run, trabajo, cp) if aut else procesar(root, t, run, eleccion, trabajo, cp)
        if f["estado"] == "OK" and subir:
            clave = f"{f['carpeta_r2']}/{run}/ddd-doble-vuelta-{run}-p75-{run_p75}.zip"  # carpeta y run: los del archivista (no propios)
            try:
                subir_nuevo(subir, existe or (lambda k: False), clave, trabajo / t / "salida" / f"ddd-doble-vuelta-{run}.zip", f["sha256_salida"])
                f["clave_r2"] = clave
            except FileExistsError:
                f["estado"] = "CLAVE_YA_EXISTE"
        filas.append(f)
        print(f"[p75] {t} run {run}: {f['estado']}" + (f" (sin casar {f['sin_casar_pct']} %)" if f["sin_casar_pct"] is not None else ""), flush=True)
    bl, al = (root / BLOQUES_AUT, root / ALIAS_AUT) if aut else (bloques_vigente(root), root / ALIAS)
    informe = {"schema": "ddd.p75-informe/1.0", "eleccion": eleccion, "run_p75": run_p75,
               "entradas": {"bloques": {"ruta": str(bl.relative_to(root)), "sha256": dv.sha256(bl)},
                            "alias": {"ruta": str(al.relative_to(root)), "sha256": dv.sha256(al)}},
               "territorios": filas, "ok": sum(f["estado"] == "OK" for f in filas), "total": len(filas)}
    if aut:
        informe["no_aplica"] = sum(f["estado"] == "NO_APLICA" for f in filas)
    return informe


def lineas_para_log(inf: dict, sha_informe: str, clave_informe: str) -> list[str]:
    """Lo que hay que fijar en el repo para publicar: clave y sha256 del INFORME y, por territorio, el sha256 y la clave de su ZIP."""
    out = [f"INFORME_CLAVE={clave_informe}", f"INFORME_SHA256={sha_informe}"]
    out += [f"P75_ZIP territorio={f['territorio']} run={f['run']} sha256={f.get('sha256_salida')} clave={f.get('clave_r2')}" for f in inf["territorios"]]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--territorios", default="", help="códigos separados por comas (vacío = todos los nac; `aut` = todos los aut)")
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
        malos = [f for f in inf["territorios"] if f["estado"] not in ("OK", "NO_APLICA")]
        for f in malos:
            print(f"::warning title=P75_{f['estado'].split(':')[0]}::{f['territorio']} run {f['run']}")
        print(f"[p75] {inf['ok']}/{inf['total']} OK")
        return 0 if not malos else 1


if __name__ == "__main__":
    sys.exit(main())
