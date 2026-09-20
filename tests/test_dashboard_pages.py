from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_operativo_existe():
    assert (ROOT / "dashboard" / "index.html").is_file()
    assert (ROOT / "dashboard" / "styles.css").is_file()


def test_pages_publica_dashboard_junto_al_visor():
    workflow = (ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
    assert "mkdir -p site/dashboard" in workflow
    assert "cp dashboard/index.html dashboard/styles.css site/dashboard/" in workflow


def test_visor_enlaza_dashboard():
    html = (ROOT / "visor" / "index.html").read_text(encoding="utf-8")
    assert 'href="dashboard/"' in html
    assert "Dashboard operativo" in html
