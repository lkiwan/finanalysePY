import yfinance as yf
import pandas as pd
import requests
import streamlit as st
from datetime import datetime
import re
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os

load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


# Paste this new function where the old ones were
# data_fetching.py

# --- IMPORTS NÉCESSAIRES AU DÉBUT DU FICHIER ---
import yfinance as yf
import pandas as pd
import requests
import streamlit as st
from datetime import datetime
import re
from bs4 import BeautifulSoup
import os

# --- Assurez-vous que les clés sont chargées ---
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
# NOUVELLE LIGNE : Charger la clé Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


# NOUVELLE VERSION AMÉLIORÉE - À COLLER DANS data_fetching.py

@st.cache_data(ttl=3600)
def get_advanced_metrics(ticker):
    """
    Récupère des métriques financières avancées depuis Alpha Vantage et yfinance,
    et calcule le ROI.
    ATTENTION : Le plan gratuit d'Alpha Vantage est limité à 25 appels par jour.
    """
    data = {}
    
    # --- 1. Données fondamentales d'Alpha Vantage ---
    try:
        # Appel 1: Vue d'ensemble de l'entreprise
        overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
        r = requests.get(overview_url)
        overview_data = r.json()
        
        net_income = 0 # Initialisation pour le calcul du ROI plus tard

        if overview_data and 'Note' not in overview_data:
            net_income = float(overview_data.get('NetIncomeTTM', 0)) # *** NOUVEAU : On stocke le Net Income
            data.update({
                "marketCap": float(overview_data.get('MarketCapitalization', 0)),
                "ebitda": float(overview_data.get('EBITDA', 0)),
                "peRatio": float(overview_data.get('PERatio', 0)) if overview_data.get('PERatio') != 'None' else 0,
                "forwardPE": float(overview_data.get('ForwardPE', 0)) if overview_data.get('ForwardPE') != 'None' else 0,
                "beta": float(overview_data.get('Beta', 0)) if overview_data.get('Beta') != 'None' else None,
                "dividendYield": float(overview_data.get('DividendYield', 0)),
                "revenue": float(overview_data.get('RevenueTTM', 0)),
                "returnOnEquity": float(overview_data.get('ReturnOnEquityTTM', 0)),
                "returnOnAssets": float(overview_data.get('ReturnOnAssetsTTM', 0)),
                "revenueGrowth": float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)),
                "earningsGrowth": float(overview_data.get('QuarterlyEarningsGrowthYOY', 0)),
                "priceToBook": float(overview_data.get('PriceToBookRatio', 0)) if overview_data.get('PriceToBookRatio') != 'None' else None,
                "fullTimeEmployees": int(overview_data.get('FullTimeEmployees', 0)) if overview_data.get('FullTimeEmployees', 0) != 'None' else 0,
                "description": overview_data.get('Description'),
                "sector": overview_data.get('Sector'),
                "country": overview_data.get('Country'),
            })

        # Appel 2: Bilan pour la dette et les capitaux propres
        balance_url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
        r = requests.get(balance_url)
        balance_data = r.json()
        
        cost_of_investment = 0 # Initialisation

        if balance_data and 'annualReports' in balance_data and balance_data['annualReports']:
            latest_report = balance_data['annualReports'][0]
            total_debt = float(latest_report.get('longTermDebt', 0)) + float(latest_report.get('shortTermDebt', 0))
            equity = float(latest_report.get('totalShareholderEquity', 1)) 
            data['totalDebt'] = total_debt
            data['debtToEquity'] = (total_debt / equity) if equity != 0 else 0
            
            # *** NOUVEAU : On calcule le coût de l'investissement pour le ROI
            cost_of_investment = total_debt + equity

        # *** NOUVEAU : Calcul et ajout du ROI au dictionnaire de données
        if cost_of_investment > 0:
            roi = net_income / cost_of_investment
            data['returnOnInvestment'] = roi # On ajoute le ROI ici
        else:
            data['returnOnInvestment'] = 0


        # Appel 3: Flux de trésorerie
        cashflow_url = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
        r = requests.get(cashflow_url)
        cashflow_data = r.json()

        if cashflow_data and 'annualReports' in cashflow_data and cashflow_data['annualReports']:
            latest_report = cashflow_data['annualReports'][0]
            data['operatingCashFlow'] = float(latest_report.get('operatingCashflow', 0))
            fcf = float(latest_report.get('operatingCashflow', 0)) - float(latest_report.get('capitalExpenditures', 0))
            data['freeCashFlow'] = fcf

    except Exception as e:
        print(f"[Erreur Alpha Vantage] : {e}")
        st.warning("Certaines données n'ont pas pu être chargées depuis Alpha Vantage. Limite d'API atteinte ?")

    # --- 2. Complément avec yfinance (au cas où) ---
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if 'beta' not in data or data['beta'] is None:
            data['beta'] = info.get('beta')
    except Exception as e:
        print(f"[Erreur yfinance] : {e}")

    return data
