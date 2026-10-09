#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: migración temporal R015
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Migración sin privilegios de workflows
FECHA: 2026-09-11
ESTADO: temporal de un solo uso
QUÉ HACE: archiva y normaliza módulos, core, herramientas, configuración y procedimiento.sh.
CAMBIOS: excluye workflows y no se autoelimina; esas operaciones se harán con la conexión GitHub autorizada.
MOTIVO: GitHub Actions rechazó el push de v1.0.0 por carecer de permiso workflows.
ANTERIOR: legacy/herramientas/r015_patch_components_v1.0.0.py
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-09-11"
PY_TARGETS = [
    "modulos/01_preparar_base_territorial.py",
    "modulos/02_construir_adyacencias.py",
    "modulos/03_construir_grafo.py",
    "modulos/04_generar_semillas.py",
    "modulos/05_optimizar_distritos.py",
    "modulos/06_consolidar_distritos.py",
    "modulos/07_agregar_resultados_electorales.py",
    "modulos/08_integrar_resultados.py",
    "ddd_core/config.py",
    "herramientas/adquirir_fuentes_ine.py",
    "herramientas/calcular_clave_preparacion.py",
    "herramientas/generar_outputs_auditables.py",
    "herramientas/registrar_ejecucion.py",
    "herramientas/validar_ejecucion.py",
]


def get_version(text: str) -> str:
    m = re.search(r"(?m)^\s*#?\s*VERSIÓN:\s*(\d+\.\d+\.\d+)\s*$", text)
    if not m:
        raise RuntimeError("VERSIÓN SemVer no encontrada")
    return m.group(1)


def bump(v: str) -> str:
    a, b, c = map(int, v.split("."))
    return f"{a}.{b}.{c+1}"


