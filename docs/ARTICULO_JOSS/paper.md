---
title: 'Diputado de Distrito: a reproducible, auditable engine for single-member district maps built from Spanish census sections'
tags:
  - Python
  - redistricting
  - GerryChain
  - ReCom
  - reproducibility
  - Spain
authors:
  - name: Jesus Murciego
    orcid: 0009-0002-4434-959X
    corresponding: true
    affiliation: 1
affiliations:
  - name: "Independent researcher"
    index: 1
date: 8 November 2026
bibliography: paper.bib
---

# Summary

Diputado de Distrito (DDD) is a modular Python engine that builds, optimises, validates and audits single-member electoral districts from the official census sections of the Spanish National Statistics Institute (INE). It is organised as eight modules (M01–M08) that each turn one verifiable state into the next: territorial base and population, adjacencies, graph, initial solution, optimisation, consolidation, electoral aggregation and result integration. Every module has a written contract, and every run records SHA-256 fingerprints of its inputs and outputs so that a published map can be traced back to its sources. The maps are a research exercise and have no official value.

# Statement of need

Spain elects the Congress by proportional representation in multi-member provincial constituencies. Studying what a single-member system would look like therefore requires building the districts from scratch, and the result depends on choices (number of districts, population tolerance, treatment of municipalities, islands and exclaves) that are rarely documented in a form others can re-run. General-purpose redistricting libraries provide the Markov-chain machinery [@deford2021recom; @gerrychain] but not the national data pipeline, the legal-territorial constraints of one country, or a trail that lets a reader verify that a published map comes from a stated source and configuration.

DDD targets researchers in political science and geography, and civic-data practitioners, who need to (i) regenerate a district map from public INE inputs, (ii) change one assumption and see which downstream products are invalidated, and (iii) check a published map against its evidence. The repository also publishes open data for 49 provincial scenarios for the 2023 general election, with 325 districts in total and per-file hashes in `datos_abiertos/INDEX.json` (CC-BY-4.0).

# State of the field

GerryChain [@gerrychain] implements the ReCom family of chains [@deford2021recom] over a dual graph and is the de facto reference for ensemble analysis. DDD does not replace it: it uses GerryChain as an alternative M05 engine (`docs/ENSEMBLES_GERRYCHAIN.md`) and adds what a country-scale study needs around it. Existing tools are, to our knowledge, oriented to US units (precincts, blocks) and US legal criteria; a contribution here would not have been feasible as a patch to them because the INE section hierarchy, the province-level seat quotas and the municipal-integrity rules are part of the problem definition rather than plug-in constraints. **PENDIENTE (autor): contrastar esta afirmación con una revisión bibliográfica y, si procede, citar herramientas alternativas (p. ej. Redistricting Analysis, otras bibliotecas de ensembles) antes del envío.**

# Software design

Three decisions shape the design. First, *modules as verifiable state transitions* (`docs/ARQUITECTURA_DEL_PROCEDIMIENTO.md`): a module exists only if it maps a checkable state A to a checkable state B, which allows re-running only the affected computation and comparing versions. Second, a *territory contract* (`docs/CONTRATO_TERRITORIO.md`, `docs/POLITICA_K_LIMITES_Y_ESQUEMA.md`): the number of districts K, its origin and justification, and the population limits (general profile 0.80 / 1.75 / 0.12) are declared before computation, and any exception must state motive, evidence and date beforehand, never after seeing an output. An executable gate (`herramientas/validar_contrato_territorial.py`) rejects ambiguous or incoherent contracts. Third, *provenance*: checkpoints and products carry fingerprints, and a change of engine, threshold or source invalidates compatible-looking checkpoints explicitly instead of silently reusing them. Territory generation is also kept separate from the later incorporation of electoral results, so that the geometry cannot be tuned to a political outcome. Dependencies are pinned in lock files (for example `requirements-gerrychain-m05.lock`: GerryChain 1.0.0, NetworkX 3.6.1).

# Research impact statement

**PENDIENTE (autor):** JOSS pide evidencia de impacto creíble o de potencial de impacto cercano (uso por terceros, citas, preprints, datos reutilizados). El repositorio solo puede aportar hechos comprobables: datos abiertos con hash (49 escenarios, 325 distritos), documentación pública y tests. No se declara aquí uso externo que no conste en ficheros.

# AI usage disclosure

**PENDIENTE (autor):** JOSS exige declarar el uso de herramientas de IA generativa en el software, la documentación y el paper. El historial del repositorio muestra trabajo con asistentes de código (Claude Code); el autor debe redactar el alcance real (qué partes, qué revisión humana).

# Acknowledgements

Territorial and population data are published by INE; official results by the Spanish Ministry of the Interior; seat tables by the BOE. **PENDIENTE:** financiación y agradecimientos.

# References
