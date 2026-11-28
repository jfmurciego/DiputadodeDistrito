"""T-510 (P40 1.8.0): deshace en memoria SOLO el traslado de las dos subidas a R2 de la web al job `subir_r2` (entorno publicacion):
vuelven a `publicar` justo antes de «Promover la doble vuelta a mapas/ (T-443)» con sus condiciones de la 1.7.0, se quitan el `id: persistir`,
las salidas de `publicar` y el job `subir_r2`. Si algo no está exactamente una vez, falla (control negativo)."""
import copy

DATOS = "Datos de la web en R2 (T-430)"
WEB = "Web en R2 (T-430)"
PROMOVER = "Promover la doble vuelta a mapas/ (T-443)"
PERSISTIR = "Persistir registro sólo después del despliegue"
SALIDAS = {"registro_persistido": "${{ steps.persistir.outcome }}", "artefacto_pages": "github-pages-${{ github.run_attempt }}"}
IF_DATOS = ("${{ steps.sitio.outcome == 'success' }}", "${{ github.ref == 'refs/heads/main' }}")
IF_WEB = ("${{ steps.datos_web.outcome == 'success' }}", "${{ github.ref == 'refs/heads/main' && steps.datos_web.outcome == 'success' }}")


def _uno(steps, nombre):
    hay = [s for s in steps if s.get("name") == nombre]
    assert len(hay) == 1, f"T-510: «{nombre}» no está exactamente una vez"
    return hay[0]


def deshacer_p40(p40: dict) -> dict:
    d = copy.deepcopy(p40)
    jobs = d["jobs"]
    assert "subir_r2" in jobs and jobs["subir_r2"].get("environment") == "publicacion", "T-510: falta el job subir_r2 con entorno publicacion"
    sube = jobs.pop("subir_r2")["steps"]
    pub = jobs["publicar"]
    assert pub.pop("outputs", None) == SALIDAS, "T-510: salidas de publicar distintas"
    persistir = _uno(pub["steps"], PERSISTIR)
    assert persistir.pop("id", None) == "persistir", "T-510: falta id persistir"
    datos, web = _uno(sube, DATOS), _uno(sube, WEB)
    assert datos.get("if") == IF_DATOS[0] and web.get("if") == IF_WEB[0], "T-510: condiciones de los pasos de R2 distintas"
    assert web.pop("id", None) == "web_r2", "T-510: falta id web_r2"
    datos["if"], web["if"] = IF_DATOS[1], IF_WEB[1]
    # orden de claves de la 1.7.0 (name, id, if, …) para que el YAML vuelva a ser el mismo
    web = {k: web[k] for k in ("name", "if", *[k for k in web if k not in ("name", "if")])}
    assert not [s for s in pub["steps"] if s.get("name") in (DATOS, WEB)], "T-510: pasos de R2 de la web aún en publicar"
    i = [s.get("name") for s in pub["steps"]].index(PROMOVER)
    pub["steps"][i:i] = [datos, web]
    return d
