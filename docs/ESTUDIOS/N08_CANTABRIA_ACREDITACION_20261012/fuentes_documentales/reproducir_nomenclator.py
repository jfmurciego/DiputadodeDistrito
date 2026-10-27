#!/usr/bin/env python3
"""Versión0.1.0; nombre reproducir_nomenclator; fecha2026-10-12.
Alcance: evidencia Cantabria, diagnóstico; estadoDIAGNOSTIC.
Cambio/origen: herramienta nueva; motivo validar extracto INE, sin imputación.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as E
import zipfile
BASE = Path(__file__).resolve().parent
SOURCE = BASE / "INE_NOMENCLATOR_39_2025.xls"
with zipfile.ZipFile(SOURCE) as archive:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = ["".join(item.itertext()) for item in E.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    rows = []
    for row in E.fromstring(archive.read("xl/worksheets/sheet1.xml")).findall(".//m:row", ns):
        values = []
        for cell in row:
            node = cell.find("m:v", ns)
            value = node.text if node is not None else ""
            values.append(strings[int(value)] if cell.get("t") == "s" and value else value)
        if len(values) > 2 and values[1] in ["035", "061", "075", "101"]:
            rows.append(dict(zip(["CPRO", "CMUN", "unidad_poblacional", "total2025", "hombres2025", "mujeres2025"], values)))
result = {"source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "derivation": "OOXML sharedStrings + sheet1 XML sin librerías externas; filtrar CMUN035061075101", "rows": rows}
expected = json.loads((BASE / "EXTRACTO_NOMENCLATOR_4_MUNICIPIOS.json").read_text())
assert result == expected, "Extracto no reproducible"
municipality = next(row for row in rows if row["CMUN"] == "101" and row["unidad_poblacional"].startswith("000000 "))
assert municipality["total2025"] == "249"
assert sum(int(row["total2025"]) for row in rows if row["CMUN"] == "101" and row["unidad_poblacional"][:6].endswith("00") and not row["unidad_poblacional"].startswith("000000")) == 249
print("PASS: extracto idéntico; municipio39101=249; entidades singulares=249; sin CUSEC/partes en fuente")
