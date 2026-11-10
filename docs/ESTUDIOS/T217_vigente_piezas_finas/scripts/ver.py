import json, sys
C = json.load(open(sys.argv[1]))
v = C.get("vigente", {})
print(f"## {C['territorio']} · ganador {C['ganador']} · huella {C['huella_resultado'][:12]}")
print("vigente:", {k: x for k, x in v.items() if k not in ("piezas_finas", "violaciones")},
      "violaciones:", [(x["regla"], x["ambito"]) for x in v.get("violaciones", [])][:5])
print("piezas finas:", v.get("piezas_finas") or next((c["extra"].get("piezas_finas") for c in C["candidatos"] if c["extra"].get("piezas_finas")), None))
for c in C["candidatos"]:
    e = c["extra"]
    print(f"  {c['id']:24} {c['estado']:9} fuera {c['fuera_tolerancia']:>3}  clave {[round(x,4) if isinstance(x,float) else x for x in (c.get('clave_naturalidad') or [])[:3]]}"
          f"  inicio {e.get('inicio')}  unidades {e.get('unidades')}  únicos {e.get('unicos')}")
