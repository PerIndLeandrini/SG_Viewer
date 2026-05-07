import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
from fpdf import FPDF
import matplotlib.pyplot as plt

from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

def sidebar_logo():
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.sidebar.warning("Logo non trovato in assets/logo.png")

# =========================================================
# CONFIG
# =========================================================
BASE_PATH = "moduli_compilati"
os.makedirs(BASE_PATH, exist_ok=True)

# --- DATE STANDARD ---
UI_FMT = "%d/%m/%Y"
ISO_FMT = "%Y-%m-%d"

def iso_date(d: date) -> str:
    return d.strftime(ISO_FMT)

def parse_iso_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s), ISO_FMT).date()
    except Exception:
        return None

def safe_iso_from_any(x) -> str:
    """
    Converte date/str in ISO YYYY-MM-DD se possibile.
    Se non convertibile, ritorna stringa pulita.
    """
    if x is None:
        return ""
    if isinstance(x, (datetime, date)):
        return iso_date(x if isinstance(x, date) else x.date())
    s = str(x).strip()
    if not s:
        return ""
    # prova ISO
    d = parse_iso_date(s)
    if d:
        return iso_date(d)
    # prova UI dd/mm/yyyy
    try:
        d2 = datetime.strptime(s, UI_FMT).date()
        return iso_date(d2)
    except Exception:
        return s


# --- FILE NAME STANDARD (canonici) ---
# Chiave = nome modulo "logico" (senza .xlsx)
FILE_MAP = {
    "MOD-400-A-Contesto": "MOD-400-A-Contesto.xlsx",
    "MOD-400-B-Parti interessate": "MOD-400-B-Parti_Interessate.xlsx",
    "MOD-530-B-Ruoli e requisiti": "MOD-530-B-Ruoli_e_Requisiti.xlsx",
    "MOD-530-C-Matrice delle responsabilità": "MOD-530-C-Matrice_Responsabilita.xlsx",
    "MOD-610-B-Risk management": "MOD-610-B-Risk_Management.xlsx",
    "MOD-620-B-Pianificazione": "MOD-620-B-Pianificazione.xlsx",
    "MOD-710-A-Ambienti di lavoro": "MOD-710-A-Ambienti_Lavoro.xlsx",
    "MOD-710-B-Dispositivi": "MOD-710-B-Dispositivi.xlsx",
    "MOD-710-C-Risorse misurazione": "MOD-710-C-Risorse_Misurazione.xlsx",
    "MOD-710-D-Attrezzature": "MOD-710-D-Attrezzature.xlsx",
    "MOD-710-E-Conoscenza organizzativa": "MOD-710-E-Conoscenza_Organizzativa.xlsx",
    "MOD-710-Supporti": "MOD-710-Supporti.xlsx",
    "MOD-720-C-Registro formazione": "MOD-720-C-Registro_Formazione.xlsx",
    "MOD-720-F.1-Monitoraggio formazione": "MOD-720-F1-Monitoraggio_Formazione.xlsx",
    "MOD-720-F.2-Monitoraggio formazione CS": "MOD-720-F2-Monitoraggio_Formazione_CS.xlsx",
    "MOD-720-G-Piano formazione annuale": "MOD-720-G-Piano_Formazione_Annuale.xlsx",
    "MOD-740-B-Monitoraggio comunicazione": "MOD-740-B-Monitoraggio_Comunicazione.xlsx",
    "MOD-840-A Mappatura fornitori": "MOD-840-A-Mappatura_Fornitori.xlsx",
    # NOTA: nel tuo codice non avevi un form per 850-B, ma lo aggiungo e lo rendo canonico
    "MOD-850-B-Identificazione e tracciabilità": "MOD-850-B-Identificazione_Tracciabilita.xlsx",
    "MOD-850-H-Controllo per variabili": "MOD-850-H-Controllo_Variabili.xlsx",
    "MOD-850-I-Controllo per attributi": "MOD-850-I-Controllo_Attributi.xlsx",
    "MOD-870-B- Prodotti non conformi": "MOD-870-B-Prodotti_Non_Conformi.xlsx",
    "MOD-910-C-Soddisfazione clienti": "MOD-910-C-Soddisfazione_Clienti.xlsx",
    "MOD-910-E-Soddisfazione persone": "MOD-910-E-Soddisfazione_Persone.xlsx",
    "MOD-910-G-Soddisfazione fornitori": "MOD-910-G-Soddisfazione_Fornitori.xlsx",
    "MOD-910-H-Performance": "MOD-910-H-Performance.xlsx",

    # NC / AC
    "MOD-1020-A-Apertura Non Conformità": "MOD-1020-A-Apertura_NC.xlsx",
    "MOD-1020-B-Azioni Correttive": "MOD-1020-B-Azioni_Correttive.xlsx",

    # Se lo vuoi davvero usare più avanti:
    "MOD-920-E-Monitoraggioauditing": "MOD-920-E-Monitoraggio_Auditing.xlsx",
    "REG-DOC - Registro Documenti SGQ": "REG-DOC-Registro_Documenti_SGQ.xlsx",

}

def get_file_path(key: str) -> str:
    """
    Restituisce il path del file Excel canonico.
    Tollerante a errori: se passi "....xlsx" lo ripulisce.
    """
    key = str(key).strip()
    key = key.replace(".xlsx", "")  # tollera errori tipici

    fname = FILE_MAP.get(key)
    if not fname:
        raise ValueError(
            f"File key non mappata: {key}\n"
            f"Chiavi valide: {list(FILE_MAP.keys())}"
        )
    return os.path.join(BASE_PATH, fname)


def next_action_id(file_azioni_path: str, today: date) -> str:
    """
    formato: AC01_03_02_2026
    progressivo incrementale globale sul file azioni
    """
    dd = today.strftime("%d")
    mm = today.strftime("%m")
    yyyy = today.strftime("%Y")

    prog = 1
    if os.path.exists(file_azioni_path):
        try:
            df = pd.read_excel(file_azioni_path)
            if "ID AZIONE" in df.columns:
                existing = df["ID AZIONE"].dropna().astype(str).tolist()
                nums = []
                for x in existing:
                    # ACxx_...
                    if x.startswith("AC") and len(x) >= 4:
                        try:
                            nums.append(int(x[2:4]))
                        except Exception:
                            pass
                prog = max(nums) + 1 if nums else (len(df) + 1)
            else:
                prog = len(df) + 1
        except Exception:
            prog = 1

    return f"AC{prog:02d}_{dd}_{mm}_{yyyy}"

