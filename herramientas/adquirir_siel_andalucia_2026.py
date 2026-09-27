#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://ws040.juntadeandalucia.es/siel-api/v1"
ELECTION_KEY = 202605
OFFICIAL_CANDIDATE_VOTES = 4_157_539
UA = {"User-Agent": "DDD-SIEL-Andalucia-2026/1.0"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch_json(endpoint: str, params: dict, timeout: int = 20, retries: int = 3):
    url = BASE + "/" + endpoint + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if getattr(r, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {getattr(r,'status',None)}")
                return json.loads(r.read().decode("utf-8")), url
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"{url}: {type(last).__name__}: {last}")


def options(endpoint: str, params: dict):
    payload, _ = fetch_json("opciones/" + endpoint, params)
    if not isinstance(payload, list):
        raise ValueError(f"Nomenclátor {endpoint} no es lista")
    return [x for x in payload if isinstance(x, dict) and str(x.get("clave") or "").strip()]


def parse_votes(payload: dict, expected: dict) -> list[dict]:
    ident = payload.get("idescrutinio") or {}
    fconv = ((ident.get("fconvocatoria") or {}).get("clave"))
    ca = ((ident.get("cautonoma") or {}).get("clave"))
    if int(fconv or 0) != ELECTION_KEY or int(ca or 0) != 1:
        raise ValueError(f"Identidad SIEL inesperada: fconv={fconv}, cautonoma={ca}")
    for field, value in expected.items():
        observed = ((ident.get(field) or {}).get("clave"))
        if str(observed).lstrip("0") != str(value).lstrip("0"):
            raise ValueError(f"Identidad {field} inesperada: {observed} != {value}")
    votes = payload.get("votos") or []
    if not isinstance(votes, list) or not votes:
        raise ValueError(f"SIEL sin votos para {expected}")
    out = []
    for row in votes:
        party = str(row.get("conjunto") or "").strip()
        if not party:
            raise ValueError(f"Fila SIEL sin candidatura: {row}")
        n = int(row.get("numvotos") or 0)
        if n < 0:
            raise ValueError(f"Votos negativos: {row}")
        out.append({"party": party, "votes": n})
    return out


def get_scope(endpoint: str, province, municipality=None, district=None, section=None):
    params = {"cautonoma": 1, "tconvocatoria": 5, "provincia": province, "fconvocatoria": ELECTION_KEY}
    expected = {"provincia": province}
    if municipality is not None:
        params["municipio"] = municipality
        expected["municipio"] = municipality
    if district is not None:
        params["distrito"] = district
        expected["distrito"] = district
    if section is not None:
        params["seccion"] = section
        expected["seccion"] = int(str(section))
    payload, url = fetch_json(endpoint, params)
    return parse_votes(payload, expected), url


def build(out_dir: Path, workers: int = 16) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    convocatorias = options("fconvocatoria", {"tconvocatoria": 5})
    if not any(int(x.get("clave") or 0) == ELECTION_KEY for x in convocatorias):
        raise ValueError("SIEL no contiene convocatoria 202605")

    provinces = options("provincia", {"cautonoma": 1})
    if len(provinces) != 8:
        raise ValueError(f"Se esperaban 8 provincias; SIEL devuelve {len(provinces)}")

    province_controls = {}
    province_rows = []
    cera_rows = []
    for prov in provinces:
        p = prov["clave"]
        total_votes, total_url = get_scope("escrutinio/ambito/provincia", p)
        cera_votes, cera_url = get_scope("escrutinio/ambito/rausentes/provincia", p)
        total = sum(x["votes"] for x in total_votes)
        cera = sum(x["votes"] for x in cera_votes)
        province_controls[str(p)] = {
            "province_name": prov.get("valor"),
            "candidate_votes_total": total,
            "candidate_votes_cera": cera,
            "candidate_votes_geocodable_expected": total - cera,
            "province_endpoint": total_url,
            "cera_endpoint": cera_url,
        }
        for r in total_votes:
            province_rows.append({"province": str(p), **r})
        for r in cera_votes:
            cera_rows.append({"province": str(p), **r})

    tasks = []
    section_meta = {}
    for prov in provinces:
        p = prov["clave"]
        municipalities = options("municipio", {
            "cautonoma": 1, "provincia": p, "tconvocatoria": 5, "fconvocatoria": ELECTION_KEY
        })
        for muni in municipalities:
            m = muni["clave"]
            districts = options("distrito", {
                "cautonoma": 1, "provincia": p, "tconvocatoria": 5,
                "fconvocatoria": ELECTION_KEY, "municipio": m
            })
            for dist in districts:
                d = dist["clave"]
                sections = options("seccion", {
                    "cautonoma": 1, "provincia": p, "tconvocatoria": 5,
                    "fconvocatoria": ELECTION_KEY, "municipio": m, "distrito": d
                })
                for sec in sections:
                    s = str(sec.get("valor") or sec.get("clave") or "").strip()
                    if not s:
                        raise ValueError(f"Sección vacía: {prov} {muni} {dist} {sec}")
                    key = (str(p), str(m), str(d), s)
                    if key in section_meta:
                        raise ValueError(f"Sección duplicada: {key}")
                    section_meta[key] = {
                        "province_name": prov.get("valor"),
                        "municipality_name": muni.get("valor"),
                        "district_name": dist.get("valor"),
                    }
                    tasks.append((p, m, d, s))

    if not tasks:
        raise ValueError("SIEL no produjo secciones 2026")

    rows = []
    errors = []
    def one(t):
        p,m,d,s = t
        votes, url = get_scope("escrutinio/ambito/seccion", p, m, d, s)
        return t, votes, url

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(one, t): t for t in tasks}
        for fut in as_completed(futures):
            t = futures[fut]
            try:
                (p,m,d,s), votes, url = fut.result()
                for r in votes:
                    rows.append({
                        "province": str(p),
                        "municipality": str(m),
                        "district": str(d),
                        "section": str(s),
                        "party": r["party"],
                        "votes": r["votes"],
                    })
            except Exception as exc:
                errors.append({"section": list(map(str,t)), "error": str(exc)})
                if len(errors) >= 20:
                    for f in futures: f.cancel()
                    break

    if errors:
        raise ValueError(f"Fallos SIEL ({len(errors)} primeros): {errors}")
    if not rows:
        raise ValueError("SIEL produjo cero filas de votos")

    section_sum_by_province = {}
    for r in rows:
        section_sum_by_province[r["province"]] = section_sum_by_province.get(r["province"], 0) + int(r["votes"])

    for p, ctrl in province_controls.items():
        observed = section_sum_by_province.get(p, 0)
        expected = int(ctrl["candidate_votes_geocodable_expected"])
        ctrl["candidate_votes_sections"] = observed
        ctrl["reconciles"] = observed == expected
        if observed != expected:
            raise ValueError(f"Provincia {p}: secciones={observed} != total-CERA={expected}")

    official_total = sum(int(x["candidate_votes_total"]) for x in province_controls.values())
    cera_total = sum(int(x["candidate_votes_cera"]) for x in province_controls.values())
    section_total = sum(int(x["votes"]) for x in rows)
    if official_total != OFFICIAL_CANDIDATE_VOTES:
        raise ValueError(f"SIEL total={official_total} != BOJA={OFFICIAL_CANDIDATE_VOTES}")
    if section_total + cera_total != official_total:
        raise ValueError(f"Reconciliación global: secciones={section_total} + CERA={cera_total} != {official_total}")

    csv_path = out_dir / "andalucia_2026_siel_secciones.csv"
    rows.sort(key=lambda x:(int(x["province"]),int(x["municipality"]),int(x["district"]),int(x["section"]),x["party"]))
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["province","municipality","district","section","party","votes"])
        w.writeheader(); w.writerows(rows)

    cera_path = out_dir / "andalucia_2026_siel_cera_provincias.csv"
    with cera_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["province","party","votes"])
        w.writeheader(); w.writerows(sorted(cera_rows,key=lambda x:(int(x["province"]),x["party"])))

    manifest = {
        "schema": "ddd-siel-andalucia-snapshot/1.0",
        "territory_id": "andalucia",
        "election_id": "andalucia_parlamento_2026",
        "election_date": "2026-05-17",
        "siel_election_key": ELECTION_KEY,
        "publisher": "Junta de Andalucía — Sistema de Información Electoral de Andalucía (SIEL)",
        "source_base": BASE,
        "official_reference": "https://www.juntadeandalucia.es/boja/2026/115/1",
        "sections": len(section_meta),
        "vote_rows": len(rows),
        "candidate_votes_sections": section_total,
        "candidate_votes_cera": cera_total,
        "candidate_votes_official": official_total,
        "province_controls": province_controls,
        "sections_sha256": sha256(csv_path),
        "cera_sha256": sha256(cera_path),
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    print(json.dumps(build(args.out, args.workers), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
