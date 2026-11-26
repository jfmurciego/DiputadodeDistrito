"""T-505 (auto-merge 1.3.4, P90 1.5.4), posteriores a la 2a: se deshace solo eso para comparar con las copias congeladas.

- auto-merge: la fusión REST con título y cuerpo vacío vuelve a la orden `gh pr merge --squash --match-head-commit`.
- p90-automatico: se quitan los pasos con «(T-505)» en el nombre (comprobación `coautores` del guardián).
"""
import copy
import re

_FUSION = re.compile(r'  titulo="\$\(jq -r \.title [^\n]*\n(?:  #[^\n]*\n)?  gh api -X PUT [^\n]*\\\n    -f commit_title="\$titulo \(#\$pr\)" -f commit_message=""\n')
_VIEJA = '  gh pr merge "$pr" --squash --match-head-commit "$SHA"\n'


def deshacer(nombre, d):
    d = copy.deepcopy(d)
    if nombre == "auto-merge":
        for paso in d["jobs"]["fusionar"]["steps"]:
            if "run" in paso:
                paso["run"] = _FUSION.sub(lambda _: _VIEJA, paso["run"])
    elif nombre == "p90-automatico":
        for job in d["jobs"].values():
            if "steps" in job:
                job["steps"] = [p for p in job["steps"] if "(T-505)" not in p.get("name", "")]
    return d