def form_reg_doc():
    st.subheader("📁 REG-DOC - Registro Documenti SGQ")
    st.caption("Indice documentale del sistema qualità: procedure, istruzioni, manuale, modulistica, ecc.")

    file_key = "REG-DOC - Registro Documenti SGQ"
    fp = get_file_path(file_key)

    # Se non esiste ancora, lo inizializziamo con intestazioni standard
    if not os.path.exists(fp):
        st.warning("Registro non ancora creato. Creo un file vuoto con intestazioni standard.")
        df0 = pd.DataFrame([{
            "Famiglia": "",
            "Documento": "",
            "Percorso": "",
            "Revisione (guess)": "",
            "Data (guess)": "",
            "Pagine": "",
            "Snippet prima pagina": "",
            "Stato aggiornamento": "Da verificare",
            "Note": ""
        }])
        df0.to_excel(fp, index=False)
        st.success("Creato registro vuoto. Ora puoi importare/compilare le righe.")

    # Carico registro
    try:
        df = pd.read_excel(fp).fillna("")
    except Exception as e:
        st.error(f"Errore lettura registro: {e}")
        return

    # --- Filtri
    st.markdown("### 🔎 Filtri")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 2.0])

    famiglie = [""] + sorted([x for x in df.get("Famiglia", pd.Series()).unique().tolist() if str(x).strip() != ""])
    revisioni = [""] + sorted([x for x in df.get("Revisione (guess)", pd.Series()).unique().tolist() if str(x).strip() != ""])
    stati = [""] + sorted([x for x in df.get("Stato aggiornamento", pd.Series()).unique().tolist() if str(x).strip() != ""])

    with c1:
        f_fam = st.selectbox("Famiglia", famiglie, key="regdoc_fam")
    with c2:
        f_rev = st.selectbox("Revisione", revisioni, key="regdoc_rev")
    with c3:
        f_stato = st.selectbox("Stato aggiornamento", stati, key="regdoc_stato")
    with c4:
        q = st.text_input("Cerca (titolo / snippet / note)", value="", key="regdoc_q")

    df_view = df.copy()

    if f_fam and "Famiglia" in df_view.columns:
        df_view = df_view[df_view["Famiglia"] == f_fam]
    if f_rev and "Revisione (guess)" in df_view.columns:
        df_view = df_view[df_view["Revisione (guess)"] == f_rev]
    if f_stato and "Stato aggiornamento" in df_view.columns:
        df_view = df_view[df_view["Stato aggiornamento"] == f_stato]

    if q:
        ql = q.lower().strip()

        def _match(row):
            for col in ["Documento", "Snippet prima pagina", "Note", "Percorso"]:
                if col in row and ql in str(row[col]).lower():
                    return True
            return False

        df_view = df_view[df_view.apply(_match, axis=1)]

    st.markdown("### 📋 Registro (filtrato)")
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 📄 Apri / Scarica documento")
    if df_view.empty:
        st.info("Nessun documento corrisponde ai filtri.")
        return

    labels = df_view["Documento"].tolist() if "Documento" in df_view.columns else []
    if not labels:
        st.warning("Colonna 'Documento' mancante nel registro.")
        return

    doc_sel = st.selectbox("Seleziona documento", labels, key="regdoc_docsel")
    row = df_view[df_view["Documento"] == doc_sel].iloc[0]
    path_pdf = str(row.get("Percorso", "")).strip()


    # --- Download PDF del documento selezionato
    st.markdown("### 📄 Apri / Scarica documento")
    if df_view.empty:
        st.info("Nessun documento corrisponde ai filtri.")
        return

    # selezione documento (usa Documento come label)
    labels = df_view["Documento"].tolist() if "Documento" in df_view.columns else []
    if not labels:
        st.warning("Colonna 'Documento' mancante nel registro.")
        return

    doc_sel = st.selectbox("Seleziona documento", labels)
    row = df_view[df_view["Documento"] == doc_sel].iloc[0]
    path_pdf = str(row.get("Percorso", "")).strip()

    cA, cB = st.columns([2, 1])
    with cA:
        st.write(f"**Famiglia:** {row.get('Famiglia','')}")
        st.write(f"**Revisione:** {row.get('Revisione (guess)','')}")
        st.write(f"**Data:** {row.get('Data (guess)','')}")
        st.write(f"**Stato:** {row.get('Stato aggiornamento','')}")
        if row.get("Snippet prima pagina", ""):
            st.caption(row.get("Snippet prima pagina", ""))

    with cB:
        if path_pdf and os.path.exists(path_pdf):
            with open(path_pdf, "rb") as f:
                st.download_button(
                    "⬇️ Scarica PDF",
                    data=f,
                    file_name=os.path.basename(path_pdf),
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.warning("Percorso PDF non valido o file non trovato.")
            st.caption(path_pdf if path_pdf else "(vuoto)")

# =========================================================
# STREAMLIT BASE
# =========================================================
st.set_page_config(page_title="Suite ISO 9001", page_icon="📄", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Per aprire MOD-1020-C in modo non ambiguo
if "ac_selected_action_id" not in st.session_state:
    st.session_state.ac_selected_action_id = None

# Per aprire MOD-1020-A direttamente su una NC specifica
if "nc_selected_id" not in st.session_state:
    st.session_state.nc_selected_id = None


# =========================================================
# SIDEBAR NAV (state-aware)
# =========================================================
def infer_sezione_from_page(p: str) -> str:
    if p == "Dashboard":
        return "Generali"
    if p.startswith("MOD-1020-A"):
        return "Non Conformità"
    if p.startswith("MOD-1020-B") or p.startswith("MOD-1020-C"):
        return "Azioni Correttive"
    return "Altri moduli"

# --- SYNC NAV: se navighiamo via goto(), resettiamo i widget della sidebar
if st.session_state.get("_sync_nav", False):
    for k in ("nav_page", "nav_sezione"):
        st.session_state.pop(k, None)  # importantissimo: elimina lo stato dei widget
    st.session_state._sync_nav = False

def goto(page_name: str, **state_updates):
    for k, v in state_updates.items():
        st.session_state[k] = v

    st.session_state.page = page_name
    st.session_state._sync_nav = True  # forza riallineamento sidebar al rerun
    st.rerun()

def _nav_page_changed():
    st.session_state.page = st.session_state.nav_page

with st.sidebar:
    sidebar_logo()

    st.markdown("### Navigazione")

    if st.button("🏠 Dashboard", use_container_width=True):
        goto("Dashboard")

    st.markdown("---")

    sezioni = ["Generali", "Non Conformità", "Azioni Correttive", "Altri moduli"]

    current_page = st.session_state.get("page", "Dashboard")
    default_sezione = infer_sezione_from_page(current_page)
    sezione_idx = sezioni.index(default_sezione) if default_sezione in sezioni else 0

    sezione = st.radio("Sezione", sezioni, index=sezione_idx, key="nav_sezione")

    if sezione == "Generali":
        options = ["Dashboard"]
    elif sezione == "Non Conformità":
        options = ["MOD-1020-A - Apertura Non Conformità"]
    elif sezione == "Azioni Correttive":
        options = [
            "MOD-1020-B - Gestisci Azioni Correttive",
            "MOD-1020-C - Visualizza Azioni Correttive",
        ]
    else:
        options = [
            "REG-DOC - Registro Documenti SGQ",
            "MOD-400-A-Contesto",
            "MOD-400-B-Parti interessate",
            "MOD-530-B-Ruoli e requisiti",
            "MOD-530-C-Matrice delle responsabilità",
            "MOD-610-B-Risk management",
            "MOD-620-B-Pianificazione",
            "MOD-710-A-Ambienti di lavoro",
            "MOD-710-B-Dispositivi",
            "MOD-710-C-Risorse misurazione",
            "MOD-710-D-Attrezzature",
            "MOD-710-E-Conoscenza organizzativa",
            "MOD-710-Supporti",
            "MOD-720-C-Registro formazione",
            "MOD-720-F.1-Monitoraggio formazione",
            "MOD-720-F.2-Monitoraggio formazione CS",
            "MOD-720-G-Piano formazione annuale",
            "MOD-740-B-Monitoraggio comunicazione",
            "MOD-840-A Mappatura fornitori",
            "MOD-850-B-Identificazione e tracciabilità",
            "MOD-850-H-Controllo per variabili",
            "MOD-850-I-Controllo per attributi",
            "MOD-870-B- Prodotti non conformi",
            "MOD-910-C-Soddisfazione clienti",
            "MOD-910-E-Soddisfazione persone",
            "MOD-910-G-Soddisfazione fornitori",
            "MOD-910-H-Performance",
        ]

    idx = options.index(current_page) if current_page in options else 0

    st.radio(
        "Pagina",
        options,
        index=idx,
        key="nav_page",
        on_change=_nav_page_changed
    )

class SGQSA_PDF(FPDF):
    def __init__(self, module_seq: str, module_name: str, logo_path: str | None = None):
        super().__init__()
        self.module_seq = module_seq
        self.module_name = module_name
        self.logo_path = logo_path

        # Impostazioni generali
        self.set_auto_page_break(auto=True, margin=18)  # lascia spazio al footer

    def header(self):
        # Logo in alto a sinistra
        if self.logo_path and os.path.exists(self.logo_path):
            # x=10, y=8, w=22 (regola la larghezza)
            self.image(self.logo_path, x=10, y=8, w=22)

        # Testo intestazione in alto a destra
        self.set_font("Arial", size=10)
        self.set_y(10)

        header_right = f"Seq. {self.module_seq}  |  {self.module_name}"
        # cella a tutta larghezza, allineata a destra
        self.cell(0, 10, header_right, ln=True, align="R")

        # linea sottile sotto header
        self.set_draw_color(200, 200, 200)
        self.line(10, 22, 200, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=9)
        self.set_text_color(80, 80, 80)

        footer_left = "Estratto SG-QSA aziendale Luppichini Ulisse S.r.l."
        self.cell(0, 8, footer_left, ln=0, align="L")

        self.set_y(-15)
        self.cell(0, 8, f"{self.page_no()}/{{nb}}", ln=0, align="R")

def make_pdf(module_seq: str, module_name: str) -> SGQSA_PDF:
    pdf = SGQSA_PDF(
        module_seq=module_seq,
        module_name=module_name,
        logo_path=str(LOGO_PATH) if LOGO_PATH.exists() else None
    )
    pdf.alias_nb_pages()  # abilita {nb}
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    return pdf

# -------------------------
# PDF helpers (bold label / normal value + spacing)
# -------------------------
PDF_FONT = "Arial"
PDF_BODY_SIZE = 11
PDF_TITLE_SIZE = 13
PDF_LINE_H = 6  # altezza riga

def pdf_kv(pdf: FPDF, label: str, value: str, gap_after: bool = False):
    """Etichetta in grassetto, valore normale sulla stessa riga (quando possibile)."""
    value = "" if value is None else str(value)

    # label bold
    pdf.set_font(PDF_FONT, "B", PDF_BODY_SIZE)
    w = pdf.get_string_width(label + ":") + 2
    pdf.cell(w, PDF_LINE_H, f"{label}:", ln=0)

    # value regular
    pdf.set_font(PDF_FONT, "", PDF_BODY_SIZE)
    pdf.multi_cell(0, PDF_LINE_H, f" {value}")

    # doppia riga di spazio dove richiesto
    if gap_after:
        pdf.ln(PDF_LINE_H * 2)  # 2 righe vuote

def pdf_title(pdf: FPDF, text: str):
    pdf.set_font(PDF_FONT, "B", PDF_TITLE_SIZE)
    pdf.multi_cell(0, 8, text)
    pdf.ln(2)
    pdf.set_font(PDF_FONT, "", PDF_BODY_SIZE)


def kpi_card(label: str, value: str, hint: str = ""):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        st.markdown(f"### {value}")
        if hint:
            st.caption(hint)

# =========================================================
# UI
# =========================================================
st.title("📄 Suite Inserimento Moduli ISO 9001")


# =========================================================
# FORMS
# =========================================================
def append_to_excel(file_key: str, new_row: pd.DataFrame) -> None:
    fp = get_file_path(file_key)
    if os.path.exists(fp):
        existing = pd.read_excel(fp)
        updated = pd.concat([existing, new_row], ignore_index=True)
    else:
        updated = new_row
    updated.to_excel(fp, index=False)

# =========================
# ARCHIVIO MODULI - HELPERS
# =========================

def load_df_safe(file_key: str) -> tuple[pd.DataFrame, str]:
    """
    Ritorna (df, status) dove status = 'ok' | 'missing' | 'error'
    """
    try:
        fp = get_file_path(file_key)
        if not os.path.exists(fp):
            return pd.DataFrame(), "missing"
        df = pd.read_excel(fp).fillna("")
        return df, "ok"
    except Exception:
        return pd.DataFrame(), "error"


def infer_last_date(df: pd.DataFrame) -> str:
    """
    Prova a trovare una "data più recente" in modo robusto.
    Cerca colonne tipiche e prova a parse-are date ISO o dd/mm/yyyy.
    """
    if df is None or df.empty:
        return "-"

    candidate_cols = [
        "Data", "DATA", "Data rilevamento", "Data apertura", "Data inserimento",
        "Scadenza", "Data chiusura prevista", "Validità fino al"
    ]

    col = None
    for c in candidate_cols:
        if c in df.columns:
            col = c
            break
    if not col:
        return "-"

    s = df[col].astype(str).replace("", pd.NA).dropna()
    if s.empty:
        return "-"

    # Provo parse ISO e poi dd/mm/yyyy
    dt = pd.to_datetime(s, errors="coerce", format=ISO_FMT)
    if dt.isna().all():
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)

    dt = dt.dropna()
    if dt.empty:
        return "-"

    last = dt.max()
    return last.strftime(UI_FMT)


def file_badge(status: str) -> str:
    if status == "ok":
        return "🟢"
    if status == "missing":
        return "🟡"
    return "🔴"

def dashboard_archivio_moduli():
    st.markdown("---")
    st.subheader("📚 Archivio Moduli SG-QSA")
    st.caption("Panoramica completa: stato file, numero record, ultima data inserita e accesso diretto ai moduli.")

    # REGISTRO COMPLETO (qui aggiungi/togli in futuro senza impazzire)
    MOD_GROUPS = {
        "📁 Documenti & Procedure": [
            "REG-DOC - Registro Documenti SGQ",
        ],

        "🏛️ Contesto & Governance": [
            "MOD-400-A-Contesto",
            "MOD-400-B-Parti interessate",
            "MOD-530-B-Ruoli e requisiti",
            "MOD-530-C-Matrice delle responsabilità",
        ],
        "🧭 Pianificazione & Supporto": [
            "MOD-620-B-Pianificazione",
            "MOD-710-A-Ambienti di lavoro",
            "MOD-710-B-Dispositivi",
            "MOD-710-C-Risorse misurazione",
            "MOD-710-D-Attrezzature",
            "MOD-710-E-Conoscenza organizzativa",
            "MOD-710-Supporti",
        ],
        "🏭 Operatività & Controllo": [
            "MOD-740-B-Monitoraggio comunicazione",
            "MOD-840-A Mappatura fornitori",
            "MOD-850-B-Identificazione e tracciabilità",
            "MOD-850-H-Controllo per variabili",
            "MOD-850-I-Controllo per attributi",
            "MOD-870-B- Prodotti non conformi",
        ],
        "📈 Valutazione & Miglioramento": [
            "MOD-610-B-Risk management",
            "MOD-910-C-Soddisfazione clienti",
            "MOD-910-E-Soddisfazione persone",
            "MOD-910-G-Soddisfazione fornitori",
            "MOD-910-H-Performance",
            "MOD-1020-A-Apertura Non Conformità",
            "MOD-1020-B-Azioni Correttive",
        ],
    }

    # Mappa tra file_key e "page" usata nel routing sidebar
    # (alcuni nomi differiscono!)
    KEY_TO_PAGE = {
        "MOD-1020-A-Apertura Non Conformità": "MOD-1020-A - Apertura Non Conformità",
        "MOD-1020-B-Azioni Correttive": "MOD-1020-B - Gestisci Azioni Correttive",
        # per gli altri coincide con file_key
    }

    # piccola legenda
    with st.expander("Legenda stato file", expanded=False):
        st.write("🟢 file presente e leggibile")
        st.write("🟡 file mancante (non ancora creato)")
        st.write("🔴 errore lettura file (formato / permessi / file aperto)")

    # Render gruppi
    for group_title, keys in MOD_GROUPS.items():
        with st.expander(group_title, expanded=True):

            # intestazione tabellare
            h1, h2, h3, h4, h5 = st.columns([0.6, 3.2, 1.2, 1.5, 1.4])
            with h1: st.markdown("**Stato**")
            with h2: st.markdown("**Modulo**")
            with h3: st.markdown("**Record**")
            with h4: st.markdown("**Ultima data**")
            with h5: st.markdown("**Azione**")

            st.divider()

            for k in keys:
                df, status = load_df_safe(k)
                badge = file_badge(status)
                n = len(df) if status == "ok" else 0
                last_date = infer_last_date(df) if status == "ok" else "-"

                page_name = KEY_TO_PAGE.get(k, k)  # se non mappato, usa lo stesso nome

                c1, c2, c3, c4, c5 = st.columns([0.6, 3.2, 1.2, 1.5, 1.4])
                with c1:
                    st.write(badge)
                with c2:
                    st.write(k)
                with c3:
                    st.write(n)
                with c4:
                    st.write(last_date)
                with c5:
                    # chiave unica per ogni bottone
                    if st.button("Apri / Consulta", key=f"open_{k}", use_container_width=True):
                        goto(page_name)

def dashboard_home():
    st.subheader("📊 Dashboard SG-QSA ")

    # --- file path principali
    fp_nc = get_file_path("MOD-1020-A-Apertura Non Conformità")
    fp_ac = get_file_path("MOD-1020-B-Azioni Correttive")
    fp_risk = get_file_path("MOD-610-B-Risk management")
    fp_form_reg = get_file_path("MOD-720-C-Registro formazione")
    fp_form_mon = get_file_path("MOD-720-F.1-Monitoraggio formazione")
    fp_form_mon_cs = get_file_path("MOD-720-F.2-Monitoraggio formazione CS")

    # --- load DF (robusto)
    def load_df(fp: str) -> pd.DataFrame:
        if not os.path.exists(fp):
            return pd.DataFrame()
        try:
            return pd.read_excel(fp).fillna("")
        except Exception:
            return pd.DataFrame()

    df_nc = load_df(fp_nc)
    df_ac = load_df(fp_ac)
    df_risk = load_df(fp_risk)
    df_reg = load_df(fp_form_reg)
    df_mon = load_df(fp_form_mon)
    df_mon_cs = load_df(fp_form_mon_cs)

    # =========================================================
    # TABS
    # =========================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧩 Quadro Generale",
        "❗ Non Conformità & Azioni",
        "⚠️ Rischi & Opportunità",
        "🎓 Formazione"
    ])

    # =========================================================
    # TAB 1 — QUADRO GENERALE
    # =========================================================
    with tab1:
        c1, c2, c3, c4 = st.columns(4)

        # --- NC KPI
        if not df_nc.empty and "Stato" in df_nc.columns:
            nc_aperte = int((df_nc["Stato"] == "Aperta").sum())
            nc_analisi = int((df_nc["Stato"] == "In Analisi").sum())
            nc_chiuse = int((df_nc["Stato"] == "Chiusa").sum())
            nc_tot = len(df_nc)
        else:
            nc_aperte = nc_analisi = nc_chiuse = nc_tot = 0

        # --- Azioni KPI
        if not df_ac.empty and "Stato" in df_ac.columns:
            ac_aperte = int((df_ac["Stato"] == "Aperta").sum())
            ac_analisi = int((df_ac["Stato"] == "In Analisi").sum())
            ac_chiuse = int((df_ac["Stato"] == "Chiusa").sum())
            ac_tot = len(df_ac)
        else:
            ac_aperte = ac_analisi = ac_chiuse = ac_tot = 0

        with c1:
            kpi_card("NC aperte", str(nc_aperte), f"Totale NC: {nc_tot}")
            if st.button("➡️ Vai a MOD-1020-A (NC)", key="go_nc_from_gen"):
                goto("MOD-1020-A - Apertura Non Conformità")

        with c2:
            kpi_card("Azioni correttive aperte", str(ac_aperte), f"Totale azioni: {ac_tot}")
            if st.button("➡️ Vai a MOD-1020-B (Azioni)", key="go_ac_from_gen"):
                goto("MOD-1020-B - Gestisci Azioni Correttive")

        # --- Rischi “Alti”
        with c3:
            rischi_alti = 0
            if not df_risk.empty and "Valutazione" in df_risk.columns:
                rischi_alti = int((df_risk["Valutazione"] == "Alto").sum())
            kpi_card("Rischi ALTI", str(rischi_alti), f"Record risk: {len(df_risk)}")
            if st.button("➡️ Vai a MOD-610-B (Risk)", key="go_risk_from_gen"):
                goto("MOD-610-B-Risk management")

        # --- Formazione (monitoraggio scadenze)
        with c4:
            scadute = 0
            in_scadenza = 0
            # MOD-720-F.1 ha “Stato” già pronto
            if not df_mon.empty and "Stato" in df_mon.columns:
                scadute += int((df_mon["Stato"] == "Scaduto").sum())
                in_scadenza += int((df_mon["Stato"] == "In scadenza").sum())

            kpi_card("Formazione", f"{in_scadenza} in scadenza", f"{scadute} scadute")
            if st.button("➡️ Vai a MOD-720-F.1 (Monitoraggio)", key="go_form_from_gen"):
                goto("MOD-720-F.1-Monitoraggio formazione")

        st.divider()

        # Mini “azioni rapide” (jump diretti)
        st.markdown("### ⚡ Azioni rapide")
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button("➕ Nuova NC", use_container_width=True):
                goto("MOD-1020-A - Apertura Non Conformità")
        with q2:
            if st.button("🛠️ Registra Azione correttiva", use_container_width=True):
                goto("MOD-1020-B - Gestisci Azioni Correttive")
        with q3:
            if st.button("⚠️ Inserisci nuovo rischio", use_container_width=True):
                goto("MOD-610-B-Risk management")
        with q4:
            if st.button("🎓 Registro formazione", use_container_width=True):
                goto("MOD-720-C-Registro formazione")

    # =========================================================
    # TAB 2 — NC & AZIONI (con drill-down)
    # =========================================================
    with tab2:
        st.markdown("### ❗ Non Conformità")
        if df_nc.empty:
            st.info("Nessuna NC registrata.")
        else:
            # Filtri rapidi
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                cat = st.selectbox("Categoria", [""] + sorted(df_nc.get("Categoria", pd.Series()).replace("", pd.NA).dropna().unique().tolist()))
            with f2:
                grav = st.selectbox("Gravità", [""] + sorted(df_nc.get("Gravità", pd.Series()).replace("", pd.NA).dropna().unique().tolist()))
            with f3:
                rep = st.selectbox("Reparto", [""] + sorted(df_nc.get("Reparto", pd.Series()).replace("", pd.NA).dropna().unique().tolist()))
            with f4:
                stt = st.selectbox("Stato", [""] + sorted(df_nc.get("Stato", pd.Series()).replace("", pd.NA).dropna().unique().tolist()))

            df_view = df_nc.copy()
            if cat and "Categoria" in df_view.columns:
                df_view = df_view[df_view["Categoria"] == cat]
            if grav and "Gravità" in df_view.columns:
                df_view = df_view[df_view["Gravità"] == grav]
            if rep and "Reparto" in df_view.columns:
                df_view = df_view[df_view["Reparto"] == rep]
            if stt and "Stato" in df_view.columns:
                df_view = df_view[df_view["Stato"] == stt]

            st.dataframe(df_view, use_container_width=True, hide_index=True)

            # Drill-down: seleziono una NC e salto al modulo NC
            if "ID NC" in df_view.columns and not df_view.empty:
                st.markdown("#### 🔎 Apri NC nel modulo")
                chosen_nc = st.selectbox("Seleziona ID NC", df_view["ID NC"].tolist())
                if st.button("➡️ Apri NC in MOD-1020-A", use_container_width=True):
                    goto(
                        "MOD-1020-A - Apertura Non Conformità",
                        nc_selected_id=chosen_nc
                    )

                colA, colB = st.columns([1, 2])
                with colA:
                    if st.button("➡️ Vai a MOD-1020-A", use_container_width=True):
                        # non hai ancora un preselettore per NC nel modulo A,
                        # quindi salto semplice (se vuoi lo aggiungiamo dopo)
                        goto("MOD-1020-A - Apertura Non Conformità")

                with colB:
                    # Jump intelligente: porta direttamente alle azioni collegate
                    if st.button("➡️ Vai a MOD-1020-B (Azioni collegate)", use_container_width=True):
                        # qui non serve preselezione, perché in B filtri già per ID NC con selectbox
                        goto("MOD-1020-B - Gestisci Azioni Correttive")

        st.divider()

        st.markdown("### 🛠️ Azioni Correttive")
        if df_ac.empty:
            st.info("Nessuna azione correttiva registrata.")
        else:
            st.dataframe(df_ac, use_container_width=True, hide_index=True)

            if "ID AZIONE" in df_ac.columns and not df_ac.empty:
                st.markdown("#### 👀 Apri Azione nello viewer (MOD-1020-C)")
                chosen_ac = st.selectbox("Seleziona ID AZIONE", df_ac["ID AZIONE"].tolist())
                if st.button("➡️ Apri in MOD-1020-C", use_container_width=True):
                    goto("MOD-1020-C - Visualizza Azioni Correttive", ac_selected_action_id=chosen_ac)

    # =========================================================
    # TAB 3 — RISK (con jump al modulo)
    # =========================================================
    with tab3:
        st.markdown("### ⚠️ Rischi & Opportunità")
        if df_risk.empty:
            st.info("Nessun rischio/opportunità registrato.")
            if st.button("➕ Vai a MOD-610-B (inserisci)", use_container_width=True):
                goto("MOD-610-B-Risk management")
        else:
            st.dataframe(df_risk, use_container_width=True, hide_index=True)
            if st.button("➡️ Vai a MOD-610-B (gestisci)", use_container_width=True):
                goto("MOD-610-B-Risk management")

    # =========================================================
    # TAB 4 — FORMAZIONE (con jump ai moduli)
    # =========================================================
    with tab4:
        st.markdown("### 🎓 Formazione")
        c1, c2, c3 = st.columns(3)

        with c1:
            kpi_card("Registro formazione (MOD-720-C)", str(len(df_reg)), "Eventi registrati")
            if st.button("➡️ Vai a MOD-720-C", key="go_720c"):
                goto("MOD-720-C-Registro formazione")

        with c2:
            kpi_card("Monitoraggio dipendenti (MOD-720-F.1)", str(len(df_mon)), "Record monitorati")
            if st.button("➡️ Vai a MOD-720-F.1", key="go_720f1"):
                goto("MOD-720-F.1-Monitoraggio formazione")

        with c3:
            kpi_card("Monitoraggio CS (MOD-720-F.2)", str(len(df_mon_cs)), "Record monitorati")
            if st.button("➡️ Vai a MOD-720-F.2", key="go_720f2"):
                goto("MOD-720-F.2-Monitoraggio formazione CS")

        st.divider()

        if not df_mon.empty:
            st.markdown("#### 📌 Stato formazione (dipendenti)")
            st.dataframe(df_mon, use_container_width=True, hide_index=True)

        if not df_mon_cs.empty:
            st.markdown("#### 📌 Stato formazione (CS)")
            st.dataframe(df_mon_cs, use_container_width=True, hide_index=True)

    # ---- PARTE 6: Archivio completo moduli
    dashboard_archivio_moduli()


