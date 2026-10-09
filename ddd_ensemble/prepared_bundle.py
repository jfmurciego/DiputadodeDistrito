from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


SCHEMA = "ddd.prepared-bundle/1.0"
REQUIRED_PRODUCTS = ("m01_sections", "m02_edges", "m03_graph")


class BundleValidationError(ValueError):
    """El paquete preparado no cumple el contrato."""


@dataclass(frozen=True)
class BundleValidation:
    manifest: dict[str, Any]
    archive_sha256: str
    verified_products: tuple[str, ...]


def _safe_member(info: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(info.filename)
    mode = info.external_attr >> 16
    return (
        bool(info.filename)
        and not path.is_absolute()
        and ".." not in path.parts
        and not stat.S_ISLNK(mode)
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_prepared_bundle(path: str, expected_territory: str | None = None) -> BundleValidation:
    with open(path, "rb") as source:
        archive_bytes = source.read()
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise BundleValidationError("El fichero no es un ZIP válido") from exc

    with archive:
        infos = archive.infolist()
        if not infos or any(not _safe_member(info) for info in infos):
            raise BundleValidationError("El ZIP contiene rutas inseguras o enlaces")
        names = {info.filename for info in infos if not info.is_dir()}
        manifests = sorted(name for name in names if PurePosixPath(name).name == "manifest.json")
        if len(manifests) != 1:
            raise BundleValidationError("Debe existir exactamente un manifest.json")
        try:
            manifest = json.loads(archive.read(manifests[0]))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise BundleValidationError("manifest.json no es JSON UTF-8 válido") from exc

        if manifest.get("schema") != SCHEMA:
            raise BundleValidationError(f"Esquema requerido: {SCHEMA}")
        territory = manifest.get("territory_id")
        if not isinstance(territory, str) or not territory:
            raise BundleValidationError("territory_id es obligatorio")
        if expected_territory and territory != expected_territory:
            raise BundleValidationError("El territorio no coincide con el solicitado")
        if not manifest.get("bundle_id"):
            raise BundleValidationError("bundle_id es obligatorio")

        quality = manifest.get("quality", {})
        if quality.get("status") != "PASS":
            raise BundleValidationError("La preparación no tiene estado PASS")
        if not isinstance(quality.get("section_count"), int) or quality["section_count"] <= 0:
            raise BundleValidationError("section_count debe ser positivo")
        if not isinstance(quality.get("population_total"), (int, float)) or quality["population_total"] <= 0:
            raise BundleValidationError("population_total debe ser positivo")

        fields = manifest.get("fields", {})
        for field in ("section_id", "population", "province", "municipality"):
            if not fields.get(field):
                raise BundleValidationError(f"Falta el campo canónico {field}")
        comarca_declared = bool(fields.get("comarca_code") or fields.get("comarca_name"))
        if comarca_declared and quality.get("comarca_coverage_ratio") != 1.0:
            raise BundleValidationError("La comarca declarada exige cobertura 1.0")

        products = manifest.get("products", {})
        verified: list[str] = []
        manifest_root = PurePosixPath(manifests[0]).parent
        for product_id in REQUIRED_PRODUCTS:
            descriptor = products.get(product_id)
            if not isinstance(descriptor, dict):
                raise BundleValidationError(f"Falta el producto {product_id}")
            rel_path = PurePosixPath(str(descriptor.get("path", "")))
            if rel_path.is_absolute() or ".." in rel_path.parts:
                raise BundleValidationError(f"Ruta insegura en {product_id}")
            candidates = [str(rel_path), str(manifest_root / rel_path)]
            member = next((candidate for candidate in candidates if candidate in names), None)
            if member is None:
                raise BundleValidationError(f"No existe el fichero declarado por {product_id}")
            expected_hash = descriptor.get("sha256")
            actual_hash = _sha256(archive.read(member))
            if not isinstance(expected_hash, str) or expected_hash.lower() != actual_hash:
                raise BundleValidationError(f"Hash incorrecto en {product_id}")
            verified.append(product_id)

    return BundleValidation(manifest, _sha256(archive_bytes), tuple(verified))
