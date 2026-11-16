#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico de generales en el Gestor 2.0: plan y ejecución del paso A por provincia y elección (T-113).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.3.0 · FECHA: 2026-11-15 · ESTADO: candidato
CAMBIOS 1.3.0 (T-334): `_m06` busca el territorio en datos_abiertos/INDEX.json con `en_mapa` (el Gestor pasa ids nacNN y el INDEX conserva los viejos: KeyError antes);
  `registro_tabla` verifica el sha256 de la tabla contra el de configuracion/equivalencia_seccionado_ine_<año>_a_2023.json (T-328)
  y falla cerrado (TABLA_SHA256_DISTINTO) si no coincide; la PUERTA vuelca `m07` (PASS o PASS_WITH_DECLARED_EXCEPTIONS, sin reducirlo a PASS) y
  `perdidos` (votos sin asignar) de la reconciliación de M07; pasa `--mapa` a historico_m07m08.py.
CAMBIOS 1.2.0 (T-329): `--mapa 2023` (por defecto, D-105): el paso A lleva los votos de cada sección histórica al mapa vigente 2023 con la
  tabla configuracion/equivalencia_seccionado_ine_<año>_a_2023.csv (T-328) y la regla de M07 7.4.0 (la sección partida va ENTERA al
  distrito de mayor población, sin repartir votos); el paquete lleva los votos por sección histórica y el contrato declara
  section_reconciliation.equivalence_table (M07 la aplica); la participación se lleva con la misma regla. `--mapa 2025` conserva el
  camino anterior (reagregación de T-83 con reparto por población). Con 2023 no hay paso B: la puerta es M07 PASS.
CAMBIOS: 1.1.0 (T-123): soporta las cinco generales 2011-2023 (2011, 2015, 2016, 2019-04 y 2019-11) con el mismo paso A y
  la misma puerta; `plan` añade `prueba` (primer territorio, lote de prueba antes del resto).
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-10, D-12 y D-22 del propietario: la opción «histórico» del «0 Gestor de Campañas» ejecuta el paso A de T-83
  (reagregacion_historico.py --paquete + historico_m07m08.py) en las 52 provincias, una elección por campaña,
  empezando por 2019-11. Motor repetible: cada ejecución regenera desde fuentes con huella, nada se reutiliza.
CAMBIOS 1.1.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/historico_campana_v1.2.0_20261114.py
QUÉ HACE: `plan(ids, eleccion)` comprueba por territorio lo que el paso A necesita (elección soportada, M06 publicado en
  datos_abiertos/INDEX.json, composición en datos/composicion/, fichero del espejo T-89 en su manifiesto) y devuelve la
  matriz; lo pedido y no soportado falla con NoDisponible; con «todos» se omite y se informa.
  `ejecutar` (un territorio, en el runner): reconstruye seccionado 2025 y padrón 65034 desde inputs/partes (sha256),
  baja el M06 del blob (sha256 contra INDEX), el fichero del espejo de la elección (sha256 del manifiesto) y los
  seccionados INE históricos (sha256 de T-83/T-85), ejecuta el paso A y deja el resultado en `--salida`.
  Puerta: código 0 solo si el cuadre del paso B es exacto, M07 da PASS y el ganador coincide con B en cada distrito.
NO HACE: publicar (la 04 del histórico no está adaptada: publicar = «sí» falla al planificar), ni escribir en
  datos/resultados/historico/ del repositorio (el resultado va al artefacto del run).
Uso: python herramientas/historico_campana.py ejecutar --territorio nac22 --eleccion 201911 --salida DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio, fichero_por_id, en_mapa  # noqa: E402  (T-220: id viejo o nuevo)

ROOT = Path(__file__).resolve().parents[1]
SOPORTADAS = ("201111", "201512", "201606", "201904", "201911")
CLAVES = {"histórico: generales 2019-11": "201911", "histórico: generales 2019-04": "201904",
          "histórico: generales 2016": "201606", "histórico: generales 2015": "201512",
          "histórico: generales 2011": "201111"}