def form_mod_400_a():
    st.subheader("Compilazione: MOD-400-A-Contesto")
    f1 = st.text_input("FATTORI INFLUENTI SULLA CAPACITA' DI SODDISFARE IL CLIENTE")
    ambito = st.text_input("AMBITO")
    ie = st.selectbox("I/E", ["I", "E"])
    indice = st.selectbox("INDICE DI INFLUENZA", [1, 2, 3])
    valore = "Basso" if indice == 1 else "Medio" if indice == 2 else "Alto"
    processo = st.text_input("PROCESSO INFLUENZATO")
    analisi = st.text_input("ANALISI DA PARTE DI")
    check = st.selectbox("CHECK", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "FATTORI INFLUENTI SULLA CAPACITA' DI SODDISFARE IL CLIENTE": f1,
            "AMBITO": ambito,
            "I/E": ie,
            "INDICE DI INFLUENZA": indice,
            "VALORE INFLUENZA": valore,
            "PROCESSO INFLUENZATO": processo,
            "ANALISI DA PARTE DI": analisi,
            "CHECK": check
        }])
        append_to_excel("MOD-400-A-Contesto", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_400_b():
    st.subheader("Compilazione: MOD-400-B-Parti interessate")
    parti = st.text_input("PARTI INTERESSATE")
    esigenze = st.text_input("ESIGENZE E ASPETTATIVE")
    ie = st.selectbox("I/E", ["I", "E"])
    indice = st.selectbox("INDICE DI INFLUENZA", [1, 2, 3])
    valore = "Basso" if indice == 1 else "Medio" if indice == 2 else "Alto"
    check = st.selectbox("CHECK", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "PARTI INTERESSATE": parti,
            "ESIGENZE E ASPETTATIVE": esigenze,
            "I/E": ie,
            "INDICE DI INFLUENZA": indice,
            "VALORE INFLUENZA": valore,
            "CHECK": check
        }])
        append_to_excel("MOD-400-B-Parti interessate", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_530_b():
    st.subheader("Compilazione: MOD-530-B-Ruoli e requisiti")
    ruolo = st.text_input("Ruolo")
    esperienza = st.text_input("Esperienza")
    inglese = st.selectbox("Inglese", ["Base", "Intermedio", "Avanzato"])
    dipendente = st.text_input("Dipendente")
    contesto = st.checkbox("Conoscenza di contesto e parti interessate")

    proc_istruzioni = st.slider("Procedure e istruzioni", 1, 5)
    norme_iso = st.slider("Norme ISO", 1, 5)
    risk_thinking = st.slider("Risk based thinking", 1, 5)
    approccio_proc = st.slider("Approccio per processi", 1, 5)
    media_competenza = round((proc_istruzioni + norme_iso + risk_thinking + approccio_proc) / 4, 2)

    politica = st.slider("Politica, rischi e obiettivi", 1, 5)
    organigramma = st.slider("Organigramma e mansioni", 1, 5)
    risorse = st.slider("Risorse interne", 1, 5)
    media_consapevolezza = round((politica + organigramma + risorse) / 3, 2)

    media_totale = round((media_competenza + media_consapevolezza) / 2, 2)

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Ruolo": ruolo,
            "Esperienza": esperienza,
            "Inglese": inglese,
            "Dipendente": dipendente,
            "Contesto e parti interessate": "Sì" if contesto else "No",
            "Procedure e istruzioni": proc_istruzioni,
            "Norme ISO": norme_iso,
            "Risk based thinking": risk_thinking,
            "Approccio per processi": approccio_proc,
            "Media competenza acquisita": media_competenza,
            "Politica, rischi e obiettivi": politica,
            "Organigramma e mansioni": organigramma,
            "Risorse interne": risorse,
            "Media consapevolezza acquisita": media_consapevolezza,
            "Media totale": media_totale
        }])
        append_to_excel("MOD-530-B-Ruoli e requisiti", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_530_c():
    st.subheader("Compilazione: MOD-530-C-Matrice delle responsabilità")

    processo = st.selectbox("PROCESSO", [
        "Monitoraggio del contesto", "Organizzazione del personale", "Gestione rischi e opportunità",
        "Obiettivi", "Pianificazione delle modifiche", "Emergenze", "Valutazione dei rischi S&S",
        "Gestione delle risorse", "Persone e competenze", "Comunicazione", "Documentazione SGI derivante da PROC",
        "Requisiti", "Progettazione", "Gestione fornitori", "Approvvigionamento", "Produzione",
        "Assistenza post vendita", "Preservazione", "Controllo output non conformi",
        "Monitoraggio, misurazione e analisi", "Audit interni", "Riesame di direzione",
        "Non conformità e azioni correttive", "Miglioramento continuo"
    ])

    fase = st.text_input("FASE DEL PROCESSO")
    documentazione = st.text_input("DOCUMENTAZIONE/STRUMENTO")
    responsabile = st.text_input("RESPONSABILE")
    check = st.selectbox("CHECK", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "PROCESSO": processo,
            "FASE DEL PROCESSO": fase,
            "DOCUMENTAZIONE/STRUMENTO": documentazione,
            "RESPONSABILE": responsabile,
            "CHECK": check
        }])
        append_to_excel("MOD-530-C-Matrice delle responsabilità", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_610_b():
    st.subheader("Compilazione: MOD-610-B - Risk management")

    descrizione = st.text_area("Descrizione rischio")
    area = st.selectbox("Area", ["Sicurezza", "Ambiente", "Qualità"])

    col1, col2 = st.columns(2)
    with col1:
        rischio_opportunita = st.selectbox("Tipo", ["", "R (Rischio)", "O (Opportunità)"])
        probabilita = st.selectbox("Probabilità (1-4)", [1, 2, 3, 4])
        conseguenza = st.selectbox("Conseguenza (1-4)", [1, 2, 3, 4])
        indice = probabilita * conseguenza

        if indice == 0:
            valutazione = ""
        elif indice < 4:
            valutazione = "Basso"
        elif indice < 8:
            valutazione = "Medio"
        else:
            valutazione = "Alto"

    with col2:
        trattamento = st.multiselect("Trattamento", [
            "Trasferire Rischio", "Evitare Rischio", "Mitigare Rischio", "Accettare Rischio", "Gestire opportunità"
        ])
        azione = st.text_input("Azione (collegata al trattamento)")
        responsabile = st.text_input("Responsabile")
        check = st.checkbox("Check completato")

        prob_ricalc = st.selectbox("Probabilità ricalcolata (1-4)", [1, 2, 3, 4])
        cons_ricalc = st.selectbox("Conseguenza ricalcolata (1-4)", [1, 2, 3, 4])
        indice_ricalc = prob_ricalc * cons_ricalc

        if indice_ricalc == 0:
            valutazione_ricalc = ""
        elif indice_ricalc < 4:
            valutazione_ricalc = "Basso"
        elif indice_ricalc < 8:
            valutazione_ricalc = "Medio"
        else:
            valutazione_ricalc = "Alto"

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Descrizione rischio": descrizione,
            "Area": area,
            "Tipo": rischio_opportunita,
            "Probabilità": probabilita,
            "Conseguenza": conseguenza,
            "Indice": indice,
            "Valutazione": valutazione,
            "Trattamento": ", ".join(trattamento),
            "Azione": azione,
            "Responsabile": responsabile,
            "Check": "OK" if check else "",
            "Probabilità ricalcolata": prob_ricalc,
            "Conseguenza ricalcolata": cons_ricalc,
            "Indice rivalutato": indice_ricalc,
            "Valutazione rivalutata": valutazione_ricalc
        }])
        append_to_excel("MOD-610-B-Risk management", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_620_b():
    st.subheader("Compilazione: MOD-620-B-Pianificazione")

    obiettivo = st.text_input("Obiettivo")
    descrizione = st.text_area("Descrizione")
    processo = st.text_input("Processo/Funzione")
    responsabile = st.text_input("Responsabile")
    risorse = st.text_input("Risorse")
    scadenza = st.date_input("Scadenza")

    oggi = date.today()
    giorni_rimanenti = (scadenza - oggi).days
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Obiettivo": obiettivo,
            "Descrizione": descrizione,
            "Processo/Funzione": processo,
            "Responsabile": responsabile,
            "Risorse": risorse,
            "Scadenza": iso_date(scadenza),
            "Giorni dalla scadenza": giorni_rimanenti,
            "Check": check
        }])
        append_to_excel("MOD-620-B-Pianificazione", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_a():
    st.subheader("Compilazione: MOD-710-A-Ambienti di lavoro")

    data_ins = st.date_input("Data")
    ambiente = st.text_input("Ambiente")
    sede = st.text_input("Sede")
    area = st.text_input("Area")

    col1, col2, col3 = st.columns(3)
    with col1:
        luminosita = st.slider("Luminosità", 1, 5)
        temperatura = st.slider("Temperatura", 1, 5)
    with col2:
        spazio = st.slider("Spazio", 1, 5)
        ordine = st.slider("Ordine", 1, 5)
    with col3:
        pulizia = st.slider("Pulizia", 1, 5)

    risultato = round((luminosita + temperatura + spazio + ordine + pulizia) / 5, 2)

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Ambiente": ambiente,
            "Sede": sede,
            "Area": area,
            "Luminosità": luminosita,
            "Temperatura": temperatura,
            "Spazio": spazio,
            "Ordine": ordine,
            "Pulizia": pulizia,
            "Risultato": risultato
        }])
        append_to_excel("MOD-710-A-Ambienti di lavoro", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_b():
    st.subheader("Compilazione: MOD-710-B-Dispositivi")

    data_ins = st.date_input("Data")
    dispositivo = st.text_input("Nome dispositivo")
    ubicazione = st.text_input("Ubicazione")
    responsabile = st.text_input("Responsabile")
    funzionalita = st.slider("Funzionalità (1=scarso, 5=ottimo)", 1, 5)
    stato = st.slider("Stato generale (1=scarso, 5=ottimo)", 1, 5)
    manutenzione = st.slider("Manutenzione recente (1=mai, 5=frequente)", 1, 5)
    media_valutazione = round((funzionalita + stato + manutenzione) / 3, 2)

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Dispositivo": dispositivo,
            "Ubicazione": ubicazione,
            "Responsabile": responsabile,
            "Funzionalità": funzionalita,
            "Stato generale": stato,
            "Manutenzione": manutenzione,
            "Valutazione media": media_valutazione
        }])
        append_to_excel("MOD-710-B-Dispositivi", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_c():
    st.subheader("Compilazione: MOD-710-C-Risorse di misurazione")

    data_ins = st.date_input("Data")
    strumento = st.text_input("Strumento di misura")
    codice = st.text_input("Codice identificativo")
    ubicazione = st.text_input("Ubicazione")
    responsabile = st.text_input("Responsabile")
    taratura = st.selectbox("Taratura eseguita", ["Sì", "No"])
    scadenza_taratura = st.date_input("Scadenza taratura")

    giorni_rimanenti = (scadenza_taratura - date.today()).days

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Strumento": strumento,
            "Codice": codice,
            "Ubicazione": ubicazione,
            "Responsabile": responsabile,
            "Taratura eseguita": taratura,
            "Scadenza taratura": iso_date(scadenza_taratura),
            "Giorni alla scadenza": giorni_rimanenti
        }])
        append_to_excel("MOD-710-C-Risorse misurazione", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_d():
    st.subheader("Compilazione: MOD-710-D-Attrezzature")

    data_ins = st.date_input("Data")
    attrezzatura = st.text_input("Nome attrezzatura")
    codice = st.text_input("Codice identificativo")
    ubicazione = st.text_input("Ubicazione")
    responsabile = st.text_input("Responsabile")
    verifica_sicurezza = st.selectbox("Verifica sicurezza eseguita", ["Sì", "No"])
    manutenzione = st.selectbox("Manutenzione eseguita", ["Sì", "No"])
    prossima_verifica = st.date_input("Prossima verifica programmata")

    giorni_mancanti = (prossima_verifica - date.today()).days

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Attrezzatura": attrezzatura,
            "Codice": codice,
            "Ubicazione": ubicazione,
            "Responsabile": responsabile,
            "Verifica sicurezza": verifica_sicurezza,
            "Manutenzione": manutenzione,
            "Prossima verifica": iso_date(prossima_verifica),
            "Giorni alla prossima verifica": giorni_mancanti
        }])
        append_to_excel("MOD-710-D-Attrezzature", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_e():
    st.subheader("Compilazione: MOD-710-E-Conoscenza organizzativa")

    data_ins = st.date_input("Data")
    contesto = st.text_input("Contesto di riferimento")
    conoscenza = st.text_area("Conoscenza necessaria")
    modalita_accesso = st.text_input("Modalità di accesso alla conoscenza")
    aggiornamento_previsto = st.selectbox("Aggiornamento previsto", ["Sì", "No"])
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Contesto": contesto,
            "Conoscenza necessaria": conoscenza,
            "Modalità di accesso": modalita_accesso,
            "Aggiornamento previsto": aggiornamento_previsto,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-710-E-Conoscenza organizzativa", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_710_supporti():
    st.subheader("Compilazione: MOD-710-Supporti")

    data_ins = st.date_input("Data")
    supporto = st.text_input("Tipo di supporto")
    utilizzo = st.text_area("Utilizzo previsto")
    accessibilita = st.selectbox("Accessibilità", ["Alta", "Media", "Bassa"])
    protezione = st.selectbox("Protezione dati", ["Alta", "Media", "Bassa"])
    conservazione = st.text_input("Modalità di conservazione")
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Supporto": supporto,
            "Utilizzo previsto": utilizzo,
            "Accessibilità": accessibilita,
            "Protezione dati": protezione,
            "Conservazione": conservazione,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-710-Supporti", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_720_c():
    st.subheader("Compilazione: MOD-720-C-Registro formazione")

    data_ins = st.date_input("Data")
    nome = st.text_input("Nome partecipante")
    corso = st.text_input("Corso frequentato")
    ore = st.number_input("Ore di formazione", min_value=0.0, step=0.5)
    esito = st.selectbox("Esito", ["Idoneo", "Non idoneo", "In attesa"])
    validita = st.date_input("Validità fino al")
    responsabile = st.text_input("Responsabile del corso")

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Nome": nome,
            "Corso": corso,
            "Ore": ore,
            "Esito": esito,
            "Validità fino al": iso_date(validita),
            "Responsabile": responsabile
        }])
        append_to_excel("MOD-720-C-Registro formazione", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_720_f1():
    st.subheader("Compilazione: MOD-720-F.1 - Monitoraggio formazione")

    data_ins = st.date_input("Data")
    nome = st.text_input("Nome dipendente")
    formazione = st.text_input("Tipo di formazione")
    scadenza = st.date_input("Data di scadenza")
    giorni_alla_scadenza = (scadenza - date.today()).days
    stato = st.selectbox("Stato", ["Aggiornato", "Scaduto", "In scadenza"])
    note = st.text_area("Note aggiuntive")

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Nome": nome,
            "Formazione": formazione,
            "Scadenza": iso_date(scadenza),
            "Giorni alla scadenza": giorni_alla_scadenza,
            "Stato": stato,
            "Note": note
        }])
        append_to_excel("MOD-720-F.1-Monitoraggio formazione", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_720_f2():
    st.subheader("Compilazione: MOD-720-F.2 - Monitoraggio formazione CS")

    data_ins = st.date_input("Data")
    nome = st.text_input("Nome collaboratore")
    corso = st.text_input("Corso specifico (es. sicurezza, antincendio, ecc.)")
    scadenza = st.date_input("Data di scadenza")
    giorni_rimanenti = (scadenza - date.today()).days
    ente = st.text_input("Ente formatore")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Nome": nome,
            "Corso": corso,
            "Scadenza": iso_date(scadenza),
            "Giorni alla scadenza": giorni_rimanenti,
            "Ente formatore": ente,
            "Check": check
        }])
        append_to_excel("MOD-720-F.2-Monitoraggio formazione CS", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_720_g():
    st.subheader("Compilazione: MOD-720-G - Piano formazione annuale")

    anno = st.number_input("Anno di riferimento", min_value=2000, max_value=2100, step=1)
    corso = st.text_input("Corso previsto")
    destinatari = st.text_area("Destinatari (ruoli, reparti o nomi)")
    obiettivi = st.text_area("Obiettivi del corso")
    ore_programmate = st.number_input("Ore programmate", min_value=0.0, step=0.5)
    periodo = st.text_input("Periodo di svolgimento previsto")
    stato = st.selectbox("Stato", ["Pianificato", "Erogato", "Annullato"])
    note = st.text_area("Note aggiuntive")

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Anno": int(anno),
            "Corso": corso,
            "Destinatari": destinatari,
            "Obiettivi": obiettivi,
            "Ore programmate": ore_programmate,
            "Periodo": periodo,
            "Stato": stato,
            "Note": note
        }])
        append_to_excel("MOD-720-G-Piano formazione annuale", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_740_b():
    st.subheader("Compilazione: MOD-740-B - Monitoraggio comunicazione")

    data_ins = st.date_input("Data")
    canale = st.selectbox("Canale di comunicazione", ["Email", "Verbale", "Bacheca", "Gestione documentale", "Altro"])
    messaggio = st.text_area("Contenuto / Messaggio comunicato")
    destinatari = st.text_input("Destinatari / Reparti coinvolti")
    efficacia = st.selectbox("Efficacia percepita", ["Alta", "Media", "Bassa"])
    followup = st.text_area("Azioni / Follow-up previste")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Canale": canale,
            "Messaggio": messaggio,
            "Destinatari": destinatari,
            "Efficacia": efficacia,
            "Follow-up": followup,
            "Check": check
        }])
        append_to_excel("MOD-740-B-Monitoraggio comunicazione", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_840_a():
    st.subheader("Compilazione: MOD-840-A - Mappatura fornitori")

    data_ins = st.date_input("Data")
    fornitore = st.text_input("Nome fornitore")
    servizio_prodotto = st.text_input("Servizio / Prodotto fornito")
    categoria = st.selectbox("Categoria", ["Materiale diretto", "Servizi", "Consulenza", "Altro"])
    area_di_impiego = st.text_input("Area di impiego")
    criticita = st.selectbox("Criticità", ["Alta", "Media", "Bassa"])
    valutazione = st.slider("Valutazione complessiva (1-5)", 1, 5)
    approvato = st.selectbox("Approvato", ["Sì", "No", "In attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Fornitore": fornitore,
            "Servizio / Prodotto": servizio_prodotto,
            "Categoria": categoria,
            "Area di impiego": area_di_impiego,
            "Criticità": criticita,
            "Valutazione": valutazione,
            "Approvato": approvato
        }])
        append_to_excel("MOD-840-A Mappatura fornitori", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_850_b():
    st.subheader("Compilazione: MOD-850-B - Identificazione e tracciabilità")

    data_ins = st.date_input("Data")
    prodotto = st.text_input("Prodotto / Componente")
    codice = st.text_input("Codice identificativo")
    fase = st.text_input("Fase di lavorazione / processo")
    metodo_identificazione = st.selectbox("Metodo di identificazione", ["Etichetta", "Marcatura", "Sistema digitale", "Altro"])
    tracciabilita = st.selectbox("Tracciabilità garantita", ["Sì", "Parziale", "No"])
    note = st.text_area("Note aggiuntive")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Prodotto / Componente": prodotto,
            "Codice": codice,
            "Fase": fase,
            "Metodo identificazione": metodo_identificazione,
            "Tracciabilità": tracciabilita,
            "Note": note,
            "Check": check
        }])
        # FIX: niente _X
        append_to_excel("MOD-850-B-Identificazione e tracciabilità", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_850_h():
    st.subheader("Compilazione: MOD-850-H - Controllo per variabili")

    data_ins = st.date_input("Data")
    caratteristica = st.text_input("Caratteristica misurata")
    unita_misura = st.text_input("Unità di misura")
    valore_rilevato = st.number_input("Valore rilevato", format="%.3f")
    limite_min = st.number_input("Limite minimo", format="%.3f")
    limite_max = st.number_input("Limite massimo", format="%.3f")

    esito = "Non conforme" if (valore_rilevato < limite_min or valore_rilevato > limite_max) else "Conforme"
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Caratteristica": caratteristica,
            "Unità di misura": unita_misura,
            "Valore rilevato": valore_rilevato,
            "Limite minimo": limite_min,
            "Limite massimo": limite_max,
            "Esito": esito,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-850-H-Controllo per variabili", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_850_i():
    st.subheader("Compilazione: MOD-850-I - Controllo per attributi")

    data_ins = st.date_input("Data")
    oggetto = st.text_input("Oggetto del controllo")
    attributo = st.text_input("Attributo verificato (es. presenza, colore, integrità)")
    criterio = st.text_input("Criterio di accettazione")
    esito = st.selectbox("Esito", ["Conforme", "Non conforme"])
    azione = st.text_area("Azione intrapresa (se non conforme)")
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Oggetto": oggetto,
            "Attributo": attributo,
            "Criterio": criterio,
            "Esito": esito,
            "Azione intrapresa": azione,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-850-I-Controllo per attributi", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_870_b():
    st.subheader("Compilazione: MOD-870-B - Prodotti non conformi")

    data_ins = st.date_input("Data")
    prodotto = st.text_input("Prodotto / Componente non conforme")
    descrizione_nc = st.text_area("Descrizione della non conformità")
    rilevata_da = st.text_input("Rilevata da")
    fase = st.text_input("Fase in cui è stata rilevata")
    azione = st.text_area("Azione correttiva / contenitiva")
    destinazione = st.selectbox("Destinazione", ["Scarto", "Rilavorazione", "Accettazione condizionata", "Altro"])
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Prodotto": prodotto,
            "Descrizione NC": descrizione_nc,
            "Rilevata da": rilevata_da,
            "Fase": fase,
            "Azione": azione,
            "Destinazione": destinazione,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-870-B- Prodotti non conformi", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_910_c():
    st.subheader("Compilazione: MOD-910-C - Soddisfazione clienti")

    data_ins = st.date_input("Data")
    cliente = st.text_input("Nome cliente")
    commessa = st.text_input("Commessa / progetto")
    criteri = st.multiselect("Criteri valutati", ["Qualità", "Tempi", "Comunicazione", "Assistenza", "Prezzo", "Altro"])
    punteggio = st.slider("Punteggio complessivo (1–5)", 1, 5)
    note = st.text_area("Note / Osservazioni")
    responsabile = st.text_input("Responsabile analisi")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Cliente": cliente,
            "Commessa": commessa,
            "Criteri valutati": ", ".join(criteri),
            "Punteggio": punteggio,
            "Note": note,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-910-C-Soddisfazione clienti", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_910_e():
    st.subheader("Compilazione: MOD-910-E - Soddisfazione persone")

    data_ins = st.date_input("Data")
    nome = st.text_input("Nome lavoratore / collaboratore")
    reparto = st.text_input("Reparto / funzione")
    criteri = st.multiselect("Criteri valutati", ["Ambiente di lavoro", "Strumenti", "Relazioni", "Organizzazione", "Sicurezza", "Altro"])
    soddisfazione = st.slider("Livello di soddisfazione (1–5)", 1, 5)
    suggerimenti = st.text_area("Suggerimenti o richieste")
    valutatore = st.text_input("Valutatore / HR")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Nome": nome,
            "Reparto": reparto,
            "Criteri valutati": ", ".join(criteri),
            "Soddisfazione": soddisfazione,
            "Suggerimenti": suggerimenti,
            "Valutatore": valutatore,
            "Check": check
        }])
        append_to_excel("MOD-910-E-Soddisfazione persone", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_910_g():
    st.subheader("Compilazione: MOD-910-G - Soddisfazione fornitori")

    data_ins = st.date_input("Data")
    fornitore = st.text_input("Nome fornitore")
    tipologia = st.text_input("Tipologia di fornitura (materiale/servizio)")
    criteri = st.multiselect("Criteri valutati", ["Pagamenti", "Relazione commerciale", "Comunicazione", "Logistica", "Contrattualistica", "Altro"])
    soddisfazione = st.slider("Livello di soddisfazione (1–5)", 1, 5)
    feedback = st.text_area("Feedback ricevuto / osservazioni")
    valutatore = st.text_input("Valutatore interno")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Fornitore": fornitore,
            "Tipologia": tipologia,
            "Criteri valutati": ", ".join(criteri),
            "Soddisfazione": soddisfazione,
            "Feedback": feedback,
            "Valutatore": valutatore,
            "Check": check
        }])
        append_to_excel("MOD-910-G-Soddisfazione fornitori", new_row)
        st.success("Dati salvati correttamente nel file Excel")


