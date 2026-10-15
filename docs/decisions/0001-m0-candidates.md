# 0001 — M0 data, encoder and hosting candidates

Date: 2026-10-12. Status: **conditional; open gates remain**.

**Historical candidate record**, superseded by [0002 — measured M0 implementation path](0002-m0-feasibility-selection.md) and the subsequent implementation/deployment decisions in the [current plan](../../IMPLEMENTATION_PLAN.md). M0–M2 are now complete; the candidate-stage gates below are not current M2 blockers. M3 requires explicit approval.

1. **Legacy reuse:** historical metadata/identity leads only. Preserve originals and quarantine eligibility until verified. Current prices/platform zeros cannot support production hard filters.
2. **Source candidate:** Steam Store structured appdetails for identity, categories, platform and regional-price observations; Scrapling static pages for selective tags/extra evidence after canonical-ID verification. Ten-response probe supports this candidate. Undocumented endpoint stability, terms applicability, reviews and sensitive-content classification remain open before bulk selection.
3. **Model candidate:** pinned all-MiniLM-L6-v2 revision from the feasibility report. Float ONNX is the reference spike; AVX2 quantization shows promising memory/latency but is not activated. Offline parity and retrieval evaluation must decide production representation.
4. **Hosting:** retain Netlify Free, Render Free and Supabase Free planning direction conditionally. Actual account settings, full API memory and PostgreSQL sizing must pass; no paid substitution or mandatory AI service has been introduced.
5. **Tooling:** separate Python 3.13 job package with uv lock. Audit uses standard-library code and meaningful unittest checks; optional collection/benchmark dependencies remain separate from future API dependencies. CI test-tool integration is M1 work.

Evidence: [data audit](../reports/data-audit.md), [feasibility](../reports/feasibility.md). No M0 completion or recommendation-quality improvement is claimed.
