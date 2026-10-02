import copy
import unittest

from ddd_core.electoral_gap_filler import compose_records, compose_declared_gap_csv


IDENTITY = dict(election_id="x_2025", election_date="2025-12-21", election_type="regional", scope="x")
SHA = "a"*64


def meta(source_id="main", status="FINAL", granularity="section", **kw):
    x = dict(source_id=source_id, granularity=granularity, result_status=status,
             artifact_sha256=SHA, artifact=f"{source_id}.csv", table="data", **IDENTITY)
    x.update(kw)
    return x


def row(unit, party, votes, **kw):
    return dict(unit_id=unit, party=party, votes=votes, **kw)


class GapFillTests(unittest.TestCase):
    def test_same_election_fills_only_accredited_gap_and_provenance(self):
        p=[row("01001","A",10), row("01001","B",0)]
        f=[row("01002","A",7,source_row=8), row("01002","B",2,source_row=9)]
        out=compose_records(p,meta(),[(meta("frag"),f)],
             expected_keys={("01001","A"),("01001","B"),("01002","A"),("01002","B")},
             allowed_parties={"A","B"})
        self.assertEqual(out["report"]["status"],"PASS")
        self.assertEqual(out["report"]["added_keys"],2)
        added=[r for r in out["rows"] if r["unit_id"]=="01002"][0]
        self.assertEqual(added["provenance"]["source_id"],"frag")
        self.assertEqual(added["provenance"]["source_row"],8)

    def test_clm_2023_plus_europe_2024_is_hard_block(self):
        pmeta=meta(election_id="castilla_la_mancha_cortes_2023", election_date="2023-05-28")
        emeta=meta("eu", election_id="europeas_2024", election_date="2024-06-09")
        out=compose_records([],pmeta,[(emeta,[row("16001","A",1)])],
                            expected_keys={("16001","A")})
        self.assertEqual(out["report"]["status"],"BLOCK")
        self.assertEqual(out["report"]["conflicts"][0]["code"],"ELECTION_IDENTITY_MISMATCH")

    def test_explicit_zero_is_present_not_gap(self):
        out=compose_records([row("01001","A",0)],meta(),[(meta("f"),[row("01001","A",5)])],
                            expected_keys={("01001","A")})
        self.assertEqual(out["rows"][0]["votes"],0)
        self.assertEqual(out["report"]["conflicts"][0]["code"],"PRIMARY_OVERLAP_CONFLICT")

    def test_identical_duplicate_no_double_count_and_contradiction_blocks_unit(self):
        ok=compose_records([row("01001","A",3)],meta(),[(meta("f"),[row("01001","A",3)])],
                           expected_keys={("01001","A")})
        self.assertEqual(ok["report"]["geographic_candidate_votes"],3)
        bad=compose_records([],meta(),[(meta("f"),[row("01002","A",1),row("01002","A",2),row("01002","B",4)])],
                            expected_keys={("01002","A"),("01002","B")})
        self.assertEqual(bad["report"]["status"],"BLOCK")
        self.assertEqual(bad["report"]["added_keys"],0)

    def test_granularity_overlap_is_blocked(self):
        out=compose_records([],meta(),[(meta("f",granularity="polling_station"),[row("x","A",1)])],
                            expected_keys={("x","A")})
        self.assertEqual(out["report"]["conflicts"][0]["code"],"GRANULARITY_MISMATCH")

    def test_unresolved_party_is_blocked(self):
        out=compose_records([],meta(),[(meta("f"),[row("x","UNKNOWN",1)])],
                            expected_keys={("x","UNKNOWN")},allowed_parties={"A"})
        self.assertEqual(out["report"]["conflicts"][0]["code"],"UNRESOLVED_PARTY")

    def test_provisional_final_mismatch_blocks_unless_explicit_policy(self):
        args=dict(primary_rows=[],primary_source=meta(status="PROVISIONAL"),
                  fragments=[(meta("f",status="FINAL"),[row("x","A",1)])],
                  expected_keys={("x","A")})
        blocked=compose_records(**args)
        self.assertEqual(blocked["report"]["conflicts"][0]["code"],"RESULT_STATUS_MISMATCH")
        allowed=compose_records(**args,allowed_status_pairs={("PROVISIONAL","FINAL")})
        self.assertEqual(allowed["report"]["status"],"PASS")

    def test_incomplete_coverage_and_total_mismatch(self):
        out=compose_records([row("x","A",1)],meta(),[],expected_keys={("x","A"),("y","A")},
                            official_geographic_candidate_votes=9)
        self.assertEqual(out["report"]["status"],"BLOCK")
        self.assertTrue(out["report"]["remaining_missing_keys"])
        self.assertEqual(out["report"]["reconciliation_errors"][0]["code"],"GEOGRAPHIC_TOTAL_MISMATCH")

    def test_special_external_unit_is_separate_never_geocoded(self):
        p=[row("01001","A",10)]
        f=[row("CERA-01","A",2,unit_kind="external")]
        out=compose_records(p,meta(),[(meta("f",status="FINAL"),f)],
                            expected_keys={("01001","A")},
                            official_geographic_candidate_votes=10,
                            official_total_candidate_votes=12)
        self.assertEqual(out["report"]["status"],"PASS")
        self.assertEqual(len(out["rows"]),1)
        self.assertEqual(out["report"]["special_candidate_votes"],2)

    def test_determinism_idempotence_and_primary_conservation(self):
        p=[row("001","A",1),row("001","B",0)]
        f=[row("002","A",2),row("002","B",3)]
        expected={("001","A"),("001","B"),("002","A"),("002","B")}
        original=copy.deepcopy(p)
        a=compose_records(p,meta(),[(meta("f"),f)],expected_keys=expected)
        b=compose_records(p,meta(),[(meta("f"),list(reversed(f)))],expected_keys=expected)
        self.assertEqual(a["report"]["logical_digest"],b["report"]["logical_digest"])
        self.assertEqual(p,original)
        fail=compose_records(a["rows"],meta(),[(meta("bad",election_id="wrong"),f)],expected_keys=expected)
        self.assertEqual(
            {(r["unit_id"],r["party"],r["votes"]) for r in a["rows"]},
            {(r["unit_id"],r["party"],r["votes"]) for r in fail["rows"]},
        )
        self.assertEqual(a["report"]["logical_digest"],fail["report"]["logical_digest"])

    def test_declared_csv_integration_requires_election_evidence(self):
        import csv, hashlib, json, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            primary=root/"primary.csv"; fragment=root/"fragment.csv"
            for path, rows in ((primary,[("001","A","1")]),(fragment,[("002","A","2")])):
                with path.open("w",encoding="utf-8",newline="") as fh:
                    w=csv.writer(fh,delimiter=";"); w.writerow(["unit","party","votes"]); w.writerows(rows)
            (root/"expected.json").write_text(
                json.dumps([{"unit_id":"001","party":"A"},{"unit_id":"002","party":"A"}]),
                encoding="utf-8",
            )
            sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            ident={"election_id":"x_2025","election_date":"2025-12-21","election_type":"regional","scope":"x"}
            def src(sid,status):
                return {
                    "id":sid,"source_table":"data","result_status":status,
                    "election_evidence":{**ident,"references":[f"https://example.invalid/{sid}"]},
                    "composition_fields":{"unit":"unit","party":"party","votes":"votes","delimiter":";"},
                }
            decl={
                "composition":{
                    "kind":"electoral_gap_filler","primary_source_id":"p",
                    "election_identity":ident,"granularity":"section",
                    "expected_keys":"expected.json","allowed_parties":["A"],
                    "allowed_status_pairs":[["PROVISIONAL","FINAL"]],
                    "official_geographic_candidate_votes":3,
                },
                "sources":[src("p","PROVISIONAL"),src("f","FINAL")],
            }
            selected=[
                {"id":"p","sha256":sha(primary),"artifact_path":"p.csv"},
                {"id":"f","sha256":sha(fragment),"artifact_path":"f.csv"},
            ]
            out=compose_declared_gap_csv(
                source_paths=[primary,fragment],selected_sources=selected,
                source_declarations=decl["sources"],declaration=decl,root=root,out_dir=root/"out")
            self.assertEqual(out["report"]["status"],"PASS")
            self.assertEqual(out["report"]["added_keys"],1)
            self.assertTrue(out["lineage_path"].is_file())
            bad=copy.deepcopy(decl); del bad["sources"][1]["election_evidence"]
            with self.assertRaisesRegex(ValueError,"sin election_evidence"):
                compose_declared_gap_csv(
                    source_paths=[primary,fragment],selected_sources=selected,
                    source_declarations=bad["sources"],declaration=bad,root=root,out_dir=root/"bad")

    def test_real_badajoz_snapshot_proves_cera_not_geographic_gap(self):
        import csv, io, zipfile
        from pathlib import Path
        import openpyxl

        base=Path(__file__).parent/"fixtures"/"electoral_gap_filler"
        with zipfile.ZipFile(base/"extremadura-provisional.zip") as zf:
            name=next(n for n in zf.namelist() if n.endswith("resultados_electorales_normalizados.csv"))
            primary_raw=list(csv.DictReader(io.TextIOWrapper(zf.open(name),encoding="utf-8"),delimiter=";"))
        primary=[
            {"unit_id":r["CUSEC_KEY"],"party":r["party"],"votes":r["votes"],"source_row":i}
            for i,r in enumerate(primary_raw,2) if r["CUSEC_KEY"].startswith("06")
        ]

        wb=openpyxl.load_workbook(base/"badajoz-opte.xlsx",data_only=True,read_only=True)
        ws=wb["Indra ministerio"]
        values=list(ws.iter_rows(values_only=True))
        headers=[str(x or "") for x in values[0][1:25]]
        table=[]
        for raw in values[1:]:
            if not raw[1]:
                continue
            rowx={}
            for key,value in zip(headers,raw[1:25]):
                if isinstance(value,float) and value.is_integer(): value=int(value)
                rowx[key]=value
            table.append(rowx)

        party_map={"UED-SYT":"UED-SyT","VOX":"VOX","PSOE":"PSOE","PODEMOS-IU-AV":"PODEMOS-IU-AV",
                   "JUNTOS-LEVANTA":"JUNTOS-LEVANTA","MUNDO+JUSTO":"MUNDO+JUSTO","CS":"Cs",
                   "PP":"PP","PACMA":"PACMA","NEX":"NEX"}
        aggregates={}; source_rows={}
        aux={"electors":0,"voters":0,"null":0,"blank":0}
        bad_accounting=0; accounting_delta=0
        for line,rowx in enumerate(table,2):
            mesa=rowx["Id_mesa"]; parts=mesa.split("-"); is_cera=(parts[2]=="999")
            if is_cera:
                unit="CERA-BADAJOZ"; kind="external"
            else:
                unit=f"{parts[1]}{int(parts[2]):03d}{int(parts[3]):02d}{int(parts[4]):03d}"
                kind="geographic"
            cand=sum(int(rowx[col] or 0) for col in party_map)
            voters=int(rowx["Número total de votantes"] or 0)
            null=int(rowx["Votos nulos"] or 0); blank=int(rowx["votos en blanco"] or 0)
            if voters != cand+null+blank:
                bad_accounting += 1; accounting_delta += voters-(cand+null+blank)
            aux["electors"] += int(rowx["Número de electores censados"] or 0)
            aux["voters"] += voters; aux["null"] += null; aux["blank"] += blank
            for col,party in party_map.items():
                key=(kind,unit,party); aggregates[key]=aggregates.get(key,0)+int(rowx[col] or 0)
                source_rows.setdefault(key,[]).append(line)
            if not is_cera:
                key=("geographic",unit,"NA"); aggregates.setdefault(key,0); source_rows.setdefault(key,[]).append(line)
        fragment=[
            {"unit_id":unit,"party":party,"votes":votes,"unit_kind":kind,
             "source_row":source_rows[(kind,unit,party)][0],
             "provenance":{"source_rows":source_rows[(kind,unit,party)]}}
            for (kind,unit,party),votes in sorted(aggregates.items())
        ]
        pmeta=meta("minsait_extremadura",status="PROVISIONAL")
        fmeta=meta("opte_indra_badajoz",status="FINAL")
        expected={(r["unit_id"],r["party"]) for r in primary}
        out=compose_records(
            primary,pmeta,[(fmeta,fragment)],expected_keys=expected,
            allowed_parties={r["party"] for r in primary},
            allowed_status_pairs={("PROVISIONAL","FINAL")},
            official_geographic_candidate_votes=325305,
            official_total_candidate_votes=326196,
        )
        self.assertEqual(out["report"]["status"],"PASS")
        self.assertEqual(out["report"]["added_keys"],0)
        self.assertEqual(out["report"]["geographic_candidate_votes"],325305)
        self.assertEqual(out["report"]["special_candidate_votes"],891)
        self.assertEqual(out["report"]["candidate_votes_with_special"],326196)
        self.assertEqual(len({r["unit_id"] for r in out["rows"]}),553)
        self.assertEqual(len(table),905)
        self.assertEqual(aux,{"electors":551372,"voters":337056,"null":6689,"blank":4158})
        self.assertNotEqual(aux,{"electors":551424,"voters":337037,"null":6694,"blank":4147})
        self.assertEqual(bad_accounting,15)
        self.assertEqual(accounting_delta,13)


if __name__ == "__main__":
    unittest.main()
