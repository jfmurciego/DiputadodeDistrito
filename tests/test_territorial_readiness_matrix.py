from pathlib import Path
import yaml

from herramientas.resolver_ejecucion_completa import build_plan, generation_enablement, resolve_publication_mode

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


def test_all_prepared_authorized_territories_pass_generation_preflight():
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    prepared = []
    pending = []
    for row in catalog["territories"]:
        state = row["editions"]["2025"]
        item = (row["name"], row["territory_id"], state)
        if (
            state.get("preparation_status") == "READY"
            and state.get("territorial_contract_complete") is True
            and state.get("production_authorization") == "AUTHORIZED"
        ):
            prepared.append(item)
        else:
            pending.append(item)

    assert len(prepared) == 14
    assert len(pending) == 5

    for name, territory_id, state in prepared:
        gate = generation_enablement(
            root_dir=ROOT,
            contract_path=state["contract_path"],
            territory_id=territory_id,
            certified_product_ready=bool(state.get("territorial_product_available")),
        )
        assert gate["allowed"], (name, gate)
        plan = build_plan(
            territory=name,
            edition="2025",
            execution_mode="reuse",
            catalog=CATALOG,
            root_dir=ROOT,
            force_selected_algorithm=True,
        )
        assert plan["run_generate"] is True
        assert plan["generation_gate"]["allowed"] is True

    for name, territory_id, state in pending:
        gate = generation_enablement(
            root_dir=ROOT,
            contract_path=state.get("contract_path"),
            territory_id=territory_id,
            certified_product_ready=False,
        )
        assert gate["allowed"] is False, (name, gate)


def test_missing_election_downgrades_to_territorial_publication():
    clm = build_plan(
        territory="Castilla-La Mancha",
        edition="2025",
        execution_mode="reuse",
        catalog=CATALOG,
        root_dir=ROOT,
        force_selected_algorithm=True,
    )
    assert resolve_publication_mode(clm, "electoral", root_dir=ROOT) == "territorial_only"

    galicia = build_plan(
        territory="Galicia",
        edition="2025",
        execution_mode="reuse",
        catalog=CATALOG,
        root_dir=ROOT,
        force_selected_algorithm=True,
    )
    assert resolve_publication_mode(galicia, "electoral", root_dir=ROOT) == "electoral"