def form_mod_910_h():
    st.subheader("Compilazione: MOD-910-H - Performance")

    data_ins = st.date_input("Data")
    processo = st.text_input("Processo / Area analizzata")
    indicatore = st.text_input("Indicatore di performance (KPI)")
    valore_rilevato = st.number_input("Valore rilevato", format="%.2f")
    valore_atteso = st.number_input("Valore atteso / target", format="%.2f")
    scostamento = valore_rilevato - valore_atteso
    giudizio = "Superato" if scostamento >= 0 else "Non raggiunto"
    note = st.text_area("Note o azioni correttive")
    responsabile = st.text_input("Responsabile")
    check = st.selectbox("Check", ["ok", "attesa"])

    if st.button("Salva dati nel file Excel"):
        new_row = pd.DataFrame([{
            "Data": iso_date(data_ins),
            "Processo / Area": processo,
            "Indicatore": indicatore,
            "Valore rilevato": valore_rilevato,
            "Valore atteso": valore_atteso,
            "Scostamento": scostamento,
            "Giudizio": giudizio,
            "Note": note,
            "Responsabile": responsabile,
            "Check": check
        }])
        append_to_excel("MOD-910-H-Performance", new_row)
        st.success("Dati salvati correttamente nel file Excel")


# ==============================
# MOD-1020-A - Apertura NC
# ==============================
def form_mod_1020_a():
    st.subheader("Compilazione: MOD-1020-A - Apertura Non Conformità")

    file_key = "MOD-1020-A-Apertura Non Conformità"
    file_path = get_file_path(file_key)

    tab = st.radio("Scegli la funzione", ["📥 Nuova NC", "📋 Riepilogo NC", "📊 Dashboard", "📝 Aggiorna / PDF"])

    if tab == "📥 Nuova NC":
        data_nc = st.date_input("Data rilevamento", value=date.today())
        rilevatore = st.selectbox("Rilevata da", ["Operatore", "Controllo Qualità", "Responsabile", "Cliente", "Audit Interno", "Altro"])
        reparto = st.text_input("Reparto / Area coinvolta")

        categoria = st.radio("Categoria della Non Conformità", ["Prodotto", "Processo", "Fornitore", "Cliente"])
        descrizione = st.text_area("Descrizione sintetica della non conformità")

        ordine = st.text_input("Ordine di produzione / fornitura / cliente")
        lotto = st.text_input("Numero di lotto (se presente)")
        codice_prodotto = st.text_input("Codice prodotto")

        gravita = st.selectbox("Gravità / Priorità", ["Alta", "Media", "Bassa"])
        azione_contenitiva = st.text_area("Azione contenitiva immediata")

        file = st.file_uploader("Carica un file (immagine o PDF)", type=["png", "jpg", "jpeg", "pdf"])

        if st.button("Salva Non Conformità"):
            oggi = date.today()
            progressivo = 1
            if os.path.exists(file_path):
                df_exist = pd.read_excel(file_path)
                progressivo = len(df_exist) + 1

            id_nc = f"NC{progressivo:02d}_{oggi.day:02d}_{oggi.month:02d}_{oggi.year}"

            new_row = pd.DataFrame([{
                "ID NC": id_nc,
                "Data rilevamento": iso_date(data_nc),  # ISO
                "Rilevata da": rilevatore,
                "Reparto": reparto,
                "Categoria": categoria,
                "Descrizione": descrizione,
                "Ordine": ordine,
                "Lotto": lotto,
                "Codice prodotto": codice_prodotto,
                "Gravità": gravita,
                "Azione contenitiva": azione_contenitiva,
                "Nome file allegato": file.name if file else "",
                "Stato": "Aperta",
                "Responsabile azione correttiva": "",
                "Sintesi azione correttiva": "",
                "Verifica efficacia": ""
            }])

            append_to_excel(file_key, new_row)
            st.success(f"NC registrata con ID {id_nc}")

            if file:
                allegati_dir = os.path.join(BASE_PATH, "allegati_nc")
                os.makedirs(allegati_dir, exist_ok=True)
                with open(os.path.join(allegati_dir, file.name), "wb") as f:
                    f.write(file.getbuffer())
                st.info(f"📎 File allegato salvato come: {file.name}")

    elif tab == "📋 Riepilogo NC":
        if os.path.exists(file_path):
            df = pd.read_excel(file_path).fillna("")
            st.markdown("### Filtri")
            col1, col2, col3 = st.columns(3)
            with col1:
                categoria = st.selectbox("Categoria", ["Tutte"] + sorted(df["Categoria"].dropna().unique().tolist()))
            with col2:
                gravita = st.selectbox("Gravità", ["Tutte"] + sorted(df["Gravità"].dropna().unique().tolist()))
            with col3:
                stato = st.selectbox("Stato", ["Tutti"] + sorted(df["Stato"].dropna().unique().tolist()))

            if categoria != "Tutte":
                df = df[df["Categoria"] == categoria]
            if gravita != "Tutte":
                df = df[df["Gravità"] == gravita]
            if stato != "Tutti":
                df = df[df["Stato"] == stato]

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Nessuna non conformità registrata.")

    elif tab == "📊 Dashboard":
        if os.path.exists(file_path):
            df = pd.read_excel(file_path).fillna("")
            st.markdown("### Grafico: Non Conformità per Reparto")
            reparto_count = df["Reparto"].value_counts()
            fig1, ax1 = plt.subplots()
            reparto_count.plot(kind="bar", ax=ax1)
            ax1.set_ylabel("Numero di NC")
            ax1.set_xlabel("Reparto")
            st.pyplot(fig1)

            st.markdown("### Grafico: Distribuzione per Categoria")
            cat_count = df["Categoria"].value_counts()
            fig2, ax2 = plt.subplots()
            cat_count.plot(kind="pie", autopct='%1.1f%%', ax=ax2)
            ax2.set_ylabel("")
            st.pyplot(fig2)

            st.markdown("### Grafico: Trend mensile")
            df["_data"] = pd.to_datetime(df["Data rilevamento"], errors="coerce")  # ISO -> ok
            df["Mese"] = df["_data"].dt.to_period("M")
            trend = df.groupby("Mese").size()
            fig3, ax3 = plt.subplots()
            trend.plot(kind="line", marker='o', ax=ax3)
            ax3.set_ylabel("Numero di NC")
            ax3.set_xlabel("Mese")
            st.pyplot(fig3)
        else:
            st.warning("Nessun dato disponibile per la dashboard.")

    elif tab == "📝 Aggiorna / PDF":
        if not os.path.exists(file_path):
            st.warning("Nessuna NC registrata.")
            return

        df = pd.read_excel(file_path).fillna("")
        ids = df["ID NC"].tolist()
        # preselezione da dashboard (se presente)
        default_id = ids[0]
        if st.session_state.get("nc_selected_id") in ids:
            default_id = st.session_state.nc_selected_id

        selected_id = st.selectbox(
            "Seleziona ID NC da aggiornare",
            ids,
            index=ids.index(default_id)
        )

        # una volta usata, la puliamo
        st.session_state.nc_selected_id = None

        row_idx = df.index[df["ID NC"] == selected_id][0]
        selected_nc = df.loc[row_idx].fillna("")

        st.write("**Descrizione NC:**", selected_nc.get("Descrizione", ""))

        resp = st.text_input("Responsabile azione correttiva", value=selected_nc.get("Responsabile azione correttiva", ""))
        sint = st.text_area("Sintesi azione correttiva", value=selected_nc.get("Sintesi azione correttiva", ""))

        valori_verifica = ["", "Sì", "No"]
        ver_corr = str(selected_nc.get("Verifica efficacia", ""))
        idx_ver = valori_verifica.index(ver_corr) if ver_corr in valori_verifica else 0
        ver = st.selectbox("Verifica efficacia completata", valori_verifica, index=idx_ver)

        valori_stato = ["Aperta", "In Analisi", "Chiusa"]
        st_corr = str(selected_nc.get("Stato", "Aperta"))
        idx_st = valori_stato.index(st_corr) if st_corr in valori_stato else 0
        stato = st.selectbox("Stato", valori_stato, index=idx_st)

        if st.button("💾 Salva aggiornamenti NC"):
            df.at[row_idx, "Responsabile azione correttiva"] = resp
            df.at[row_idx, "Sintesi azione correttiva"] = sint
            df.at[row_idx, "Verifica efficacia"] = ver
            df.at[row_idx, "Stato"] = stato
            df.to_excel(file_path, index=False)
            st.success("Aggiornamento salvato con successo")

        if st.button("📄 Esporta PDF della NC"):
            pdf = make_pdf(module_seq="1020-A", module_name="Apertura Non Conformità")

            pdf_title(pdf, f"Report Non Conformità - {selected_id}")

            # Campi principali (ordine "pulito")
            pdf_kv(pdf, "ID NC", selected_id)
            pdf_kv(pdf, "Data rilevamento", df.at[row_idx, "Data rilevamento"])
            pdf_kv(pdf, "Rilevata da", df.at[row_idx, "Rilevata da"])
            pdf_kv(pdf, "Reparto", df.at[row_idx, "Reparto"], gap_after=True)

            pdf_kv(pdf, "Categoria", df.at[row_idx, "Categoria"])
            pdf_kv(pdf, "Gravità", df.at[row_idx, "Gravità"])
            pdf_kv(pdf, "Stato", df.at[row_idx, "Stato"], gap_after=True)

            pdf_kv(pdf, "Descrizione", df.at[row_idx, "Descrizione"], gap_after=True)

            pdf_kv(pdf, "Ordine", df.at[row_idx, "Ordine"])
            pdf_kv(pdf, "Lotto", df.at[row_idx, "Lotto"])
            pdf_kv(pdf, "Codice prodotto", df.at[row_idx, "Codice prodotto"], gap_after=True)

            pdf_kv(pdf, "Azione contenitiva", df.at[row_idx, "Azione contenitiva"], gap_after=True)

            # Se vuoi includere anche i campi di gestione/chiusura:
            pdf_kv(pdf, "Responsabile azione correttiva", df.at[row_idx, "Responsabile azione correttiva"], gap_after=True)
            pdf_kv(pdf, "Sintesi azione correttiva", df.at[row_idx, "Sintesi azione correttiva"], gap_after=True)
            pdf_kv(pdf, "Verifica efficacia", df.at[row_idx, "Verifica efficacia"], gap_after=True)

            # Allegato (solo nome file)
            pdf_kv(pdf, "Nome file allegato", df.at[row_idx, "Nome file allegato"])

            pdf_file = os.path.join(BASE_PATH, f"NC_{selected_id}.pdf")
            pdf.output(pdf_file)

            with open(pdf_file, "rb") as f:
                st.download_button(
                    "📥 Scarica PDF",
                    data=f,
                    file_name=os.path.basename(pdf_file),
                    mime="application/pdf"
                )


