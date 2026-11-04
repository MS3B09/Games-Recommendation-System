# 🎮 Steam Games Analytics & Recommendation System

> **Current local assistant closeout — 2026-10-30:** [Measured results and remaining gates](docs/reports/assistant-closeout-2026-10-30.md) · [Current native architecture](docs/architecture-assistant.md) · [Finite protocol](docs/assistant-closeout-protocol.md). LLM-first conversation with bounded catalog/history tools and complete conversation-scoped server archives; independent New Chat and main discovery.261backend/74frontend tests and current real catalog/archive/UI integration pass.40-request RRF/cosine retrieval comparison has zero hard-filter violations; broader owner relevance/live naturalness/grounding remain pending, and warm retrieval p952.364s misses1s target. Original owner judgments require improvements, not final acceptance. All historical checkpoint/resume commands below are superseded by the new source-locked v22 development journal. No publication/portfolio-ready claim; hosted M2 unchanged.

> **Latest local revision — 2026-10-28:** [Friendly errors and recovery actions](docs/reports/friendly-errors-2026-10-28.md) implemented across chat/catalog/storage. Precise quota/provider/timeout reasons, local reset times, cooldowns, edit/retry/confirmed-reset actions and hidden diagnostic IDs;201backend/72frontend tests,10isolated DB checks and223scripted-provider catalog checks pass. Additive Alembic0006 preserves counters/limits; no new live inference. **Frozen v6 source/checkpoints are archived; current serving source requires a separately versioned evaluation continuation, not the older resume commands below.** R4/human/latency acceptance remains incomplete. Existing hosted M2 is unchanged. [Local operation](docs/operations-assistant.md).

> **Current R4 — 2026-10-27:** [Temporary quota increase and progress](docs/reports/r4-quota-increase-2026-10-27.md). **100 calls /1,500,000 reserved units per day** applied for R4, preserving consumed usage and normal50/500,000 defaults.193backend tests,15scratch quota checks and rollback-only runtime probe pass. Proposed v6 development13/13 passes; held-out32method-turns attempted with eight pricing-prose failures retained. Today's95calls/778,069units demonstrate the higher allowance; work pauses at conservative provider-token headroom, not the app ceiling. R4/quality/latency/human gates remain incomplete. Use the documented quota wrapper to resume, preserve C: journals, and restart the backend for runtime settings. Older statuses below are historical; hosted M2 unchanged.

> **Latest R4 checkpoint — 2026-10-26:** [Resume report](docs/reports/conversational-rag-r4-resume-2026-10-26.md). Played/undo handling and journal durability improved; current proposed played → inspect → undo passes3/3live. **189 backend tests**,313catalog/API integration assertions and18byte-exact packet replays pass their stated scopes. Current v6 development9/26attempts, one retained baseline claim failure; full live/human quality remains incomplete. Today's **50calls/393,494reserved units** exhaust daily calls. Resume on later UTC days under existing approval; preserve the authoritative C: journal described in the report. Current runtime retrieval p95717ms/90warm samples; small successful live totalp954.93s is not a complete latency/quality gate. No new credentials/configuration needed. October25 status below is historical; R4 is not accepted, hosted M2 unchanged.

