"""Small helper for a root-conditioned connectivity lazy cut."""


def rooted_cut_terms(component, boundary, x_var, root_var):
    """Return coefficients and upper bound for a valid rooted cut.

    For a component S, require x(S)-x(N(S))-|S|r(S) <= |S|-1.
    If all of S is assigned but has no assigned boundary, this is violated
    exactly when the selected root lies outside S. If the root lies in S,
    the cut is relaxed, allowing a valid connected district equal to S.
    """
    component = tuple(component)
    if not component:
        raise ValueError('empty component')
    terms = {x_var[u]: 1 for u in component}
    for v in set(boundary) - set(component):
        terms[x_var[v]] = terms.get(x_var[v], 0) - 1
    for u in component:
        terms[root_var[u]] = terms.get(root_var[u], 0) - len(component)
    return terms, len(component) - 1
