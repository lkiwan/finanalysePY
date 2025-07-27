# analysis.py
import google.generativeai as genai

def calculate_financial_score(data):
    """Calcule un score financier simple sur 10 basé sur plusieurs métriques clés."""
    score = 0
    max_score = 14
    
    if data.get('roe') is not None:
        if data['roe'] > 0.20: score += 2
        elif data['roe'] > 0.10: score += 1
        
    if data.get('netMargin') is not None:
        if data['netMargin'] > 0.15: score += 2
        elif data['netMargin'] > 0.05: score += 1
        
    if data.get('peRatio') is not None:
        if 0 < data['peRatio'] < 15: score += 3
        elif data['peRatio'] < 25: score += 2
        elif data['peRatio'] < 40: score += 1
        
    if data.get('debtToEquity') is not None:
        if data['debtToEquity'] < 50: score += 3
        elif data['debtToEquity'] < 100: score += 2
        elif data['debtToEquity'] < 200: score += 1
        
    if data.get('revenue') is not None:
        if data['revenue'] > 100e9: score += 2
        elif data['revenue'] > 20e9: score += 1
        
    if data.get('dividendYield') is not None:
        if data['dividendYield'] > 0.03: score += 2
        elif data['dividendYield'] > 0.01: score += 1
        
    return min(10, (score / max_score) * 10) if max_score > 0 else 0

def generate_ai_analysis(data, model):
    """Génère une analyse financière brève en utilisant le modèle IA de Google."""
    if not model:
        return "Le service d'analyse par IA est désactivé."
        
    prompt = f"""
    En tant qu'analyste financier expert pour des investisseurs particuliers, rédige une analyse très concise (environ 100 mots) de l'entreprise {data.get('name')} ({data.get('symbol')}).
    
    Voici quelques données financières clés :
    - Prix de l'action : ${data.get('price', 0):.2f}
    - Ratio Cours/Bénéfice (PER) : {data.get('peRatio', 0):.1f}
    - Marge nette : {data.get('netMargin', 0) * 100:.1f}%
    - Ratio Dette/Capitaux propres : {data.get('debtToEquity', 0):.2f}
    - Chiffre d'affaires (12 derniers mois) : {data.get('revenue', 0) / 1e9:.1f} Mds $

    Ton analyse doit inclure :
    1. Un résumé rapide du profil de l'entreprise.
    2. Un point fort principal (ex: rentabilité élevée, faible endettement, etc.).
    3. Un point de vigilance principal (ex: valorisation élevée, dépendance à un produit, etc.).
    
    Adopte un ton neutre et factuel. Ne fournis **aucun conseil d'investissement** explicite ou implicite. Termine par une clause de non-responsabilité.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Une erreur est survenue lors de la génération de l'analyse par IA : {e}"