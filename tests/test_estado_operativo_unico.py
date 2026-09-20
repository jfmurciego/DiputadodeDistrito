from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from herramientas.estado_operativo import (
    END_MARKER,
    START_MARKER,
    build,
    render_readme_state,
    write_state,
)


def _catalog(root: Path) -> None:
    (root / "configuracion").mkdir(parents=True)
    (root / "territorios/demo/evidencia/catalogo").mkdir(parents=True)
    for name, payload in {
        "territorial_product_2025.json": {
            "run_id": 101,
            "artifact_name": "ddd-state-101-M06",
            "artifact_sha256": "a" * 64,
            "decision": "PASS",
        },
        "electoral_source_2025.json": {
            "run_id": 102,
            "artifact_name": "ddd-electoral-package-demo-2025-102",
            "artifact_sha256": "b" * 64,
        },
        "electoral_product_2025.json": {
            "run_id": 103,
            "artifact_name": "ddd-state-103-M08",
            "artifact_sha256": "c" * 64,
        },
    }.items():
        (root / "territorios/demo/evidencia/catalogo" / name).write_text(
            json.dumps(payload), encoding="utf-8"
        )
    catalog = {
        "schema": "ddd-preparation-catalog/1.1",
        "default_edition": "2025",
        "territories": [
            {
                "territory_id": "demo",
                "name": "Demo",
                "editions": {
                    "2025": {
                        "contract_path": "territorios/demo/config/demo_2025.yaml",
                        "territorial_sources_prepared": True,
                        "territorial_source_declaration": "territorios/demo/config/fuentes.yaml",
                        "preparation_evidence": {
                            "run_id": 100,
                            "artifact_name": "ddd-source-package-demo-2025-100",
                            "artifact_sha256": "d" * 64,
                        },
                        "territorial_product_available": True,
                        "territorial_certification": "PASS",
                        "production_authorization": "AUTHORIZED",
                        "electoral_source_prepared": True,
                        "electoral_product_available": True,
                        "last_valid_checkpoint": {"run_id": 103, "stage": "M08"},
                        "evidence": {
                            "territorial_product": "territorios/demo/evidencia/catalogo/territorial_product_2025.json",
                            "electoral_source": "territorios/demo/evidencia/catalogo/electoral_source_2025.json",
                            "electoral_product": "territorios/demo/evidencia/catalogo/electoral_product_2025.json",
                        },
                    }
                },
            },
            {
                "territory_id": "pendiente",
                "name": "Pendiente",
                "editions": {
                    "2025": {
                        "contract_path": "territorios/pendiente/config/pendiente_2025.yaml",
                        "territorial_sources_prepared": False,
                        "territorial_product_available": False,
                        "electoral_source_prepared": False,
                        "electoral_product_available": False,
                        "territorial_certification": "PREFLIGHT",
                        "production_authorization": "PREFLIGHT",
                    }
                },
            },
        ],
    }
    (root / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def test_estado_operativo_es_fuente_unica_para_readme_y_dashboard():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _catalog(root)
        (root / "README.md").write_text(
            "# Proyecto\n\n# Estado operativo del proyecto\n\nViejo\n\n## Arquitectura\n\nTexto\n",
            encoding="utf-8",
        )
        payload = write_state(
            root=root,
            generated_at="2026-09-21T00:00:00+00:00",
            canonical_path=Path("publicado/estado_operativo.json"),
            dashboard_path=Path("publicado/dashboard/status.json"),
            readme_path=Path("README.md"),
        )
        canonical = json.loads((root / "publicado/estado_operativo.json").read_text(encoding="utf-8"))
        dashboard = json.loads((root / "publicado/dashboard/status.json").read_text(encoding="utf-8"))
        readme = (root / "README.md").read_text(encoding="utf-8")

        assert payload == canonical == dashboard
        assert payload["kpis"]["complete"] == 1
        assert payload["kpis"]["complete_names"] == ["Demo"]
        assert next(r for r in payload["territories"] if r["territory_id"] == "demo")["status"] == "Cadena completa"
        assert "Puerta de validación pendiente" in readme
        assert "Preflight" not in readme
        assert START_MARKER in readme and END_MARKER in readme
        assert "01 Preparación de Datos Territoriales" in readme
        assert "05 Publicación del Visor" in readme


def test_render_readme_es_determinista_para_el_mismo_estado():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _catalog(root)
        payload = build(root, "2025", generated_at="2026-09-21T00:00:00+00:00")
        assert render_readme_state(payload) == render_readme_state(payload)
