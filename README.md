# Steam Game Discovery Platform

Steam Game Discovery Platform is a guest-friendly app for finding your next Steam game. Pick games you like, set your limits, and explore recommendations, catalog analytics, or an independent AI assistant. The live catalog contains **2,000 eligible games**.

**[Try the app](https://steam-discovery.netlify.app/) · [Explore the dashboard](https://steam-discovery.netlify.app/dashboard) · [API documentation](https://steam-discovery-api.fastapicloud.dev/docs)**

## What you can do

- **Discover games** using favorites and filters for price, platform, genre, and play mode. Save games or provide feedback for future recommendations.
- **Explore the catalog** through four summary metrics, eight charts, interactive plots, and a description word cloud.
- **Ask the assistant** for game information or recommendations in a conversation separate from your main discovery preferences.
- **Use it without an account.** Favorites, saved games, and feedback are saved in your browser; relevant preferences are sent to the API when you request recommendations. Assistant conversations use a server-side archive. Erase the chat in the app before clearing browser storage: clearing storage alone removes its access key, not the archive.

Prices are recorded US/USD observations, not live Steam offers. Linux support does not independently establish Steam Deck compatibility.

## How it works

The React/TypeScript frontend talks to a FastAPI backend backed by PostgreSQL and pgvector. Main discovery combines game-content embeddings with explicit filters and feedback. The assistant can use title lookup, game details, and lexical/semantic retrieval to ground its replies in the catalog. MiniLM embeddings run on CPU using ONNX; Groq receives assistant requests for optional, rate-limited language-model inference. Core discovery does not require an LLM.

The dashboard, discovery, and assistant use the same versioned catalog. Steam data is collected and normalized by developer jobs; source observations and generated artifacts are versioned separately from the app.

## Run locally

You need **Python 3.13**, **uv**, **Node.js 24**, and a PostgreSQL database with pgvector and an activated catalog. A fresh clone does **not** include the hosted database or the full 2,000-game snapshot. Follow the [setup guide](docs/setup.md) to prepare your own database, data, and optional AI configuration.

```bash
git clone https://github.com/MS3B09/Games-Recommendation-System.git
cd Games-Recommendation-System
uv sync --project backend --locked --extra dev --extra benchmark --extra api-spike
# Configure backend/.env from backend/.env.example first.
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. The development frontend defaults to the local API at port 8000. Never put database credentials or provider keys in frontend environment variables.

## Project history

This project began as a Streamlit analytics and recommendation app. Its full-stack rebuild followed these phases:

1. **M0:** audited the original data and tested source, hosting, and embedding feasibility.
2. **M1–M2:** built the API, database, deployment foundation, reproducible catalog pipeline, and initial 40-game discovery experience.
3. **M3–M4:** added guest persistence, feedback, richer controls, and AI-assisted discovery. The chat experience was later redesigned as an independent assistant.
4. **Assistant follow-up:** developed catalog retrieval, conversation state, validation, and browser integration; later simplified the conversation engine and added catalog-wide name grounding.
5. **Final release work:** expanded the shared catalog to 2,000 games, built the dashboard, and deployed the app. Dashboard and assistant refinements were published on November 7, 2026.

The final three-task plan replaced the older remaining M5–M8 roadmap; it did **not** turn unfinished evaluation work into a pass. [Progress and phase evidence](docs/progress.md) · [Documentation index](docs/README.md)

## Verification and limitations

The November 7 release passed [backend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600236) (302 tests, one skipped) and [frontend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600180) (81 tests). Hosted checks covered discovery, saves, dashboard interactions, and responsive accessibility in Chromium.

Recommendation relevance and assistant response quality are **not** claimed as comprehensively evaluated: earlier experiments include failures and incomplete human judgments. The latest catalog-name fix was tested against the active titles and scripted responses, but not with a fresh live-provider quality test. See the [evaluation summary](docs/evaluation.md) and [release history](docs/progress.md).

## Repository map

| Path | Contents |
| --- | --- |
| [`frontend/`](frontend/) | React application and browser tests |
| [`backend/`](backend/) | FastAPI, catalog and retrieval logic, migrations, jobs, and tests |
| [`data/fixtures/`](data/fixtures/) | Small tracked inputs and catalog manifests |
| [`docs/`](docs/README.md) | Setup, architecture, project history, and reports |

No project-wide license file has been declared; third-party components retain their own license notices.
