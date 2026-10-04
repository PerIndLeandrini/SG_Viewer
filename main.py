import os
from pathlib import Path
from datetime import datetime
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# =========================================================
# PORTALE QUALIFICA FORNITORE - VIEWER ESTERNO SGQ
# ---------------------------------------------------------
# App Streamlit SOLO LETTURA per utenti esterni.
# - Login tramite .streamlit/secrets.toml
# - Nessuna funzione di scrittura/modifica dati
# - Menu ridotto per evidenze condivisibili
# - Colonne sensibili nascoste
# - Dashboard iniziale per qualifica fornitore
# =========================================================

# =========================================================
# CONFIG BASE
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
# Cartella multi-azienda. Ogni utente, dopo il login, viene agganciato
# alla propria cartella aziendale tramite Streamlit Secrets.
ROOT_MODULES_DIR = BASE_DIR / "moduli_aziende"
DEFAULT_COMPANY_SLUG = "interglobo"

# Fallback: mantiene compatibilità con la vecchia struttura /moduli_compilati
# utile in locale o se vuoi continuare a testare una singola azienda.
DEFAULT_BASE_PATH = BASE_DIR / "moduli_compilati"
BASE_PATH = DEFAULT_BASE_PATH

ASSETS_DIR = BASE_DIR / "assets"

# Loghi:
# - logo_home.png: mostrato nella pagina di login / accesso generale
# - logo_<azienda>.png: mostrato dopo il login in base allo slug aziendale
#   Esempi: logo_interglobo.png, logo_shipping_service.png
# - logo.png: fallback generico, se presente
HOME_LOGO_PATH = ASSETS_DIR / "logo_home.png"
DEFAULT_LOGO_PATH = ASSETS_DIR / "logo.png"

APP_TITLE = "Portale Qualifica Fornitore"
APP_SUBTITLE = "Viewer evidenze Sistema di Gestione Qualità"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🤝",
    layout="wide",
)

# =========================================================
# OPZIONI VIEWER ESTERNO
# =========================================================
# download disattivati di default per viewer esterno
ALLOW_CSV_DOWNLOAD = False
ALLOW_DOCUMENT_DOWNLOAD = False

# deterrente anti-copia lato browser
ANTI_COPY_PROTECTION = True

# usa tabelle HTML statiche al posto di st.dataframe
# Motivo: st.dataframe/render grid può avere menu contestuali interni non intercettabili bene.
USE_STATIC_NO_COPY_TABLES = True
MAX_STATIC_TABLE_ROWS = 500


