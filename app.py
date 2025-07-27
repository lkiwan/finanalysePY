# app.py (Version finale, nettoyée et fonctionnelle)

import streamlit as st
import os
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import google.generativeai as genai

# --- IMPORTS DE VOS FICHIERS PROJET (PROPRES) ---
from analysis import calculate_financial_score, generate_ai_analysis
from data_fetching import (
    check_ticker_validity, get_advanced_metrics, get_historical_data,
    get_dividend_data, get_zonebourse_consensus, get_yfinance_news
)
from export import generate_excel_report, generate_professional_pdf

# --- CONFIGURATION (UNE SEULE FOIS) ---
load_dotenv()
st.set_page_config(page_title="FinAnalyse Pro", page_icon="📈", layout="wide")

# --- INITIALISATION DES SERVICES (UNE SEULE FOIS) ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model = None
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.sidebar.error(f"Erreur d'initialisation de l'IA: {e}")
else:
    st.sidebar.warning("Analyse IA désactivée (clé Google API manquante).")

# ==================================
# DÉFINITION DES PAGES
# ==================================

def render_analysis_page():
    """Affiche la page principale d'analyse d'entreprise."""
    st.header("Analyse Financière Interactive")
    ticker_input = st.text_input("Entrez un symbole d'action (ex: AAPL, MSFT, ORA.PA)", "AAPL").upper()

    if st.button("Analyser", key="analyse_btn"):
        st.session_state.ticker_to_analyse = ticker_input

    if 'ticker_to_analyse' in st.session_state:
        ticker = st.session_state.ticker_to_analyse
        
        with st.spinner(f"Analyse de {ticker} en cours..."):
            is_valid, info = check_ticker_validity(ticker)
            if not is_valid:
                st.error(f"Symbole '{ticker}' introuvable ou données insuffisantes.")
                return

            stock = yf.Ticker(ticker)
            advanced = get_advanced_metrics(ticker)
            hist_data = get_historical_data(ticker)
            dividend_history = get_dividend_data(ticker)
            zb_consensus = get_zonebourse_consensus(ticker)
            news = get_yfinance_news(ticker)
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

            full_data = {"name": info.get("longName", ticker), "symbol": ticker, **info, **advanced}
            score = calculate_financial_score(full_data)
            ai_summary = generate_ai_analysis(full_data, model)

            excel_file = generate_excel_report(financials, balance_sheet, cash_flow, hist_data)
            pdf_file = generate_professional_pdf(full_data, score, ai_summary)

        st.title(f"{full_data.get('name', ticker)} ({full_data.get('symbol', '')})")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Synthèse", "📈 Graphiques", "📂 Finances", "📝 Profil & Actus"])
        
        with tab1:
            st.subheader("Exporter le Rapport Complet")
            c1, c2 = st.columns(2)
            c1.download_button("📥 Télécharger en Excel", excel_file, f"rapport_excel_{ticker}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            c2.download_button("📄 Télécharger en PDF", pdf_file, f"rapport_pdf_{ticker}.pdf", "application/pdf")
            st.divider()
            
            st.subheader("Vue d'Ensemble")
            c1, c2, c3 = st.columns(3)
            c1.metric("Prix Actuel", f"${full_data.get('price', 0):.2f}")
            c2.metric("Score", f"{score:.1f}/10")
            c3.metric("Consensus ZB", zb_consensus)
            
            if model:
                st.subheader("🤖 Analyse par IA")
                with st.expander("Lire l'analyse de l'IA Gemini", expanded=True):
                    st.write(ai_summary)

        with tab2:
            st.subheader("Historique des Prix (1 an)")
            fig = go.Figure(data=[go.Candlestick(x=hist_data.index, open=hist_data['Open'], high=hist_data['High'], low=hist_data['Low'], close=hist_data['Close'])])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Dividendes Annuels")
            if not dividend_history.empty:
                st.bar_chart(dividend_history)
            else:
                st.info("Aucun dividende trouvé sur les 5 dernières années.")

        with tab3:
            st.subheader("Compte de Résultat")
            st.dataframe(financials)
            st.subheader("Bilan")
            st.dataframe(balance_sheet)
            st.subheader("Flux de Trésorerie")
            st.dataframe(cash_flow)
            
        with tab4:
            st.subheader("Description de l'entreprise")
            st.write(full_data.get("description", "Non disponible."))
            st.subheader("Dernières Actualités")
            if news:
                for article in news[:5]:
                    title = article.get('title', 'Titre non disponible')
                    link = article.get('link', '#')
                    publisher = article.get('publisher', 'Source inconnue')
                    st.markdown(f"**[{title}]({link})** - _{publisher}_")
                    st.divider()
            else:
                st.info("Aucune actualité récente pour ce titre.")

def render_chat_page():
    """Affiche la page de Chat avec l'IA."""
    st.header("Chat avec FinAnalyse AI")
    if not model:
        st.error("Service de Chat IA indisponible. Configurez votre GOOGLE_API_KEY.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Posez une question financière..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                response = model.generate_content(prompt).text
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

def render_news_page():
    """Affiche les actualités générales du marché."""
    st.header("Dernières Actualités des Marchés (S&P 500)")
    articles = get_yfinance_news('SPY') # On utilise un ticker général comme le S&P 500
    if not articles:
        st.warning("Aucun article n'a pu être chargé.")
        return

    for article in articles[:10]:
        title = article.get('title', 'Titre non disponible')
        link = article.get('link', '#')
        publisher = article.get('publisher', 'Source inconnue')
        st.subheader(f"[{title}]({link})")
        st.write(f"_{publisher}_")
        st.divider()

# ==================================
# NAVIGATION PRINCIPALE
# ==================================

with st.sidebar:
    st.title("📈 FinAnalyse Pro")
    page = st.radio(
        "Navigation",
        ["Analyse d'entreprise", "Chat AI", "Actualités"],
        key="navigation_radio"
    )

# --- Routage des pages ---
if page == "Analyse d'entreprise":
    render_analysis_page()
elif page == "Chat AI":
    render_chat_page()
elif page == "Actualités":
    render_news_page()