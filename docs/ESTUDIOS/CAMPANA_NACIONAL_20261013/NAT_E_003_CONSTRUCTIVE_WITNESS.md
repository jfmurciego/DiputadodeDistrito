# NAT-E-003 — conditional constructive witnesses for K=1

Date: 2026-10-13. Origin: new read-only Congress diagnostic. Base:
`21a4a150eb14f1abecd5d798b159d84a71df1f4a`.

## Scope and method

`ddd_core/congreso_constructive_witness.py` checks the 52 per-unit N08
preflight reports against each checkpoint, the versioned N08 topology product
manifest/unit, and the current Congress contract. The receipt binds SHA-256
for all five files per unit. It verifies the contract quota universe and
sum (`52/52`, `K=407`), N06/N08 policy values, edition-2025 source bindings,
preflight M01–M03 PASS, exact CUSEC uniqueness/coverage as represented in the
product, population totals, part inventory/component bindings, and every
accepted graph edge as a unique positive linear geometric contact with zero
overlap and a contact hash. No buffer, tolerance, synthetic edge, raw source
rewrite or M04–M06 call is performed.

For K=1, assigning every listed CUSEC to the single local label `01` is a
constructive witness only when section and polygon-part component inventories
are each connected and exact hard population bounds hold. The assignment is
diagnostic and conditional on the hashed source product. This label is not an
electoral district identifier. External boundary accreditation and named
exceptions are reported independently; missing accreditation keeps territorial
factibility at `INSUFFICIENT_EVIDENCE` even when an internal graph witness is
found. For other K values, no search is run. Component count greater than K
is reported only as `NECESSARY_CONDITION_FAILED_CONDITIONAL`, never as a
province-level impossibility proof.

## Reproduced 52-unit result

The evaluator consumed the already-produced per-province reports/checkpoints
and the existing N08 product and contract. All 52 receipts passed identity and
hash consistency (`errors=[]`). Results:

| Diagnostic state | Units |
| --- | ---: |
| `WITNESS_FOUND_CONDITIONAL` | 7 |
| `NECESSARY_CONDITION_FAILED_CONDITIONAL` | 9 |
| `SEARCH_NOT_RUN` | 36 |

Every unit remains `territorial_factibility_status=INSUFFICIENT_EVIDENCE`
because its external boundary accreditation is `NOT_EVIDENCED_NO_INDEPENDENT_BOUNDARY`.
No unit is declared territorially feasible, impossible, certified, generated,
or authorized by this diagnostic.

| CPRO | Sections | P 2025 | K | Floor | Cap | Assignment SHA-256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 05 | 308 | 160,738 | 1 | 136,628 | 184,848 | `c18fc8fa58854c42dc3da484d6ecdf1431d5167cf8d256c943f535b080fefd38` |
| 40 | 276 | 158,251 | 1 | 134,514 | 181,988 | `b8fad29b6d80e37dee73f018e9e9ba737e2ddab78ad4e7b61db5ba7225830353` |
| 42 | 218 | 90,183 | 1 | 76,656 | 103,710 | `8d7a0478e58ad1773b9717a6ab08770dd9276fca75a72649dd65c4c5dadfe8ad` |
| 44 | 284 | 136,091 | 1 | 115,678 | 156,504 | `0d318d8064d6f3fcd4e9eafd4fc621f21b55099b79e15f67e7a70a0f4f655c57` |
| 49 | 315 | 165,564 | 1 | 140,730 | 190,398 | `d537bc956525a19c772794825e6289767cd6716152728cb8783d2645f76095b3` |
| 51 | 56 | 83,567 | 1 | 71,032 | 96,102 | `b12d7d8964be79ba459de9f74954342a7d24bf2e2cc0dbaa8c7135653f55c170` |
| 52 | 44 | 87,067 | 1 | 74,007 | 100,127 | `ce8b4817945b4038fe772124b147528f64a0c2fc5282a4dbce6a2d2374c3cd3b` |

CPRO 34 also has K=1, but its represented section graph has three components
and its part graph has six; it therefore falls in the conditional component
bound group. Eight other units also have more represented physical-part
components than K, giving nine such units in total. The remaining 36 units
have K>1 and were not searched.

The full receipt, including assignments and per-unit hashes, is
`NAT_E_003_WITNESSES.json` (SHA-256 recorded in this commit's review note).
The input campaign reports are external runtime inputs; their individual
hashes are embedded in the receipt. The compact reproduction command is:

```sh
python -m ddd_core.congreso_constructive_witness \
  --preflight-root <root-with-PREFLIGHT_CPRO01..52> \
  --product-root docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto \
  --contract territorios/congreso/contrato_congreso_2026.json \
  --output NAT_E_003_WITNESSES.json
```

The receipt fixes `generation_authorized=false`, `districts_generated=0`, and
`product_certification=NOT_PERFORMED` for every result and at batch level.
