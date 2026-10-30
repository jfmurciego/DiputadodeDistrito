"""Regresión de compatibilidad entre el cálculo M08 y el catálogo de main.

Dos snapshots Git: un producto se calcula sobre A y su persistidor actualizado
opera sobre B, cuyo catálogo agrega pilotos. Incluye actualización concurrente
a C, idempotencia y rechazo de corrupción global sin escribir productos.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import validate_repository
from herramientas.persistir_producto_electoral_operacional import (
    ABSENT_FINGERPRINT,
    current_electoral_product_fingerprint,
    persist_electoral_product,
)
from tests.test_registro_producto_electoral_concurrencia import (
    clone,
    git,
    make_remote,
    territory_state,
)


def _add_pilot(root: Path, territory_id: str, name: str) -> None:
    """Crear un segundo universo válido en fixtures, sin generar distritos."""
    master_path = root / "configuracion/catalogo_territorios_espana_2025.yaml"
    master = yaml.safe_load(master_path.read_text(encoding="utf-8"))
    master.setdefault("pilot_territories", []).append(
        {"territory_id": territory_id, "name": name, "scope": "congreso"}
    )
    master_path.write_text(
        yaml.safe_dump(master, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    catalog_path = root / "configuracion/catalogo_preparacion.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["territories"].append(territory_state(territory_id, name))
    catalog_path.write_text(
        yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    # Fuente y contrato ficticios: se comprueba integridad del catálogo,
    # no se crea un producto M04/M05/M06/M08 para el piloto.
    previous = root / "territorios/beta"
    target = root / "territorios" / territory_id
    shutil.copytree(previous, target)
    for file in list(target.rglob("*")):
        if not file.is_file():
            continue
        data = file.read_text(encoding="utf-8")
        file.write_text(
            data.replace("beta", territory_id).replace("Beta", name),
            encoding="utf-8",
        )
        if file.name == "beta_2025.yaml":
            file.rename(file.with_name(f"{territory_id}_2025.yaml"))


def _push_pilot(remote: Path, path: Path, territory_id: str, name: str) -> None:
    clone(remote, path)
    git(path, "config", "user.name", "test")
    git(path, "config", "user.email", "test@example.invalid")
    _add_pilot(path, territory_id, name)
    git(path, "add", ".")
    git(path, "commit", "-m", f"add isolated congress pilot {territory_id}")
    git(path, "push", "origin", "HEAD:main")


@unittest.skipUnless(shutil.which("git"), "git executable required")
class CatalogPilotM08EvolutionTests(unittest.TestCase):
    def test_old_product_registers_after_two_pilot_additions_and_push_race(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            clone(remote, writer)
            source_sha = git(writer, "rev-parse", "HEAD")
            self.assertEqual(
                current_electoral_product_fingerprint(
                    root_dir=writer, territory_id="alpha", edition="2025"
                ),
                ABSENT_FINGERPRINT,
            )
            _push_pilot(remote, base / "pilot-a", "congreso_huesca", "Congreso Huesca")
            # Antes del push del registrador aparece un segundo piloto en main.
            def add_second_pilot(attempt: int) -> None:
                if attempt == 1:
                    _push_pilot(
                        remote, base / "pilot-b",
                        "congreso_leon", "Congreso León",
                    )

            result_path = base / "registered.json"
            persisted_head = persist_electoral_product(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
                run_id=810,
                artifact_name="ddd-state-810-M08",
                artifact_sha256="e" * 64,
                source_commit=source_sha,
                expected_previous_fingerprint=ABSENT_FINGERPRINT,
                result_json=result_path,
                before_push=add_second_pilot,
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "REGISTERED")
            self.assertGreaterEqual(result["attempt"], 2)
            verify = base / "verify"
            clone(remote, verify)
            self.assertEqual(git(verify, "rev-parse", "HEAD"), persisted_head)
            self.assertEqual(validate_repository(root_dir=verify), [])
            master = yaml.safe_load(
                (verify / "configuracion/catalogo_territorios_espana_2025.yaml")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(
                {r["territory_id"] for r in master["pilot_territories"]},
                {"congreso_huesca", "congreso_leon"},
            )
            self.assertEqual(
                {r["territory_id"] for r in master["territories"]},
                {"alpha", "beta"},
            )
            receipt = json.loads(
                (verify / "territorios/alpha/evidencia/catalogo/electoral_product_2025.json")
                .read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["source_commit"], source_sha)
            self.assertEqual(receipt["artifact_sha256"], "e" * 64)
            self.assertEqual(receipt["artifact_name"], "ddd-state-810-M08")
            self.assertEqual(receipt["run_id"], 810)

            another_writer = base / "repeat"
            clone(remote, another_writer)
            repeat_result = base / "noop.json"
            self.assertEqual(
                persist_electoral_product(
                    root_dir=another_writer, territory_id="alpha",
                    edition="2025", run_id=810,
                    artifact_name="ddd-state-810-M08",
                    artifact_sha256="e" * 64,
                    source_commit=source_sha, result_json=repeat_result,
                ),
                persisted_head,
            )
            self.assertEqual(
                json.loads(repeat_result.read_text(encoding="utf-8"))["status"],
                "NO_OP",
            )

    def test_duplicate_identity_across_territory_and_pilots_blocks_registration(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            clone(remote, writer)
            source_sha = git(writer, "rev-parse", "HEAD")
            broken = base / "broken"
            clone(remote, broken)
            master_path = broken / "configuracion/catalogo_territorios_espana_2025.yaml"
            master = yaml.safe_load(master_path.read_text(encoding="utf-8"))
            master["pilot_territories"] = [
                {"territory_id": "alpha", "name": "Falso Congreso Alpha"}
            ]
            master_path.write_text(
                yaml.safe_dump(master, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            git(broken, "config", "user.name", "test")
            git(broken, "config", "user.email", "test@example.invalid")
            git(broken, "add", ".")
            git(broken, "commit", "-m", "inject duplicate identity")
            git(broken, "push", "origin", "HEAD:main")
            broken_head = git(broken, "rev-parse", "HEAD")
            with self.assertRaisesRegex(ValueError, "CATALOG_MASTER_DUPLICATE: alpha"):
                persist_electoral_product(
                    root_dir=writer, territory_id="alpha", edition="2025",
                    run_id=820, artifact_name="ddd-state-820-M08",
                    artifact_sha256="e" * 64, source_commit=source_sha,
                )
            verify = base / "verify"
            clone(remote, verify)
            self.assertEqual(git(verify, "rev-parse", "HEAD"), broken_head)
            self.assertFalse(
                (verify / "territorios/alpha/evidencia/catalogo/electoral_product_2025.json")
                .exists()
            )

    def test_malformed_unrelated_pilot_blocks_registration(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            clone(remote, writer)
            source_sha = git(writer, "rev-parse", "HEAD")
            broken = base / "broken"
            clone(remote, broken)
            master_path = broken / "configuracion/catalogo_territorios_espana_2025.yaml"
            master = yaml.safe_load(master_path.read_text(encoding="utf-8"))
            master["pilot_territories"] = [
                {"territory_id": "congreso_sin_nombre", "name": ""}
            ]
            master_path.write_text(yaml.safe_dump(master), encoding="utf-8")
            git(broken, "config", "user.name", "test")
            git(broken, "config", "user.email", "test@example.invalid")
            git(broken, "add", ".")
            git(broken, "commit", "-m", "inject malformed pilot")
            git(broken, "push", "origin", "HEAD:main")
            with self.assertRaisesRegex(ValueError, "CATALOG_MASTER_INVALID"):
                persist_electoral_product(
                    root_dir=writer, territory_id="alpha", edition="2025",
                    run_id=830, artifact_name="ddd-state-830-M08",
                    artifact_sha256="e" * 64, source_commit=source_sha,
                )


if __name__ == "__main__":
    unittest.main()
