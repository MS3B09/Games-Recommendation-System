
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
import ast
import streamlit_shadcn_ui as ui
import streamlit as st
import pandas as pd
import pickle
import numpy as np
import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain import PromptTemplate
import random
from time import sleep

def load_common_css():
    st.markdown("""
    <style>
    :root {
        --primary: #1b2838;
        --secondary: #2a475e;
        --accent: #66c0f4;
        --light: #f8f9fa;
        --dark: #171a21;
        --success: #28a745;
        --warning: #ffc107;
        --danger: #dc3545;
        --radius: 16px;
        --shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    
    
    /* Title and header */
    .title-container {
        text-align: center; 
        padding: 30px 20px; 
        margin-bottom: 10px;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
    }
    
    .game-title {
        font-size: 2.8rem; 
        font-weight: 800;
        background: linear-gradient(90deg, #1b2838 0%, #2a475e 50%, #66c0f4 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        animation: pulse 2s infinite;
    }
    
    .tagline {
        font-size: 1.2rem;
        color: var(--dark);
        opacity: 0.8;
        margin-bottom: 20px;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .game-title {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    #############################

# Sidebar Navigation
st.set_page_config(page_title="🎮 Game Suite", layout="wide", initial_sidebar_state="expanded")
load_common_css()
# 📊 Sidebar
with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <img src="https://i.pinimg.com/736x/b4/36/19/b43619b5bf760747bbbb327746a3a91c.jpg" width="80" style="margin-bottom: 15px;">
                <h3 style="color: var(--primary); margin-bottom: 5px;">Step into the world of gaming</h3>
            </div>
            """, unsafe_allow_html=True)
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Recommendation System", "Chatbot"])

