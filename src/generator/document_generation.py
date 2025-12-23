import os
import tempfile
import re
from fpdf import FPDF

def create_pdf(text, task_title, task_id):
    try:
        pdf_path = os.path.join(tempfile.gettempdir(), f"{task_id}.pdf")

        # Очищаем текст от Markdown разметки перед созданием PDF
        task_title_clean = task_title.replace('**', '')
        
        # Убираем Markdown из основного текста
        text_clean = text.replace('**', '')  # Убираем звёздочки
        text_clean = re.sub(r'\*([^*]+)\*', r'\1', text_clean)  # Убирает *курсив*
        text_clean = re.sub(r'#+\s*', '', text_clean)  # Убирает # заголовки
        text_clean = re.sub(r'`([^`]+)`', r'\1', text_clean)  # Убирает `код`
        text_clean = text.replace('*', '')  # Убираем звёздочки

        pdf = FPDF()
        pdf.add_page()

        font_path = "Montserrat.ttf"
        pdf.add_font("Montserrat", "", font_path, uni=True)
        pdf.set_font("Montserrat", size=14)

        pdf.multi_cell(0, 10, task_title_clean)
        pdf.ln()
        pdf.multi_cell(0, 10, text_clean)

        pdf.output(pdf_path)
        return pdf_path

    except Exception as e:
        print(f"PDF Error: {e}")
        txt_path = os.path.join(tempfile.gettempdir(), f"{task_id}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"{task_title}\n\n{text}")
        return txt_path