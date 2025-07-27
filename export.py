# export.py (Version finale avec correction de l'encodage)

import pandas as pd
from io import BytesIO
from datetime import date
from fpdf import FPDF

# --- Fonction Excel (ne change pas) ---
def generate_excel_report(financials, balance_sheet, cash_flow, hist_data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not financials.empty:
            financials.iloc[::-1].to_excel(writer, sheet_name='Compte de Résultat')
        if not balance_sheet.empty:
            balance_sheet.iloc[::-1].to_excel(writer, sheet_name='Bilan')
        if not cash_flow.empty:
            cash_flow.iloc[::-1].to_excel(writer, sheet_name='Flux de Trésorerie')
        if not hist_data.empty:
            hist_data_local = hist_data.copy()
            if hasattr(hist_data_local.index, 'tz') and hist_data_local.index.tz is not None:
                hist_data_local.index = hist_data_local.index.tz_localize(None)
            hist_data_local.to_excel(writer, sheet_name='Historique des Prix')
    return output.getvalue()


# --- Classe PDF (ne change pas) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Rapport Financier - FinAnalyse Pro', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, text):
        if text is None:
            text = "Information non disponible."
        self.set_font('Helvetica', '', 12)
        text = str(text).encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, text)
        self.ln()
        
    def metric_box(self, label, value):
        self.set_font('Helvetica', 'B', 11)
        self.cell(45, 8, label, border=1)
        self.set_font('Helvetica', '', 11)
        self.cell(0, 8, str(value), border=1)
        self.ln()

def generate_professional_pdf(full_data, score, ai_summary):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 10, full_data.get('name', 'N/A'), 0, 1)
    pdf.set_font('Helvetica', 'I', 14)
    pdf.cell(0, 8, f"{full_data.get('symbol', 'N/A')} - Rapport du {date.today().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(10)

    pdf.chapter_title('Synthèse des Métriques Clés')
    pdf.metric_box('Prix Actuel', f"${full_data.get('price', 0):.2f}")
    pdf.metric_box('Score Financier', f"{score:.1f}/10")
    pdf.metric_box('Capitalisation', f"${full_data.get('marketCap', 0) / 1e9:.2f} Mds")
    pdf.metric_box('Ratio C/B (PE)', f"{full_data.get('peRatio', 0):.2f}")
    pdf.metric_box('ROE', f"{full_data.get('returnOnEquity', 0) * 100:.2f}%")
    pdf.ln(5)

    pdf.chapter_title("Analyse par l'IA (Gemini)")
    pdf.chapter_body(ai_summary)

    pdf.chapter_title("Description de l'entreprise")
    pdf.chapter_body(full_data.get('description', 'Non disponible.'))
    
    # --- DÉBUT DE LA CORRECTION ---
    # On convertit explicitement le bytearray en bytes, le format attendu par Streamlit.
    return bytes(pdf.output(dest='S'))