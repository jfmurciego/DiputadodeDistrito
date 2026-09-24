from __future__ import annotations

import re
from pathlib import Path

import yaml

MASTER = Path("configuracion/catalogo_territorios_espana_2025.yaml")
CODE_RE = re.compile(r"^(\d{2})\s*·\s*(.+)$")


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def load_master(path: Path = MASTER) -> list[dict]:
    rows = _yaml(path).get("territories")
    if not isinstance(rows, list) or len(rows) != 19:
        raise ValueError("El catálogo territorial maestro debe contener exactamente 19 territorios")
    seen_ids: set[str] = set()
    seen_codes: set[str] = set()
    result: list[dict] = []
    for row in rows:
        territory_id = str(row.get("territory_id") or "")
        name = str(row.get("name") or "")
        code = str(row.get("autonomous_community_code_ine") or "")
        if not territory_id or not name:
            raise ValueError("Catálogo territorial maestro con identidad incompleta")
        if not re.fullmatch(r"\d{2}", code):
            raise ValueError(f"{territory_id}: autonomous_community_code_ine inválido: {code!r}")
        if territory_id in seen_ids:
            raise ValueError(f"territory_id duplicado: {territory_id}")
        if code in seen_codes:
            raise ValueError(f"autonomous_community_code_ine duplicado: {code}")
        seen_ids.add(territory_id)
        seen_codes.add(code)
        result.append(dict(row))
    expected = {f"{n:02d}" for n in range(1, 20)}
    if seen_codes != expected:
        raise ValueError(f"CODAUTO incompletos: esperados {sorted(expected)}, observados {sorted(seen_codes)}")
    return sorted(result, key=lambda row: row["autonomous_community_code_ine"])


def master_index(path: Path = MASTER) -> dict[str, dict]:
    return {row["territory_id"]: row for row in load_master(path)}


def format_territory_label(row: dict) -> str:
    return f"{row['autonomous_community_code_ine']} · {row['name']}"


def normalize_territory_input(value: str) -> str:
    text = str(value or "").strip()
    match = CODE_RE.fullmatch(text)
    return match.group(2).strip() if match else text


def resolve_master(value: str, path: Path = MASTER) -> dict:
    wanted = normalize_territory_input(value)
    matches = [
        row for row in load_master(path)
        if wanted in {str(row["territory_id"]), str(row["name"])}
    ]
    if len(matches) != 1:
        raise KeyError(f"Territorio no registrado de forma única: {value!r}")
    return matches[0]