> **Current status — 2026-10-25:** R0–R3 are complete locally; **R4 evaluation is in progress, not accepted**. The [public demo](https://steam-discovery.netlify.app/) remains hosted M2. [R4 results/failures](docs/reports/conversational-rag-evaluation.md) · [Architecture](docs/architecture-assistant.md) · [Walkthrough](docs/walkthrough-assistant.md) · [Local startup](docs/operations-assistant.md).

## Independent conversational RAG — R4 measured findings, incomplete quality gate

[Coding-agent implementation plan](docs/conversational-rag-plan.md) · [Visual HTML roadmap](docs/design/conversational-rag-plan.html) · [Progress](docs/progress.md)

**[Latest R4 fixes/checkpoint](docs/reports/conversational-rag-r4-continuation.md):** strict schema-constrained generation retains the four-card validator; unsupported-platform metadata and continuation references are corrected. The live proposed multiplayer → Spider-Man mismatch → more multiplayer journey now passes3/3. A fixed three-pass runtime benchmark measures retrieval p95 **487ms** across90warm observations; journaled spikes remain reported.180backend tests/static/contracts and313actual-catalog/scripted-provider assertions pass. The current paired development run is13/26turns; full held-out live/human quality is pending. **Additional free-tier inference is approved, but today's49/50calls (390,773reserved units) pause further two-call turns.** No new permission/key/config/model is needed to resume on later UTC days. Earlier [retrieval comparison/failures](docs/reports/conversational-rag-evaluation.md) remain: title Hit@5 9/9 vs8/9 is conditional retrieval, not end-to-end quality improvement. Frontend unchanged; R3 browser evidence remains historical. Restart backend for fixes. R4 is not accepted; publication remains separately gated.

## Current full-stack application

React/TypeScript frontend → modular FastAPI backend → one restricted PostgreSQL/pgvector database. The owner selected the exact **Current** visual and subsequently authorized completing M3 in that system. Both `/` and `/current-original.html` load the same guest application.

- Real catalog search, artwork favorite picker and explicitly submitted recommendations, starting with Hades / Windows / single-player / recorded ≤$20 USD.
- **My limits:** multi-choice required play modes → platform → catalog genre → a two-handle recorded-USD price range. All selected modes/genres must match; any selected platform may match. One desktop row, two columns at ≤900px, one column at ≤640px. $0–$0 means explicit free-to-play only. Exact exclusions/undo remain; the former advanced/preferred/unwanted text UI is removed and legacy terms clear on submission. Genre-led rows expose evidence, dates and tradeoffs; prices are snapshots, not live quotes.
- **Saved on this device:** favorites/preferences, `/saved` with cached metadata, recommendation feedback and recent summaries. Limits: 50 favorites / 200 saves / 500 feedback / 20 history. Main actions: Save Game (bookmark only), Not For Me (hide/exclude and gently downweight similar content), Already Played (hide/exclude exact title only). Dismissing one result retains the others in order; next explicit discovery applies saved feedback. Earlier Interested/exclusion records remain manageable.
- Protected versioned storage, truthful temporary mode when storage fails, tab synchronization and clear-data handling that invalidates pending work.
- **Independent floating game assistant:** native LLM conversation with bounded catalog/history tools, typed preferences/corrections and a complete server-side conversation archive within explicit storage ceilings. It never inherits main favorites, limits, feedback or saved/history lists. Canonical cards expand inside chat with Save/Steam. The tab retains the private capability and bounded reload cache; older originals remain paged from the server. New Chat/clear actually erase the current archive and begin with empty memory. AI chat requires configured Groq; main recommendations do not. Full conversational quality remains under evaluation.
- Free-only operation and no sign-in. Core discovery does not require an LLM. Broader relevance evaluation is underway against one cosine-only baseline; no quality improvement is claimed before actual owner judgments.

**Latest follow-up evidence:** 80 backend tests, strict mypy18/Ruff, 29 frontend tests, TypeScript/build/targeted lint/contracts. Seven real-catalog cases with mocked Groq/accounting; owned live eight API cases/twelve clean scans plus two fixture-card visual checks. One mobile-focus finding RESOLVED; **SHIP at ONE-MOBILE-FOCUS-FIX UI verdict scope**, not whole-product/publication approval. [Full scope and limits](docs/reports/independent-assistant.md). [Historical M4 evidence](docs/reports/m4-implementation.md) retains earlier 68/25 and SQL-budget checks; old integrated-text UI is superseded.

**Controls revision complete locally, main confirmed:** the one material metadata-failure fix is **RESOLVED**; **ship at ONE-SCORED-FIX verdict-pass scope**, not blanket whole-product/publication approval. All 18 refreshed captures were reopened with no regression attributable to the fix; earlier full controls review found no material visual/a11y regression. Unavailable facets preserve stored null maximum/free-only false, displaying **Any price / No maximum price** instead of imposing a rendering fallback as budget. Full **21 frontend tests (15 browser + 6 storage)**, TypeScript/build/lint and live **nine cases / 18 clean scans** passed again (axe 0/no overflow/page errors). Backend **51**, Ruff, strict mypy13, OpenAPI/generated drift and detector `[]` remain passed. [Controls report](docs/reports/discovery-controls.md) · [refreshed JSON](docs/reports/discovery-controls-live.json). Actual E: source used existing C: tools; fresh frontend installation, remote M3 CI and real-phone checks remain unverified.

**Completed M3 baseline, historical:** [49 backend/17 frontend checks and six-case/12-scan evidence](docs/reports/m3-implementation.md) retain the earlier four-material-fixes **RESOLVED / ship at the four-scored-fixes verdict-pass scope** disposition. This remains separate from the controls one-fix verdict and is not blanket whole-product/UI release approval.

**The final interactive :4173 build targets API :8001.** The verifier stops its owned :8002 API; no persistent owned background API remains. Start/restart the backend using the project-local `backend/.venv/Scripts/python.exe`, start/reuse preview and refresh both entry routes. [Current startup and AI prerequisites](docs/operations-assistant.md). Removed temporary interpreter paths are not current instructions. Main discovery needs no Groq key; actual chat additionally needs deliberate quota initialization and server-only provider configuration.

**Historical M2 evidence:** [implementation](docs/reports/m2-implementation.md) and [approved clean replay](docs/reports/m2-clean-replay.md) retain owner-confirmed hosted acceptance and two reproducible fresh PostgreSQL/pgvector builds. No evaluated relevance improvement is claimed.

Start locally with [independent-assistant operations](docs/operations-assistant.md); [M4 operations](docs/operations-m4.md) retain compatible backend text/model/quota workflows and [M3 operations](docs/operations-m3.md) the earlier device-storage baseline. [Deployment](docs/deployment.md) records historical hosted M2 settings. [DESIGN.md](DESIGN.md) describes the selected visual system.

## Preserved legacy Streamlit application

The sections below describe the earlier application and its historical features, not the current full-stack release status.

A comprehensive web application built with Streamlit that provides interactive analytics, AI-powered game recommendations, and an intelligent chatbot for exploring Steam's vast gaming library.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-FF4B4B.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 📊 Interactive Dashboard
- **Comprehensive Analytics**: Visualize 15,000+ Steam games with interactive charts
- **Price Analysis**: Distribution of game prices and discount patterns
- **Genre Insights**: Top 15 game genres with detailed breakdowns
- **Platform Support**: Cross-platform availability statistics (Windows, macOS, Linux, SteamOS)
- **Release Trends**: Monthly and yearly game release patterns
- **Developer Statistics**: Top developers and publishers by game count
- **Review Analysis**: User review distribution and sentiment
- **Word Cloud**: Visual representation of game descriptions and themes

### 🎯 AI-Powered Recommendation System
- **Smart Recommendations**: Content-based filtering using cosine similarity
- **Personalized Results**: Get 1-15 similar game suggestions
- **Rich Game Cards**: Beautiful UI with game images, pricing, and discounts
- **Detailed Information**: Full game details including:
  - Release dates
  - Developer and publisher info
  - Original pricing and current discounts
  - Direct Steam store links
- **Responsive Design**: Mobile-friendly interface with modern aesthetics

### 🤖 Intelligent Game Chatbot
- **Conversational AI**: Powered by Llama 3 (8B parameters) via Groq
- **RAG Architecture**: Retrieval-Augmented Generation using FAISS vector database
- **Natural Language Understanding**: Ask questions in plain English
- **Game Discovery**: Get personalized recommendations through conversation
- **Context-Aware**: Remembers chat history for coherent dialogues
- **Rich Responses**: Detailed game information and suggestions

## 📸 Screenshots

### Dashboard
<img width="1913" height="835" alt="Capture d'écran 2025-10-08 213546" src="https://github.com/user-attachments/assets/ac50485c-7a87-4fd6-a12b-4343ce89fe2b" />
<img width="1919" height="826" alt="Capture d'écran 2025-10-08 213608" src="https://github.com/user-attachments/assets/8ef49971-678b-4709-8d12-2ebe36b46efa" />


### Recommendation System
<img width="1916" height="816" alt="Capture d'écran 2025-10-08 213741" src="https://github.com/user-attachments/assets/116e61d7-0b1c-4e57-8327-120bab75e412" />
<img width="1910" height="841" alt="Capture d'écran 2025-05-30 183931" src="https://github.com/user-attachments/assets/65aa0407-6d1a-4e1c-bec5-07d55f524499" />

### AI Chatbot
<img width="1877" height="871" alt="Capture d'écran 2025-05-30 183347" src="https://github.com/user-attachments/assets/c0c0ee14-bd8d-45f9-87b2-53e79140ba05" />

---
## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Setup Instructions

1. **Clone the repository**
```bash
git https://github.com/HaFares/Game-Recommendation-System-.git
cd Game-Recommendation-System
```

2. **Create a virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up API keys**

Create a `.env` file in the root directory or set environment variables:
```bash
export HUGGINGFACEHUB_API_TOKEN="your_huggingface_token"
export GROQ_API_KEY="your_groq_api_key"
```

5. **Prepare data files**

Ensure the following files are in your project directory:
- `game_data_for_dashboard.csv` - Main dataset for analytics
- `games_data_recomendation.csv` - Dataset for recommendations
- `similarity_finale.pkl` - Pre-computed similarity matrix
- `faiss_index/` - FAISS vector database directory

## 📁 Project Structure

```
steam-games-analytics/
│
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
│
├── data/
│   ├── game_data_for_dashboard.csv
│   ├── games_data_recomendation.csv
│   └── similarity_finale.pkl
│
├── faiss_index/                    # Vector database for chatbot
│   ├── index.faiss
│   └── index.pkl
│
└── assets/                         # Images and static files
```

## 🎯 Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Navigation

Use the sidebar to switch between three main sections:

1. **Dashboard** - Explore comprehensive game analytics
2. **Recommendation System** - Find similar games based on your preferences
3. **Chatbot** - Chat with AI to discover new games

## 🛠️ Technologies Used

### Core Framework
- **Streamlit** - Web application framework
- **Python 3.8+** - Programming language

### Data Processing & Visualization
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Plotly** - Interactive visualizations
- **Matplotlib & Seaborn** - Statistical graphics
- **WordCloud** - Text visualization

### Machine Learning & AI
- **LangChain** - LLM application framework
- **Groq** - Fast LLM inference (Llama 3)
- **HuggingFace** - Embeddings (all-MiniLM-L6-v2)
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Text embeddings

### UI Components
- **streamlit-shadcn-ui** - Enhanced UI components

## 📊 Data Sources

The application uses Steam game data including:
- Game titles and descriptions
- Pricing information and discounts
- Release dates
- Developer and publisher details
- Platform compatibility
- User reviews and ratings
- Genre classifications
- Game images and Steam store links

## 🙏 Acknowledgments

- Steam for providing the gaming data
- Groq for fast LLM inference
- HuggingFace for embedding models
- The Streamlit team for the amazing framework
- The open-source community for various libraries used

⭐ If you find this project useful, please consider giving it a star!

Made with ❤️ and ☕