# ========== Dashboard ==========
if page == "Dashboard":

    # Page configuration
    # Title Section
    st.markdown("""
    <div class="title-container">
        <div class="game-title">Steam Games Dashboard</div>
        <div class="tagline">Explore comprehensive analytics and insights about thousands of games</div>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
            <span style="background: #e9f7fe; color: #0c7abf; padding: 5px 12px; border-radius: 20px;">📊 15,000+ Games</span>
            <span style="background: #e6f9ee; color: #0a8f4e; padding: 5px 12px; border-radius: 20px;">📈 Real-time Stats</span>
            <span style="background: #f5e9ff; color: #1b2838; padding: 5px 12px; border-radius: 20px;">🔍 Deep Insights</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Load dataset
    @st.cache_data
    def load_data():
        df = pd.read_csv("game_data_for_dashboard.csv")  # Replace with actual file path
        return df

    df = load_data()

    # Data cleaning
    df['Original Price'] = pd.to_numeric(df['Original Price'], errors='coerce')
    df['Discount %'] = pd.to_numeric(df['Discount %'], errors='coerce')
    df['Release Month'] = pd.Categorical(df['Release Month'], 
                                        categories=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                                        ordered=True)

    # Process genre data - fixed approach
    df['genre'] = df['genre'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    all_genres = [genre for sublist in df['genre'] for genre in sublist]
    genre_counts = pd.Series(all_genres).value_counts().head(15).reset_index()
    genre_counts.columns = ['Genre', 'Count']  # Proper column names

    # Process platform data
    platform_counts = pd.DataFrame({
        'Platform': ['Windows', 'macOS', 'Linux', 'SteamOS'],
        'Count': [df['Windows'].sum(), df['macOS'].sum(), df['Linux'].sum(), df['SteamOS'].sum()]
    })

    # Process review data - fixed approach
    if 'review_count' in df.columns:
        review_counts = df['review_count'].value_counts().sort_index().reset_index()
        review_counts.columns = ['Review Count', 'Number of Games']
        
    if 'review_type' in df.columns:
        review_type_counts = df['review_type'].value_counts().reset_index()
        review_type_counts.columns = ['Review Type', 'Count']


    # Les métriques
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("<div style='font-weight:bold; font-size:22px;'>Total Games</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:28px; color:green;'>{df.shape[0]:,}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='font-weight:bold; font-size:22px;'>Avg. Price</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:28px; color:green;'>${df['Original Price'].mean():.2f}</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div style='font-weight:bold; font-size:22px;'>Avg. Discount</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:28px; color:green;'>{df['Discount %'].mean():.2f}%</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("<div style='font-weight:bold; font-size:22px;'>Total Developers</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:28px; color:green;'>{df['developer'].nunique()}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Row 1: Games by Month & Free vs Paid
    col1, col2 = st.columns(2)

    with col1:
        fig_month = px.histogram(
            df,
            x='Release Month',
            color='Release Year',
            barmode='group',
            title='<b>Games Released by Month</b>',
            category_orders={'Release Month': df['Release Month'].cat.categories}
        )
        fig_month.update_layout(
            xaxis_title='Month', 
            yaxis_title='Number of Games',
            title_x=0.5  # center the title
        )
        st.plotly_chart(fig_month, use_container_width=True)

    with col2:
        free_paid_counts = df['Free/paid'].value_counts().reset_index()
        free_paid_counts.columns = ['Type', 'Count']

        fig_free_paid = px.pie(
            free_paid_counts,
            values='Count',
            names='Type',
            hole=0.4,
            title='<b>Free vs Paid Games</b>',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_free_paid.update_traces(textposition='inside', textinfo='percent+label')
        fig_free_paid.update_layout(title_x=0.5)
        st.plotly_chart(fig_free_paid, use_container_width=True)

    # Row 2: Price Distribution & Discount Distribution
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        price_bins = [0, 5, 10, 20, 50, 100, float('inf')]
        price_labels = ['0–5', '5–10', '10–20', '20–50', '50–100', '>100']
        df['Price Range'] = pd.cut(df['Original Price'], bins=price_bins, labels=price_labels, right=False)

        price_counts = df['Price Range'].value_counts().sort_index().reset_index()
        price_counts.columns = ['Price Range', 'Number of Games']

        fig_price = px.bar(
            price_counts,
            x='Price Range',
            y='Number of Games',
            title='<b>Games by Price Range</b>',
            text='Number of Games'
        )
        fig_price.update_layout(
            xaxis_title='Price ($)', 
            yaxis_title='Games Count',
            title_x=0.5
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with col2:
        discount_bins = [0, 10, 25, 50, 75, 90, 100, float('inf')]
        discount_labels = ['0–10%', '10–25%', '25–50%', '50–75%', '75–90%', '90–100%', '>100%']
        df['Discount Range'] = pd.cut(df['Discount %'], bins=discount_bins, labels=discount_labels, right=False)

        discount_counts = df['Discount Range'].value_counts().sort_index().reset_index()
        discount_counts.columns = ['Discount Range', 'Number of Games']

        fig_discount = px.bar(
            discount_counts,
            x='Discount Range',
            y='Number of Games',
            title='<b>Games by Discount %</b>',
            text='Number of Games'
        )
        fig_discount.update_layout(
            xaxis_title='Discount %', 
            yaxis_title='Games Count',
            title_x=0.5
        )
        st.plotly_chart(fig_discount, use_container_width=True)

    # Row 3: Genre Distribution & Supported Platforms
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig_genre = px.bar(
            genre_counts,
            x='Genre',
            y='Count',
            title='<b>Top 15 Game Genres</b>',
            color='Count',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig_genre.update_layout(
            xaxis_title='Genre', 
            yaxis_title='Number of Games',
            title_x=0.5
        )
        st.plotly_chart(fig_genre, use_container_width=True)

    with col2:
        fig_platform = px.bar(
            platform_counts,
            x='Platform',
            y='Count',
            title='<b>Supported Platforms</b>',
            color='Platform',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_platform.update_layout(
            xaxis_title='Platform', 
            yaxis_title='Number of Games',
            title_x=0.5
        )
        st.plotly_chart(fig_platform, use_container_width=True)

    # Row 4: Top Developers/Publishers & Review Analysis
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if 'developer' in df.columns:
            top_devs = df['developer'].value_counts().head(10).reset_index()
            top_devs.columns = ['Developer', 'Count']
            
            fig_dev = px.bar(
                top_devs,
                x='Developer',
                y='Count',
                title='<b>Top 10 Developers by Game Count</b>',
                color='Count',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_dev.update_layout(
                xaxis_title='Developer', 
                yaxis_title='Number of Games',
                title_x=0.5
            )
            st.plotly_chart(fig_dev, use_container_width=True)

    with col2:
        if 'review_type' in df.columns and hasattr(review_type_counts, 'columns'):
            fig_review = px.pie(
                review_type_counts,
                values='Count',
                names='Review Type',
                title='<b>Review Type Distribution</b>',
                hole=0.3,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_review.update_traces(textposition='inside', textinfo='percent+label')
            fig_review.update_layout(title_x=0.5)
            st.plotly_chart(fig_review, use_container_width=True)

    # Row 5: Word Cloud from Game Descriptions
    st.markdown("---")
    st.subheader("Word Cloud from Game Descriptions")

    if 'about_game' in df.columns:
        text = ' '.join(df['about_game'].dropna().astype(str))
        max_chars = 1_000_000  # 1 million characters
        text = text[:max_chars]
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

        fig, ax = plt.subplots(figsize=(13, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)


# ========== Recommendation System ==========
elif page == "Recommendation System":

    # --- Custom CSS for enhanced typography and styling ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .game-card {
            border: 1px solid #e8ecf0;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
            border: 1px solid rgba(255,255,255,0.8);
            backdrop-filter: blur(10px);
        }
        
        .game-card:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 12px 28px rgba(0,0,0,0.15), 0 4px 8px rgba(0,0,0,0.08);
            border-color: #667eea;
        }
        
        .price-free {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.4em;
            background: linear-gradient(135deg, #10b981, #34d399, #6ee7b7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
            letter-spacing: -0.02em;
        }
        
        .price-paid {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.4em;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8, #1e40af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
            letter-spacing: -0.02em;
        }
        
        .price-na {
            font-family: 'Inter', sans-serif;
            color: #64748b;
            font-style: italic;
            font-size: 1.1em;
            font-weight: 400;
            opacity: 0.8;
        }
        
        .game-title {
            font-family: 'Poppins', sans-serif;
            font-size: 1.25em;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 12px;
            text-align: center;
            line-height: 1.4;
            letter-spacing: -0.01em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        .game-info {
            background: linear-gradient(135deg, #f1f5f9 0%, #f8fafc 100%);
            padding: 16px;
            border-radius: 12px;
            margin: 12px 0;
            border-left: 4px solid #667eea;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
        }
        
        .release-date {
            font-family: 'Inter', sans-serif;
            color: #475569;
            font-size: 0.9em;
            font-weight: 500;
            letter-spacing: 0.025em;
            opacity: 0.9;
        }
        
        .developer-info {
            font-family: 'Inter', sans-serif;
            color: #64748b;
            font-size: 0.85em;
            font-weight: 400;
            font-style: italic;
            margin-top: 4px;
            opacity: 0.8;
        }
        
        .discount-badge {
            background: linear-gradient(135deg, #ef4444, #dc2626, #b91c1c);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-family: 'Poppins', sans-serif;
            font-size: 0.75em;
            font-weight: 700;
            display: inline-block;
            margin-left: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .main-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            font-size: 3.2em;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
            text-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
            line-height: 1.1;
        }
        
        .main-subtitle {
            font-family: 'Inter', sans-serif;
            color: #64748b;
            text-align: center;
            font-size: 1.2em;
            font-weight: 400;
            margin-bottom: 32px;
            letter-spacing: 0.01em;
            line-height: 1.6;
        }
        
        .similar-games-header {
            font-family: 'Poppins', sans-serif;
            color: #1e293b;
            font-weight: 700;
            font-size: 1.8em;
            border-bottom: 3px solid transparent;
            background: linear-gradient(90deg, #667eea, #764ba2) padding-box,
                        linear-gradient(90deg, #667eea, #764ba2) border-box;
            border-image: linear-gradient(90deg, #667eea, #764ba2) 1;
            padding-bottom: 12px;
            margin-bottom: 28px;
            letter-spacing: -0.01em;
        }
        
        .feature-text {
            font-family: 'Inter', sans-serif;
            color: #475569;
            font-size: 1.05em;
            line-height: 1.7;
            font-weight: 400;
            margin-bottom: 8px;
        }
        
        .feature-title {
            font-family: 'Poppins', sans-serif;
            color: #1e293b;
            font-weight: 600;
            font-size: 1.4em;
            margin-bottom: 16px;
            letter-spacing: -0.01em;
        }
        
        .sidebar-header {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 1.1em;
            color: #1e293b;
            letter-spacing: -0.005em;
        }
        
        .metric-label {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 0.9em;
            color: #64748b;
            letter-spacing: 0.025em;
        }
        
        .welcome-info {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Inter', sans-serif;
            color: #1e40af;
            font-weight: 500;
        }
        
        .warning-text {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border: 1px solid #f59e0b;
            border-radius: 12px;
            padding: 16px;
            font-family: 'Inter', sans-serif;
            color: #92400e;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Load Data and Model ---
    st.cache_data.clear()
    def load_data():
       df = pd.read_csv("games_data_recomendation.csv")
       return df
    @st.cache_data 
    def load_similarity_matrix():
        similarity_matrix = pickle.load(open("similarity_finale.pkl", 'rb'))
        return similarity_matrix
    try:
        df = load_data()
        similarity_matrix = load_similarity_matrix()
        
        # Check if model and data dimensions match
        if similarity_matrix is not None and df is not None:
            if similarity_matrix.shape[0] != df.shape[0] or similarity_matrix.shape[1] != df.shape[0]:
                st.error(f"Mismatch between similarity matrix dimensions ({similarity_matrix.shape}) and dataset length ({df.shape[0]}). Cannot proceed.")
                st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    # --- Recommendation Function ---
    def get_recommendations(title, similarity_matrix, df, k=5):
        try:
            idx = df[df["title"] == title].index[0]
            sim_scores = list(enumerate(similarity_matrix[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:k+1]
            game_indices = [i[0] for i in sim_scores]
            return df.iloc[game_indices]
        except IndexError:
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting recommendations: {e}")
            return pd.DataFrame()

    # --- Helper Functions ---
    def format_price(price):
        """Format price with appropriate styling"""
        if pd.isna(price):
            return '<span class="price-na">Price N/A</span>'
        elif price == 0:
            return '<span class="price-free">FREE</span>'
        else:
            return f'<span class="price-paid">${price:.2f}</span>'

    def format_release_date(date):
        """Format release date"""
        if pd.isna(date) or date == 'N/A':
            return "N/A"
        return f"{date}"

    def get_discount_badge(discount):
        """Get discount badge HTML if discount exists"""
        if pd.notna(discount) and discount > 0:
            return f'<span class="discount-badge">-{discount:.0f}%</span>'
        return ""

    # --- Initialize session state for details ---
    if "selected_game_details" not in st.session_state:
        st.session_state.selected_game_details = None
    if "show_details_dialog" not in st.session_state:
        st.session_state.show_details_dialog = False

    # --- Page Layout ---
        # Title Section
    st.markdown("""
    <div class="title-container">
        <div class="game-title">🎮 Game Recommendation System</div>
        <div class="tagline">✨Discover your next favorite game with AI-powered recommendations</div>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
            <span style="background: #e9f7fe; color: #0c7abf; padding: 5px 12px; border-radius: 20px;">🤖 AI-Powered</span>
            <span style="background: #e6f9ee; color: #0a8f4e; padding: 5px 12px; border-radius: 20px;">🎯 Personalized</span>
            <span style="background: #f5e9ff; color: #1b2838; padding: 5px 12px; border-radius: 20px;">💎 3,000+ Games</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Sidebar: Settings ---
    with st.sidebar:
        st.markdown('<h2 class="sidebar-header">🛠️ Recommendation Settings</h2>', unsafe_allow_html=True)
        k_recommendations = st.slider(
            "Number of Recommendations",
            min_value=1,
            max_value=15,
            value=5,
            step=1,
            key="k_slider",
            help="Choose how many similar games you'd like to discover"
        )
        
        



    # --- Main Area: Game Selection ---
    game_list = df["title"].unique().tolist()
    selected_game = st.selectbox(
        "🔍 Choose a game you enjoy and let our AI find similar titles:",
        options=["Select a game..."] + sorted(game_list),
        index=0,
        key="game_select",
        help="Start typing to search for your favorite game"
    )

    if selected_game != "Select a game...":
        st.markdown(f'Games Curated for Fans of "{selected_game}"</h2>', unsafe_allow_html=True)
        recommended_games = get_recommendations(selected_game, similarity_matrix, df, k=k_recommendations)

        if not recommended_games.empty:
            # Display recommendations in cards
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, (index, row) in enumerate(recommended_games.iterrows()):
                with cols[idx % num_cols]:
                    # Game card container
                    st.markdown('<div class="game-card">', unsafe_allow_html=True)
                    
                    # Game image
                    if pd.notna(row.get("image")) and row["image"]:
                        st.image(row["image"], width=300, use_container_width=True)
                    else:
                        st.markdown("*No image available*")
                    
                    # Game title
                    st.markdown(f'<div class="game-title">{row["title"]}</div>', unsafe_allow_html=True)
                    
                    # Game info container
                    st.markdown('<div class="game-info">', unsafe_allow_html=True)
                    
                    # Price and Release Date side by side
                    col_price, col_date = st.columns([1, 1])
                    with col_price:
                        price_html = format_price(row.get("Original Price"))
                        discount_badge = get_discount_badge(row.get("Discount %", 0))
                        st.markdown(f'{price_html}{discount_badge}', unsafe_allow_html=True)
                    
                    with col_date:
                        release_date = format_release_date(row.get("Release Date"))
                        st.markdown(f'<div class="release-date"> {release_date}</div>', unsafe_allow_html=True)
                    
                    # Developer info
                    if pd.notna(row.get("developer")):
                        st.markdown(f'<div class="developer-info"> Developed by : {row["developer"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Close game-info
                    
                    # Action buttons
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if pd.notna(row.get("Link")):
                            st.link_button("View on Steam", row["Link"], use_container_width=True)
                    
                    with col_btn2:
                        if st.button("Full Details", key=f"details_{index}", use_container_width=True):
                            st.session_state.selected_game_details = row.to_dict()
                            st.session_state.show_details_dialog = True
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Close game-card
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-text">🔍 Hmm, we couldn\'t find similar games for that title. Try selecting a different game from our extensive library!</div>', unsafe_allow_html=True)
    # --- Game Detail Dialog --- 
    if st.session_state.show_details_dialog and st.session_state.selected_game_details:
        game = st.session_state.selected_game_details

        @st.dialog(f"Game Details: {game['title']}")
        def show_game_details(game_details):
            # Header with image
            col1, col2 = st.columns([1, 2])
            with col1:
                if pd.notna(game_details.get("image")) and game_details["image"]:
                    st.image(game_details["image"], use_container_width=True)
            
            with col2:
                st.markdown(f"# {game_details['title']}")
                
                # Price and discount
                price_html = format_price(game_details.get("Original Price"))
                discount_badge = get_discount_badge(game_details.get("Discount %", 0))
                st.markdown(f'## {price_html}{discount_badge}', unsafe_allow_html=True)
                
                # Basic info with enhanced styling
                st.markdown(f"**Released:** {game_details.get('Release Date', 'Unknown Date')}")
                st.markdown(f"**Developer:** {game_details.get('developer', 'Independent Developer')}")
                st.markdown(f"**Publisher:** {game_details.get('publisher', 'Self-Published')}")

            st.markdown("---")
            
            # Description
            st.subheader("Game Overview")
            description = game_details.get("about_game", 'N/A')
            if not description or pd.isna(description) or description == "N/A":
                description = game_details.get('Game Description', 'This game offers an exciting gaming experience with unique features and engaging gameplay mechanics that will keep you entertained for hours.')
            
            # Clean up description if it's too long
            if len(str(description)) > 800:
                description = str(description)[:800] + "..."
            
            st.markdown(f'<div class="feature-text">{description}</div>', unsafe_allow_html=True)
            
            # Additional metrics
            st.markdown("---")
            st.subheader("Game Economics & Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                price_val = game_details.get("Original Price")
                if pd.notna(price_val):
                    if price_val == 0:
                        st.metric("Price", "FREE", delta="Best Value!", delta_color="normal")
                    else:
                        st.metric("Price", f"${price_val:.2f}")
                else:
                    st.metric("Price", "Contact Developer")
            
            with col2:
                discount_val = game_details.get('Discount %', 0)
                if discount_val > 0:
                    savings = game_details.get('Original Price', 0) * discount_val / 100
                    st.metric("Discount", f"{discount_val:.1f}%", delta=f"Save ${savings:.2f}", delta_color="normal")
                else:
                    st.metric("Discount", "Full Price")
            
            with col3:
                release_date = game_details.get('Release Date', 'TBA')
                if release_date and release_date != 'N/A':
                    st.metric("Release", release_date)
                else:
                    st.metric("Release", "Coming Soon")
            
            # Action buttons
            st.markdown("---")
            col1, col2 = st.columns([1, 1])
            with col1:
                if pd.notna(game_details.get("Link")):
                    st.link_button("Explore on Steam", game_details["Link"], use_container_width=True)
            
            with col2:
                if st.button("Close Details", key="close_dialog", use_container_width=True):
                    st.session_state.show_details_dialog = False
                    st.session_state.selected_game_details = None
                    st.rerun()

    # Call the dialog function
        show_game_details(game)

# ========== Chatbot ==========
elif page == "Chatbot":

    # 🔐 Configuration des clés API
    #hf_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
    groq_key = st.secrets["GROQ_API_KEY"]

    # 🔁 Mise en cache
    @st.cache_resource
    def initialize_llm():
        return ChatGroq(groq_api_key=groq_key, model_name="llama-3.1-8b-instant")

    @st.cache_resource
    def initialize_embeddings():
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    @st.cache_resource
    def load_vectors():
        embeddings = initialize_embeddings()
        try:
            return FAISS.load_local(
                "faiss_index",
                embeddings=embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            st.error(f"Erreur lors du chargement de l'index FAISS : {e}")
            return None

    # 🎨 Enhanced CSS with Steam blue color scheme
    def load_css():
        st.markdown("""
        <style>
        :root {
            --primary: #1b2838;
            --secondary: #2a475e;
            --accent: #66c0f4;
            --light: #f8f9fa;
            --dark: #171a21;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --radius: 16px;
            --shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        
        .main {background: #f8f9fa;}
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
        }
        
        /* Chat containers */
        .chat-container, .input-container, .stats-container {
            background: white; 
            border-radius: var(--radius); 
            padding: 20px;
            margin: 10px 0; 
            box-shadow: var(--shadow);
            border: 1px solid #eaeef2;
            transition: all 0.3s ease;
        }
        
        /* Messages */
        .user-message {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 16px 20px; 
            border-radius: 18px 18px 4px 18px;
            margin: 12px 0; 
            max-width: 85%; 
            margin-left: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            animation: slideInRight 0.3s ease;
        }
        
        .bot-message {
            background: var(--light); 
            padding: 16px 20px; 
            border-radius: 18px 18px 18px 4px;
            margin: 12px 0; 
            border: 1px solid #e2e8f0; 
            max-width: 85%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            animation: slideInLeft 0.3s ease;
        }
        
        /* Animations */
        @keyframes slideInLeft {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideInRight {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        /* Title and header */
        .title-container {
            text-align: center; 
            padding: 30px 20px; 
            margin-bottom: 10px;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }
        
        .game-title {
            font-size: 2.8rem; 
            font-weight: 800;
            background: linear-gradient(90deg, #1b2838 0%, #2a475e 50%, #66c0f4 100%);
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            animation: pulse 2s infinite;
        }
        
        .tagline {
            font-size: 1.2rem;
            color: var(--dark);
            opacity: 0.8;
            margin-bottom: 20px;
        }
        
        /* Buttons and inputs */
        .stButton > button {
            border-radius: 14px; 
            padding: 14px 28px; 
            font-weight: 600;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(27, 40, 56, 0.3);
        }
        
        .stTextInput > div > div > input {
            border-radius: 14px;
            padding: 12px 16px;
            border: 1px solid #e2e8f0;
        }
        
        /* Sidebar */
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .game-title {
                font-size: 2rem;
            }
            .user-message, .bot-message {
                max-width: 95%;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def display_message(role, content):
        """Message display maintaining original formatting"""
        style = "user-message" if role == "user" else "bot-message"
        st.markdown(f'<div class="{style}">{content}</div>', unsafe_allow_html=True)

    # 🚀 Fonction principale
    def main():
        load_css()

        llm = initialize_llm()
        vectors = load_vectors()

        if vectors is None:
            return      

        # 🧠 Prompt (original version)
        prompt_template = PromptTemplate(
            template="""
You are a friendly and enthusiastic game recommendation assistant. Follow these strict rules in every interaction to ensure helpful, accurate, and polite responses:

1. Respond Only to the User's Request
Never suggest games unless the user explicitly asks for a recommendation.

For any other type of query (e.g., game details, Steam link, release date), only answer if the game exists in the dataset or context.

If the game isn't found, say:

"I don't have information about that specific game in my database, but I'd love to help you find something similar!"

2. Game Recommendations (Only When Explicitly Requested)
When the user clearly asks for a recommendation, respond with only games from the dataset or context.

Use this exact format for each game:

Game Title – A short, creative 1–2 sentence description that highlights what makes the game special.

Example:

Stardew Valley – Escape to a peaceful farm life where every season brings new friendships, surprises, and secrets beneath the soil.

3. Game Details Requests (Release Date, Steam Link, etc.)
If the user asks for game-specific details like:

Release date

Steam link

Developer

Genre, etc.

➤ Only respond if the game is in the dataset.
➤ Format the response clearly and concisely.
➤ If the game is not found:

"I don't have information about that specific game, but I'd love to help you find something similar!"

4. End of Conversation Handling
If the user says “thank you”, “thanks”, “bye”, “goodbye”, etc.:

Do NOT recommend a game.

Do NOT continue the conversation.

Just reply politely once:

"You're welcome! Have a great day!"
OR
"Glad I could help. See you next time!"

5. Tone and Style
Always be creative, helpful, and positive.

Avoid robotic or repetitive language like "based on my database".

Never suggest random games or filler. Stay clear, direct, and human-like.

With this update, your assistant will behave logically and respectfully, giving:

Game info only if it's found

Recommendations only when requested

Proper conversation ending behavior

Clear tone and structured answers
            Context:
            {context}

            Previous conversation:
            {chat_history}

            Current Question: {question}

            Response:
            """,
            input_variables=["context", "chat_history", "question"]
        )

        chain = ConversationalRetrievalChain.from_llm(
            llm,
            retriever=vectors.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt_template}
        )

        # 💬 Historique
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 🎮 Enhanced Title Section
        st.markdown("""
        <div class="title-container">
            <div class="game-title">AI Game Assistant</div>
            <div class="tagline">Discover your next favorite game with AI-powered recommendations!</div>
            <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
                <span style="background: #e9f7fe; color: #0c7abf; padding: 5px 12px; border-radius: 20px;">🎮 4,000+ Games</span>
                <span style="background: #e6f9ee; color: #0a8f4e; padding: 5px 12px; border-radius: 20px;">🤖 AI-Powered</span>
                <span style="background: #f5e9ff; color: #1b2838; padding: 5px 12px; border-radius: 20px;">✨ Personalized</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 💬 Affichage du chat
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                display_message("assistant", "🎮 Welcome! Tell me what kind of games you like, and I'll help you find great ones!")
            for msg in st.session_state.messages:
                display_message(msg["role"], msg["content"])

        # 🔤 Zone de saisie
        input_container = st.container()
        with input_container:
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input(
                    "Ask about games...", 
                    placeholder="Your Message",
                    key="user_input",
                    label_visibility="collapsed"
                )
            with col2:
                send = st.button("Send", key="send_button", use_container_width=True)

        # 🤖 Traitement utilisateur
        if send and user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                try:
                    # Get actual response
                    result = chain({
                        "question": user_input,
                        "chat_history": st.session_state.chat_history
                    })
                    answer = result["answer"]
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.chat_history.append((user_input, answer))
                except Exception as e:
                    error = f"⚠️ Sorry, an error occurred: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error})
                    st.error(error)
            st.rerun()

    if __name__ == "__main__":
        main()

        # Paste full content from chatbot.py (UI, CSS, LLM init, FAISS load, chat loop, etc.)
        # Keep all original formatting and behavior



