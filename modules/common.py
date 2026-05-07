import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================================================
# PATHS / ASSETS
# =========================================================
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

BASE_PATH = "moduli_compilati"
os.makedirs(BASE_PATH, exist_ok=True)

# =========================================================
# DATE HELPERS
# =========================================================
UI_FMT = "%d/%m/%Y"
ISO_FMT = "%Y-%m-%d"

def iso_date(d: date) -> str:
    return d.strftime(ISO_FMT)

def parse_iso_date(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(str(s), ISO_FMT).date()
    except Exception:
        return None

def safe_iso_from_any(x) -> str:
    if x is None:
        return ""
    if isinstance(x, (datetime, date)):
        return iso_date(x if isinstance(x, date) else x.date())

    s = str(x).strip()
    if not s:
        return ""

    d = parse_iso_date(s)
    if d:
        return iso_date(d)

    try:
        d2 = datetime.strptime(s, UI_FMT).date()
        return iso_date(d2)
    except Exception:
        return s

# =========================================================
# FILE MAP
# =========================================================
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
    "MOD-850-B-Identificazione e tracciabilità": "MOD-850-B-Identificazione_Tracciabilita.xlsx",
    "MOD-850-H-Controllo per variabili": "MOD-850-H-Controllo_Variabili.xlsx",
    "MOD-850-I-Controllo per attributi": "MOD-850-I-Controllo_Attributi.xlsx",
    "MOD-870-B- Prodotti non conformi": "MOD-870-B-Prodotti_Non_Conformi.xlsx",
    "MOD-910-C-Soddisfazione clienti": "MOD-910-C-Soddisfazione_Clienti.xlsx",
    "MOD-910-E-Soddisfazione persone": "MOD-910-E-Soddisfazione_Persone.xlsx",
    "MOD-910-G-Soddisfazione fornitori": "MOD-910-G-Soddisfazione_Fornitori.xlsx",
    "MOD-910-H-Performance": "MOD-910-H-Performance.xlsx",

    "MOD-1020-A-Apertura Non Conformità": "MOD-1020-A-Apertura_NC.xlsx",
    "MOD-1020-B-Azioni Correttive": "MOD-1020-B-Azioni_Correttive.xlsx",

    "MOD-920-E-Monitoraggioauditing": "MOD-920-E-Monitoraggio_Auditing.xlsx",
    "REG-DOC - Registro Documenti SGQ": "REG-DOC-Registro_Documenti_SGQ.xlsx",
}

def get_file_path(key: str) -> str:
    key = str(key).strip().replace(".xlsx", "")
    fname = FILE_MAP.get(key)
    if not fname:
        raise ValueError(f"File key non mappata: {key}")
    return os.path.join(BASE_PATH, fname)

# =========================================================
# UI HELPERS
# =========================================================
def sidebar_logo():
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.sidebar.warning("Logo non trovato in assets/logo.png")

def goto(page_name: str, **state_updates):
    for k, v in state_updates.items():
        st.session_state[k] = v
    st.session_state.page = page_name
    st.session_state._sync_nav = True
    st.rerun()

# =========================================================
# STORAGE HELPERS (Excel)
# =========================================================
def append_to_excel(file_key: str, new_row: pd.DataFrame) -> None:
    fp = get_file_path(file_key)
    if os.path.exists(fp):
        existing = pd.read_excel(fp)
        updated = pd.concat([existing, new_row], ignore_index=True)
    else:
        updated = new_row
    updated.to_excel(fp, index=False)

def load_df_safe(file_key: str):
    try:
        fp = get_file_path(file_key)
        if not os.path.exists(fp):
            return pd.DataFrame(), "missing"
        df = pd.read_excel(fp).fillna("")
        return df, "ok"
    except Exception:
        return pd.DataFrame(), "error"

def infer_last_date(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "-"

    candidate_cols = [
        "Data", "DATA", "Data rilevamento", "Data apertura", "Data inserimento",
        "Scadenza", "Data chiusura prevista", "Validità fino al"
    ]
    col = next((c for c in candidate_cols if c in df.columns), None)
    if not col:
        return "-"

    s = df[col].astype(str).replace("", pd.NA).dropna()
    if s.empty:
        return "-"

    dt = pd.to_datetime(s, errors="coerce", format=ISO_FMT)
    if dt.isna().all():
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)

    dt = dt.dropna()
    if dt.empty:
        return "-"

    return dt.max().strftime(UI_FMT)

def file_badge(status: str) -> str:
    return "🟢" if status == "ok" else "🟡" if status == "missing" else "🔴"