def archive(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.read_bytes() != src.read_bytes():
            raise RuntimeError(f"legacy distinto ya existente: {dst}")
        return
    shutil.copy2(src, dst)


def legacy_path(rel: str, old: str) -> str:
    p = Path(rel)
    if p.parts[0] == "modulos":
        return f"legacy/modulo{p.name[:2]}/{p.stem}_v{old}.py"
    if p.parts[0] == "herramientas":
        return f"legacy/herramientas/{p.stem}_v{old}.py"
    if rel == "ddd_core/config.py":
        return f"legacy/core/config_v{old}.py"
    raise RuntimeError(rel)


def normalize_python(rel: str) -> tuple[str, str]:
    src = ROOT / rel
    text = src.read_text(encoding="utf-8")
    old = get_version(text)
    new = bump(old)
    prev = legacy_path(rel, old)
    archive(src, ROOT / prev)
    a = text.find('"""')
    b = text.find('"""', a + 3)
    if a < 0 or b < 0:
        raise RuntimeError(f"sin docstring de cabecera: {rel}")
    lines = text[a+3:b].strip("\n").splitlines()
    out = []
    got_v = got_name = False
    for line in lines:
        s = line.strip()
        if s.startswith("VERSIÓN:"):
            out.append(f"VERSIÓN: {new}")
            got_v = True
        elif s.startswith("NOMBRE DE VERSIÓN:"):
            out.append(f"NOMBRE DE VERSIÓN: {s.split(':',1)[1].strip()} — Gobernanza R015")
            got_name = True
        elif s.startswith("FECHA:"):
            out.append(f"FECHA: {DATE}")
        elif s.startswith(("ESTADO:", "CAMBIOS:", "CAMBIOS VS", "MOTIVO:", "ANTERIOR:", "VERSIÓN ANTERIOR:", "ORIGEN:", "POR QUÉ CAMBIA:")):
            continue
        else:
            out.append(line)
    if not got_v:
        raise RuntimeError(f"cabecera sin VERSIÓN: {rel}")
    if not got_name:
        out.insert(1, "NOMBRE DE VERSIÓN: Gobernanza R015")
    out += [
        "ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.",
        "CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.",
        "MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.",
        f"ANTERIOR: {prev}",
    ]
    updated = text[:a] + '"""\n' + "\n".join(out) + '\n"""' + text[b+3:]
    updated = re.sub(rf'(["\']version["\']\s*:\s*["\']){re.escape(old)}(["\'])', rf'\g<1>{new}\g<2>', updated)
    src.write_text(updated, encoding="utf-8")
    return old, new


def normalize_comments(rel: str, prev_template: str) -> tuple[str, str]:
    src = ROOT / rel
    text = src.read_text(encoding="utf-8")
    old = get_version(text)
    new = bump(old)
    prev = prev_template.format(old=old)
    archive(src, ROOT / prev)
    lines = text.splitlines()
    cut = 0
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#!"):
            cut = i + 1
            continue
        if line.startswith("#") or not line.strip():
            cut = i + 1
            continue
        break
    head, body = lines[:cut], lines[cut:]
    out = []
    for line in head:
        s = line.lstrip("# ").strip()
        if s.startswith("VERSIÓN:"):
            out.append(f"# VERSIÓN: {new}")
        elif s.startswith("NOMBRE DE VERSIÓN:"):
            out.append(f"# NOMBRE DE VERSIÓN: {s.split(':',1)[1].strip()} — Gobernanza R015")
        elif s.startswith("FECHA:"):
            out.append(f"# FECHA: {DATE}")
        elif s.startswith(("ESTADO:", "CAMBIOS:", "CAMBIOS VS", "MOTIVO:", "ANTERIOR:", "VERSIÓN ANTERIOR:", "POR QUÉ CAMBIA:")):
            continue
        else:
            out.append(line)
    out += [
        "# ESTADO: vigente — R015 de gobernanza; comportamiento heredado sin cambios.",
        "# CAMBIOS: normaliza metadatos y predecesor legacy; no cambia comportamiento.",
        "# MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.",
        f"# ANTERIOR: {prev}",
    ]
    src.write_text("\n".join(out + body) + "\n", encoding="utf-8")
    return old, new


def normalize_config() -> tuple[str, str]:
    rel = "configuracion/aragon_2025.yaml"
    src = ROOT / rel
    text = src.read_text(encoding="utf-8")
    old = get_version(text)
    new = bump(old)
    prev = f"legacy/configuracion/aragon_2025_v{old}.yaml"
    archive(src, ROOT / prev)
    lines = []
    for line in text.splitlines():
        s = line.lstrip("# ").strip()
        if line.startswith("#") and s.startswith("VERSIÓN:"):
            lines.append(f"# VERSIÓN: {new}")
        elif line.startswith("#") and s.startswith("NOMBRE DE VERSIÓN:"):
            lines.append(f"# NOMBRE DE VERSIÓN: {s.split(':',1)[1].strip()} — Gobernanza R015")
        elif line.startswith("#") and s.startswith("FECHA:"):
            lines.append(f"# FECHA: {DATE}")
        elif line.startswith("#") and s.startswith(("ESTADO:", "CAMBIOS", "MOTIVO:", "ANTERIOR:")):
            continue
        else:
            lines.append(line)
    i = lines.index("meta:")
    lines[i:i] = [
        "# ESTADO: vigente — R015 de gobernanza; parámetros funcionales idénticos a la versión anterior.",
        "# CAMBIOS: actualiza solo versión, estado y trazabilidad; ningún parámetro funcional cambia.",
        "# MOTIVO: alinear la configuración activa con R014 validado y la política R015.",
        f"# ANTERIOR: {prev}",
    ]
    updated = "\n".join(lines) + "\n"
    updated = re.sub(r"(?m)^(\s*schema_version:\s*)" + re.escape(old) + r"\s*$", rf"\g<1>{new}", updated)
    src.write_text(updated, encoding="utf-8")
    return old, new


def main() -> None:
    versions = {}
    for rel in PY_TARGETS:
        versions[rel] = normalize_python(rel)
    versions["configuracion/aragon_2025.yaml"] = normalize_config()
    versions["procedimiento.sh"] = normalize_comments("procedimiento.sh", "legacy/procedimiento/procedimiento_v{old}.sh")
    report = ROOT / "docs" / "R015_COMPONENTES_NORMALIZADOS.tsv"
    report.write_text("archivo\tanterior\tnueva\n" + "\n".join(f"{p}\t{o}\t{n}" for p,(o,n) in sorted(versions.items())) + "\n", encoding="utf-8")
    print(f"R015 normalizó {len(versions)} componentes no-workflow")

if __name__ == "__main__":
    main()
