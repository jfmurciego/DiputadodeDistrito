from __future__ import annotations

POPULATION_PASS = "PASS"
POPULATION_BELOW_FLOOR = "BELOW_FLOOR"
POPULATION_ABOVE_CEILING = "ABOVE_CEILING"


def _connected(nodes, adjacency):
    nodes = set(nodes)
    if not nodes:
        return False
    seed = next(iter(nodes))
    seen = {seed}
    stack = [seed]
    while stack:
        node = stack.pop()
        for neighbor in adjacency.get(node, set()):
            if neighbor in nodes and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == nodes


def validate_and_annotate_partition(
    gdf,
    *,
    id_field,
    district_field,
    province_field,
    expected_k,
    province_quota,
    adjacency,
    floor,
    cap,
    floor_exempt_partitions=(),
):
    """Validate structural M04 invariants and annotate population compliance.

    Population floor/cap violations are diagnostic only. Structural failures
    remain fatal: missing assignment, wrong K, wrong provincial cardinality,
    cross-province districts, or disconnected districts.
    """
    if district_field not in gdf.columns:
        raise SystemExit(f"M04: falta campo estructural {district_field}")
    if id_field not in gdf.columns:
        raise SystemExit(f"M04: falta campo estructural {id_field}")
    if province_field not in gdf.columns:
        raise SystemExit(f"M04: falta campo estructural {province_field}")
    if gdf[district_field].isna().any():
        missing = int(gdf[district_field].isna().sum())
        raise SystemExit(f"M04: {missing} secciones sin distrito")

    observed_k = int(gdf[district_field].nunique())
    if observed_k != int(expected_k):
        raise SystemExit(f"M04: generados {observed_k} distritos, esperado {expected_k}")

    quota = {str(k).zfill(2): int(v) for k, v in (province_quota or {}).items()}
    counts = {}
    district_province = {}
    for district, group in gdf.groupby(district_field):
        provinces = sorted(set(group[province_field].astype(str).str.zfill(2)))
        if len(provinces) != 1:
            raise SystemExit(f"M04: distrito {district} cruza provincia: {provinces}")
        province = provinces[0]
        district_province[int(district)] = province
        counts[province] = counts.get(province, 0) + 1

        nodes = set(group[id_field].astype(str))
        if not _connected(nodes, adjacency):
            raise SystemExit(f"M04: distrito {district} desconectado antes de exportar")

    if counts != quota:
        raise SystemExit(f"M04: cardinalidad provincial {counts}, esperada {quota}")

    exempt = {str(value).zfill(2) for value in floor_exempt_partitions}
    pops = gdf.groupby(district_field)["district_pop_section"].sum()
    status_by_district = {}
    rows = []
    for district, population in pops.items():
        district = int(district)
        population = int(population)
        province = district_province[district]
        if population > cap:
            status = POPULATION_ABOVE_CEILING
        elif population < floor and province not in exempt:
            status = POPULATION_BELOW_FLOOR
        else:
            status = POPULATION_PASS
        status_by_district[district] = status
        rows.append(
            {
                "district_id": district,
                "province": province,
                "population": population,
                "floor": float(floor),
                "cap": float(cap),
                "population_status": status,
            }
        )

    gdf["ddd_population_status"] = gdf[district_field].map(status_by_district)
    hard = sum(status != POPULATION_PASS for status in status_by_district.values())
    return {
        "hard_population_violations": int(hard),
        "districts_below_floor": sum(
            status == POPULATION_BELOW_FLOOR for status in status_by_district.values()
        ),
        "districts_above_ceiling": sum(
            status == POPULATION_ABOVE_CEILING for status in status_by_district.values()
        ),
        "population_districts": sorted(rows, key=lambda item: item["district_id"]),
        "province_counts": counts,
    }
