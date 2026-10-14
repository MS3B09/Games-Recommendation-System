# 🎮 Steam Games Analytics & Recommendation System

> **Full-stack rebuild in progress:** M0 is complete; M1's local foundation is verified, with live-hosting verification pending owner deployment. [Run the new stack](docs/setup.md) · [Deploy M1](docs/deployment.md) · [Progress and checks](docs/progress.md). The Streamlit documentation below describes the preserved legacy application; the new recommendation experience/evaluation is not published yet.

## New application foundation

The React/TypeScript frontend calls a modular FastAPI backend using generated API contracts. PostgreSQL metadata uses a restricted runtime role, bounded SQLAlchemy pooling and explicit Alembic migrations. A responsive status page distinguishes an unpublished catalog from service failure; no sign-in is required.

**Verified locally:** 28 Python tests, backend lint/strict foundation typing, frontend lint/type/build/API drift checks, 7 browser checks and a real browser → API → PostgreSQL smoke test. No catalog/recommendations are activated at M1. CI and free-hosting configuration are included; live deployment remains to verify.

For setup commands, exact hosting settings and milestone boundaries, see [docs/setup.md](docs/setup.md) and [docs/deployment.md](docs/deployment.md).

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
