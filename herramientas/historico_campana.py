#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico de generales en el Gestor 2.0: plan y ejecución del paso A por provincia y elección (T-113).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS: 1.1.0 (T-123): soporta las cinco generales 2011-2023 (2011, 2015, 2016, 2019-04 y 2019-11) con el mismo paso A y
  la misma puerta; `plan` añade `prueba` (primer territorio, lote de prueba antes del resto).
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-10, D-12 y D-22 del propietario: la opción «histórico» del «0 Gestor de Campañas» ejecuta el paso A de T-83
  (reagregacion_historico.py --paquete + historico_m07m08.py) en las 52 provincias, una elección por campaña,
  empezando por 2019-11. Motor repetible: cada ejecución regenera desde fuentes con huella, nada se reutiliza.
CAMBIOS 1.1.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/historico_campana_v1.1.0_20261112.py
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
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402  (T-220: id viejo o nuevo)

ROOT = Path(__file__).resolve().parents[1]
SOPORTADAS = ("201111", "201512", "201606", "201904", "201911")
CLAVES = {"histórico: generales 2019-11": "201911", "histórico: generales 2019-04": "201904",
          "histórico: generales 2016": "201606", "histórico: generales 2015": "201512",
          "histórico: generales 2011": "201111"}
ESPEJO = "orchestracion/fuente_nazioenbehatokia.json"
INDEX = "datos_abiertos/INDEX.json"
INE = "https://www.ine.es/prodyser/cartografia/seccionado_{}.zip"
# Huellas de los seccionados INE históricos usados en T-85/T-83 (datos/resultados/historico/MANIFEST.json).
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


def requisitos(territorio: str, provincia: str, clave: str, root: Path = ROOT) -> list[str]:
    """Lo que falta para el paso A de un territorio (vacío si se puede ejecutar)."""
    falta = []
    if territorio not in _json(root, INDEX)["territorios"]:
        falta.append("sin M06 publicado (datos_abiertos/INDEX.json)")
    if not (root / f"datos/composicion/{territorio}.csv").is_file():
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
    e = _json(ROOT, INDEX)["territorios"][territorio]
    repo = os.environ.get("GITHUB_REPOSITORY", "jfmurciego/diputadodedistrito")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.raw"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return _bajar(f"https://api.github.com/repos/{repo}/git/blobs/{e['blob_sha']}", destino, e["sha256_origen"], h)


def _correr(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT).returncode


def ejecutar(territorio: str, provincia: str, clave: str, trabajo: Path, salida: Path) -> int:
    falta = requisitos(territorio, provincia, clave)
    if clave not in SOPORTADAS or falta:
        raise SystemExit(f"NO_SOPORTADO {territorio} {clave}: {'; '.join(falta) or 'elección no soportada'}")
    subprocess.run(["bash", str(ROOT / "inputs/partes/reconstruir_fuentes.sh")], check=True)
    seccionado, padron = ROOT / "inputs/seccionado_2025.zip", ROOT / "inputs/65034.csv.zip"
    espejo = _json(ROOT, ESPEJO)
    ruta = f"data/{clave}/sekzioa/{provincia}.json"
    _bajar(espejo["url"] + ruta, trabajo / "espejo" / ruta, espejo["ficheros"][ruta]["sha256"])
    hist = trabajo / "historicos"
    for año, h in HISTORICOS.items():
        _bajar(INE.format(año), hist / f"seccionado_{año}.zip", h)
    m06 = _m06(territorio, trabajo / f"{territorio}_m06.zip")
    paquete = trabajo / "paquete"
    rb = _correr(["herramientas/reagregacion_historico.py", "--espejo", str(trabajo / "espejo"), "--historicos",
                  str(hist), "--seccionado", str(seccionado), "--padron", str(padron), "--territorio", territorio,
                  "--provincia", provincia, "--distritos", str(m06), "--salida", str(salida), "--paquete",
                  str(paquete), "--elecciones", clave])
    ra = _correr(["herramientas/historico_m07m08.py", "--paquete", str(paquete), "--territorio", territorio,
                  "--seccionado", str(seccionado), "--distritos", str(m06), "--padron", str(padron),
                  "--trabajo", str(trabajo / "m07"), "--salida", str(salida)])
    puerta = {"territorio": territorio, "clave": clave, "paso_b_cuadre": rb == 0, "paso_a_m07": ra == 0}
    puerta["estado"] = "PASS" if rb == ra == 0 else "FAIL"
    (salida / f"PUERTA_{territorio}_{clave}.json").write_text(json.dumps(puerta, ensure_ascii=False, indent=1) + "\n",
                                                             encoding="utf-8")
    print(json.dumps(puerta, ensure_ascii=False), flush=True)
    return 0 if puerta["estado"] == "PASS" else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["ejecutar"])
    ap.add_argument("--territorio", required=True)
    ap.add_argument("--provincia", help="código INE de dos cifras (por defecto, el de la legislatura vigente)")
    ap.add_argument("--eleccion", required=True, help="clave del espejo, p. ej. 201911")
    ap.add_argument("--trabajo", type=Path, default=ROOT / ".cache/ddd/historico_campana")
    ap.add_argument("--salida", type=Path, default=ROOT / "salida_historico")
    a = ap.parse_args(argv)
    prov = a.provincia
    if not prov:
        import yaml
        cfg = yaml.safe_load((ROOT / "configuracion/legislatura_vigente.yaml").read_text(encoding="utf-8"))
        prov = next(r["codigo"] for r in cfg["territorios"] if mismo_territorio(str(r["territory_id"] or ""), str(a.territorio)))
    a.salida.mkdir(parents=True, exist_ok=True)
    return ejecutar(a.territorio, prov, a.eleccion, a.trabajo / a.territorio, a.salida)


if __name__ == "__main__":
    sys.exit(main())
