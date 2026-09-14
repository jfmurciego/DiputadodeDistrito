from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github/workflows/regresion-m06-aragon.yml",
    ROOT / ".github/workflows/regresion-m06-castilla-y-leon.yml",
)


def _trigger_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("\non:\n") + 1
    end = text.index("\npermissions:\n", start)
    return text[start:end]


def test_regresiones_territoriales_solo_admiten_orden_manual():
    for workflow in WORKFLOWS:
        trigger = _trigger_block(workflow)
        assert trigger == "on:\n  workflow_dispatch:\n"
        assert "push:" not in trigger
        assert "schedule:" not in trigger