# def get_advanced_metrics(ticker):
#     try:
#         url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
#         response = requests.get(url)

#         if response.status_code != 200:
#             return {}

#         profile_data = response.json()
#         if not profile_data or not isinstance(profile_data, list):
#             return {}

#         data = profile_data[0]  # ✅ ici on définit "data"

#         return {
#             "operatingCashFlow": data.get("operatingCashFlow"),
#             "freeCashFlow": data.get("freeCashFlow"),
#             "totalDebt": data.get("totalDebt"),
#             "debtToEquity": data.get("debtToEquity"),
#             "revenueGrowth": data.get("revenueGrowth"),
#             "earningsGrowth": data.get("earningsGrowth"),
#             "returnOnAssets": data.get("returnOnAssets"),
#             "returnOnEquity": data.get("returnOnEquity"),
#             "returnOnInvestment": data.get("returnOnInvestment"),
#             "ebitda": data.get("ebitda"),
#             "fullTimeEmployees": data.get("fullTimeEmployees"),
#             "sector": data.get("sector"),
#             "country": data.get("country"),
#             "description": data.get("description") or data.get("longBusinessSummary"),
#         }

#     except Exception as e:
#         print(f"[Erreur] get_advanced_metrics : {e}")
#         return {}


@st.cache_data(ttl=3600)
def check_ticker_validity(ticker):
    """Vérifie si un ticker est valide et retourne ses informations de base."""
    stock = yf.Ticker(ticker)
    if stock.history(period="1d").empty:
        return False, None
    info = stock.info
    if 'currentPrice' not in info or info['currentPrice'] is None:
        return False, None
    return True, info

@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    """Récupère les informations générales d'un ticker."""
    return yf.Ticker(ticker.upper()).info

@st.cache_data(ttl=3600)

# def get_advanced_metrics(ticker):
#     """Récupère des métriques financières avancées."""
#     stock = yf.Ticker(ticker.upper())
#     info = stock.info
#     cashflow = stock.cashflow
#     op_cash, capital_expenditures, free_cashflow = None, None, None
#     if not cashflow.empty and isinstance(cashflow, pd.DataFrame):
#         op_cash = cashflow.loc['Total Cash From Operating Activities'].iloc[0] if 'Total Cash From Operating Activities' in cashflow.index else None
#         capital_expenditures = cashflow.loc['Capital Expenditures'].iloc[0] if 'Capital Expenditures' in cashflow.index else None
#         if pd.notna(op_cash) and pd.notna(capital_expenditures):
#             free_cashflow = op_cash + capital_expenditures
#     return {
#         "debtToEquity": info.get('debtToEquity'), "freeCashFlow": free_cashflow,
#         "dividendYield": info.get('dividendYield', 0), "marketCap": info.get("marketCap"),
#         "beta": info.get("beta"), "priceToBook": info.get("priceToBook"),
#         "forwardPE": info.get("forwardPE"), "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
#         "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
    
# }
        
    
@st.cache_data(ttl=86400)
def get_historical_data(ticker):
    """Récupère l'historique des prix sur 1 an."""
    return yf.Ticker(ticker.upper()).history(period="1y")

@st.cache_data(ttl=86400)
def get_dividend_data(ticker):
    """Récupère les dividendes des 5 dernières années et les somme par an."""
    dividends = yf.Ticker(ticker.upper()).dividends.last('5Y')
    return dividends.resample('YE').sum() if not dividends.empty else pd.Series(dtype='float64')

TICKER_TO_ZB_URL_NAME = {
    "AAPL": "APPLE-INC-4849", "MSFT": "MICROSOFT-CORPORATION-4835",
    "GOOGL": "ALPHABET-INC-62394", "META": "META-PLATFORMS-INC-10547341",
    "LVMH": "LVMH-MOET-HENNESSY-LOUIS-4669",
    "TTE": "TOTALENERGIES-SE-4716"  # <-- Ajout de la nouvelle valeur
}

@st.cache_data(ttl=86400)
def get_zonebourse_consensus(ticker):
    """Récupère le consensus des analystes sur Zone Bourse via web scraping."""
    url_name = TICKER_TO_ZB_URL_NAME.get(ticker.upper())
    if not url_name:
        return "N/A"
    url = f"https://www.zonebourse.com/cours/action/{url_name}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        consensus_element = soup.find("div", class_=re.compile(r'c-face-instrument__rating-text'))
        return consensus_element.get_text(strip=True) if consensus_element else "Non trouvé"
    except Exception:
        return "Erreur"

# --- LA FONCTION QUE VOUS DEVEZ AVOIR ---
@st.cache_data(ttl=1800) # Cache de 30 minutes
def get_yfinance_news(ticker):
    """Récupère les actualités pour un ticker donné via yfinance."""
    try:
        stock = yf.Ticker(ticker)
        # La méthode .news retourne une liste de dictionnaires
        news = stock.news
        return news if news else []
    except Exception as e:
        print(f"Erreur lors de la récupération des actualités yfinance : {e}")
        return []