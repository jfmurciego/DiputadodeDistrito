from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_operativo_existe():
    assert (ROOT / "dashboard" / "index.html").is_file()
    assert (ROOT / "dashboard" / "styles.css").is_file()


def test_pages_publica_dashboard_junto_al_visor():
    workflow = (ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
    assert "mkdir -p site/dashboard" in workflow
    assert "cp dashboard/index.html dashboard/styles.css site/dashboard/" in workflow


def test_publicacion_web_expone_selector_manual():
    workflow = (ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "pagina_publicar:" in workflow
    assert "type: choice" in workflow
    assert "- Sitio completo" in workflow
    assert "- Visor territorial" in workflow
    assert "- Dashboard operativo" in workflow


def test_publicacion_selectiva_no_elimina_otras_paginas():
    workflow = (ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
    assert "cp visor/index.html visor/app.js visor/styles.css site/" in workflow
    assert "cp dashboard/index.html dashboard/styles.css site/dashboard/" in workflow


def test_visor_enlaza_dashboard():
    html = (ROOT / "visor" / "index.html").read_text(encoding="utf-8")
    assert 'href="dashboard/"' in html
    assert "Dashboard operativo" in html


def test_publicacion_web_esta_en_critical_path():
    doc = (ROOT / "docs" / "ORQUESTACION" / "CRITICAL_PATH_EJECUTABLES.md").read_text(encoding="utf-8")
    assert "Publicar Sitio Web" in doc
    assert ".github/workflows/desplegar-visor-publico.yml" in doc