# ==============================
# MOD-1020-B - Azioni Correttive
# ==============================
def form_mod_1020_b():
    st.subheader("📌 MOD-1020-B - Visualizza e Gestisci Azioni Correttive")

    file_nc_path = get_file_path("MOD-1020-A-Apertura Non Conformità")
    file_azioni_path = get_file_path("MOD-1020-B-Azioni Correttive")

    if not os.path.exists(file_nc_path):
        st.warning("Non sono presenti Non Conformità registrate.")
        return

    df_nc = pd.read_excel(file_nc_path).fillna("")

    st.markdown("### 🔍 Filtra le NC registrate")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        filtro_id = st.selectbox("ID NC", [""] + sorted(df_nc["ID NC"].dropna().unique().tolist()))
    with col2:
        filtro_categoria = st.selectbox("Categoria", [""] + sorted(df_nc["Categoria"].dropna().unique().tolist()))
    with col3:
        filtro_codice = st.selectbox("Codice prodotto", [""] + sorted(df_nc["Codice prodotto"].dropna().unique().tolist()))
    with col4:
        filtro_reparto = st.selectbox("Reparto / Area", [""] + sorted(df_nc["Reparto"].dropna().unique().tolist()))
    with col5:
        filtro_resp = st.selectbox(
            "Responsabile",
            [""] + sorted(df_nc["Responsabile azione correttiva"].replace("", "[Non assegnato]").unique().tolist())
        )

    if filtro_id:
        df_nc = df_nc[df_nc["ID NC"] == filtro_id]
    if filtro_categoria:
        df_nc = df_nc[df_nc["Categoria"] == filtro_categoria]
    if filtro_codice:
        df_nc = df_nc[df_nc["Codice prodotto"] == filtro_codice]
    if filtro_reparto:
        df_nc = df_nc[df_nc["Reparto"] == filtro_reparto]
    if filtro_resp and filtro_resp != "[Non assegnato]":
        df_nc = df_nc[df_nc["Responsabile azione correttiva"] == filtro_resp]

    if df_nc.empty:
        st.warning("Nessuna NC trovata con i criteri di ricerca.")
        return

    id_selezionato = st.selectbox("Seleziona NC", df_nc["ID NC"].tolist())
    selected_nc = df_nc[df_nc["ID NC"] == id_selezionato].iloc[0].fillna("")

    st.markdown("---")
    st.markdown(f"### 💾 Dati registrati della NC - {id_selezionato}")
    with st.expander("Visualizza tutti i dettagli della NC"):
        for col in selected_nc.index:
            st.write(f"**{col}**: {selected_nc[col]}")

    st.markdown("### 🛠️ Compilazione Azione Correttiva")

    responsabile = st.text_input("Responsabile azione correttiva", value=selected_nc.get("Responsabile azione correttiva", ""))
    sintesi = st.text_area("Sintesi azione correttiva", value=selected_nc.get("Sintesi azione correttiva", ""))

    data_apertura = st.date_input("Data apertura azione correttiva", value=date.today())
    data_chiusura = st.date_input("Data prevista chiusura", value=date.today())

    valori_verifica = ["", "Sì", "No"]
    ver_corr = selected_nc.get("Verifica efficacia", "")
    idx_ver = valori_verifica.index(ver_corr) if ver_corr in valori_verifica else 0
    verifica = st.selectbox("Verifica efficacia completata", valori_verifica, index=idx_ver)

    descrizione_verifica = st.text_area("Descrizione esito verifica efficacia", value="")

    valori_stato = ["Aperta", "In Analisi", "Chiusa"]
    st_corr = selected_nc.get("Stato", "Aperta")
    idx_st = valori_stato.index(st_corr) if st_corr in valori_stato else 0
    stato = st.selectbox("Stato", valori_stato, index=idx_st)

    if st.button("📂 Salva come nuova azione correttiva collegata"):
        id_azione = next_action_id(file_azioni_path, date.today())
        new_action = pd.DataFrame([{
            "ID AZIONE": id_azione,
            "ID NC": id_selezionato,
            "Data apertura": iso_date(data_apertura),               # ISO
            "Data chiusura prevista": iso_date(data_chiusura),      # ISO
            "Responsabile": responsabile,
            "Sintesi": sintesi,
            "Verifica efficacia": verifica,
            "Descrizione esito": descrizione_verifica,
            "Stato": stato
        }])

        if os.path.exists(file_azioni_path):
            df_actions = pd.read_excel(file_azioni_path).fillna("")
            df_actions = pd.concat([df_actions, new_action], ignore_index=True)
        else:
            df_actions = new_action

        df_actions.to_excel(file_azioni_path, index=False)
        st.success(f"Azione correttiva salvata correttamente: {id_azione}")

    if st.button("📄 Esporta PDF della NC"):
        pdf = make_pdf(module_seq="1020-B", module_name="Gestione Azioni Correttive")

        pdf_title(pdf, f"Report Non Conformità - {id_selezionato}")

        # Dati NC (da selected_nc che è una Serie)
        pdf_kv(pdf, "ID NC", id_selezionato)
        pdf_kv(pdf, "Data rilevamento", selected_nc.get("Data rilevamento", ""))
        pdf_kv(pdf, "Rilevata da", selected_nc.get("Rilevata da", ""))
        pdf_kv(pdf, "Reparto", selected_nc.get("Reparto", ""), gap_after=True)

        pdf_kv(pdf, "Categoria", selected_nc.get("Categoria", ""))
        pdf_kv(pdf, "Gravità", selected_nc.get("Gravità", ""))
        pdf_kv(pdf, "Stato", selected_nc.get("Stato", ""), gap_after=True)

        pdf_kv(pdf, "Descrizione", selected_nc.get("Descrizione", ""), gap_after=True)

        pdf_kv(pdf, "Ordine", selected_nc.get("Ordine", ""))
        pdf_kv(pdf, "Lotto", selected_nc.get("Lotto", ""))
        pdf_kv(pdf, "Codice prodotto", selected_nc.get("Codice prodotto", ""), gap_after=True)

        pdf_kv(pdf, "Azione contenitiva", selected_nc.get("Azione contenitiva", ""), gap_after=True)

        pdf_kv(pdf, "Responsabile azione correttiva", selected_nc.get("Responsabile azione correttiva", ""), gap_after=True)
        pdf_kv(pdf, "Sintesi azione correttiva", selected_nc.get("Sintesi azione correttiva", ""), gap_after=True)
        pdf_kv(pdf, "Verifica efficacia", selected_nc.get("Verifica efficacia", ""), gap_after=True)

        pdf_file = os.path.join(BASE_PATH, f"NC_{id_selezionato}.pdf")
        pdf.output(pdf_file)

        with open(pdf_file, "rb") as f:
            st.download_button(
                "📥 Scarica PDF",
                data=f,
                file_name=os.path.basename(pdf_file),
                mime="application/pdf"
            )

    # Storico azioni per NC
    if os.path.exists(file_azioni_path):
        st.markdown("---")
        st.markdown("### 🛠 Storico delle Azioni Correttive (per questa NC)")
        df_azioni = pd.read_excel(file_azioni_path).fillna("")
        df_sel = df_azioni[df_azioni["ID NC"] == id_selezionato].copy()

        st.dataframe(df_sel, use_container_width=True, hide_index=True)

        if not df_sel.empty:
            st.markdown("#### 🔎 Apri una azione nel viewer (MOD-1020-C)")

            # selezione per ID AZIONE (robusto)
            id_azione_sel = st.selectbox("Seleziona ID AZIONE", df_sel["ID AZIONE"].tolist())

            if st.button("➡️ Apri dettagli in MOD-1020-C"):
                st.session_state.ac_selected_action_id = id_azione_sel
                st.session_state.page = "MOD-1020-C - Visualizza Azioni Correttive"
                st.rerun()
    else:
        st.info("Nessuna azione correttiva registrata.")