# =========================================================
# CSS LEGGERO
# =========================================================
def inject_css():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.0rem;
            font-weight: 750;
            color: #102A43;
            margin-bottom: 0.10rem;
        }
        .main-subtitle {
            font-size: 1.00rem;
            color: #52606D;
            margin-bottom: 1.10rem;
        }
        .soft-card {
            padding: 1rem 1.1rem;
            border-radius: 16px;
            border: 1px solid #E5EAF0;
            background: #FFFFFF;
            box-shadow: 0 2px 10px rgba(16, 42, 67, 0.05);
        }
        .status-ok {
            display: inline-block;
            padding: 0.18rem 0.65rem;
            border-radius: 999px;
            background: #D9F2E3;
            color: #176B3A;
            font-weight: 650;
            font-size: 0.86rem;
        }
        .status-warn {
            display: inline-block;
            padding: 0.18rem 0.65rem;
            border-radius: 999px;
            background: #FFF2CC;
            color: #7A5700;
            font-weight: 650;
            font-size: 0.86rem;
        }
        .status-info {
            display: inline-block;
            padding: 0.18rem 0.65rem;
            border-radius: 999px;
            background: #DDEBFF;
            color: #174A7C;
            font-weight: 650;
            font-size: 0.86rem;
        }
        div[data-testid="stSidebar"] {
            background: #F3F6FA;
        }
        .sgq-table-wrap {
            width: 100%;
            max-height: 560px;
            overflow: auto;
            border: 1px solid #E5EAF0;
            border-radius: 14px;
            background: #FFFFFF;
            box-shadow: 0 2px 8px rgba(16, 42, 67, 0.04);
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }
        table.sgq-static-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            line-height: 1.35;
            user-select: none !important;
        }
        table.sgq-static-table thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: #F3F6FA;
            color: #243B53;
            text-align: left;
            font-weight: 700;
            border-bottom: 1px solid #D9E2EC;
            padding: 0.58rem 0.65rem;
            white-space: nowrap;
        }
        table.sgq-static-table tbody td {
            border-bottom: 1px solid #E5EAF0;
            padding: 0.50rem 0.65rem;
            vertical-align: top;
            color: #243B53;
        }
        table.sgq-static-table tbody tr:nth-child(even) {
            background: #FAFBFC;
        }
        table.sgq-static-table tbody tr:hover {
            background: #EEF4FF;
        }
        .sgq-table-note {
            font-size: 0.82rem;
            color: #7B8794;
            margin-top: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# =========================================================
# PROTEZIONE ANTI-COPIA / ANTI-TASTO DESTRO
# ---------------------------------------------------------
# Nota importante: questa protezione è un deterrente lato browser.
# Non può impedire screenshot, foto dello schermo, OCR o accessi tecnici
# avanzati tramite strumenti del browser. Serve però a evitare copia/incolla
# banale, selezione testo, tasto destro e scorciatoie comuni.
# =========================================================
def apply_anti_copy_protection():
    if not ANTI_COPY_PROTECTION:
        return

    st.markdown(
        """
        <style>
        html, body, .stApp, .main, [data-testid="stAppViewContainer"],
        [data-testid="stDataFrame"], [data-testid="stMarkdownContainer"],
        table, thead, tbody, tr, td, th, div, span, p {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }

        input, textarea, [contenteditable="true"],
        div[data-baseweb="input"] *, div[data-baseweb="textarea"] * {
            -webkit-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
        }

        @media print {
            body {
                display: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;

            function isEditable(el) {
                if (!el) return false;
                const tag = (el.tagName || "").toLowerCase();
                if (["input", "textarea", "select"].includes(tag)) return true;
                if (el.isContentEditable) return true;
                if (el.closest && (
                    el.closest('input') ||
                    el.closest('textarea') ||
                    el.closest('[contenteditable="true"]') ||
                    el.closest('[data-baseweb="input"]') ||
                    el.closest('[data-baseweb="textarea"]')
                )) return true;
                return false;
            }

            function clearSelection() {
                try {
                    const sel = doc.getSelection ? doc.getSelection() : null;
                    if (sel) sel.removeAllRanges();
                } catch (err) {}
            }

            function install() {
                if (doc.__sgqAntiCopyInstalled) return;
                doc.__sgqAntiCopyInstalled = true;

                doc.addEventListener('contextmenu', function (e) {
                    if (!isEditable(e.target)) {
                        e.preventDefault();
                        clearSelection();
                        return false;
                    }
                }, true);

                doc.addEventListener('copy', function (e) {
                    if (!isEditable(e.target)) {
                        e.preventDefault();
                        clearSelection();
                        return false;
                    }
                }, true);

                doc.addEventListener('cut', function (e) {
                    if (!isEditable(e.target)) {
                        e.preventDefault();
                        clearSelection();
                        return false;
                    }
                }, true);

                doc.addEventListener('selectstart', function (e) {
                    if (!isEditable(e.target)) {
                        e.preventDefault();
                        return false;
                    }
                }, true);

                doc.addEventListener('dragstart', function (e) {
                    if (!isEditable(e.target)) {
                        e.preventDefault();
                        return false;
                    }
                }, true);

                doc.addEventListener('keydown', function (e) {
                    const key = (e.key || '').toLowerCase();
                    const combo = e.ctrlKey || e.metaKey;

                    if (isEditable(e.target)) return true;

                    // Blocca copia, taglia, seleziona tutto, salva, stampa, sorgente pagina.
                    if (combo && ['c', 'x', 'a', 's', 'p', 'u'].includes(key)) {
                        e.preventDefault();
                        clearSelection();
                        return false;
                    }

                    // Blocca scorciatoie comuni devtools. Non è una sicurezza assoluta.
                    if (key === 'f12') {
                        e.preventDefault();
                        return false;
                    }
                    if (combo && e.shiftKey && ['i', 'j', 'c'].includes(key)) {
                        e.preventDefault();
                        return false;
                    }
                }, true);
            }

            install();
        })();
        </script>
        """,
        height=0,
        width=0,
    )

apply_anti_copy_protection()

# =========================================================
# LOGHI DINAMICI
# =========================================================
def get_company_logo_filename(slug: str) -> str:
    """
    Restituisce il nome file logo associato allo slug aziendale.

    Di default usa: logo_<slug>.png
    Esempio: interglobo -> logo_interglobo.png

    Puoi anche sovrascrivere da secrets:
    [viewer_company_logos]
    interglobo = "logo_interglobo.png"
    shipping_service = "logo_shipping.png"
    """
    logo_map = _secrets_dict("viewer_company_logos")
    default_name = f"logo_{slug}.png"
    return str(logo_map.get(slug, default_name)).strip() or default_name


def get_company_logo_path(slug: str) -> Path:
    return ASSETS_DIR / get_company_logo_filename(slug)


def get_active_logo_path() -> Path:
    """
    Prima del login mostra logo_home.png.
    Dopo il login mostra il logo dell'azienda associata all'utente.
    Se il logo specifico non esiste, usa logo.png come fallback.
    """
    logged = bool(st.session_state.get("viewer_logged", False))

    if not logged:
        if HOME_LOGO_PATH.exists():
            return HOME_LOGO_PATH
        return DEFAULT_LOGO_PATH

    slug = get_current_company_slug()
    company_logo = get_company_logo_path(slug)
    if company_logo.exists():
        return company_logo

    return DEFAULT_LOGO_PATH


def sidebar_logo():
    try:
        logo_path = get_active_logo_path()
        if logo_path.exists():
            img = Image.open(logo_path)
            st.image(img, use_container_width=True)
        else:
            st.caption("Logo non disponibile")
    except Exception as e:
        st.caption(f"Logo non caricabile: {e}")


def render_login_home():
    """Pagina centrale mostrata prima del login."""
    st.markdown("<br>", unsafe_allow_html=True)
    logo_path = HOME_LOGO_PATH if HOME_LOGO_PATH.exists() else DEFAULT_LOGO_PATH

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        if logo_path.exists():
            st.image(Image.open(logo_path), use_container_width=True)

    st.markdown(
        f"<div class='main-title' style='text-align:center;'>🤝 {APP_TITLE}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='main-subtitle' style='text-align:center;'>{APP_SUBTITLE}</div>",
        unsafe_allow_html=True,
    )
    st.info("Inserire le credenziali nella barra laterale per accedere al viewer documentale.")

# =========================================================
# FILE MAP - SOLO MODULI UTILIZZABILI NEL VIEWER
# =========================================================
FILE_MAP = {
    "REG-DOC - Registro Documenti SGQ": "REG-DOC-Registro_Documenti_SGQ.xlsx",
    "MOD-530-B-Ruoli e requisiti": "MOD-530-B-Ruoli_e_Requisiti.xlsx",
    "MOD-530-C-Matrice delle responsabilità": "MOD-530-C-Matrice_Responsabilita.xlsx",
    "MOD-620-B-Pianificazione": "MOD-620-B-Pianificazione.xlsx",
    "MOD-720-G-Piano formazione annuale": "MOD-720-G-Piano_Formazione_Annuale.xlsx",
    "MOD-740-B-Monitoraggio comunicazione": "MOD-740-B-Monitoraggio_Comunicazione.xlsx",
    "MOD-840-A Mappatura fornitori": "MOD-840-A-Mappatura_Fornitori.xlsx",
    "MOD-870-B-Servizi non conformi": "MOD-870-B-Prodotti_Non_Conformi.xlsx",
    "MOD-910-C-Soddisfazione clienti": "MOD-910-C-Soddisfazione_Clienti.xlsx",
    "MOD-910-H-Performance": "MOD-910-H-Performance.xlsx",
    "MOD-920-A-Piano audit annuale": "MOD-920-A-Piano_Audit_Annuale.xlsx",
    "MOD-920-E-Monitoraggioauditing": "MOD-920-E-Monitoraggio_Auditing.xlsx",
}

# =========================================================
# MENU VISIBILE AGLI UTENTI ESTERNI
# =========================================================
EXTERNAL_PAGES = {
    "🏠 Dashboard Qualifica": "dashboard",
    "📁 Registro Documenti SGQ": "REG-DOC - Registro Documenti SGQ",
    "🏢 Ruoli e Requisiti": "MOD-530-B-Ruoli e requisiti",
    "🧩 Matrice Responsabilità": "MOD-530-C-Matrice delle responsabilità",
    "🎯 Obiettivi e Pianificazione": "MOD-620-B-Pianificazione",
    "🎓 Piano Formazione": "MOD-720-G-Piano formazione annuale",
    "📢 Comunicazioni SGQ": "MOD-740-B-Monitoraggio comunicazione",
    "🤝 Qualifica Fornitori": "MOD-840-A Mappatura fornitori",
    "⚠️ Servizi Non Conformi": "MOD-870-B-Servizi non conformi",
    "😊 Soddisfazione Clienti": "MOD-910-C-Soddisfazione clienti",
    "📊 Performance e KPI": "MOD-910-H-Performance",
    "🔍 Audit Interni": "audit_esterno",
}

EXTERNAL_PAGES["⚠️ Risk Management"] = "risk_management"
# Integrazione audit: lettura Excel esistente e visualizzazione del PDF originale.
FILE_MAP.update({
    "MOD-920-B-Programma audit": "MOD-920-B-Programma_Audit.xlsx",
    "MOD-920-C-Verbale audit": "MOD-920-C-Verbale_Audit.pdf",
})
EXTERNAL_PAGES["📋 Programma Audit"] = "MOD-920-B-Programma audit"
EXTERNAL_PAGES["📄 MOD-920-C — Verbale Audit"] = "audit_verbale_pdf"

# =========================================================
# COLONNE DA NASCONDERE NEL VIEWER ESTERNO
# ---------------------------------------------------------
# I nomi sono volutamente ampi: se una colonna non esiste,
# viene ignorata senza errore.
# =========================================================
HIDDEN_COLUMNS_BY_MODULE = {
    "REG-DOC - Registro Documenti SGQ": [
        "Percorso interno", "Path interno", "Note interne", "Responsabile interno",
    ],
    "MOD-530-B-Ruoli e requisiti": [
        "Note interne", "Retribuzione", "Costo", "Telefono", "Email personale",
    ],
    "MOD-530-C-Matrice delle responsabilità": [
        "Note interne", "Dettagli riservati",
    ],
    "MOD-620-B-Pianificazione": [
        "Budget", "Costo", "Importo", "Fatturato", "Margine", "Note interne",
        "Dato economico", "Dati economici",
    ],
    "MOD-720-G-Piano formazione annuale": [
        "Note interne", "Costo", "Budget", "Docente interno", "Email", "Telefono",
    ],
    "MOD-740-B-Monitoraggio comunicazione": [
        "Note interne", "Destinatario nominativo", "Email", "Telefono",
    ],
    "MOD-840-A Mappatura fornitori": [
        "Note interne", "Motivazione criticità", "Valutazione interna",
        "Costo", "Prezzo", "Condizioni economiche", "Contatto", "Telefono", "Email",
    ],
    "MOD-870-B-Servizi non conformi": [
        "Cliente", "Commessa", "Codice ordine", "Ordine", "Riferimento cliente",
        "Descrizione dettagliata NC", "Responsabile interno", "Note interne",
        "Costo", "Importo", "Penale", "Nominativo",
    ],
    "MOD-910-C-Soddisfazione clienti": [
        "Cliente", "Contatto", "Email", "Telefono", "Note interne",
        "Reclamo dettagliato", "Riferimento ordine",
    ],
    "MOD-910-H-Performance": [
        "Note interne", "Dato economico", "Dati economici", "Margine", "Fatturato",
        "Costo", "Importo", "Cliente", "Commessa",
    ],
    "MOD-920-A-Piano audit annuale": [
        "Auditor", "Referente area", "Criteri / Riferimenti", "Obiettivi", "Note",
    ],
    "MOD-920-E-Monitoraggioauditing": [
        "Auditor", "Responsabile", "Descrizione", "Azione prevista",
        "ID NC collegata", "ID Azione Correttiva",
        "Verifica efficacia / Evidenze", "Note interne", "Dettaglio NC", "Evidenza riservata",
    ],
}

# parole chiave generiche: se contenute nel nome colonna, vengono nascoste
SENSITIVE_KEYWORDS = [
    "password", "token", "secret", "telefono", "cellulare", "email personale",
    "codice fiscale", "iban", "retribuzione", "stipendio", "margine",
]

# =========================================================
# UTILITY
# =========================================================
def _secrets_dict(section: str) -> dict:
    """Legge una sezione dei secrets come dizionario, senza rompere l'app se manca."""
    try:
        return dict(st.secrets.get(section, {}))
    except Exception:
        return {}


def get_user_company_slug(username: str) -> str:
    """
    Restituisce lo slug aziendale associato all'utente.

    Esempio secrets:
    [viewer_user_companies]
    Guest = "interglobo"
    guest_2 = "shipping_service"
    """
    user_companies = _secrets_dict("viewer_user_companies")
    slug = str(user_companies.get(username, DEFAULT_COMPANY_SLUG)).strip()
    return slug or DEFAULT_COMPANY_SLUG


def get_company_display_name(slug: str) -> str:
    """
    Restituisce il nome azienda leggibile.

    Esempio secrets:
    [viewer_company_names]
    interglobo = "Interglobo"
    shipping_service = "Shipping Service"
    """
    company_names = _secrets_dict("viewer_company_names")
    fallback = slug.replace("_", " ").replace("-", " ").title()
    return str(company_names.get(slug, fallback)).strip() or fallback


def set_current_company_for_user(username: str) -> None:
    slug = get_user_company_slug(username)
    st.session_state.viewer_company_slug = slug
    st.session_state.viewer_company_name = get_company_display_name(slug)


def get_current_company_slug() -> str:
    return str(st.session_state.get("viewer_company_slug", DEFAULT_COMPANY_SLUG)).strip() or DEFAULT_COMPANY_SLUG


def get_current_company_name() -> str:
    return str(
        st.session_state.get(
            "viewer_company_name",
            get_company_display_name(get_current_company_slug()),
        )
    ).strip()


def get_current_base_path() -> Path:
    """
    Percorso effettivo dei moduli per l'azienda loggata.

    Struttura prevista:
    moduli_aziende/
        interglobo/
            moduli_compilati/
        shipping_service/
            moduli_compilati/

    Se la cartella multi-azienda non esiste, usa il vecchio fallback:
    moduli_compilati/
    """
    slug = get_current_company_slug()
    company_path = ROOT_MODULES_DIR / slug / "moduli_compilati"

    if company_path.exists():
        return company_path

    return DEFAULT_BASE_PATH


def get_file_path(file_key: str) -> Path:
    fname = FILE_MAP.get(file_key)
    if not fname:
        raise ValueError(f"Modulo non mappato: {file_key}")
    return get_current_base_path() / fname


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.fillna("")
    return df


def hide_sensitive_columns(df: pd.DataFrame, file_key: str) -> pd.DataFrame:
    df = df.copy()

    hidden_cols = set(HIDDEN_COLUMNS_BY_MODULE.get(file_key, []))

    # nasconde anche colonne con parole chiave sensibili nel nome
    for col in df.columns:
        col_l = str(col).lower().strip()
        if any(k in col_l for k in SENSITIVE_KEYWORDS):
            hidden_cols.add(col)

    cols_to_drop = [c for c in hidden_cols if c in df.columns]
    return df.drop(columns=cols_to_drop, errors="ignore")


def read_excel_safe(file_key: str) -> pd.DataFrame | None:
    fp = get_file_path(file_key)
    if not fp.exists():
        return None

    try:
        # default: primo foglio del file Excel
        df = pd.read_excel(fp)
        df = normalize_df(df)
        df = hide_sensitive_columns(df, file_key)
        return df
    except Exception as e:
        st.error(f"Errore lettura file '{fp.name}': {e}")
        return None


def count_records(file_key: str) -> int:
    df = read_excel_safe(file_key)
    if df is None or df.empty:
        return 0
    # evita di contare righe completamente vuote
    df2 = df.copy()
    df2 = df2[df2.astype(str).apply(lambda r: any(x.strip() for x in r), axis=1)]
    return len(df2)


def make_record_label(row: pd.Series, idx: int) -> str:
    pieces = []
    for col in row.index[:4]:
        val = str(row.get(col, "")).strip()
        if val:
            pieces.append(val[:45])
    if not pieces:
        pieces = ["record"]
    return f"{idx + 1:03d} | " + " | ".join(pieces)


def status_badge(value: str) -> str:
    s = str(value).lower().strip()
    if s in ["disponibile", "attivo", "presente", "ok", "tracciato", "monitorato"]:
        return "<span class='status-ok'>Disponibile</span>"
    if "sintesi" in s or "aggreg" in s:
        return "<span class='status-info'>Sintesi consultabile</span>"
    return "<span class='status-warn'>In verifica</span>"

def render_no_copy_table(df: pd.DataFrame, caption: str | None = None, max_rows: int | None = None):
    """
    Renderizza una tabella statica HTML al posto di st.dataframe.
    Questo evita il menu contestuale interno della grid Streamlit, che può sfuggire
    ai blocchi JS/CSS anti-copia.
    """
    if df is None or df.empty:
        st.info("Nessun dato disponibile.")
        return

    max_rows = MAX_STATIC_TABLE_ROWS if max_rows is None else max_rows
    df_show = df.copy()
    truncated = False
    if max_rows and len(df_show) > max_rows:
        df_show = df_show.head(max_rows)
        truncated = True

    columns = [str(c) for c in df_show.columns]
    thead = "".join(f"<th>{html.escape(c)}</th>" for c in columns)

    rows_html = []
    for _, row in df_show.iterrows():
        cells = []
        for c in columns:
            val = row.get(c, "")
            text = "" if pd.isna(val) else str(val)
            cells.append(f"<td>{html.escape(text)}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    note = caption or ""
    if truncated:
        note = (note + " — " if note else "") + f"Mostrate le prime {len(df_show)} righe su {len(df)}. Usa filtri/ricerca per restringere i risultati."

    st.markdown(
        f"""
        <div class="sgq-table-wrap" oncontextmenu="return false;" oncopy="return false;" oncut="return false;" onselectstart="return false;">
            <table class="sgq-static-table" oncontextmenu="return false;" oncopy="return false;" oncut="return false;" onselectstart="return false;">
                <thead><tr>{thead}</tr></thead>
                <tbody>{''.join(rows_html)}</tbody>
            </table>
        </div>
        {f'<div class="sgq-table-note">{html.escape(note)}</div>' if note else ''}
        """,
        unsafe_allow_html=True,
    )


def render_view_table(df: pd.DataFrame, caption: str | None = None):
    if USE_STATIC_NO_COPY_TABLES:
        render_no_copy_table(df, caption=caption)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# =========================================================
# LOGIN
# =========================================================
def check_login() -> bool:
    st.sidebar.markdown("### 🔐 Accesso")

    if "viewer_logged" not in st.session_state:
        st.session_state.viewer_logged = False
    if "viewer_user" not in st.session_state:
        st.session_state.viewer_user = ""
    if "viewer_company_slug" not in st.session_state:
        st.session_state.viewer_company_slug = DEFAULT_COMPANY_SLUG
    if "viewer_company_name" not in st.session_state:
        st.session_state.viewer_company_name = get_company_display_name(DEFAULT_COMPANY_SLUG)

    if st.session_state.viewer_logged:
        st.sidebar.success(f"Accesso effettuato: {st.session_state.viewer_user}")
        st.sidebar.caption(f"Azienda: {get_current_company_name()}")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.viewer_logged = False
            st.session_state.viewer_user = ""
            st.session_state.viewer_company_slug = DEFAULT_COMPANY_SLUG
            st.session_state.viewer_company_name = get_company_display_name(DEFAULT_COMPANY_SLUG)
            st.rerun()
        return True

    username = st.sidebar.text_input("Utente", key="login_user")
    password = st.sidebar.text_input("Password", type="password", key="login_pass")

    if st.sidebar.button("Entra", use_container_width=True):
        try:
            users = dict(st.secrets.get("viewer_users", {}))
        except Exception:
            users = {}

        if not users:
            st.sidebar.error("File secrets.toml non configurato: manca [viewer_users].")
            return False

        if username in users and users[username] == password:
            st.session_state.viewer_logged = True
            st.session_state.viewer_user = username
            set_current_company_for_user(username)
            st.rerun()
        else:
            st.sidebar.error("Credenziali non valide")

    return False

# =========================================================
# DASHBOARD QUALIFICA
# =========================================================
def dashboard_qualifica():
    company_logo = get_company_logo_path(get_current_company_slug())
    if company_logo.exists():
        c_logo, c_title = st.columns([0.18, 0.82])
        with c_logo:
            st.image(Image.open(company_logo), use_container_width=True)
        with c_title:
            st.markdown(f"<div class='main-title'>🤝 {APP_TITLE}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='main-subtitle'>{APP_SUBTITLE}. Area riservata alla consultazione delle evidenze rese disponibili.</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='main-subtitle'>Azienda consultata: <strong>{html.escape(get_current_company_name())}</strong></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(f"<div class='main-title'>🤝 {APP_TITLE}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='main-subtitle'>{APP_SUBTITLE}. Area riservata alla consultazione delle evidenze rese disponibili.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='main-subtitle'>Azienda consultata: <strong>{html.escape(get_current_company_name())}</strong></div>",
            unsafe_allow_html=True,
        )

    st.info(
        "Il portale è in sola lettura: non consente inserimenti, modifiche o cancellazioni. "
        "Le informazioni mostrate sono limitate alle evidenze condivisibili ai fini della qualifica fornitore."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Sistema Qualità", "Attivo", "SGQ")
    with c2:
        st.metric("Documenti", count_records("REG-DOC - Registro Documenti SGQ"), "record")
    with c3:
        st.metric("Piano formazione", count_records("MOD-720-G-Piano formazione annuale"), "record")
    with c4:
        st.metric("KPI / Performance", count_records("MOD-910-H-Performance"), "record")

    st.markdown("### Stato evidenze disponibili")

    evidence_data = [
        {
            "Area": "Documentazione SGQ",
            "Stato": "Disponibile",
            "Descrizione": "Registro documenti, procedure, evidenze documentali e documenti condivisibili.",
        },
        {
            "Area": "Organizzazione",
            "Stato": "Disponibile",
            "Descrizione": "Ruoli, requisiti e matrice delle responsabilità.",
        },
        {
            "Area": "Pianificazione",
            "Stato": "Disponibile",
            "Descrizione": "Obiettivi, pianificazione e azioni di sistema condivisibili.",
        },
        {
            "Area": "Formazione",
            "Stato": "Disponibile",
            "Descrizione": "Piano formazione annuale in forma aggregata/documentale.",
        },
        {
            "Area": "Qualifica fornitori",
            "Stato": "Disponibile",
            "Descrizione": "Evidenze del processo di qualifica e monitoraggio fornitori.",
        },
        {
            "Area": "Non conformità e miglioramento",
            "Stato": "Sintesi consultabile",
            "Descrizione": "Riepilogo dei servizi non conformi, senza dettagli riservati.",
        },
        {
            "Area": "Soddisfazione clienti",
            "Stato": "Sintesi consultabile",
            "Descrizione": "Indicatori e dati consultabili in forma non riservata.",
        },
        {
            "Area": "Performance e audit",
            "Stato": "Disponibile",
            "Descrizione": "KPI del sistema qualità e monitoraggio audit interni.",
        },
    ]

    df_evidence = pd.DataFrame(evidence_data)
    render_view_table(df_evidence)

    st.markdown("### Moduli inclusi nel viewer")
    available_rows = []
    for page_label, file_key in EXTERNAL_PAGES.items():
        if file_key == "dashboard":
            continue

        if file_key == "audit_verbale_pdf":
            verbale_path = get_file_path("MOD-920-C-Verbale audit")
            available_rows.append({
                "Area": page_label,
                "File": verbale_path.name,
                "Disponibilità": "Presente" if verbale_path.exists() else "Non trovato",
                "Record": "Documento PDF",
            })
            continue

        if file_key == "risk_management":
            risk_paths = [get_current_base_path() / filename for filename in RISK_WORKBOOKS.values()]
            available_rows.append({
                "Area": page_label,
                "File": " + ".join(RISK_WORKBOOKS.values()),
                "Disponibilità": f"{sum(path.exists() for path in risk_paths)} / 2 file presenti",
                "Record": "Vedi area Risk Management",
            })
            continue

        # La sezione Audit è una vista composta: il dato principale esposto
        # all'esterno è il Piano Audit Annuale; i follow-up sono un riepilogo accessorio.
        if file_key == "audit_esterno":
            plan_key = "MOD-920-A-Piano audit annuale"
            follow_key = "MOD-920-E-Monitoraggioauditing"
            fp_plan = get_file_path(plan_key)
            fp_follow = get_file_path(follow_key)
            files_shown = FILE_MAP.get(plan_key, "")
            if fp_follow.exists():
                files_shown += " + " + FILE_MAP.get(follow_key, "")
            available_rows.append(
                {
                    "Area": page_label,
                    "File": files_shown,
                    "Disponibilità": "Presente" if fp_plan.exists() else "Non trovato",
                    "Record": count_records(plan_key) if fp_plan.exists() else 0,
                }
            )
            continue

        fp = get_file_path(file_key)
        available_rows.append(
            {
                "Area": page_label,
                "File": FILE_MAP.get(file_key, ""),
                "Disponibilità": "Presente" if fp.exists() else "Non trovato",
                "Record": count_records(file_key) if fp.exists() else 0,
            }
        )
    render_view_table(pd.DataFrame(available_rows))

# =========================================================
# VIEWER AUDIT ESTERNO - PIANO ANNUALE + FOLLOW-UP
# ---------------------------------------------------------
# La pagina Audit esterna NON apre direttamente il registro
# MOD-920-E. Compone invece una vista consultabile basata su:
# - MOD-920-A: Piano Audit Annuale, documento principale;
# - MOD-920-E: riepilogo follow-up, se presente.
# Non espone Programmi, Verbali, nominativi o dettagli NC/AC.
# =========================================================
def _audit_filter_values(df: pd.DataFrame, column: str) -> list[str]:
    """Restituisce valori filtro puliti e ordinati per una colonna presente."""
    if df is None or df.empty or column not in df.columns:
        return ["Tutti"]
    values = (
        df[column]
        .astype(str)
        .map(str.strip)
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    return ["Tutti"] + sorted(values)


def _audit_apply_text_search(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Ricerca semplice su tutti i campi della vista già depurata."""
    if df is None or df.empty or not query.strip():
        return df
    ql = query.lower().strip()
    return df[df.apply(lambda row: any(ql in str(v).lower() for v in row.values), axis=1)]


def viewer_audit_esterno():
    plan_key = "MOD-920-A-Piano audit annuale"
    follow_key = "MOD-920-E-Monitoraggioauditing"

    st.markdown("<div class='main-title'>🔍 Audit Interni</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='main-subtitle'>Consultazione del Piano Audit Annuale e dello stato generale dei follow-up condivisibili.</div>",
        unsafe_allow_html=True,
    )
    st.info(
        "La vista è resa disponibile ai fini della qualifica fornitore e riporta la pianificazione "
        "e lo stato degli audit. Il Programma Audit e il Verbale PDF sono consultabili nelle "
        "rispettive voci del menu."
    )

    plan_path = get_file_path(plan_key)
    if not plan_path.exists():
        st.warning(f"Piano Audit Annuale non disponibile: {plan_path.name}")
        st.caption(
            "Carica il file MOD-920-A-Piano_Audit_Annuale.xlsx nella cartella "
            "moduli_compilati dell'azienda associata all'utente."
        )
        return

    plan = read_excel_safe(plan_key)
    if plan is None or plan.empty:
        st.info("Il Piano Audit Annuale non contiene registrazioni consultabili.")
        return

    plan = plan[plan.astype(str).apply(lambda r: any(x.strip() for x in r), axis=1)].copy()

    follow = read_excel_safe(follow_key)
    if follow is not None and not follow.empty:
        follow = follow[follow.astype(str).apply(lambda r: any(x.strip() for x in r), axis=1)].copy()
    else:
        follow = pd.DataFrame()

    # ---------------------------
    # Indicatori sintetici
    # ---------------------------
    stato_series = (
        plan["Stato"].astype(str).str.strip().str.lower()
        if "Stato" in plan.columns
        else pd.Series([""] * len(plan))
    )
    n_audit = len(plan)
    n_chiusi = int((stato_series == "chiuso").sum())
    n_eseguiti = int(stato_series.str.contains("eseguito|chiuso", case=False, regex=True, na=False).sum())
    n_follow = len(follow) if not follow.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Audit a piano", n_audit)
    c2.metric("Audit eseguiti / chiusi", n_eseguiti)
    c3.metric("Audit chiusi", n_chiusi)
    c4.metric("Follow-up registrati", n_follow)

    # ---------------------------
    # Piano Audit Annuale
    # ---------------------------
    st.markdown("### 📅 Piano Audit Annuale")

    f1, f2, f3, f4 = st.columns([1.0, 1.15, 1.5, 1.7])
    with f1:
        anno = st.selectbox("Anno", _audit_filter_values(plan, "Anno"), key="audit_ext_anno")
    with f2:
        stato = st.selectbox("Stato", _audit_filter_values(plan, "Stato"), key="audit_ext_stato")
    with f3:
        tipologia = st.selectbox(
            "Tipologia audit",
            _audit_filter_values(plan, "Tipologia audit"),
            key="audit_ext_tipologia",
        )
    with f4:
        ricerca = st.text_input("Cerca nel piano audit", key="audit_ext_search")

    plan_view = plan.copy()
    if anno != "Tutti" and "Anno" in plan_view.columns:
        plan_view = plan_view[plan_view["Anno"].astype(str).str.strip() == anno]
    if stato != "Tutti" and "Stato" in plan_view.columns:
        plan_view = plan_view[plan_view["Stato"].astype(str).str.strip() == stato]
    if tipologia != "Tutti" and "Tipologia audit" in plan_view.columns:
        plan_view = plan_view[plan_view["Tipologia audit"].astype(str).str.strip() == tipologia]
    plan_view = _audit_apply_text_search(plan_view, ricerca)

    # Campi deliberatamente esposti al viewer esterno.
    plan_public_cols = [
        "ID Audit",
        "Anno",
        "Processo / Area",
        "Tipologia audit",
        "Periodicità",
        "Data pianificata",
        "Stato",
        "Data effettiva",
        "Esito sintetico",
    ]
    plan_public_cols = [c for c in plan_public_cols if c in plan_view.columns]
    render_view_table(
        plan_view[plan_public_cols] if plan_public_cols else plan_view,
        caption=f"Audit visualizzati: {len(plan_view)} / {len(plan)}",
    )

    # ---------------------------
    # Follow-up condivisibili
    # ---------------------------
    st.markdown("### ✅ Monitoraggio follow-up")

    if follow.empty:
        st.info("Nessun follow-up audit condivisibile presente nel registro.")
        return

    ff1, ff2, ff3 = st.columns([1.25, 1.25, 2.0])
    with ff1:
        fu_audit = st.selectbox(
            "ID Audit follow-up",
            _audit_filter_values(follow, "ID Audit"),
            key="audit_ext_fu_id",
        )
    with ff2:
        fu_stato = st.selectbox(
            "Stato follow-up",
            _audit_filter_values(follow, "Stato follow-up"),
            key="audit_ext_fu_stato",
        )
    with ff3:
        fu_ricerca = st.text_input("Cerca nei follow-up", key="audit_ext_fu_search")

    follow_view = follow.copy()
    if fu_audit != "Tutti" and "ID Audit" in follow_view.columns:
        follow_view = follow_view[follow_view["ID Audit"].astype(str).str.strip() == fu_audit]
    if fu_stato != "Tutti" and "Stato follow-up" in follow_view.columns:
        follow_view = follow_view[follow_view["Stato follow-up"].astype(str).str.strip() == fu_stato]
    follow_view = _audit_apply_text_search(follow_view, fu_ricerca)

    # Esclusi volutamente: descrizione puntuale, responsabili,
    # azioni interne, ID NC/AC ed evidenze di chiusura.
    follow_public_cols = [
        "ID Audit",
        "ID Follow-up",
        "Tipologia rilievo",
        "Data apertura",
        "Scadenza",
        "Stato follow-up",
        "Monitoraggio scadenza",
    ]
    follow_public_cols = [c for c in follow_public_cols if c in follow_view.columns]
    render_view_table(
        follow_view[follow_public_cols] if follow_public_cols else follow_view,
        caption=f"Follow-up visualizzati: {len(follow_view)} / {len(follow)}",
    )


# =========================================================
# VIEWER GENERICO SOLO LETTURA
# =========================================================
def viewer_readonly(file_key: str):
    st.markdown(f"<div class='main-title'>{file_key}</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-subtitle'>Consultazione in sola lettura.</div>", unsafe_allow_html=True)

    fp = get_file_path(file_key)
    if not fp.exists():
        st.warning(f"File non trovato: {fp}")
        st.caption("Verifica che il file sia presente nella cartella aziendale assegnata all'utente loggato.")
        return

    df = read_excel_safe(file_key)
    if df is None:
        return

    if df.empty:
        st.info("Nessun dato disponibile.")
        return

    # rimuove righe completamente vuote
    df = df[df.astype(str).apply(lambda r: any(x.strip() for x in r), axis=1)]

    st.markdown("### 🔎 Filtri e ricerca")
    c1, c2, c3 = st.columns([1.1, 1.3, 2.2])

    with c1:
        filter_col = st.selectbox(
            "Colonna filtro",
            [""] + list(df.columns),
            key=f"{file_key}_filter_col",
        )

    with c2:
        if filter_col:
            values_raw = df[filter_col].astype(str).map(str.strip).replace("", pd.NA).dropna().unique().tolist()
            values = ["Tutti"] + sorted(values_raw)
            filter_value = st.selectbox(
                "Valore",
                values,
                key=f"{file_key}_filter_value",
            )
        else:
            filter_value = "Tutti"

    with c3:
        q = st.text_input("Cerca in tutti i campi", key=f"{file_key}_search")

    df_view = df.copy()

    if filter_col and filter_value != "Tutti":
        df_view = df_view[df_view[filter_col].astype(str).map(str.strip) == str(filter_value).strip()]

    if q:
        ql = q.lower().strip()

        def match_row(row):
            return any(ql in str(v).lower() for v in row.values)

        df_view = df_view[df_view.apply(match_row, axis=1)]

    st.markdown("### 📋 Dati consultabili")
    render_view_table(df_view, caption=f"Record visualizzati: {len(df_view)} / {len(df)}")
    if ALLOW_CSV_DOWNLOAD and not df_view.empty:
        csv = df_view.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            "⬇️ Scarica CSV",
            data=csv,
            file_name=f"{file_key.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=False,
        )

    st.divider()
    st.markdown("### 📄 Scheda record")

    if df_view.empty:
        st.info("Nessun record selezionabile.")
        return

    df_sel = df_view.reset_index(drop=True)
    labels = [make_record_label(df_sel.loc[i], i) for i in range(len(df_sel))]

    selected = st.selectbox("Seleziona record", labels, key=f"{file_key}_record")
    idx = labels.index(selected)
    rec = df_sel.loc[idx].to_dict()

    with st.container(border=True):
        cols = st.columns(2)
        for n, (k, v) in enumerate(rec.items()):
            target = cols[n % 2]
            with target:
                st.markdown(f"**{k}:**")
                st.write(v)

    # download documento/PDF se il registro contiene un percorso valido
    if file_key == "REG-DOC - Registro Documenti SGQ":
        possible_path_cols = [
            c for c in df_sel.columns
            if str(c).lower().strip() in ["percorso", "path", "filepath", "file", "percorso pdf"]
        ]
        if possible_path_cols:
            if not ALLOW_DOCUMENT_DOWNLOAD:
                st.caption("Download documenti disabilitato nella versione viewer esterno protetta.")
            else:
                path_col = possible_path_cols[0]
                doc_path = Path(str(rec.get(path_col, "")).strip())
                if doc_path.exists() and doc_path.is_file():
                    try:
                        with open(doc_path, "rb") as f:
                            st.download_button(
                                "⬇️ Scarica documento selezionato",
                                data=f,
                                file_name=doc_path.name,
                                mime="application/octet-stream",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.warning(f"Documento non scaricabile: {e}")

# Area autonoma di consultazione: nessuna modifica alla lettura degli altri moduli.
RISK_WORKBOOKS = {
    "Mod.02.PO.06.1 — Risk management (P × C)": "Mod.02.PO.06.1_Risk_management.xlsx",
    "Mod.01.PO.06.1 — Valutazione rischi (RPN)": "Mod.01.PO.06.1_VR.xlsx",
}

def risk_number(value):
    return pd.to_numeric(str(value).strip().replace(",", "."), errors="coerce")

def risk_level(value, scale):
    number = risk_number(value)
    if pd.isna(number) or number <= 0:
        return ""
    if scale == "RPN":
        return "Basso" if number < 50 else "Medio" if number < 75 else "Alto"
    return "Basso" if number < 4 else "Medio" if number < 9 else "Alto"

def risk_cell_style(column, value, scale, opportunity=False):
    name = str(column).strip().lower()
    text = str(value).strip().lower()
    colors = {"basso": "#b7e1cd", "medio": "#fff2cc", "alto": "#f4c7c3"}
    color = ""
    numeric = risk_number(value)
    if name.startswith("δ"):
        if pd.notna(numeric):
            color = "#d0e8ff" if numeric > 0 else "#f2f2f2" if numeric == 0 else "#e6ccb2"
    elif name in ("valutazione", "valutazione residuo"):
        color = colors.get(text, "") if not opportunity else ""
    elif name in ("indice", "rischio residuo") or "rpn" in name or name.startswith("indice iniziale") or name.startswith("indice residuo"):
        if opportunity:
            color = "#d0e8ff" if pd.notna(numeric) and numeric > 0 else ""
        else:
            color = colors.get(risk_level(value, scale).lower(), "")
    elif scale == "P×C" and name in ("probabilità", "conseguenza", "prob.", "cons."):
        if pd.notna(numeric):
            color = "#b7e1cd" if numeric == 1 else "#fff2cc" if numeric in (2, 3) else "#f4c7c3" if numeric == 4 else ""
    elif name == "check":
        if text in ("ok", "gestito", "completato"):
            color = "#b7e1cd"
        elif text in ("attesa", "in programma", "in corso"):
            color = "#fff2cc"
        elif text in ("non gestito", "critico"):
            color = "#f4c7c3"
    return f"background-color:{color};color:#111;" if color else ""

def render_risk_table(df, scale, caption="", colorize=True):
    """Tabella HTML protetta con gli stessi colori della Suite, limitata all'area rischi."""
    if df.empty:
        st.info("Nessun dato da visualizzare.")
        return
    shown = df.head(MAX_STATIC_TABLE_ROWS) if MAX_STATIC_TABLE_ROWS else df
    header = "".join(f"<th>{html.escape(str(c))}</th>" for c in shown.columns)
    rows = []
    for _, row in shown.iterrows():
        cells = []
        opportunity = str(row.get("Tipo", row.get("R/O", ""))).strip().upper() == "O"
        for col, value in row.items():
            text = "" if pd.isna(value) else str(value)
            css = risk_cell_style(col, value, scale, opportunity) if colorize else ""
            cells.append(f'<td style="{html.escape(css, quote=True)}">{html.escape(text)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(
        '<div class="sgq-table-wrap" oncontextmenu="return false;" oncopy="return false;" oncut="return false;" onselectstart="return false;">'
        f'<table class="sgq-static-table"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )
    if len(shown) < len(df):
        caption += f" — Prime {len(shown)} righe su {len(df)}; restringere la ricerca."
    if caption:
        st.caption(caption)

def load_risk_sheet(path, sheet, header=None):
    """Legge anche i valori delle celle unite; conserva tutti i dati del foglio."""
    from openpyxl import load_workbook
    book = load_workbook(path, data_only=True)
    try:
        ws = book[sheet]
        values = [[cell.value for cell in row] for row in ws.iter_rows()]
        for merged in ws.merged_cells.ranges:
            value = ws.cell(merged.min_row, merged.min_col).value
            for r in range(merged.min_row, merged.max_row + 1):
                for c in range(merged.min_col, merged.max_col + 1):
                    if header is None or c == merged.min_col:
                        values[r - 1][c - 1] = value
        if header is None:
            # Vista integrale: nessuna riga o colonna non vuota viene esclusa.
            df = pd.DataFrame(values)
            from openpyxl.utils import get_column_letter
            df.columns = [get_column_letter(i + 1) for i in range(len(df.columns))]
            df.insert(0, "Riga Excel", range(1, len(df) + 1))
        else:
            names, counts = [], {}
            for i, value in enumerate(values[header]):
                name = str(value).strip() if value is not None else f"Colonna {i + 1}"
                counts[name] = counts.get(name, 0) + 1
                names.append(name if counts[name] == 1 else f"{name}.{counts[name] - 1}")
            df = pd.DataFrame(values[header + 1:], columns=names)
        return hide_sensitive_columns(normalize_df(df), "risk_management")
    finally:
        book.close()

def load_risk_analysis(path, scale):
    if scale == "P×C":
        sheet, header = "RISK MANAGEMENT", 16
    else:
        sheet, header = "Mod.02.PO.06.1_Risk management", 22
    df = load_risk_sheet(path, sheet, header)
    required = ["RISCHIO/OPPORTUNITA'", "ID VR", "R/O"]
    if not set(required).issubset(df.columns):
        raise ValueError(f"Intestazioni non riconosciute nel foglio {sheet}; usare la vista Fogli del modulo.")
    types = df["R/O"].astype(str).str.strip().str.upper()
    if scale == "RPN":
        # Nel modello VR le righe opportunità possono avere ID e tipo vuoti:
        # sono il blocco dopo gli ultimi rischi, prima della riga vuota e delle note.
        names = df["RISCHIO/OPPORTUNITA'"].astype(str).str.strip()
        risk_rows = df.index[types.eq("R")]
        opportunities = pd.Series(False, index=df.index)
        if len(risk_rows):
            last_risk = max(risk_rows)
            blank_rows = df.index[(df.index > last_risk) & names.eq("")]
            end = min(blank_rows) if len(blank_rows) else last_risk
            opportunities = (df.index > last_risk) & (df.index < end) & types.eq("") & df["ID VR"].astype(str).str.strip().eq("") & names.ne("")
        types = types.mask(opportunities, "O")
    df["R/O"] = types
    df = df[types.isin(["R", "O"])].copy()
    # Mantiene tutte le colonne sorgente e aggiunge solo campi di visualizzazione.
    df["ID"] = df["ID VR"]
    df["Descrizione rischio"] = df["RISCHIO/OPPORTUNITA'"]
    df["Tipo"] = df["R/O"].astype(str).str.strip().str.upper()
    df["Scala indice"] = "P × C" if scale == "P×C" else "RPN"
    if scale == "RPN":
        df.loc[df["Tipo"].eq("O"), "Scala indice"] = "P × beneficio (opportunità)"
    if scale == "P×C":
        for source, target in (("PROB.", "Probabilità"), ("CONS.", "Conseguenza"), ("INDICE", "Indice")):
            df[target] = df[source].map(risk_number) if source in df else float("nan")
        valid = df["Probabilità"].isin([1, 2, 3, 4]) & df["Conseguenza"].isin([1, 2, 3, 4])
        df.loc[valid, "Indice"] = df.loc[valid, "Probabilità"] * df.loc[valid, "Conseguenza"]
    else:
        for source, target in (("INDICE INIZIALE / POTENZIALE", "Indice"), ("INDICE RESIDUO / REALIZZATO", "Rischio residuo")):
            df[target] = df[source].map(risk_number) if source in df else float("nan")
    df["Valutazione"] = df["Indice"].map(lambda value: risk_level(value, scale))
    df.loc[df["Tipo"].eq("O"), "Valutazione"] = "Opportunità"
    if "Rischio residuo" in df:
        df["Valutazione residuo"] = df["Rischio residuo"].map(lambda value: risk_level(value, scale))
        df["Δ (Indice - Residuo)"] = df["Indice"] - df["Rischio residuo"]
        df.loc[df["Tipo"].eq("O"), ["Valutazione residuo", "Δ (Indice - Residuo)"]] = ["", float("nan")]
    df = df.rename(columns={"RESPONSABILE": "Responsabile", "TRATTAMENTO": "Trattamento", "AZIONE": "Azione", "CHECK": "Check"})
    return df

def filter_risk_analysis(df, key):
    fields = ["Tipo", "Valutazione", "Responsabile", "Check"]
    with st.expander("Filtri e ricerca", expanded=True):
        for col in fields:
            if col in df:
                values = sorted({str(v).strip() for v in df[col] if str(v).strip()})
                selected = st.multiselect(col, values, key=f"{key}_filter_{col}")
                if selected:
                    df = df[df[col].astype(str).str.strip().isin(selected)]
        query = st.text_input("Cerca in tutti i campi", key=f"{key}_query")
        if query.strip():
            df = df[df.astype(str).apply(lambda row: row.str.contains(query.strip(), case=False, regex=False)).any(axis=1)]
    return df

def render_risk_analysis(df, scale, key):
    df = filter_risk_analysis(df, key)
    risks = df[df["Tipo"].eq("R")]
    counts = st.columns(4)
    counts[0].metric("Rischi", len(risks))
    for col, level in zip(counts[1:], ("Alto", "Medio", "Basso")):
        col.metric(level, int(risks["Valutazione"].eq(level).sum()))
    missing = int(risks["Valutazione"].eq("").sum())
    st.caption(f"Opportunità: {int(df['Tipo'].eq('O').sum())}. Rischi senza valutazione: {missing}.")
    if scale == "P×C":
        st.caption("Scala P × C: verde 1–3 · giallo 4–8 · rosso ≥9. Probabilità/conseguenza: 1 verde, 2–3 giallo, 4 rosso.")
        valid = risks[risks["Probabilità"].isin([1, 2, 3, 4]) & risks["Conseguenza"].isin([1, 2, 3, 4])]
        if not valid.empty:
            st.markdown("### Matrice Probabilità × Conseguenza — numero di rischi")
            matrix = pd.crosstab(valid["Probabilità"], valid["Conseguenza"]).reindex(index=[1, 2, 3, 4], columns=[1, 2, 3, 4], fill_value=0)
            matrix.index.name = "Probabilità"
            render_risk_table(matrix.reset_index(), scale, colorize=False)
        st.caption("Questo modulo non contiene il rischio residuo. Il confronto iniziale/residuo si trova nel modulo VR, con scala RPN.")
    else:
        st.caption("Scala RPN P × G × R (fattori 1–10): verde <50 · giallo 50–74 · rosso ≥75. I valori RPN restano distinti dall'indice P × C.")
        st.markdown("### Prima e dopo il trattamento")
        comparison = ["ID", "Descrizione rischio", "Indice", "Valutazione", "Rischio residuo", "Valutazione residuo", "Δ (Indice - Residuo)", "Responsabile"]
        render_risk_table(risks[comparison], scale)
        st.caption("Variazione: celeste = miglioramento · grigio = invariato · marrone = peggioramento. Dati mancanti: nessun confronto calcolato.")
    st.markdown("### Rischi con indice più alto")
    preferred = ["ID", "Descrizione rischio", "Tipo", "Scala indice", "Probabilità", "Conseguenza", "Indice", "Valutazione", "Rischio residuo", "Valutazione residuo", "Trattamento", "Azione", "Responsabile", "Check"]
    columns = [c for c in preferred if c in df]
    top = risks[risks["Indice"].notna()].sort_values("Indice", ascending=False).head(10)
    render_risk_table(top[columns], scale)
    st.markdown("### Registro rischi e opportunità")
    render_risk_table(df[columns], scale, caption=f"Record filtrati: {len(df)}")
    if df.empty:
        return
    selected = st.selectbox("Scheda record", range(len(df)), format_func=lambda i: f"{df.iloc[i]['ID']} — {df.iloc[i]['Descrizione rischio']}", key=f"{key}_record")
    record = df.iloc[selected]
    # Tutti i campi sorgente inclusi nella scheda; celle colorate come nelle tabelle.
    st.markdown("### Dettaglio del record")
    render_risk_table(pd.DataFrame([record]), scale)

def viewer_risk_management():
    st.markdown("## ⚠️ Risk Management")
    st.caption(f"Azienda: {get_current_company_name()} · Consultazione in sola lettura")
    available = {label: get_current_base_path() / filename for label, filename in RISK_WORKBOOKS.items()}
    for label, path in available.items():
        if not path.exists():
            st.info(f"{label}: modulo non disponibile per l'azienda corrente.")
    present = [label for label, path in available.items() if path.exists()]
    if not present:
        return
    selected = st.selectbox("Modulo rischi", present, key="risk_management_workbook")
    path = available[selected]
    scale = "RPN" if path.name == "Mod.01.PO.06.1_VR.xlsx" else "P×C"
    mode = st.radio("Visualizzazione", ["Analisi rischi", "Fogli del modulo"], horizontal=True, key="risk_management_mode")
    key = f"risk_{get_current_company_slug()}_{scale}"
    try:
        if mode == "Analisi rischi":
            df = load_risk_analysis(path, scale)
            render_risk_analysis(df, scale, key)
        else:
            with pd.ExcelFile(path) as book:
                sheets = book.sheet_names
            sheet = st.selectbox("Foglio", sheets, key=f"{key}_sheet")
            raw_mode = st.checkbox("Mostra tutte le righe del foglio, comprese intestazioni e note", value=True, key=f"{key}_{sheet}_raw")
            layouts = {"RISK MANAGEMENT": 16, "MOD_02_PO_03_VAL RISCHI": 3,
                       "Mod.02.PO.06.1_Risk management": 22}
            header = None if raw_mode or sheet not in layouts else layouts[sheet]
            df = load_risk_sheet(path, sheet, header)
            query = st.text_input("Cerca nel foglio", key=f"{key}_{sheet}_search")
            if query.strip():
                df = df[df.astype(str).apply(lambda row: row.str.contains(query.strip(), case=False, regex=False)).any(axis=1)]
            render_risk_table(df, scale, caption=f"Foglio {sheet} — {len(df)} righe", colorize=header is not None)
            if raw_mode:
                st.caption("I valori delle celle unite sono ripetuti per facilitarne la lettura. I colori e i riepiloghi sono disponibili nella vista Analisi rischi; per le tabelle strutturate disattivare la vista integrale.")
    except Exception as exc:
        st.error(f"Impossibile leggere il modulo rischi: {exc}")



def render_verbale_page(path, page_number, dpi=150):
    """Renderizza una pagina del PDF in memoria, senza modificare il documento."""
    import pymupdf
    with pymupdf.open(str(path)) as document:
        return document[page_number].get_pixmap(dpi=dpi, alpha=False).tobytes("png")

def viewer_verbale_audit_pdf():
    st.markdown("## MOD-920-C — Verbale Audit")
    st.caption(f"Azienda: {get_current_company_name()} · Consultazione del documento PDF")
    path = get_file_path("MOD-920-C-Verbale audit")
    if not path.exists():
        st.info(f"Verbale non disponibile per l'azienda corrente: {path.name}")
        return
    try:
        import pymupdf
    except ImportError:
        st.error("Visualizzazione PDF non disponibile: aggiungere PyMuPDF al requirements.txt e riavviare l'app.")
        return
    try:
        with pymupdf.open(str(path)) as document:
            if document.needs_pass:
                st.warning("Il PDF è protetto da password e non può essere visualizzato.")
                return
            pages = document.page_count
        if pages == 0:
            st.info("Il PDF non contiene pagine visualizzabili.")
            return
        key = f"audit_pdf_{get_current_company_slug()}"
        page = st.selectbox("Pagina", list(range(pages)), format_func=lambda index: f"Pagina {index + 1} di {pages}", key=f"{key}_page")
        dpi = st.selectbox("Definizione", [150, 200, 100], format_func=lambda value: {100: "Standard", 150: "Alta", 200: "Molto alta"}[value], key=f"{key}_dpi")
        st.image(render_verbale_page(path, page, dpi), use_container_width=True)
        st.caption(f"{path.name} — pagina {page + 1} di {pages}")
        if ALLOW_DOCUMENT_DOWNLOAD:
            st.download_button("Scarica verbale PDF", data=path.read_bytes(), file_name=path.name, mime="application/pdf", key=f"{key}_download")
    except Exception as exc:
        st.error(f"Impossibile visualizzare il verbale PDF: {exc}")


# =========================================================
# APP
# =========================================================
def main():
    with st.sidebar:
        sidebar_logo()
        st.markdown(f"### {APP_TITLE}")
        st.caption(APP_SUBTITLE)

    if not check_login():
        render_login_home()
        st.stop()

    with st.sidebar:
        st.markdown("---")
        st.caption(f"Azienda corrente: {get_current_company_name()}")
        st.markdown("### Navigazione")
        selected_label = st.radio(
            "Seleziona area",
            list(EXTERNAL_PAGES.keys()),
            label_visibility="collapsed",
        )
        selected_page = EXTERNAL_PAGES[selected_label]

        st.markdown("---")
        st.caption("Versione viewer esterno - sola lettura")
        st.caption(f"Aggiornamento pagina: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    if selected_page == "dashboard":
        dashboard_qualifica()
    elif selected_page == "audit_esterno":
        viewer_audit_esterno()
    elif selected_page == "audit_verbale_pdf":
        viewer_verbale_audit_pdf()
    elif selected_page == "risk_management":
        viewer_risk_management()
    else:
        viewer_readonly(selected_page)


if __name__ == "__main__":
    main()
