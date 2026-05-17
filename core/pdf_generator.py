# core/pdf_generator.py
from fpdf import FPDF
import os

class TravelPDF(FPDF):
    def __init__(self):
        super().__init__()
        # 預留字體加載空間，若有 .ttf 檔可在此 add_font
        
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Travel Itinerary Plan', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def export(self, itinerary_text):
        self.add_page()
        self.set_font('Arial', size=12)
        
        # 處理內容中的分隔符號，使其在 PDF 中更易讀
        formatted_content = itinerary_text.replace("---DAY_SEPARATOR---", "\n" + "="*40 + "\n")
        
        # 進行基本的特殊字元替換以防報錯
        clean_text = formatted_content.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 10, txt=clean_text)
        
        return self.output(dest='S')