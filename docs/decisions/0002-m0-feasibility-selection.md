# 0002 — Select the measured M0 implementation path

Date: 2026-10-13. Status: **accepted engineering defaults**; deployment/release checks outstanding. Supersedes conditional choices in 0001 where evidence is now available.

- **Model:** pinned `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; CPU Sentence Transformers offline, float ONNX online; 256 tokens, mean pooling, normalized 384-dimensional output. Float parity passed; quantization is not selected. No quality improvement is claimed.
- **Capacity:** target 6,000 normalized/enriched games, prioritizing recognizable favorites and discovery value. Growth to 8,000 requires remeasurement; the 10,000 projection exceeds the target. This is a technical budget, not a quota to fill with low-quality records.
- **Retrieval:** exact pgvector cosine search plus PostgreSQL full-text indexing first. Approximate indexing requires measured size/latency/filtered recall.
- **Sources:** best-effort Steam Store appdetails, scoped aggregate reviews, selective Scrapling static-page enrichment. Verify identity; explicit released-game/content checks; unknown facts remain unknown/quarantined. No gate bypass or adopted Store API quota.
- **Free path:** Netlify static SPA, bounded one-worker Render API, Supabase PostgreSQL/pgvector. Local gates passed; actual Free account/settings and hosted behavior remain to verify.
- **Credentials:** separate privileged developer connection and least-privilege runtime login. The M1 runtime role exists; its password must be configured locally/provider-side by the owner. No browser DB credentials or end-user accounts.

Evidence: [feasibility](../reports/feasibility.md). M0 is complete as implementation feasibility, not as a public deployment, activated catalog, complete pipeline or relevance evaluation.
