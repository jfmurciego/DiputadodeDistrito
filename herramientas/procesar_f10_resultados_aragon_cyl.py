#!/usr/bin/env python3
"""F10_PROCESSOR — version 1.0.0 (2026-10-20).

Scope: normalize and reconcile official 2026 election result sources for Aragón
and Castilla y León. New utility; no predecessor. This processor does not
resolve temporal section correspondence or promote electoral admissibility.

Normalización reproducible de los originales electorales oficiales de Aragón y CYL 2026.

La herramienta conserva CERA separado como control por provincia en Aragón. En
Castilla y León mantiene los códigos especiales presentes en la publicación,
sin asignarlos a secciones geográficas. Nunca estima ni redistribuye votos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/AUDITORIAS/F10_ELECTORAL_TRES_TERRITORIOS_20261020"
ARAGON_RAW = EVIDENCE / "originales/aragon"
CYL_RAW = EVIDENCE / "originales/castilla_y_leon"

ARAGON_XLS_PARTIES = {
    "PSOE": "PSOE", "ETXSBC": "ETXSBC", "COALICIÓN ARAGONESA": "COALICION_ARAGONESA",
    "CHA": "CHA", "PODEMOS -AV": "PODEMOS_AV", "VOX": "VOX", "PAR": "PAR",
    "PP": "PP", "PACMA": "PACMA", "EXISTE": "EXISTE", "ESCAÑOS EN BLANCO": "ESCANOS_EN_BLANCO",
    "IU- MOVIMIENTO SUMAR": "IU_MOVIMIENTO_SUMAR", "MUNDO+JUSTO": "MUNDO_MAS_JUSTO",
    "SALF": "SALF", "PCTE": "PCTE",
}
ARAGON_OD_PARTIES = {
    "PARTIDO SOCIALISTA OBRERO ESPAÑOL": "PSOE",
    "ENTRE TODOS BAJO / BAIX CINCA": "ETXSBC",
    "COALICIÓN ARAGONESA": "COALICION_ARAGONESA",
    "CHUNTA ARAGONESISTA": "CHA",
    "PODEMOS - ALIANZA VERDE": "PODEMOS_AV",
    "VOX": "VOX", "PARTIDO ARAGONES REGIONALISTA": "PAR", "PARTIDO POPULAR": "PP",
    "PARTIDO ANIMALISTA CON EL MEDIO AMBIENTE": "PACMA",
    "TERUEL EXISTE-COALICIÓN EXISTE": "EXISTE",
    "ESCAÑOS EN BLANCO PARA DEJAR ESCAÑOS VACÍOS": "ESCANOS_EN_BLANCO",
    "IZQUIERDA UNIDA- MOVIMIENTO SUMAR": "IU_MOVIMIENTO_SUMAR",
    "POR UN MUNDO MAS JUSTO": "MUNDO_MAS_JUSTO", "SE ACABÓ LA FIESTA": "SALF",
    # El CSV publicado trae mojibake en este único nombre; el código de candidatura y
    # el cotejo completo con el XLS provincial identifican la candidatura PCTE.
    "PARTIDO COMUNISTA DE LOS TRABAJADORES DE ESPAÃ‘A": "PCTE",
}
ARAGON_PROVINCES = {
    "Huesca": ("22", "DatEscrut_Def_Auto_2026_Huesca.xls"),
    "Teruel": ("44", "DatEscrut_Def_Auto_2026_Teruel.xls"),
    "Zaragoza": ("50", "DatEscrut_Def_Auto_2026_Zaragoza.xls"),
}
CYL_PROVINCES = {"Ávila":"05", "Burgos":"09", "León":"24", "Palencia":"34",
                 "Salamanca":"37", "Segovia":"40", "Soria":"42", "Valladolid":"47", "Zamora":"49"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonnegative_int(value: object, label: str) -> int:
    try:
        number = int(float(value or 0))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label}: valor no entero {value!r}") from exc
    if float(value or 0) != number or number < 0:
        raise ValueError(f"{label}: valor negativo o fraccionario {value!r}")
    return number


def aragon_cusec(province: str, municipality: object, mesa: str) -> str:
    match = re.fullmatch(r"(\d{1,2})-(\d{3})-([A-Z])", mesa.strip())
    if not match:
        raise ValueError(f"Mesa Aragón inválida: {mesa!r}")
    district, section, _poll = match.groups()
    province_code = str(province).zfill(2)
    municipality_code = nonnegative_int(municipality, "Aragón Codmun")
    if not province_code.isdigit() or len(province_code) != 2 or municipality_code > 999:
        raise ValueError(f"Identidad provincial/municipal Aragón inválida: {province}/{municipality}")
    if int(district) < 1 or int(section) < 1:
        raise ValueError(f"Distrito/sección Aragón fuera de rango: {mesa!r}")
    return f"{province_code}{municipality_code:03d}{int(district):02d}{int(section):03d}"


def cyl_cusec(province_name: str, municipality: object, district: object, section: object) -> str:
    province = CYL_PROVINCES.get(province_name)
    if province is None:
        raise ValueError(f"Provincia CYL no declarada: {province_name!r}")
    municipality_code = nonnegative_int(municipality, "CYL código municipio")
    district_code = nonnegative_int(district, "CYL distrito")
    section_code = nonnegative_int(section, "CYL sección")
    if municipality_code > 999 or not 1 <= district_code <= 99 or not 1 <= section_code <= 999:
        raise ValueError(f"Identidad municipal/seccional CYL fuera de rango: {municipality}/{district}/{section}")
    return f"{province}{municipality_code:03d}{district_code:02d}{section_code:03d}"


def write_long(path: Path, votes: Counter, separator: str, key_field: str = "CUSEC_KEY") -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=separator, lineterminator="\n")
        writer.writerow([key_field, "party", "votes"])
        for (section, party), value in sorted(votes.items()):
            if value:
                writer.writerow([section, party, value])
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def process_aragon(out: Path) -> dict:
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError("Falta xlrd==2.0.2; instalar requirements-f10-electoral.lock") from exc

    geography: Counter = Counter()
    cera: Counter = Counter()
    by_province_party: Counter = Counter()
    source_mesa_count = 0
    cera_mesa_count = 0
    ballot_equation_failures = []
    provincial = {}
    xls_sections: set[tuple[str, str]] = set()

    for name, (province, filename) in ARAGON_PROVINCES.items():
        path = ARAGON_RAW / filename
        sheet = xlrd.open_workbook(path, on_demand=True).sheet_by_name("Mesas")
        header = [str(value).strip() for value in sheet.row_values(0)]
        if header[:13] != ["Codcir", "Codmun", "Municipio", "Mesa", "Censo", "Certif. Alta",
                           "Certif. Correc.", "Censo Total", "Votos Electores", "Votos Interventores",
                           "Votos Totales", "Votos Nulos", "Votos Blancos"]:
            raise ValueError(f"Estructura inesperada en XLS Aragón {filename}")
        unknown = set(header[13:]) - set(ARAGON_XLS_PARTIES)
        if unknown:
            raise ValueError(f"Candidaturas desconocidas en {filename}: {sorted(unknown)}")
        candidates = {header[i]: ARAGON_XLS_PARTIES[header[i]] for i in range(13, len(header))}
        prov_votes = prov_nulls = prov_blank = prov_turnout = 0
        for rowno in range(1, sheet.nrows):
            row = sheet.row_values(rowno)
            if not row or not isinstance(row[0], (float, int)):
                continue
            if f"{int(row[0]):02d}" != province:
                raise ValueError(f"Codcir inesperado en {filename}, fila {rowno + 1}")
            municipality = nonnegative_int(row[1], f"{filename} Codmun")
            total = nonnegative_int(row[10], f"{filename} Votos Totales")
            nulls = nonnegative_int(row[11], f"{filename} Votos Nulos")
            blanks = nonnegative_int(row[12], f"{filename} Votos Blancos")
            candidate_values = {candidates[header[i]]: nonnegative_int(row[i], f"{filename} {header[i]}")
                                for i in range(13, len(header))}
            candidate_sum = sum(candidate_values.values())
            source_mesa_count += 1
            if total != nulls + blanks + candidate_sum:
                ballot_equation_failures.append({"file":filename,"row":rowno+1,"total":total,
                                                 "nulls":nulls,"blanks":blanks,"candidates":candidate_sum})
            prov_votes += candidate_sum
            prov_nulls += nulls
            prov_blank += blanks
            prov_turnout += total
            if municipality == 990:
                cera_mesa_count += 1
                for party, votes in candidate_values.items():
                    cera[name, party] += votes
                    by_province_party[name, party] += votes
            else:
                section = aragon_cusec(province, municipality, str(row[3]))
                xls_sections.add((section, name))
                for party, votes in candidate_values.items():
                    geography[section, party] += votes
                    by_province_party[name, party] += votes
        provincial[name] = {"candidacy_votes_including_cera": prov_votes,
                            "blank_votes": prov_blank, "null_votes": prov_nulls,
                            "ballots": prov_turnout}
    if ballot_equation_failures:
        raise ValueError(f"Ecuaciones de escrutinio XLS fallidas: {ballot_equation_failures[:3]}")

    # El catálogo Open Data publica candidatura/mesa y omite CERA. Se contrasta el
    # desglose agregado exacto por CUSEC/candidatura con los XLS definitivos.
    od = Counter()
    od_path = ARAGON_RAW / "GA_OD_resource381_CA2026.csv"
    od_rows = 0
    with od_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"cod_elec", "nombre_par", "cod_mesa", "cod_municipio", "cod_provincia", "votos_e"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Columnas incompletas en catálogo Open Data Aragón")
        for row in reader:
            od_rows += 1
            if row["cod_elec"] != "CA2026":
                raise ValueError("El CSV Open Data contiene una elección distinta de CA2026")
            if (row["cod_provincia"] != row["cod_mesa"][:2]
                    or row["cod_municipio"] != row["cod_mesa"][:5]
                    or str(int(row["cod_distrito"])).zfill(2) != row["cod_mesa"][5:7]):
                raise ValueError(f"Identidad administrativa y código de mesa Aragón no coinciden: {row['cod_mesa']}")
            party = ARAGON_OD_PARTIES.get(row["nombre_par"])
            if party is None:
                raise ValueError(f"Candidatura Open Data sin correspondencia declarada: {row['nombre_par']!r}")
            section = row["cod_mesa"][:10]
            if len(section) != 10 or not section.isdigit() or section[:2] != row["cod_provincia"]:
                raise ValueError(f"Código de mesa/CUSEC Open Data inválido: {row['cod_mesa']!r}")
            od[section, party] += nonnegative_int(row["votos_e"], "Open Data votos_e")
    if od != geography:
        mismatches = [(key, geography[key], od[key]) for key in set(od) | set(geography) if od[key] != geography[key]]
        raise ValueError(f"Open Data no concilia por CUSEC/candidatura con XLS definitivos: {mismatches[:5]}")

    normalized = write_long(ROOT / "territorios/aragon/inputs/aragon_2026_cortes_secciones_partidos.csv", geography, ";")
    election_sections = sorted({s for s, _ in geography})
    official_crosswalk = json.loads((ROOT / "territorios/aragon/config/elecciones/aragon_cortes_2026.json").read_text(encoding="utf-8"))["reconciliation"]
    result_only_detail = []
    for code in election_sections:
        code_votes = sum(value for (section, _party), value in geography.items() if section == code)
        if code == "5002501003":
            result_only_detail.append({"cusec":code,"candidate_votes":code_votes,"status":"UNMATCHED_TEMPORAL_IDENTITY"})
    if not result_only_detail or result_only_detail[0]["candidate_votes"] != 608:
        raise ValueError("El delta de alcance electoral oficial de Aragón ya no coincide con 5002501003/608")
    cera_path = out / "aragon_2026_cera_provincia_partido.csv"
    cera_path.parent.mkdir(parents=True, exist_ok=True)
    with cera_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=";", lineterminator="\n")
        writer.writerow(["province", "party", "candidate_votes"])
        for (province, party), votes in sorted(cera.items()):
            if votes:
                writer.writerow([province, party, votes])
    return {"territory":"Aragón","election_id":"aragon_cortes_2026-02-08",
            "source_status":"official_provincial_definitive_XLS; Open Data agrees exactly at CUSEC/party but omits CERA",
            "xls_mesa_rows_including_cera":source_mesa_count,"cera_mesa_rows":cera_mesa_count,
            "geographic_cusec_count":len({s for s,p in geography}),"geographic_cusec_party_rows":sum(v>0 for v in geography.values()),
            "candidate_votes_geographic":sum(geography.values()),"candidate_votes_cera":sum(cera.values()),
            "open_data_rows":od_rows,"open_data_cusec_party_mismatches":0,
            "temporal_crosswalk":{"status":"BLOCKED_UNRESOLVED_OFFICIAL_IDENTITY",
                "result_only":result_only_detail,
                "map_only":[{"cusec":"2221301003","status":"ABSENT_FROM_OFFICIAL_2026_RESULTS",
                              "source_note":"Se conserva el CUSEC del informe territorial 2025 vigente; su relación administrativa con el CUSEC electoral 2026 requiere evidencia oficial."}],
                "note":"La conciliación entre los dos formatos oficiales acredita resultados, no transferencia de votos ni identidad territorial temporal."},
            "provinces":provincial,"normalized_source":normalized,
            "cera_control":{"path":cera_path.relative_to(ROOT).as_posix(),"bytes":cera_path.stat().st_size,"sha256":sha256(cera_path)}}


def process_cyl(out: Path) -> dict:
    from ddd_core.electoral_contract import PartyDictionary

    dictionary_path = ROOT / "territorios/castilla_y_leon/config/elecciones/diccionario_partidos_cyl_2026.json"
    dictionary = PartyDictionary(json.loads(dictionary_path.read_text(encoding="utf-8")))
    source = CYL_RAW / "resultados_2026_por_mesa.csv"
    values: Counter = Counter()
    # Meta de mesa constante, candidatura única por mesa y sumas de mesa aparte.
    controls: dict[str, tuple[int,int,int,str,str,str,str]] = {}
    mesa_candidates: Counter = Counter()
    seen_mesa_party: set[tuple[str, str]] = set()
    provinces: dict[str, dict] = defaultdict(lambda:{"geographic_candidate_votes":0,"cera_candidate_votes":0,
                                                    "null_votes":0,"blank_votes":0,"voters":0})
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        required = {"ano","codigo_de_mesa","provincia","codigo_municipio","distrito","seccion","mesa",
                    "total_votantes","votos_nulos","votos_blanco","partido","no_votos"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Columnas incompletas en dataset electoral CYL")
        for row in reader:
            if row["ano"] != "2026":
                raise ValueError("El CSV CYL contiene año distinto de 2026")
            cusec = cyl_cusec(row["provincia"],row["codigo_municipio"],row["distrito"],row["seccion"])
            mesa = row["codigo_de_mesa"]
            expected_mesa = (f"{CYL_PROVINCES[row['provincia']]}-"
                             f"{int(row['codigo_municipio']):03d}-{int(row['distrito'])}-"
                             f"{int(row['seccion']):03d}-{row['mesa']}")
            if mesa != expected_mesa:
                raise ValueError(f"Identificador de mesa y provincia inconsistentes: {mesa}")
            meta = (nonnegative_int(row["total_votantes"],"total_votantes"),
                    nonnegative_int(row["votos_nulos"],"votos_nulos"),
                    nonnegative_int(row["votos_blanco"],"votos_blanco"),row["provincia"],cusec,
                    row["codigo_municipio"],row["codigo_de_mesa"])
            old = controls.get(mesa)
            if old is not None and old != meta:
                raise ValueError(f"Controles repetidos de mesa no son constantes: {mesa}")
            if old is None:
                controls[mesa] = meta
            party = dictionary.canonicalize(row["partido"])
            pair = (mesa, party)
            if pair in seen_mesa_party:
                raise ValueError(f"Candidatura duplicada en mesa CYL: {mesa}/{party}")
            seen_mesa_party.add(pair)
            candidate_votes = nonnegative_int(row["no_votos"],"no_votos")
            values[cusec,party] += candidate_votes
            mesa_candidates[mesa] += candidate_votes
    cera_codes = set()
    equation_failures=[]
    for _mesa, meta in controls.items():
        voters,nulls,blanks,province,cusec,municipality,_code = meta
        if voters != nulls + blanks + mesa_candidates[_mesa]:
            equation_failures.append({"mesa":_mesa,"voters":voters,"nulls":nulls,
                                      "blanks":blanks,"candidates":mesa_candidates[_mesa]})
        if int(municipality) == 990:
            cera_codes.add(cusec)
        prov = provinces[province]
        key = "cera_candidate_votes" if int(municipality)==990 else "geographic_candidate_votes"
        prov[key] += mesa_candidates[_mesa]
        prov["null_votes"] += nulls
        prov["blank_votes"] += blanks
        prov["voters"] += voters
    if equation_failures:
        raise ValueError(f"Ecuación de escrutinio por mesa CYL fallida: {equation_failures[:5]}")

    normalized=write_long(ROOT / "territorios/castilla_y_leon/inputs/cyl_2026_secciones_partidos.csv",values,",", "section_id")
    # Control de las rectificaciones del BOCYL del 8 de junio aplicadas en el dataset:
    # PANCAL-URCI no tiene votos en Salamanca/Zamora; PREPAL registra 311 y 333.
    correction_check = {}
    by_party_province=Counter()
    with source.open(encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream,delimiter=";"):
            if row["partido"] in {"PANCAL-URCI","PREPAL"}:
                by_party_province[row["partido"],row["provincia"]]+=nonnegative_int(row["no_votos"],"no_votos")
    correction_check={"PANCAL_URCI_SALAMANCA":by_party_province["PANCAL-URCI","Salamanca"],
                      "PANCAL_URCI_ZAMORA":by_party_province["PANCAL-URCI","Zamora"],
                      "PREPAL_SALAMANCA":by_party_province["PREPAL","Salamanca"],
                      "PREPAL_ZAMORA":by_party_province["PREPAL","Zamora"]}
    if correction_check != {"PANCAL_URCI_SALAMANCA":0,"PANCAL_URCI_ZAMORA":0,
                           "PREPAL_SALAMANCA":311,"PREPAL_ZAMORA":333}:
        raise ValueError(f"Dataset no refleja las rectificaciones BOCYL del 8 de junio: {correction_check}")
    recon_path=ROOT/"territorios/castilla_y_leon/evidencia/reconciliacion_secciones_2025_2026.json"
    recon=json.loads(recon_path.read_text(encoding="utf-8"))
    observed_sections=sorted({section for section,_party in values})
    if len(observed_sections) != recon["electoral_sections"]:
        raise ValueError("Recuento de CUSEC electorales CYL no coincide con reconciliación vigente")
    if not set(recon["electoral_only"]).issubset(set(observed_sections)):
        raise ValueError("Faltan CUSEC result-only de la reconciliación CYL vigente")
    if len(set(observed_sections)-set(recon["electoral_only"])) != recon["intersection"]:
        raise ValueError("La intersección CUSEC CYL 2025/2026 no coincide con reconciliación vigente")
    return {"territory":"Castilla y León","election_id":"castilla_y_leon_cortes_2026-03-15",
            "dataset_records":len(seen_mesa_party),
            "polling_station_count":len(controls),"result_cusec_count":len({s for s,p in values}),
            "cera_cusec_count":len(cera_codes),"cera_cusec":sorted(cera_codes),
            "temporal_crosswalk":{"status":"BLOCKED_UNRESOLVED_OFFICIAL_IDENTITY",
                "electoral_only":recon["electoral_only"],"map_only":recon["m06_only"],
                "geographic_electoral_only_votes":sum(v for (section,_party),v in values.items() if section in set(recon["electoral_only"]) and section[2:5]!="990"),
                "cera_codes_separate":sorted(cera_codes),
                "note":"La reconciliación geométrica existente identifica candidatos territoriales, pero no acredita transferencia de votos."},
            "candidate_votes_including_cera":sum(values.values()),"province_controls":dict(provinces),
            "mesa_ballot_equation_failures":0,"correction_check":correction_check,
            "normalized_source":normalized}


def prepare_candidate_contract(territory: str, source_rel: str, election_date: str,
                               publisher: str, url: str, separator: str,
                               verification: dict, out: Path) -> Path:
    contract_path=ROOT/f"territorios/{territory}/config/elecciones/{territory}_cortes_2026.json"
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    contract["artifact_metadata"]={"version":"1.0.1","name":f"Official F10 source candidate {territory} 2026",
        "date":"2026-10-20","scope":"electoral source selection; crosswalk remains independently gated",
        "status":"candidate","changes":["preserve and verify newly acquired official source bytes"],
        "reason":"Exact source reconciliation is complete; the temporal crosswalk has unresolved identities.",
        "predecessor":contract_path.relative_to(ROOT).as_posix()}
    contract["sources"]=[{"path":Path(source_rel).relative_to(Path("territorios")/territory).as_posix(),
        "sha256":sha256(ROOT/source_rel),"publisher":publisher,"source_url":url,"retrieved_at":"2026-10-20",
        "adapter":{"kind":"long_csv","separator":separator,
            "section_field":"CUSEC_KEY" if territory=="aragon" else "section_id",
            "party_field":"party","votes_field":"votes"}}]
    contract["source_verification"]=verification
    out.mkdir(parents=True,exist_ok=True)
    target=out/f"{territory}_cortes_2026_contract_candidate.json"
    target.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target


def validate_normalized_package(territory: str, source_rel: str, election_date: str,
                                candidate_contract: Path) -> dict:
    """Run the canonical frozen-source validator against the exact normalized bytes."""
    from herramientas.validar_paquete_electoral import validate_package

    contract_path = candidate_contract
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = ROOT / source_rel
    digest = sha256(source)
    with tempfile.TemporaryDirectory(prefix="ddd-f10-official-electoral-") as temp:
        package = Path(temp) / "package"
        data = package / "data"
        data.mkdir(parents=True)
        target = data / source.name
        shutil.copy2(source, target)
        manifest = {
            "schema": "ddd-electoral-package/1.0", "decision": "ACQUIRE",
            "territory_id": territory, "edition": "2025",
            "election_id": contract["election_id"], "election_date": election_date,
            "selected_source": {"path": f"data/{source.name}", "sha256": digest, "bytes": target.stat().st_size},
        }
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        params=Path(temp)/"params.yaml"
        params.write_text("meta:\n  territory_id: "+territory+"\n  year: 2025\nmodulos:\n  modulo_07_agregar_resultados_electorales:\n    election_contract: "+candidate_contract.relative_to(ROOT).as_posix()+"\n",encoding="utf-8")
        result = validate_package(package=package, params=params, territory_id=territory,
                                  edition="2025", root=ROOT)
    return result


def write_provenance(out: Path, reports: list[dict]) -> dict:
    entries = []
    urls = {
        "DatEscrut_Def_Auto_2026_Huesca.xls":"https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_huesca",
        "DatEscrut_Def_Auto_2026_Teruel.xls":"https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_teruel",
        "DatEscrut_Def_Auto_2026_Zaragoza.xls":"https://www.aragon.es/documents/d/guest/datescrut_def_auto_2026_zaragoza",
        "GA_OD_resource381_CA2026.csv":"https://opendata.aragon.es/GA_OD_Core/download?resource_id=381&formato=csv&filters=%7B%22cod_elec%22%3A%22CA2026%22%7D",
        "BOCYL-D-29042026-80-13.pdf":"https://bocyl.jcyl.es/boletines/2026/04/29/pdf/BOCYL-D-29042026-80-13.pdf",
        "BOCYL-D-08062026-108-27.pdf":"https://bocyl.jcyl.es/boletines/2026/06/08/pdf/BOCYL-D-08062026-108-27.pdf",
        "BOCYL-D-11062026-111-18.pdf":"https://bocyl.jcyl.es/boletines/2026/06/11/pdf/BOCYL-D-11062026-111-18.pdf",
        "resultados_2026_por_mesa.csv":"https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/resultados-electorales-1983-actualidad/exports/csv?where=ano%20%3E%3D%20%272026-01-01%27%20AND%20ano%20%3C%20%272027-01-01%27",
        "dataset-metadata.json":"https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/resultados-electorales-1983-actualidad",
        "2026AC0001.html":"https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001",
        "26AC0001.pdf":"https://doe.juntaex.es/pdfs/doe/2026/80o/26AC0001.pdf",
    }
    for folder in (ARAGON_RAW,CYL_RAW,EVIDENCE/"originales/extremadura"):
        for path in sorted(folder.iterdir()):
            if path.is_file():
                entries.append({"path":path.relative_to(ROOT).as_posix(),"bytes":path.stat().st_size,
                                "sha256":sha256(path),"source_url":urls.get(path.name),
                                "acquired_on":"2026-10-20"})
    payload={"schema":"ddd-f10-official-electoral-originals/1.0","acquired_on":"2026-10-20",
             "originals":entries,"processors":{"aragon":"herramientas/procesar_f10_resultados_aragon_cyl.py",
             "castilla_y_leon":"herramientas/procesar_f10_resultados_aragon_cyl.py"},
             "generated":{"aragon":reports[0],"castilla_y_leon":reports[1]}}
    out.mkdir(parents=True,exist_ok=True)
    target=out/"manifest_procesamiento.json"
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"path":target.relative_to(ROOT).as_posix(),"sha256":sha256(target)}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,default=EVIDENCE/"procesados")
    args=parser.parse_args()
    aragon=process_aragon(args.output_dir)
    cyl=process_cyl(args.output_dir)
    aragon_contract=prepare_candidate_contract("aragon",aragon["normalized_source"]["path"],"2026-02-08",
        "Gobierno de Aragón — Portal de elecciones y datos abiertos",
        "https://www.aragon.es/portal-de-elecciones/resultados-electorales",";",
        {"status":"VERIFIED_OFFICIAL_FORMATS_MATCH","geographic_candidate_votes":656725,
         "cera_candidate_votes_separate":4259,"official_candidate_votes_including_cera":660984,
         "cera_control_path":aragon["cera_control"]["path"],"cera_control_sha256":aragon["cera_control"]["sha256"]},args.output_dir)
    cyl_contract=prepare_candidate_contract("castilla_y_leon",cyl["normalized_source"]["path"],"2026-03-15",
        "Junta de Castilla y León — Datos Abiertos",
        "https://analisis.datosabiertos.jcyl.es/explore/dataset/resultados-electorales-1983-actualidad/",",",
        {"status":"VERIFIED_DATASET_AGREES_WITH_CORRECTED_BOCYL","official_candidate_votes_including_cera":1236753,
         "cera_candidate_votes_separate":11782,"cera_code_count":19,
         "correction_2026_06_08":{"PANCAL_URCI_SALAMANCA":0,"PANCAL_URCI_ZAMORA":0,
                                  "PREPAL_SALAMANCA":311,"PREPAL_ZAMORA":333}},args.output_dir)
    validations={
        "aragon":validate_normalized_package("aragon",aragon["normalized_source"]["path"],"2026-02-08",aragon_contract),
        "castilla_y_leon":validate_normalized_package("castilla_y_leon",cyl["normalized_source"]["path"],"2026-03-15",cyl_contract),
    }
    candidate_contracts={
        "aragon":{"path":aragon_contract.relative_to(ROOT).as_posix(),"sha256":sha256(aragon_contract)},
        "castilla_y_leon":{"path":cyl_contract.relative_to(ROOT).as_posix(),"sha256":sha256(cyl_contract)},
    }
    report={"schema":"ddd-f10-three-territories-processing/1.0","processed_on":date.today().isoformat(),
            "aragon":aragon,"castilla_y_leon":cyl,
            "candidate_contracts":candidate_contracts,
            "canonical_package_validation":validations,
            "extremadura":{"territory":"Extremadura","definitive_granular_source":"NOT_FOUND_PUBLICLY_OR_IN_PROTECTED_STORE",
                            "definitive_constituency_candidate_votes":{"Badajoz":326196,"Cáceres":198641,"total":524837},
                            "existing_provisional_candidate_votes":522418,"unallocated_difference":2419,
                            "official_material":{"doe_result_url":"https://doe.juntaex.es/otrosFormatos/html.php?anio=2026&doe=80o&xml=2026AC0001",
                                "jec_election_index":"https://www.juntaelectoralcentral.es/cs/jec/elecciones/Extremadura-diciembre2025?p=1392649722119",
                                "jec_cera_result_url":"https://www.juntaelectoralcentral.es/cs/jec/documentos/extremadura_2025_resultados_CERA.pdf",
                                "doe_acta_models":"https://doe.juntaex.es/pdfs/doe/2025/80e/80e.pdf",
                                "finding":"The public definitive record located is aggregate by province, with CERA records separately published; the public acta PDF is a model, not filled polling-station returns."},
                            "custodians_for_remaining_evidence":["Junta Electoral de Extremadura","Junta Electoral Provincial de Badajoz","Junta Electoral Provincial de Cáceres"],
                            "required_evidence":"Definitive polling-station/candidacy acta or official table-level export, including corrections and CERA, sufficient to reconcile 524837 without imputing the 2419 difference.",
                            "decision":"BLOCKED_EXTERNAL_NO_PUBLIC_DEFINITIVE_TABLE_LEVEL_SOURCE_FOUND"}}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    out=args.output_dir/"resultado_procesamiento.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    provenance=write_provenance(args.output_dir,[aragon,cyl])
    print(json.dumps({"result":out.relative_to(ROOT).as_posix(),"sha256":sha256(out),"manifest":provenance,
                      "aragon":aragon,"castilla_y_leon":cyl},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
