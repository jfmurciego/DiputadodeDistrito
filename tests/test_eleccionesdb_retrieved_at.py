from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from ddd_core.electoral_contract import load_election_contract
from herramientas.adaptador_eleccionesdb import build
from herramientas.validar_paquete_electoral import (
    _verified_eleccionesdb_retrieved_at,
    validate_package,
)


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_db(root: Path) -> Path:
    db = root / "eleccionesdb.sqlite"
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE elecciones(id INTEGER,fecha TEXT);
        CREATE TABLE elecciones_fuentes(eleccion_id INTEGER,fuente TEXT,url_fuente TEXT,observaciones TEXT);
        CREATE TABLE territorios(id INTEGER,tipo TEXT,codigo_ccaa TEXT,codigo_provincia TEXT,codigo_municipio TEXT,codigo_distrito TEXT,codigo_seccion TEXT);
        CREATE TABLE resumen_territorial(eleccion_id INTEGER,territorio_id INTEGER);
        CREATE TABLE partidos(id INTEGER,siglas TEXT,denominacion TEXT);
        CREATE TABLE votos_territoriales(eleccion_id INTEGER,territorio_id INTEGER,partido_id INTEGER,votos INTEGER);
        """
    )
    con.execute("INSERT INTO elecciones VALUES(237,'2023-05-28')")
    con.execute(
        "INSERT INTO elecciones_fuentes VALUES(237,'Gobierno','https://example.test/resultados','procedencia oficial')"
    )
    con.execute("INSERT INTO territorios VALUES(1,'seccion','06','39','075','01','1')")
    con.execute("INSERT INTO resumen_territorial VALUES(237,1)")
    con.execute("INSERT INTO partidos VALUES(1,'P','Partido')")
    con.execute("INSERT INTO votos_territoriales VALUES(237,1,1,10)")
    con.commit()
    con.close()
    return db


def params(root: Path) -> Path:
    path = root / "params.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "meta": {"territory_id": "cantabria", "year": 2025},
                "modulos": {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


class EleccionesDBRetrievedAtTests(unittest.TestCase):
    def test_new_package_writes_real_materialization_timestamp_and_contract_loads(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "package"
            upstream_created_at = "2026-09-28T12:34:56Z"
            manifest = build(
                fixture_db(root),
                "cantabria_parlamento_2023",
                package,
                edition="2025",
                retrieved_at=upstream_created_at,
            )
            contract_path = package / "contract/election_contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            source = contract["sources"][0]
            self.assertEqual(source["retrieved_at"], upstream_created_at)
            self.assertEqual(source["upstream_snapshot"]["retrieved_at"], upstream_created_at)
            self.assertEqual(manifest["retrieved_at"], upstream_created_at)
            loaded, _ = load_election_contract(contract_path, project_root=package)
            self.assertEqual(loaded["sources"][0]["retrieved_at"], upstream_created_at)

    def _legacy_package(self, root: Path) -> tuple[Path, Path]:
        package = root / "package"
        build(
            fixture_db(root),
            "cantabria_parlamento_2023",
            package,
            edition="2025",
            retrieved_at="2026-09-28T12:34:56Z",
        )
        contract_path = package / "contract/election_contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["sources"][0].pop("retrieved_at", None)
        contract["sources"][0].pop("retrieved_at_basis", None)
        (contract["sources"][0].get("upstream_snapshot") or {}).pop("retrieved_at", None)
        contract_path.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_path = package / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("retrieved_at", None)
        manifest["embedded_contract"]["contract_sha256"] = sha(contract_path)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return package, params(root)

    def _write_legacy_registry(
        self,
        root: Path,
        snapshot_sha256: str,
        *,
        retrieved_at: str = "2026-09-27T05:22:04Z",
    ) -> Path:
        path = root / "configuracion/procedencia_eleccionesdb_legacy.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "ddd-eleccionesdb-legacy-provenance/1.0",
            "snapshots": {
                snapshot_sha256: {
                    "retrieved_at": retrieved_at,
                    "rule": "retrieved_at_equals_upstream_artifact_created_at",
                    "upstream_artifact": {
                        "repository": "hmeleiro/eleccionesdb-etl",
                        "name": "eleccionesdb-descargas",
                        "artifact_id": 123,
                        "created_at": retrieved_at,
                        "size_in_bytes": 100,
                        "extracted_sqlite_sha256": "a" * 64,
                    },
                    "snapshot_artifact": {
                        "repository": "jfmurciego/DiputadodeDistrito",
                        "producer_run_id": 456,
                        "producer_job_id": 789,
                        "artifact_id": 321,
                        "name": "ddd-eleccionesdb-snapshot",
                        "created_at": "2026-09-28T08:34:55Z",
                        "artifact_sha256": "b" * 64,
                        "snapshot_sha256": snapshot_sha256,
                    },
                }
            },
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_legacy_package_derives_runtime_only_from_verified_upstream_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, cfg = self._legacy_package(root)
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            self._write_legacy_registry(root, manifest["snapshot_sha256"])
            result = validate_package(
                package=package,
                params=cfg,
                territory_id="cantabria",
                edition="2025",
                root=root,
                materialize=True,
            )
            runtime = root / result["runtime_contract_path"]
            loaded, _ = load_election_contract(runtime, project_root=root)
            source = loaded["sources"][0]
            self.assertEqual(source["retrieved_at"], "2026-09-27T05:22:04Z")
            self.assertNotEqual(source["retrieved_at"], manifest["generated_at"])
            self.assertEqual(
                source["retrieved_at_provenance"]["mode"],
                "verified_legacy_snapshot_registry",
            )
            self.assertEqual(
                source["retrieved_at_provenance"]["upstream_artifact"]["created_at"],
                source["retrieved_at"],
            )
            original = json.loads(
                (package / "contract/election_contract.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("retrieved_at", original["sources"][0])

    def test_legacy_generated_at_alone_never_satisfies_retrieved_at(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, cfg = self._legacy_package(root)
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["generated_at"])
            with self.assertRaisesRegex(
                ValueError,
                "ELECCIONESDB_RETRIEVED_AT_BLOCK: evidencia temporal legacy durable ausente",
            ):
                validate_package(
                    package=package,
                    params=cfg,
                    territory_id="cantabria",
                    edition="2025",
                    root=root,
                    materialize=False,
                )

    def test_legacy_registry_timestamp_must_equal_upstream_artifact_created_at(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package, cfg = self._legacy_package(root)
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            registry_path = self._write_legacy_registry(root, manifest["snapshot_sha256"])
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            entry = registry["snapshots"][manifest["snapshot_sha256"]]
            entry["upstream_artifact"]["created_at"] = "2026-09-27T05:22:05Z"
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "ELECCIONESDB_RETRIEVED_AT_BLOCK: retrieved_at no coincide",
            ):
                validate_package(
                    package=package,
                    params=cfg,
                    territory_id="cantabria",
                    edition="2025",
                    root=root,
                    materialize=True,
                )

    def test_real_castilla_la_mancha_legacy_chain_uses_upstream_created_at(self):
        registry = json.loads(
            (ROOT / "configuracion/procedencia_eleccionesdb_legacy.json").read_text(
                encoding="utf-8"
            )
        )
        snapshot = "668f8eeefe0c19f427367ee2b44f0050c30b93d39f7300fad3d6f381966d91fc"
        entry = registry["snapshots"][snapshot]
        package = entry["observed_legacy_packages"][0]
        catalog = json.loads(
            (
                ROOT
                / "territorios/castilla_la_mancha/evidencia/catalogo/electoral_source_2025.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(entry["retrieved_at"], "2026-09-27T05:22:04Z")
        self.assertEqual(entry["upstream_artifact"]["artifact_id"], 10924665843)
        self.assertEqual(
            entry["upstream_artifact"]["extracted_sqlite_sha256"],
            "2f0a789e4a7f8dcbb94a6461f3beb692fc640c4891a12cb891563b61aced14c9",
        )
        self.assertEqual(entry["snapshot_artifact"]["producer_run_id"], 36397953355)
        self.assertEqual(entry["snapshot_artifact"]["artifact_id"], 10958803823)
        self.assertEqual(entry["snapshot_artifact"]["snapshot_sha256"], snapshot)
        self.assertEqual(
            entry["snapshot_artifact"]["artifact_sha256"],
            "6ff2fb43038e137b4bc6c29e67eb06d24b564a3c6820a5a3799e3f4529f26396",
        )
        self.assertEqual(package["run_id"], 36402139263)
        self.assertEqual(package["artifact_id"], 10961251316)
        self.assertEqual(package["artifact_sha256"], catalog["artifact_sha256"])
        self.assertNotEqual(package["package_generated_at"], entry["retrieved_at"])

        retrieved_at, provenance = _verified_eleccionesdb_retrieved_at(
            {
                "adapter": "eleccionesdb_sqlite/1.0",
                "source_status": "VERIFIED_SOURCE_CHAIN",
                "snapshot_sha256": snapshot,
                "generated_at": package["package_generated_at"],
            },
            {
                "upstream_snapshot": {
                    "snapshot_sha256": snapshot,
                    "provenance": [{"fuente": "Portal de Transparencia de Castilla-La Mancha"}],
                }
            },
            root=ROOT,
        )
        self.assertEqual(retrieved_at, "2026-09-27T05:22:04Z")
        self.assertEqual(provenance["mode"], "verified_legacy_snapshot_registry")


    def test_snapshot_carries_upstream_artifact_created_at(self):
        builder = (ROOT / "herramientas/construir_snapshot_eleccionesdb.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/diagnostico-eleccionesdb-grupo-a.yml").read_text(encoding="utf-8")
        self.assertIn("ap.add_argument('--retrieved-at',required=True)", builder)
        self.assertIn("'retrieved_at':str(retrieved_at).strip()", builder)
        self.assertIn("artifact_created_at.txt", workflow)
        self.assertIn("--retrieved-at \"$(cat artifact_created_at.txt)\"", workflow)
        self.assertIn("retrieved_at=snapshot_meta['retrieved_at']", workflow)

    def test_production_preparation_uses_validated_snapshot_retrieved_at(self):
        workflow = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "retrieved_at=\"$(jq -r '.retrieved_at // empty' snapshot/ddd-eleccionesdb-snapshot.json)\"",
            workflow,
        )
        self.assertIn("retrieved_at verificable ausente o inválido", workflow)
        self.assertIn("--retrieved-at \"$retrieved_at\"", workflow)

    def test_adapter_requires_verified_retrieved_at(self):
        adapter = (ROOT / "herramientas/adaptador_eleccionesdb.py").read_text(encoding="utf-8")
        self.assertIn("def _verified_retrieved_at", adapter)
        self.assertIn("'retrieved_at':verified_retrieved_at", adapter)
        self.assertIn("ap.add_argument('--retrieved-at',required=True)", adapter)


if __name__ == "__main__":
    unittest.main()
