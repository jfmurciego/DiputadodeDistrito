from pathlib import Path
import json
import tempfile

from herramientas.generar_estado_dashboard import build

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / ".github/workflows/desplegar-visor-publico.yml"
REUSABLE = ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"


def test_dashboard_fuente_y_snapshot_publicado_existen():
    for base in (ROOT / "dashboard", ROOT / "publicado/dashboard"):
        for name in ("index.html","app.js","styles.css"):
            assert (base / name).is_file()
    assert (ROOT / "publicado/dashboard/status.json").is_file()


def test_dashboard_se_genera_desde_catalogo():
    payload=build(ROOT,"2025")
    assert payload["schema"]=="ddd-dashboard-status/1.0"
    galicia=next(r for r in payload["territories"] if r["territory_id"]=="galicia")
    assert galicia["g"]=="green"
    assert galicia["run_id"]==35513005773
    assert payload["latest_validated"]["run_id"]==35513005773


def test_publicador_manual_y_reutilizable_estan_separados():
    manual=MANUAL.read_text(encoding="utf-8")
    reusable=REUSABLE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in manual
    assert "workflow_call:" not in manual
    assert "workflow_call:" in reusable
    assert "workflow_dispatch:" not in reusable
    assert "pagina_publicar:" in manual
    assert "- Dashboard operativo" in manual
    assert "- Visor territorial" in manual
    assert "- Sitio completo" in manual


def test_produccion_automatica_preserva_dashboard_promovido():
    reusable=REUSABLE.read_text(encoding="utf-8")
    assert "cp -R publicado/dashboard/. site/dashboard/" in reusable
    assert "cp dashboard/index.html" not in reusable


def test_promocion_dashboard_es_explicita_y_trazable():
    manual=MANUAL.read_text(encoding="utf-8")
    assert "generar_estado_dashboard.py" in manual
    assert "cp dashboard/index.html dashboard/app.js dashboard/styles.css publicado/dashboard/" in manual
    assert 'git commit -m "chore: promover dashboard operativo"' in manual


def test_visor_enlaza_dashboard():
    html=(ROOT/"visor/index.html").read_text(encoding="utf-8")
    assert 'href="dashboard/"' in html


def test_evidencia_oculta_de_publicacion_se_sube():
    reusable=REUSABLE.read_text(encoding="utf-8")
    assert "path: .ddd-publication" in reusable
    assert "include-hidden-files: true" in reusable