# ==============================
# MOD-1020-C - Viewer Azioni
# ==============================
def form_mod_1020_c():
    st.subheader("👀 MOD-1020-C - Visualizza Azioni Correttive")

    file_azioni_path = get_file_path("MOD-1020-B-Azioni Correttive")
    file_nc_path = get_file_path("MOD-1020-A-Apertura Non Conformità")

    if not os.path.exists(file_azioni_path):
        st.warning("Nessuna azione correttiva registrata al momento.")
        return

    df = pd.read_excel(file_azioni_path).fillna("")

    st.markdown("### 🔍 Filtri")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_idnc = st.selectbox("ID NC", [""] + sorted(df["ID NC"].unique().tolist()))
    with c2:
        f_resp = st.selectbox("Responsabile", [""] + sorted(df["Responsabile"].unique().tolist()))
    with c3:
        f_stato = st.selectbox("Stato", [""] + sorted(df["Stato"].unique().tolist()))
    with c4:
        f_ver = st.selectbox("Verifica efficacia", [""] + sorted(df["Verifica efficacia"].unique().tolist()))

    df_view = df.copy()
    if f_idnc:
        df_view = df_view[df_view["ID NC"] == f_idnc]
    if f_resp:
        df_view = df_view[df_view["Responsabile"] == f_resp]
    if f_stato:
        df_view = df_view[df_view["Stato"] == f_stato]
    if f_ver:
        df_view = df_view[df_view["Verifica efficacia"] == f_ver]

    st.markdown("### 📋 Elenco Azioni Correttive")
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    if df_view.empty:
        st.info("Nessun record con i filtri selezionati.")
        return

    # Preselezione robusta per ID AZIONE
    options = df_view["ID AZIONE"].tolist()
    default_id = options[0]
    if st.session_state.get("ac_selected_action_id") in options:
        default_id = st.session_state.ac_selected_action_id

    selected_action_id = st.selectbox("Seleziona ID AZIONE", options, index=options.index(default_id))
    record = df[df["ID AZIONE"] == selected_action_id].iloc[0].to_dict()

    st.markdown("#### ✅ Dettagli Azione Correttiva")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**ID AZIONE:** {record.get('ID AZIONE','')}")
        st.write(f"**ID NC:** {record.get('ID NC','')}")
        st.write(f"**Data apertura:** {record.get('Data apertura','')}")
        st.write(f"**Data chiusura prevista:** {record.get('Data chiusura prevista','')}")
        st.write(f"**Responsabile:** {record.get('Responsabile','')}")
    with col2:
        st.write(f"**Stato:** {record.get('Stato','')}")
        st.write(f"**Verifica efficacia:** {record.get('Verifica efficacia','')}")
        st.write(f"**Descrizione esito:** {record.get('Descrizione esito','')}")

    st.markdown("**Sintesi:**")
    st.info(record.get("Sintesi", ""))

    # mostra dettagli NC collegata
    if os.path.exists(file_nc_path) and record.get("ID NC", ""):
        df_nc = pd.read_excel(file_nc_path).fillna("")
        match = df_nc[df_nc["ID NC"] == record["ID NC"]]
        if not match.empty:
            with st.expander("🔗 Visualizza dettagli Non Conformità collegata"):
                nc = match.iloc[0].to_dict()
                for k, v in nc.items():
                    st.write(f"**{k}**: {v}")

    if st.button("📄 Esporta PDF Azione Correttiva"):
        pdf = make_pdf(module_seq="1020-C", module_name="Viewer Azioni Correttive")

        pdf_title(pdf, "Scheda Azione Correttiva")

        # Ordine e formattazione "bella"
        pdf_kv(pdf, "ID AZIONE", record.get("ID AZIONE", ""))
        pdf_kv(pdf, "ID NC", record.get("ID NC", ""))
        pdf_kv(pdf, "Data apertura", record.get("Data apertura", ""))
        pdf_kv(pdf, "Data chiusura prevista", record.get("Data chiusura prevista", ""))

        # doppio spazio dopo Responsabile
        pdf_kv(pdf, "Responsabile", record.get("Responsabile", ""), gap_after=True)

        # doppio spazio dopo Sintesi
        pdf_kv(pdf, "Sintesi", record.get("Sintesi", ""), gap_after=True)

        # doppio spazio dopo Verifica efficacia
        pdf_kv(pdf, "Verifica efficacia", record.get("Verifica efficacia", ""), gap_after=True)

        # doppio spazio dopo Descrizione esito
        pdf_kv(pdf, "Descrizione esito", record.get("Descrizione esito", ""), gap_after=True)

        # doppio spazio dopo Stato
        pdf_kv(pdf, "Stato", record.get("Stato", ""), gap_after=True)

        pdf_file = os.path.join(BASE_PATH, f"AZIONE_CORRETTIVA_{record.get('ID AZIONE','')}.pdf")
        pdf.output(pdf_file)

        with open(pdf_file, "rb") as f:
            st.download_button(
                "⬇️ Scarica PDF",
                data=f,
                file_name=os.path.basename(pdf_file),
                mime="application/pdf"
            )


