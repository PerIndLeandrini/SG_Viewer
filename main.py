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
BASE_PATH = BASE_DIR / "moduli_compilati"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

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
# LOGO SIDEBAR
# =========================================================
def sidebar_logo():
    try:
        if LOGO_PATH.exists():
            img = Image.open(LOGO_PATH)
            st.image(img, use_container_width=True)
        else:
            st.caption("Logo non disponibile")
    except Exception as e:
        st.caption(f"Logo non caricabile: {e}")

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
    "🔍 Audit Interni": "MOD-920-E-Monitoraggioauditing",
}

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
    "MOD-920-E-Monitoraggioauditing": [
        "Auditor", "Note interne", "Dettaglio NC", "Evidenza riservata",
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
def get_file_path(file_key: str) -> Path:
    fname = FILE_MAP.get(file_key)
    if not fname:
        raise ValueError(f"Modulo non mappato: {file_key}")
    return BASE_PATH / fname


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

    if st.session_state.viewer_logged:
        st.sidebar.success(f"Accesso effettuato: {st.session_state.viewer_user}")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.viewer_logged = False
            st.session_state.viewer_user = ""
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
            st.rerun()
        else:
            st.sidebar.error("Credenziali non valide")

    return False

# =========================================================
# DASHBOARD QUALIFICA
# =========================================================
def dashboard_qualifica():
    st.markdown(f"<div class='main-title'>🤝 {APP_TITLE}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='main-subtitle'>{APP_SUBTITLE}. Area riservata alla consultazione delle evidenze rese disponibili.</div>",
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
# VIEWER GENERICO SOLO LETTURA
# =========================================================
def viewer_readonly(file_key: str):
    st.markdown(f"<div class='main-title'>{file_key}</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-subtitle'>Consultazione in sola lettura.</div>", unsafe_allow_html=True)

    fp = get_file_path(file_key)
    if not fp.exists():
        st.warning(f"File non trovato: {fp}")
        st.caption("Verifica che il file sia presente nella cartella 'moduli_compilati'.")
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

# =========================================================
# APP
# =========================================================
def main():
    with st.sidebar:
        sidebar_logo()
        st.markdown(f"### {APP_TITLE}")
        st.caption(APP_SUBTITLE)

    if not check_login():
        st.info("Inserire le credenziali per accedere al viewer documentale.")
        st.stop()

    with st.sidebar:
        st.markdown("---")
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
    else:
        viewer_readonly(selected_page)


if __name__ == "__main__":
    main()
