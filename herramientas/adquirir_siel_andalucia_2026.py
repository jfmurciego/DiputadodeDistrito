#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://ws040.juntadeandalucia.es/siel-api/v1"
ELECTION_KEY = 202605
OFFICIAL_CANDIDATE_VOTES = 4_157_539
UA = {"User-Agent": "DDD-SIEL-Andalucia-2026/1.0"}
SECTION_LOCATOR_URL = "https://pub-36ce9aa148a348ae8d9b6686b7edf0c4.r2.dev/eleccionesdb-etl/data-raw/hechos/minsait/01-andalucia.csv"
SECTION_LOCATOR_SHA256 = "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21"
EXPECTED_SECTIONS = 6044


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


def _api_code(value: object, *, section: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Código vacío en índice de secciones")
    try:
        code = str(int(float(raw.replace(",", "."))))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Código no numérico en índice de secciones: {value!r}") from exc
    return code.zfill(4) if section else code


def load_section_locator(
    path: Path,
    *,
    expected_sha256: str | None = None,
    expected_sections: int = EXPECTED_SECTIONS,
) -> tuple[list[tuple[str, str, str, str]], dict]:
    if not path.is_file():
        raise ValueError(f"Índice de secciones ausente: {path}")
    actual_sha = sha256(path)
    if expected_sha256 and actual_sha != expected_sha256:
        raise ValueError("Huella gobernada del índice provisional de secciones modificada")
    sections: set[tuple[str, str, str, str]] = set()
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"codigo_provincia", "codigo_municipio", "codigo_distrito", "codigo_seccion"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Índice provisional sin coordenadas de sección: {reader.fieldnames}")
        for row in reader:
            sections.add((
                _api_code(row["codigo_provincia"]),
                _api_code(row["codigo_municipio"]),
                _api_code(row["codigo_distrito"]),
                _api_code(row["codigo_seccion"], section=True),
            ))
    if len(sections) != expected_sections:
        raise ValueError(f"Índice provisional: secciones={len(sections)} != {expected_sections}")
    tasks = sorted(sections, key=lambda x: tuple(int(v) for v in x))
    meta = {
        "role": "SECTION_LOCATOR_ONLY",
        "source_class": "PROVISIONAL",
        "publisher": "Minsait / EleccionesDB mirror",
        "url": SECTION_LOCATOR_URL,
        "sha256": actual_sha,
        "sections": len(tasks),
        "votes_consumed": False,
    }
    return tasks, meta


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



def _checkpoint_path(checkpoint_dir: Path, task: tuple[str, str, str, str]) -> Path:
    p, m, d, s = task
    return checkpoint_dir / f"{int(p):02d}-{int(m):03d}-{int(d):02d}-{int(s):04d}.json"


def _load_checkpoint(
    checkpoint_dir: Path,
    tasks: list[tuple[str, str, str, str]],
) -> tuple[list[dict], set[tuple[str, str, str, str]]]:
    expected = set(tasks)
    rows: list[dict] = []
    completed: set[tuple[str, str, str, str]] = set()
    if not checkpoint_dir.is_dir():
        return rows, completed
    for path in sorted(checkpoint_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_task = payload.get("section")
        votes = payload.get("votes")
        if not isinstance(raw_task, list) or len(raw_task) != 4 or not isinstance(votes, list):
            raise ValueError(f"Checkpoint SIEL inválido: {path}")
        task = tuple(str(x) for x in raw_task)
        if task not in expected:
            raise ValueError(f"Checkpoint SIEL ajeno al índice actual: {task}")
        if task in completed:
            raise ValueError(f"Checkpoint SIEL duplicado: {task}")
        p, m, d, s = task
        parsed = []
        for vote in votes:
            party = str((vote or {}).get("party") or "").strip()
            n = int((vote or {}).get("votes") or 0)
            if not party or n < 0:
                raise ValueError(f"Checkpoint SIEL con voto inválido: {path}")
            parsed.append({
                "province": p,
                "municipality": m,
                "district": d,
                "section": s,
                "party": party,
                "votes": n,
            })
        if not parsed:
            raise ValueError(f"Checkpoint SIEL sin candidaturas: {path}")
        rows.extend(parsed)
        completed.add(task)
    return rows, completed


def _write_checkpoint(
    checkpoint_dir: Path,
    task: tuple[str, str, str, str],
    votes: list[dict],
) -> None:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    target = _checkpoint_path(checkpoint_dir, task)
    tmp = target.with_suffix(".tmp")
    payload = {"section": list(task), "votes": votes}
    tmp.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)


def build(
    out_dir: Path,
    workers: int = 16,
    *,
    section_index: Path | None = None,
    expected_locator_sha256: str | None = None,
    resume: bool = False,
) -> dict:
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
        total_by_party = {r["party"]: int(r["votes"]) for r in total_votes}
        cera_by_party = {r["party"]: int(r["votes"]) for r in cera_votes}
        geocodable_by_party = {
            party: int(total_by_party.get(party, 0)) - int(cera_by_party.get(party, 0))
            for party in set(total_by_party) | set(cera_by_party)
        }
        if any(v < 0 for v in geocodable_by_party.values()):
            raise ValueError(f"Provincia {p}: CERA supera total para alguna candidatura")
        province_controls[str(p)] = {
            "province_name": prov.get("valor"),
            "candidate_votes_total": total,
            "candidate_votes_cera": cera,
            "candidate_votes_geocodable_expected": total - cera,
            "candidate_votes_total_by_party": total_by_party,
            "candidate_votes_cera_by_party": cera_by_party,
            "candidate_votes_geocodable_by_party": geocodable_by_party,
            "province_endpoint": total_url,
            "cera_endpoint": cera_url,
        }
        for r in total_votes:
            province_rows.append({"province": str(p), **r})
        for r in cera_votes:
            cera_rows.append({"province": str(p), **r})

    locator_meta = None
    if section_index is not None:
        tasks, locator_meta = load_section_locator(
            section_index,
            expected_sha256=expected_locator_sha256,
        )
        province_keys = {str(int(str(x["clave"]))) for x in provinces}
        locator_provinces = {p for p, _, _, _ in tasks}
        unknown = sorted(locator_provinces - province_keys, key=int)
        if unknown:
            raise ValueError(f"Índice de secciones contiene provincias ajenas a SIEL: {unknown}")
        if locator_provinces != province_keys:
            missing = sorted(province_keys - locator_provinces, key=int)
            raise ValueError(f"Índice de secciones no cubre todas las provincias SIEL: {missing}")
    else:
        tasks = []
        seen_sections: set[tuple[str, str, str, str]] = set()
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
                        if key in seen_sections:
                            raise ValueError(f"Sección duplicada: {key}")
                        seen_sections.add(key)
                        tasks.append(key)

    if not tasks:
        raise ValueError("SIEL no produjo secciones 2026")

    checkpoint_dir = out_dir / ".checkpoint-sections"
    rows: list[dict] = []
    completed_tasks: set[tuple[str, str, str, str]] = set()
    if resume:
        rows, completed_tasks = _load_checkpoint(checkpoint_dir, tasks)
        if completed_tasks:
            print(
                f"SIEL reanudación: {len(completed_tasks)}/{len(tasks)} secciones ya disponibles",
                file=sys.stderr,
                flush=True,
            )
    pending_tasks = [t for t in tasks if t not in completed_tasks]
    errors = []
    def one(t):
        p,m,d,s = t
        votes, url = get_scope("escrutinio/ambito/seccion", p, m, d, s)
        return t, votes, url

    completed = len(completed_tasks)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(one, t): t for t in pending_tasks}
        for fut in as_completed(futures):
            t = futures[fut]
            try:
                (p,m,d,s), votes, url = fut.result()
                normalized_votes = [{"party": r["party"], "votes": int(r["votes"])} for r in votes]
                _write_checkpoint(checkpoint_dir, t, normalized_votes)
                for r in normalized_votes:
                    rows.append({
                        "province": str(p),
                        "municipality": str(m),
                        "district": str(d),
                        "section": str(s),
                        "party": r["party"],
                        "votes": r["votes"],
                    })
                completed += 1
                if completed % 250 == 0 or completed == len(tasks):
                    print(
                        f"SIEL progreso: {completed}/{len(tasks)} secciones ({100.0*completed/len(tasks):.1f}%)",
                        file=sys.stderr,
                        flush=True,
                    )
            except Exception as exc:
                errors.append({"section": list(map(str,t)), "error": str(exc)})
                if len(errors) >= 20:
                    for f in futures: f.cancel()
                    break

    if errors:
        raise ValueError(
            f"Fallos SIEL ({len(errors)} primeros): {errors}. "
            f"Checkpoint conservado en {checkpoint_dir}; reanudar con --resume."
        )
    if completed != len(tasks):
        raise ValueError(f"SIEL incompleto: {completed}/{len(tasks)} secciones")
    if not rows:
        raise ValueError("SIEL produjo cero filas de votos")

    section_sum_by_province = {}
    section_party_by_province: dict[str, dict[str, int]] = {}
    for r in rows:
        p = r["province"]
        party = r["party"]
        votes = int(r["votes"])
        section_sum_by_province[p] = section_sum_by_province.get(p, 0) + votes
        bucket = section_party_by_province.setdefault(p, {})
        bucket[party] = bucket.get(party, 0) + votes

    for p, ctrl in province_controls.items():
        observed = section_sum_by_province.get(p, 0)
        expected = int(ctrl["candidate_votes_geocodable_expected"])
        observed_by_party = section_party_by_province.get(p, {})
        expected_by_party = {
            str(k): int(v)
            for k, v in (ctrl.get("candidate_votes_geocodable_by_party") or {}).items()
        }
        ctrl["candidate_votes_sections"] = observed
        ctrl["candidate_votes_sections_by_party"] = observed_by_party
        ctrl["reconciles_total"] = observed == expected
        ctrl["reconciles_parties"] = observed_by_party == expected_by_party
        ctrl["reconciles"] = ctrl["reconciles_total"] and ctrl["reconciles_parties"]
        if observed != expected:
            raise ValueError(f"Provincia {p}: secciones={observed} != total-CERA={expected}")
        if observed_by_party != expected_by_party:
            raise ValueError(
                f"Provincia {p}: distribución por candidatura no reconcilia con total provincial-CERA"
            )

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
        "sections": len(set(tasks)),
        "vote_rows": len(rows),
        "candidate_votes_sections": section_total,
        "candidate_votes_cera": cera_total,
        "candidate_votes_official": official_total,
        "province_controls": province_controls,
        "sections_sha256": sha256(csv_path),
        "cera_sha256": sha256(cera_path),
    }
    if locator_meta is not None:
        manifest["section_locator"] = locator_meta
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if checkpoint_dir.is_dir():
        for path in checkpoint_dir.glob("*.json"):
            path.unlink()
        checkpoint_dir.rmdir()
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--section-index", type=Path)
    ap.add_argument("--section-index-sha256")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build(
        args.out,
        args.workers,
        section_index=args.section_index,
        expected_locator_sha256=args.section_index_sha256,
        resume=args.resume,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
