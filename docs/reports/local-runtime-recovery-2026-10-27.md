# Local runtime recovery — 2026-10-27

**Later owner-chat follow-up,23:42UTC:** SQL now shows100calls/813,332reserved units, against verified runtime100/1,500,000. The daily application call cap is fully consumed. New chat cannot reset it; normal next-day allowance starts2026-10-28T00:00:00Z on the next reservation, with provider limits independent. Three calls were available at the earlier97-call recovery snapshot; one normal two-call reply can leave too little allowance for another. The exact stages of the owner's failed request were not captured, so no per-request attribution is claimed. This follow-up used no inference/reservations and left frozen evaluation journals unchanged.

## Reported failure and diagnosis

The owner's browser received HTTP503 from `/api/v1/facets` and Portal search while a chat request showed its pending indicator. Those responses establish a backend catalog failure, not a frontend build failure. The original backend had stopped before inspection; its underlying exception is unavailable, so the exact historical 503 cause is **not confirmed**.

Read-only checks confirmed the remote active catalog remains `m2-649714e8b26775165f105d02`. The configured restricted runtime could connect and retrieve Portal and Portal 2. IPv4 TCP connections succeeded; the machine's IPv6 routes were unavailable, but working IPv4 catalog access did not require changing networking or credentials. A fresh database probe took about12seconds including connection setup and two repository operations.

Both configured query encoder files were absent, and the original temporary model-cache directory was gone. Missing encoder files explain unavailable semantic retrieval; they do **not** by themselves explain the catalog 503s, because the API deliberately keeps seed/filter/lexical discovery available without the encoder.

## Recovery

- Restored the same public `sentence-transformers/all-MiniLM-L6-v2` files at their existing configured paths, pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. No model/version/configuration/source change.
- Tokenizer466,247bytes: SHA256 `be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037`.
- ONNX90,405,214bytes: SHA256 `6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452`.
- Both match the existing artifact manifest; loading and an actual384-dimensional CPU query encoding passed.
- Started a fresh single-worker backend on127.0.0.1:8001 with the existing ignored configuration, then the existing frontend preview on127.0.0.1:4173.

## Actual HTTP verification

| Request | Result | Measured time |
| --- | --- | ---: |
| `GET /api/v1/games?q=Portal&limit=12` |200, Portal and Portal2|2252ms|
| `GET /api/v1/facets` |200, supported platforms and filters|2430ms|
| `GET /api/v1/catalog/status` |200, semantic matching and AI configured both true|438ms|
| `GET /health/ready` |200|400ms|
| `POST /api/v1/discover`, Portal2 favorite, Windows, recorded USD maximum2000cents, no text |200, five recommendations, seed excluded|512ms|

The first two requests ran concurrently. CORS allowed the actual preview origin. These are local observations, not a hosted latency or quality acceptance result.

## Browser and chatbot verification

The actual browser → preview → running backend → restricted remote catalog flow passed favorite resolution, filters, Portal search and discovery, all HTTP200. Search displayed both Portal titles; submitting the default Hades preferences displayed **10 catalog-backed recommendations**. No core-flow console errors were observed. [Capture](local-recovery-browser-2026-10-27.png).

[Chat integration probe](local-recovery-chat-integration-2026-10-27.json) passed **223 checks**, with the actual restored encoder/catalog and scripted provider HTTP/budget, including three warm samples. Its scope is pipeline/contract verification, not live answer quality. Earlier313-check reports used more repetitions.

A separate browser-only injected503 for chat verified that the pending indicator disappears and the explicit error/request ID is shown. That single expected simulated network error is separate from the successful real catalog flow. The interception was removed and the verification browser's test chat reset. No live chatbot inference was sent.

Application accounting before and after recovery remains **97calls/789,272reserved units** for UTC2026-10-27: zero new actual calls/reservations from this work. This includes two calls/11,203units above the immutable evaluation snapshot of95/778,069; they are not added to frozen evaluation records. The prior conservative provider-headroom pause remains applicable. R4 acceptance is still incomplete.

## Running processes and next action

At handoff, the recovery-owned API process is **19744**, preview **14004**, both listening on their expected ports. They are left running for the owner's requested inspection. Recheck process identity before stopping either; do not stop unrelated owner processes. Startup/access logs are in `C:/Users/User/AppData/Local/Temp/opencode/catalog-recovery-api.{stdout,stderr}.log` and `catalog-recovery-preview.{stdout,stderr}.log`.

Open **http://127.0.0.1:4173/** and hard-refresh. Normal future manual startup remains in [operations](../operations-assistant.md); stop the currently running services before reusing their ports. Preserve the restored model files and authoritative R4 journal directory. No database migration/reset, source-frozen evaluation replay, paid resources or publication occurred.
