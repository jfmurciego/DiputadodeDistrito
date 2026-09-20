from pathlib import Path
import json

from herramientas.estado_operativo import build

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / ".github/workflows/desplegar-visor-publico.yml"
REUSABLE = ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"


def test_dashboard_fuente_y_snapshot_publicado_existen():
    for base in (ROOT / "dashboard", ROOT / "publicado/dashboard"):
        for name in ("index.html", "app.js", "styles.css"):
            assert (base / name).is_file()
    assert (ROOT / "publicado/dashboard/status.json").is_file()


def test_dashboard_se_genera_desde_estado_operativo_unico():
    payload = build(ROOT, "2025")
    assert payload["schema"] == "ddd-operational-state/1.0"
    galicia = next(r for r in payload["territories"] if r["territory_id"] == "galicia")
    assert galicia["g"] == "green"
    assert payload["kpis"]["complete"] >= 1
    assert payload["latest_validated"] is not None


def test_publicador_admite_llamada_manual_y_desde_00():
    manual = MANUAL.read_text(encoding="utf-8")
    reusable = REUSABLE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in manual
    assert "workflow_call:" in manual
    assert "workflow_call:" in reusable
    assert "workflow_dispatch:" not in reusable
    assert "pagina_publicar:" in manual
    assert "- Dashboard operativo" in manual
    assert "- Visor territorial" in manual
    assert "- Sitio completo" in manual


def test_produccion_automatica_preserva_dashboard_promovido():
    reusable = REUSABLE.read_text(encoding="utf-8")
    assert "cp -R publicado/dashboard/. site/dashboard/" in reusable
    assert "cp dashboard/index.html" not in reusable


def test_promocion_dashboard_y_readme_comparten_generador():
    manual = MANUAL.read_text(encoding="utf-8")
    assert "actualizar_estado_operativo" in manual
    assert "publicado/estado_operativo.json" in manual
    assert "publicado/dashboard/status.json" in manual
    assert "README.md" in manual
    assert "cp dashboard/index.html dashboard/app.js dashboard/styles.css publicado/dashboard/" in manual
    assert 'git commit -m "chore: sincronizar estado operativo para publicación"' in manual


def test_publicacion_desde_00_no_duplica_sincronizacion_y_manual_si_refresca():
    manual = MANUAL.read_text(encoding="utf-8")
    orch = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
    assert "estado_sincronizado:" in manual
    assert 'if [[ "$ESTADO_SINCRONIZADO" != "true" ]]' in manual
    assert "estado_sincronizado: true" in orch
    assert 'if [[ "$TARGET_PAGE" == "Dashboard operativo"' not in manual


def test_visor_enlaza_dashboard():
    html = (ROOT / "visor/index.html").read_text(encoding="utf-8")
    assert 'href="dashboard/"' in html


def test_evidencia_oculta_de_publicacion_se_sube():
    reusable = REUSABLE.read_text(encoding="utf-8")
    assert "path: .ddd-publication" in reusable
    assert "include-hidden-files: true" in reusable