# =========================================================
# ROUTING
# =========================================================
page = st.session_state.page

if page == "Dashboard":
    dashboard_home()
elif page == "MOD-400-A-Contesto":
    form_mod_400_a()
elif page == "MOD-400-B-Parti interessate":
    form_mod_400_b()
elif page == "MOD-530-B-Ruoli e requisiti":
    form_mod_530_b()
elif page == "MOD-530-C-Matrice delle responsabilità":
    form_mod_530_c()
elif page == "MOD-610-B-Risk management":
    form_mod_610_b()
elif page == "MOD-620-B-Pianificazione":
    form_mod_620_b()
elif page == "MOD-710-A-Ambienti di lavoro":
    form_mod_710_a()
elif page == "MOD-710-B-Dispositivi":
    form_mod_710_b()
elif page == "MOD-710-C-Risorse misurazione":
    form_mod_710_c()
elif page == "MOD-710-D-Attrezzature":
    form_mod_710_d()
elif page == "MOD-710-E-Conoscenza organizzativa":
    form_mod_710_e()
elif page == "MOD-710-Supporti":
    form_mod_710_supporti()
elif page == "MOD-720-C-Registro formazione":
    form_mod_720_c()
elif page == "MOD-720-F.1-Monitoraggio formazione":
    form_mod_720_f1()
