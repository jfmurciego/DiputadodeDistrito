# NAT-E-002 — bounded exact connected partition diagnostic

Status: synthetic technical component; not integrated and not a territorial
feasibility finding. Base: `21a4a150eb14f1abecd5d798b159d84a71df1f4a`.

`ddd_core/congreso_exact_feasibility.py` provides a small-graph diagnostic
without changing M04/M05 or the shared autonomous engine. It enumerates
connected vertex subsets within exact integer population bounds, then solves
an exact cover for exactly K non-empty groups. A witness is returned only
after a complete cover is found. `PROVEN_INFEASIBLE` is returned for a sound
aggregate arithmetic contradiction or after both subset enumeration and
exact-cover search complete. If either configured budget is exceeded, the
status is `SEARCH_EXHAUSTED`; it never implies impossibility.
The connected-group budget counts all distinct visited subsets, including the
initial singleton subsets, so it is enforced before exact-cover search begins.

Every result includes a SHA-256 of the canonical graph/weight/bounds input.
Infeasibility metadata records whether search was exhaustive, its method and
counts; reproduction consists of rerunning the function on the same input and
checking the digest. This is not a standalone mathematical proof certificate
independent of the solver implementation.

The API does not consume administrative identities, sources, municipality
rules, exceptions, or actual territorial graphs. A `SOLUTION_FOUND` proves
only connected bounded partition existence for the supplied synthetic graph;
it does not establish provincial feasibility or authorize generation.

Tests: `tests/test_congreso_exact_feasibility.py` covers a four-vertex path
positive witness, exhaustive small infeasibility, group/state budget
exhaustion distinction, deterministic input identity and invalid inputs.
