import os
from fpdf import FPDF
import streamlit as st

from .common import LOGO_PATH

# -------------------------
# PDF base
# -------------------------
PDF_FONT = "Arial"
PDF_BODY_SIZE = 11
PDF_TITLE_SIZE = 13
PDF_LINE_H = 6

class SGQSA_PDF(FPDF):
    def __init__(self, module_seq: str, module_name: str, logo_path: str | None = None):
        super().__init__()
        self.module_seq = module_seq
        self.module_name = module_name
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, x=10, y=8, w=22)

        self.set_font("Arial", size=10)
        self.set_y(10)
        header_right = f"Seq. {self.module_seq}  |  {self.module_name}"
        self.cell(0, 10, header_right, ln=True, align="R")
        self.set_draw_color(200, 200, 200)
        self.line(10, 22, 200, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Estratto SG-QSA aziendale Luppichini Ulisse S.r.l.", ln=0, align="L")
        self.set_y(-15)
        self.cell(0, 8, f"{self.page_no()}/{{nb}}", ln=0, align="R")

def make_pdf(module_seq: str, module_name: str) -> SGQSA_PDF:
    pdf = SGQSA_PDF(
        module_seq=module_seq,
        module_name=module_name,
        logo_path=str(LOGO_PATH) if LOGO_PATH.exists() else None
    )
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    return pdf

def pdf_title(pdf: FPDF, text: str):
    pdf.set_font(PDF_FONT, "B", PDF_TITLE_SIZE)
    pdf.multi_cell(0, 8, text)
    pdf.ln(2)
    pdf.set_font(PDF_FONT, "", PDF_BODY_SIZE)

def pdf_kv(pdf: FPDF, label: str, value: str, gap_after: bool = False):
    value = "" if value is None else str(value)

    pdf.set_font(PDF_FONT, "B", PDF_BODY_SIZE)
    w = pdf.get_string_width(label + ":") + 2
    pdf.cell(w, PDF_LINE_H, f"{label}:", ln=0)

    pdf.set_font(PDF_FONT, "", PDF_BODY_SIZE)
    pdf.multi_cell(0, PDF_LINE_H, f" {value}")

    if gap_after:
        pdf.ln(PDF_LINE_H * 2)

# -------------------------
# Viewer "document style"
# -------------------------
def doc_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()

def doc_section(title: str, icon: str = "📌"):
    st.markdown(f"### {icon} {title}")

def doc_field(label: str, value: str, help_text: str = ""):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        if help_text:
            st.caption(help_text)
        st.write(value if value not in (None, "") else "—")