ESPEJO = "orchestracion/fuente_nazioenbehatokia.json"
INDEX = "datos_abiertos/INDEX.json"
INE = "https://www.ine.es/prodyser/cartografia/seccionado_{}.zip"
# Huellas de los seccionados INE históricos usados en T-85/T-83 (datos/resultados/historico/MANIFEST.json).
# clave de elección del espejo → año del seccionado INE de esa elección (T-306 §3); la tabla año→2023 es de T-328.
ANIO_SECCIONADO = {"201111": "2012", "201512": "2015", "201606": "2016", "201904": "2019", "201911": "2020"}
SHA_2023 = "7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f"
MAPAS = ("2023", "2025")
HISTORICOS = {
    "2012": "772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a",
    "2015": "50dda58ed4afb57c7f1f38e6b6b8150768efaa225bfc3a523b9c210a2a218c03",
    "2016": "3410af763bfe58d1b0f9c0d0038cbdd6417e0f3f6d0fce6a3e70bef64c84b3e1",
    "2019": "656119dadadb57ef3fa9d20a8ba33399fe606e553c9fef3fc338786e52fae967",
    "2020": "07544bb49256e9e9f290b6f459a0a833e69c97900eb840c3f5bbe863914ede6e",
    "2024": "df931fa0d372808eb81abb2f2645ed5ecccbd6ed397b85db656980748ddd6bf7",
}