elif page == "MOD-720-F.2-Monitoraggio formazione CS":
    form_mod_720_f2()
elif page == "MOD-720-G-Piano formazione annuale":
    form_mod_720_g()
elif page == "MOD-740-B-Monitoraggio comunicazione":
    form_mod_740_b()
elif page == "MOD-840-A Mappatura fornitori":
    form_mod_840_a()
elif page == "MOD-850-B-Identificazione e tracciabilità":
    form_mod_850_b()
elif page == "MOD-850-H-Controllo per variabili":
    form_mod_850_h()
elif page == "MOD-850-I-Controllo per attributi":
    form_mod_850_i()
elif page == "MOD-870-B- Prodotti non conformi":
    form_mod_870_b()
elif page == "MOD-910-C-Soddisfazione clienti":
    form_mod_910_c()
elif page == "MOD-910-E-Soddisfazione persone":
    form_mod_910_e()
elif page == "MOD-910-G-Soddisfazione fornitori":
    form_mod_910_g()
elif page == "MOD-910-H-Performance":
    form_mod_910_h()
elif page == "MOD-1020-A - Apertura Non Conformità":
    form_mod_1020_a()
elif page == "MOD-1020-B - Gestisci Azioni Correttive":
    form_mod_1020_b()
elif page == "MOD-1020-C - Visualizza Azioni Correttive":
    form_mod_1020_c()
elif page == "REG-DOC - Registro Documenti SGQ":
    form_reg_doc()
else:
    st.info("Pagina non implementata.")
