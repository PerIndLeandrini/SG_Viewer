import os
from datetime import date

import pandas as pd
import streamlit as st

from .common import get_file_path, append_to_excel, iso_date, BASE_PATH
from .document_view import (
    doc_header, doc_section, doc_field,
    make_pdf, pdf_title, pdf_kv
)

def render_mod_1020_a():
    st.subheader("Compilazione: MOD-1020-A - Apertura Non Conformità")

    file_key = "MOD-1020-A-Apertura Non Conformità"
    file_path = get_file_path(file_key)

    tab = st.tabs(["📝 Editor", "👀 Documento (viewer)", "📄 Export PDF"])

    # ---------------------------------------------------------
    # TAB 1 - EDITOR
    # ---------------------------------------------------------
    with tab[0]:
        st.markdown("### 📥 Nuova NC")

        data_nc = st.date_input("Data rilevamento", value=date.today())
        rilevatore = st.selectbox("Rilevata da", ["Operatore", "Controllo Qualità", "Responsabile", "Cliente", "Audit Interno", "Audit Cliente", "Altro"])
        reparto = st.text_input("Reparto / Area coinvolta")

        categoria = st.radio("Categoria della Non Conformità", ["Prodotto", "Processo", "Fornitore", "Cliente"])
        descrizione = st.text_area("Descrizione sintetica della non conformità")

        ordine = st.text_input("Ordine di produzione / fornitura / cliente")
        lotto = st.text_input("Numero di lotto (se presente)")
        codice_prodotto = st.text_input("Codice prodotto")

        gravita = st.selectbox("Gravità / Priorità", ["Alta", "Media", "Bassa"])
        azione_contenitiva = st.text_area("Azione contenitiva immediata")

        file = st.file_uploader("Carica un file (immagine o PDF)", type=["png", "jpg", "jpeg", "pdf"])

        if st.button("✅ Salva Non Conformità", use_container_width=True):
            oggi = date.today()
            progressivo = 1
            if os.path.exists(file_path):
                df_exist = pd.read_excel(file_path)
                progressivo = len(df_exist) + 1

            id_nc = f"NC{progressivo:02d}_{oggi.day:02d}_{oggi.month:02d}_{oggi.year}"

            new_row = pd.DataFrame([{
                "ID NC": id_nc,
                "Data rilevamento": iso_date(data_nc),
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
                st.info(f"📎 Allegato salvato: {file.name}")

        st.divider()
        st.markdown("### 📝 Aggiorna NC esistente (stato/chiusura)")

        if not os.path.exists(file_path):
            st.info("Nessuna NC presente.")
        else:
            df = pd.read_excel(file_path).fillna("")
            ids = df["ID NC"].tolist()
            selected_id = st.selectbox("Seleziona ID NC", ids)

            row_idx = df.index[df["ID NC"] == selected_id][0]
            selected_nc = df.loc[row_idx].fillna("")

            resp = st.text_input("Responsabile azione correttiva", value=selected_nc.get("Responsabile azione correttiva", ""))
            sint = st.text_area("Sintesi azione correttiva", value=selected_nc.get("Sintesi azione correttiva", ""))

            ver = st.selectbox("Verifica efficacia", ["", "Sì", "No"], index=0)
            stato = st.selectbox("Stato", ["Aperta", "In Analisi", "Chiusa"],
                                 index=["Aperta", "In Analisi", "Chiusa"].index(selected_nc.get("Stato","Aperta")))

            if st.button("💾 Salva aggiornamenti", use_container_width=True):
                df.at[row_idx, "Responsabile azione correttiva"] = resp
                df.at[row_idx, "Sintesi azione correttiva"] = sint
                df.at[row_idx, "Verifica efficacia"] = ver
                df.at[row_idx, "Stato"] = stato
                df.to_excel(file_path, index=False)
                st.success("Aggiornamento salvato.")

    # ---------------------------------------------------------
    # TAB 2 - VIEWER "DOCUMENTO"
    # ---------------------------------------------------------
    with tab[1]:
        doc_header("Documento NC (viewer)", "Vista leggibile come documento: Streamlit diventa anche ‘lettore’ del SGQ.")

        if not os.path.exists(file_path):
            st.info("Nessuna NC presente.")
        else:
            df = pd.read_excel(file_path).fillna("")
            ids = df["ID NC"].tolist()
            selected_id = st.selectbox("Seleziona ID NC", ids, key="viewer_nc_id")

            rec = df[df["ID NC"] == selected_id].iloc[0].to_dict()

            doc_section("Identificazione", "🧾")
            doc_field("ID NC", rec.get("ID NC",""))
            doc_field("Data rilevamento", rec.get("Data rilevamento",""))
            doc_field("Rilevata da", rec.get("Rilevata da",""))
            doc_field("Reparto / Area", rec.get("Reparto",""))

            doc_section("Classificazione", "🏷️")
            doc_field("Categoria", rec.get("Categoria",""))
            doc_field("Gravità", rec.get("Gravità",""))
            doc_field("Stato", rec.get("Stato",""))

            doc_section("Descrizione e riferimenti", "📝")
            doc_field("Descrizione", rec.get("Descrizione",""))
            doc_field("Ordine", rec.get("Ordine",""))
            doc_field("Lotto", rec.get("Lotto",""))
            doc_field("Codice prodotto", rec.get("Codice prodotto",""))

            doc_section("Contenimento / gestione", "🧯")
            doc_field("Azione contenitiva", rec.get("Azione contenitiva",""))
            doc_field("Responsabile azione correttiva", rec.get("Responsabile azione correttiva",""))
            doc_field("Sintesi azione correttiva", rec.get("Sintesi azione correttiva",""))
            doc_field("Verifica efficacia", rec.get("Verifica efficacia",""))

            # Allegato: se esiste lo mostriamo in download
            allegato = str(rec.get("Nome file allegato","")).strip()
            if allegato:
                allegati_dir = os.path.join(BASE_PATH, "allegati_nc")
                allegato_path = os.path.join(allegati_dir, allegato)
                if os.path.exists(allegato_path):
                    with open(allegato_path, "rb") as f:
                        st.download_button("⬇️ Scarica allegato", data=f, file_name=allegato, use_container_width=True)
                else:
                    st.warning("Allegato indicato ma file non trovato in moduli_compilati/allegati_nc.")

    # ---------------------------------------------------------
    # TAB 3 - PDF EXPORT
    # ---------------------------------------------------------
    with tab[2]:
        st.markdown("### 📄 Export PDF (documento della NC)")

        if not os.path.exists(file_path):
            st.info("Nessuna NC presente.")
        else:
            df = pd.read_excel(file_path).fillna("")
            ids = df["ID NC"].tolist()
            selected_id = st.selectbox("Seleziona ID NC", ids, key="pdf_nc_id")

            row = df[df["ID NC"] == selected_id].iloc[0].to_dict()

            if st.button("📄 Genera PDF", use_container_width=True):
                pdf = make_pdf(module_seq="1020-A", module_name="Apertura Non Conformità")
                pdf_title(pdf, f"Report Non Conformità - {selected_id}")

                pdf_kv(pdf, "ID NC", row.get("ID NC",""))
                pdf_kv(pdf, "Data rilevamento", row.get("Data rilevamento",""))
                pdf_kv(pdf, "Rilevata da", row.get("Rilevata da",""))
                pdf_kv(pdf, "Reparto", row.get("Reparto",""), gap_after=True)

                pdf_kv(pdf, "Categoria", row.get("Categoria",""))
                pdf_kv(pdf, "Gravità", row.get("Gravità",""))
                pdf_kv(pdf, "Stato", row.get("Stato",""), gap_after=True)

                pdf_kv(pdf, "Descrizione", row.get("Descrizione",""), gap_after=True)

                pdf_kv(pdf, "Ordine", row.get("Ordine",""))
                pdf_kv(pdf, "Lotto", row.get("Lotto",""))
                pdf_kv(pdf, "Codice prodotto", row.get("Codice prodotto",""), gap_after=True)

                pdf_kv(pdf, "Azione contenitiva", row.get("Azione contenitiva",""), gap_after=True)

                pdf_kv(pdf, "Responsabile azione correttiva", row.get("Responsabile azione correttiva",""), gap_after=True)
                pdf_kv(pdf, "Sintesi azione correttiva", row.get("Sintesi azione correttiva",""), gap_after=True)
                pdf_kv(pdf, "Verifica efficacia", row.get("Verifica efficacia",""), gap_after=True)

                pdf_file = os.path.join(BASE_PATH, f"NC_{selected_id}.pdf")
                pdf.output(pdf_file)

                with open(pdf_file, "rb") as f:
                    st.download_button("⬇️ Scarica PDF", data=f, file_name=os.path.basename(pdf_file),
                                       mime="application/pdf", use_container_width=True)