class NoDisponible(ValueError):
    """Histórico pedido que todavía no se puede lanzar."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _json(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def tabla_2023(clave: str, root: Path = ROOT) -> Path:
    return root / f"configuracion/equivalencia_seccionado_ine_{ANIO_SECCIONADO[clave]}_a_2023.csv"


def registro_tabla(tabla: Path, root: Path = ROOT) -> dict:
    """Registro `section_reconciliation.equivalence_table` del contrato (ruta relativa al repo, sha256 y columnas). El sha256 se
    comprueba contra el que fija el JSON de la tabla (T-328): no se acepta una tabla que solo coincide consigo misma."""
    real = sha256(tabla)
    ficha = tabla.with_suffix(".json")
    esperado = (json.loads(ficha.read_text(encoding="utf-8")).get("csv") or {}).get("sha256") if ficha.is_file() else None
    if real != esperado:
        raise SystemExit(f"TABLA_SHA256_DISTINTO {tabla.name}: {real} != {esperado} ({ficha.name})")
    with tabla.open(encoding="utf-8", newline="") as fh:
        cab = next(csv.reader(fh))
    return {"path": tabla.resolve().relative_to(root.resolve()).as_posix(), "sha256": real,
            "source_column": cab[0], "target_column": cab[1], "decision": "D-105"}


def puerta_json(territorio: str, clave: str, mapa: str, ra: int, rb: int | None, salida: Path, extra: dict | None = None) -> dict:
    """PUERTA del paso A. `m07` y `perdidos` salen de la reconciliación que deja historico_m07m08.py: el estado de M07 se
    vuelca tal cual (PASS_WITH_DECLARED_EXCEPTIONS no se reduce a PASS) y `perdidos` son los votos sin asignar."""
    ruta = salida / clave / territorio / "reconciliacion.json"
    rec = json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else {}
    ok = ra == 0 and (rb is None or rb == 0)
    return {"territorio": territorio, "clave": clave, "mapa": mapa, "paso_b_cuadre": None if rb is None else rb == 0,
            "paso_a_m07": ra == 0, "m07": rec.get("status"), "perdidos": rec.get("ddd_unassigned_votes"),
            **(extra or {}), "estado": "PASS" if ok else "FAIL"}


def leer_tabla(tabla: Path) -> dict:
    """{sección histórica: {"tipo", "pesos": [(sección 2023, peso_poblacion)]}} (sin_vigente, sin pesos)."""
    out: dict = {}
    with tabla.open(encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        origen, destino = r.fieldnames[0], r.fieldnames[1]
        for f in r:
            e = out.setdefault(f[origen], {"tipo": f["tipo"], "pesos": []})
            if f["tipo"] != "sin_vigente":
                e["pesos"].append((f[destino], float(f["peso_poblacion"])))
    return out


def seccion_destino(entrada: dict, distrito_de: dict) -> str | None:
    """Regla de M07 7.4.0 (`apply_section_equivalence`): sin repartir votos; una partida va ENTERA al distrito con la mayor
    población y, dentro de él, a su sección de mayor peso. None = no se mueve (sin_vigente o destino fuera del mapa)."""
    if entrada["tipo"] == "sin_vigente":
        return None
    falta = "\x00MISSING_IN_MAP"
    por_distrito: dict = {}
    for t, w in entrada["pesos"]:
        k = distrito_de.get(t, falta)
        por_distrito[k] = por_distrito.get(k, 0.0) + w
    d = min(por_distrito, key=lambda x: (-por_distrito[x], x == falta, x))
    if d == falta:
        return None
    return min((tw for tw in entrada["pesos"] if distrito_de.get(tw[0]) == d), key=lambda tw: (-tw[1], tw[0]))[0]


def paquete_2023(carpeta: Path, territorio: str, clave: str, votos: dict, composicion: dict, ruta_espejo: str,
                 huella_espejo: str, oficial: dict | None = None, root: Path = ROOT) -> dict:
    """Paquete M07 de una elección sobre el mapa 2023 (D-105). `votos` = {sección histórica: {censo, votantes,
    votos_candidaturas, votos}} del espejo T-89, SIN reagregar: `secciones.csv` lleva los votos por sección histórica y M07
    los lleva al mapa con la tabla (contrato `section_reconciliation.equivalence_table`). `participacion.csv` se lleva con la
    misma regla (`composicion` = {sección 2023: (distrito, población)})."""
    sys.path.insert(0, str(root / "herramientas"))
    import reagregacion_historico as rh
    import fuente_nazioenbehatokia as fnb  # noqa: F401
    tabla = tabla_2023(clave, root)
    t = leer_tabla(tabla)
    distrito_de = {s: d for s, (d, _) in composicion.items()}
    part: dict = {}
    for s, r in votos.items():
        dest = seccion_destino(t[s], distrito_de) if s in t else s
        k = dest if dest is not None else s
        acc = part.setdefault(k, {c: 0 for c in rh.CAMPOS})
        for c in rh.CAMPOS:
            acc[c] += int(r[c])
    sec = {s: {"votos": r["votos"], **{c: int(r[c]) for c in rh.CAMPOS}} for s, r in votos.items()}
    huellas = rh.escribir_paquete(carpeta, territorio, clave, sec, oficial,
                                  {"path": ruta_espejo, "sha256": huella_espejo, "manifest": ESPEJO})
    # participación ya sobre el mapa 2023 (M07 solo mueve votos por partido); contrato con la tabla declarada
    with open(carpeta / "participacion.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["section_id", *rh.CAMPOS])
        for k in sorted(part):
            w.writerow([k, *(part[k][c] for c in rh.CAMPOS)])
    con = carpeta / "contrato.json"
    c = json.loads(con.read_text(encoding="utf-8"))
    c["section_reconciliation"] = {"equivalence_table": registro_tabla(tabla, root)}
    c["title"] = c["title"].replace("histórico reagregado (T-83)", "histórico sobre el mapa 2023 (T-329)")
    con.write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    huellas["participacion.csv"], huellas["contrato.json"] = sha256(carpeta / "participacion.csv"), sha256(con)
    return huellas


def requisitos(territorio: str, provincia: str, clave: str, root: Path = ROOT) -> list[str]:
    """Lo que falta para el paso A de un territorio (vacío si se puede ejecutar)."""
    falta = []
    if en_mapa(_json(root, INDEX)["territorios"], territorio) is None:
        falta.append("sin M06 publicado (datos_abiertos/INDEX.json)")
    if not fichero_por_id(root / "datos/composicion", "{}.csv", territorio).is_file():
        falta.append("sin composición (datos/composicion/)")
    if f"data/{clave}/sekzioa/{provincia}.json" not in _json(root, ESPEJO)["ficheros"]:
        falta.append(f"sin fichero del espejo T-89 para {clave}")
    return falta


def plan(eleccion: str, filas: list[dict], explicito: bool, root: Path = ROOT) -> dict:
    """filas = [{territory_id, codigo}] de la legislatura vigente (nacional). Devuelve la matriz del paso A."""
    clave = CLAVES[eleccion]
    if clave not in SOPORTADAS:
        raise NoDisponible(f"«{eleccion}» aún no está soportado en el Gestor (soportadas: "
                           f"{', '.join(SOPORTADAS)}).")
    ok, omitidos = [], {}
    for f in filas:
        falta = requisitos(f["territory_id"], f["codigo"], clave, root)
        if falta:
            omitidos[f["territory_id"]] = "; ".join(falta)
        else:
            ok.append({"territorio": f["territory_id"], "provincia": f["codigo"]})
    if omitidos and explicito:
        raise NoDisponible("Histórico no disponible para: " + " · ".join(f"{t}: {m}" for t, m in omitidos.items()))
    if not ok:
        raise NoDisponible("Ningún territorio de la selección tiene lo necesario para el histórico.")
    return {"clave": clave, "eleccion": eleccion, "prueba": ok[0], "include": ok, "omitidos": omitidos}


def plan_markdown(p: dict) -> str:
    lines = [f"Histórico {p['eleccion']} (clave {p['clave']}), paso A por territorio: reagregación a la sección "
             "vigente → M07/M08 sobre el M06 publicado. Puerta: cuadre exacto, M07 PASS y mismo ganador que el paso B. "
             "Resultado en el artefacto del run; no publica.",
             f"Lote de prueba: {p['prueba']['territorio']} (el resto solo corre si pasa la puerta).", "",
             "| Territorio | Provincia |", "|---|---|"]
    lines += [f"| {r['territorio']} | {r['provincia']} |" for r in p["include"]]
    if p["omitidos"]:
        lines += ["", "Omitidos (no soportados todavía):", ""]
        lines += [f"- {t}: {m}" for t, m in p["omitidos"].items()]
    return "\n".join(lines) + "\n"


# --- ejecución en el runner ---------------------------------------------------------------------------------------
def _bajar(url: str, destino: Path, esperado: str, headers: dict | None = None) -> Path:
    if destino.exists() and sha256(destino) == esperado:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ddd-historico", **(headers or {})})
            with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
                for b in iter(lambda: r.read(1 << 20), b""):
                    f.write(b)
            break
        except OSError as exc:
            if i == 4:
                raise SystemExit(f"DESCARGA_FALLIDA {url}: {exc}")
            import time
            time.sleep(2 ** (i + 1))
    if sha256(destino) != esperado:
        raise SystemExit(f"HUELLA_DISTINTA {url}: {sha256(destino)} != {esperado}")
    return destino


def _m06(territorio: str, destino: Path) -> Path:
    e = en_mapa(_json(ROOT, INDEX)["territorios"], territorio)  # INDEX sigue con ids viejos; el Gestor pasa nacNN
    if e is None:
        raise SystemExit(f"SIN_M06_PUBLICADO {territorio}")
    repo = os.environ.get("GITHUB_REPOSITORY", "jfmurciego/diputadodedistrito")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.raw"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return _bajar(f"https://api.github.com/repos/{repo}/git/blobs/{e['blob_sha']}", destino, e["sha256_origen"], h)


def _correr(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT).returncode


def ejecutar(territorio: str, provincia: str, clave: str, trabajo: Path, salida: Path, mapa: str = "2023") -> int:
    if mapa not in MAPAS:
        raise SystemExit(f"MAPA_NO_SOPORTADO {mapa}: {', '.join(MAPAS)}")
    falta = requisitos(territorio, provincia, clave)
    if mapa == "2023" and clave in SOPORTADAS and not tabla_2023(clave).is_file():
        falta.append(f"sin tabla año→2023 ({tabla_2023(clave).name})")
    if clave not in SOPORTADAS or falta:
        raise SystemExit(f"NO_SOPORTADO {territorio} {clave}: {'; '.join(falta) or 'elección no soportada'}")
    subprocess.run(["bash", str(ROOT / "inputs/partes/reconstruir_fuentes.sh")], check=True)
    seccionado, padron = ROOT / "inputs/seccionado_2025.zip", ROOT / "inputs/65034.csv.zip"
    espejo = _json(ROOT, ESPEJO)
    ruta = f"data/{clave}/sekzioa/{provincia}.json"
    _bajar(espejo["url"] + ruta, trabajo / "espejo" / ruta, espejo["ficheros"][ruta]["sha256"])
    hist = trabajo / "historicos"
    for año, h in (HISTORICOS if mapa == "2025" else {}).items():  # con 2023 basta la tabla versionada (T-328)
        _bajar(INE.format(año), hist / f"seccionado_{año}.zip", h)
    m06 = _m06(territorio, trabajo / f"{territorio}_m06.zip")
    paquete = trabajo / "paquete"
    if mapa == "2023":
        return _paso_a_2023(territorio, provincia, clave, trabajo, salida, m06, padron, trabajo / "espejo" / ruta,
                            espejo["ficheros"][ruta]["sha256"], ruta)
    rb = _correr(["herramientas/reagregacion_historico.py", "--espejo", str(trabajo / "espejo"), "--historicos",
                  str(hist), "--seccionado", str(seccionado), "--padron", str(padron), "--territorio", territorio,
                  "--provincia", provincia, "--distritos", str(m06), "--salida", str(salida), "--paquete",
                  str(paquete), "--elecciones", clave])
    ra = _correr(["herramientas/historico_m07m08.py", "--paquete", str(paquete), "--territorio", territorio,
                  "--seccionado", str(seccionado), "--distritos", str(m06), "--padron", str(padron),
                  "--trabajo", str(trabajo / "m07"), "--salida", str(salida)])
    puerta = puerta_json(territorio, clave, "2025", ra, rb, salida)
    (salida / f"PUERTA_{territorio}_{clave}.json").write_text(json.dumps(puerta, ensure_ascii=False, indent=1) + "\n",
                                                             encoding="utf-8")
    print(json.dumps(puerta, ensure_ascii=False), flush=True)
    return 0 if puerta["estado"] == "PASS" else 1


def _paso_a_2023(territorio, provincia, clave, trabajo, salida, m06, padron, fichero_espejo, huella, ruta) -> int:
    """D-105: sin paso B (el reparto por población de la reagregación a 2025 no se usa); la puerta es M07 PASS."""
    sys.path.insert(0, str(ROOT / "herramientas"))
    import fuente_nazioenbehatokia as fnb
    import historico_m07m08 as hm
    s2023 = _bajar(INE.format("2023"), trabajo / "historicos" / "seccionado_2023.zip", SHA_2023)
    comp = hm.leer_composicion(fichero_por_id(ROOT / "datos/composicion", "{}.csv", territorio))
    votos = fnb.leer_provincia(json.loads(fichero_espejo.read_text(encoding="utf-8")))
    import reagregacion_historico as rh
    paquete = trabajo / "paquete"
    paquete_2023(paquete / clave / territorio, territorio, clave, votos, comp, ruta, huella, rh.leer_oficial(clave, provincia))
    ra = _correr(["herramientas/historico_m07m08.py", "--paquete", str(paquete), "--territorio", territorio,
                  "--seccionado", str(s2023), "--distritos", str(m06), "--padron", str(padron),
                  "--trabajo", str(trabajo / "m07"), "--salida", str(salida),
                  "--mapa", "2023"])
    puerta = puerta_json(territorio, clave, "2023", ra, None, salida, {"tabla": registro_tabla(tabla_2023(clave))["sha256"]})
    (salida / f"PUERTA_{territorio}_{clave}.json").write_text(json.dumps(puerta, ensure_ascii=False, indent=1) + "\n",
                                                             encoding="utf-8")
    print(json.dumps(puerta, ensure_ascii=False), flush=True)
    return 0 if ra == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["ejecutar"])
    ap.add_argument("--territorio", required=True)
    ap.add_argument("--provincia", help="código INE de dos cifras (por defecto, el de la legislatura vigente)")
    ap.add_argument("--eleccion", required=True, help="clave del espejo, p. ej. 201911")
    ap.add_argument("--mapa", choices=MAPAS, default="2023", help="mapa destino (D-105: 2023; 2025 = reagregación de T-83)")
    ap.add_argument("--trabajo", type=Path, default=ROOT / ".cache/ddd/historico_campana")
    ap.add_argument("--salida", type=Path, default=ROOT / "salida_historico")
    a = ap.parse_args(argv)
    prov = a.provincia
    if not prov:
        import yaml
        cfg = yaml.safe_load((ROOT / "configuracion/legislatura_vigente.yaml").read_text(encoding="utf-8"))
        prov = next(r["codigo"] for r in cfg["territorios"] if mismo_territorio(str(r["territory_id"] or ""), str(a.territorio)))
    a.salida.mkdir(parents=True, exist_ok=True)
    return ejecutar(a.territorio, prov, a.eleccion, a.trabajo / a.territorio, a.salida, a.mapa)


if __name__ == "__main__":
    sys.exit(main())
