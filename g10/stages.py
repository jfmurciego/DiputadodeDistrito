"""Catálogo semántico G10 v2: las etapas no dependen de códigos Mxx."""
from __future__ import annotations
from dataclasses import dataclass

CATALOG_VERSION = "2.0.0"

@dataclass(frozen=True)
class Stage:
    stage_id: str
    stage_name: str
    layer_id: str
    legacy_module: str | None
    stage_order: int
    checkpoint: bool
    status: str = "active"

_STAGES = (
    Stage("G10_CONTROL", "Controlar lote y preservar evidencia", "ORCHESTRATION", None, 0, False),
    Stage("TERRITORY_CONTRACT", "Validar contrato territorial", "TERRITORIAL_GOVERNANCE", None, 0, False),
    Stage("TERRITORY_PREPARATION", "Preparar unidades territoriales", "TERRITORIAL_BASE", "M01", 1, True),
    Stage("TERRITORY_ADJACENCY", "Establecer vecindades territoriales", "TERRITORIAL_BASE", "M02", 2, True),
    Stage("TERRITORY_GRAPH", "Construir el grafo territorial", "TERRITORIAL_BASE", "M03", 3, True),
    Stage("DISTRICT_FORMATION", "Formar distritos iniciales", "DISTRICT_DESIGN", "M04", 4, True),
    Stage("DISTRICT_BALANCING", "Equilibrar y reparar distritos", "DISTRICT_DESIGN", "M05", 5, True),
    Stage("TERRITORIAL_CERTIFICATION", "Certificar distritos territoriales", "TERRITORIAL_ASSURANCE", "M06", 6, True),
    Stage("ELECTORAL_ENRICHMENT", "Incorporar resultados electorales", "ELECTORAL_PRODUCT", "M07", 7, True, "reserved"),
    Stage("PUBLIC_PRODUCT_PUBLICATION", "Publicar productos públicos", "PUBLIC_PRODUCT", "M08", 8, False, "reserved"),
)
BY_ID = {stage.stage_id: stage for stage in _STAGES}
BY_LEGACY = {stage.legacy_module: stage for stage in _STAGES if stage.legacy_module}

def describe(stage_id: str) -> dict[str, object]:
    stage = BY_ID[stage_id]
    return {"stage_catalog_version": CATALOG_VERSION, "stage_id": stage.stage_id,
            "stage_name": stage.stage_name, "layer_id": stage.layer_id,
            "legacy_module": stage.legacy_module, "stage_order": stage.stage_order,
            "checkpoint": stage.checkpoint, "status": stage.status}

def normalize(task: dict[str, object]) -> dict[str, object]:
    stage_id = task.get("stage_id")
    if not stage_id:
        legacy = str(task.get("legacy_module") or task.get("stage") or "")
        if legacy in BY_LEGACY:
            stage_id = BY_LEGACY[legacy].stage_id
        elif legacy in {"CONTROL", "G10_CONTROL"}:
            stage_id = "G10_CONTROL"
        elif legacy in {"CONTRACT", "TERRITORY_CONTRACT"}:
            stage_id = "TERRITORY_CONTRACT"
        else:
            raise ValueError(f"Etapa G10 desconocida: {legacy}")
    if stage_id not in BY_ID:
        raise ValueError(f"stage_id no existe en catálogo v{CATALOG_VERSION}: {stage_id}")
    result = dict(task)
    result.update(describe(str(stage_id)))
    return result
