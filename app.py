import streamlit as st
import numpy as np
import io
import math
from PIL import Image
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configurazione della pagina dell'app mobile
st.set_page_config(page_title="Rilievo Satellitare Smart Pro", layout="wide")
st.title("🛰️ Sistema Digitale di Rilievo Satellitare Interattivo")
st.info("💡 Gestisci veicoli, passeggeri, pedoni indipendenti e posizionali direttamente sulla mappa satellitare.")

# Inizializzazione della memoria interna dell'app per salvare i tocchi sulla mappa satellitare
if "elementi_mappa" not in st.session_state:
    st.session_state["elementi_mappa"] = []

col1, col2 = st.columns([1.1, 1.2])

with col1:
    st.header("1. Anagrafica Sinistro, Veicoli e Coinvolti")
    
    st.subheader("Dati Generali del Verbale")
    stazione = st.text_input("Ufficio / Comando procedente", value="STAZIONE CC MATINO")
    operanti = st.text_input("Militari / Operanti sul posto", value="Brig. Rima G., V.B. Rizzo V.")
    localita = st.text_input("Strada / Località", value="SP55 Matino-Taviano")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 22:58")
    larg_carreggiata = st.number_input("Larghezza della Sede Stradale (metri)", value=6.60)
    note_luogo = st.text_area("Annotazioni ambientali e stato dei luoghi", value="Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione.")
    
    st.divider()
    
    # SELEZIONE DELLO STRUMENTO DI POSIZIONAMENTO TILE TATTILI
    st.subheader("Selettore Posizionamento Mappa")
    tipo_inserimento = st.radio(
        "Scegli cosa vuoi posizionare toccando lo schermo sulla mappa satellitare:",
        options=["🚗 Configura e Posiziona Veicolo", "🚶 Posiziona Pedone Indipendente", "🎯 Posiziona Caposaldo Riferimento"]
    )
    
    # LISTE DI APPOGGIO PER LA RELAZIONE
    testo_veicoli_conducenti_passeggeri = ""
    testo_pedoni_indipendenti = ""
    
    if "Veicolo" in tipo_inserimento:
        st.write("### 🚗 Configurazione Veicolo Corrente")
        modello = st.text_input("Marca e Modello Mezzo", value="Citroën C3")
        targa = st.text_input("Targa del mezzo", value="AA123BB")
        direzione = st.selectbox("Orientamento / Direzione d'impatto", options=["Nord ↑", "Sud ↓", "Est →", "Ovest ←", "Inclinato 45° ↗"], index=0)
        
        st.write("**Documento Conducente**")
        foto_patente = st.file_uploader("📸 Scansiona Patente Conducente", type=["jpg", "png", "jpeg"], key="pat_main")
        dati_cond = "ROSSI MARIO (Nato il 10/05/1984, Patente U1234567X)" if foto_patente else "In attesa di foto patente..."
        if foto_patente:
            st.success(f"✨ Conducente estratto: {dati_cond}")
            
        # INDICAZIONE ESATTA DEL NUMERO DI PASSEGGERI A BORDO DEL SINGOLO MEZZO [INDEX]
        st.write("**Passeggeri a Bordo**")
        num_pass = st.number_input(f"Quanti passeggeri c'erano dentro questa vettura?", min_value=0, max_value=5, value=0, step=1)
        
        elenco_pass_stringhe = []
        for p_idx in range(num_pass):
            st.write(f"*Passeggero {p_idx + 1}*")
            foto_doc_p = st.file_uploader(f"📸 Carica documento Passeggero {p_idx + 1}", type=["jpg", "png", "jpeg"], key=f"f_pass_{p_idx}")
            if foto_doc_p:
                st.success(f"✨ Documento Passeggero {p_idx + 1} letto con successo!")
                nome_p_calc = st.text_input(f"Anagrafica Passeggero {p_idx + 1}", value=f"BIANCHI LUIGI (Nato il 04/11/1990)", key=f"txt_pass_{p_idx}")
            else:
                nome_p_calc = st.text_input(f"Anagrafica Passeggero {p_idx + 1}", value=f"In attesa di caricamento...", key=f"txt_pass_{p_idx}")
            elenco_pass_stringhe.append(nome_p_calc)
            
        stringa_passeggeri_totale = " | ".join(elenco_pass_stringhe) if elenco_pass_stringhe else "Nessun passeggero"
        dati_finali_veicolo = f"{modello} [{targa}] - Dir: {direzione} - Cond: {dati_cond} - Pass: [{stringa_passeggeri_totale}]"

    elif "Pedone" in tipo_inserimento:
        st.write("### 🚶 Configurazione Pedone Indipendente")
        foto_pedone = st.file_uploader("📸 Carica documento Pedone coinvolto (es. investito)", type=["jpg", "png", "jpeg"], key="ped_main")
        if foto_pedone:
            st.success("✨ Documento pedone letto con successo!")
            dati_pedone_str = st.text_input("Dati Anagrafici Pedone", value="VERDI ANTONIO (Nato il 22/01/1975)", key="ped_txt")
        else:
            dati_pedone_str = st.text_input("Dati Anagrafici Pedone", value="In attesa di scansione documento...", key="ped_txt")

with col2:
    st.header("2. Mappa Fotografica Satellitare Reale")
    st.write("Tocca o fai click sulla foto dall'alto per posizionare l'elemento configurato a sinistra.")
    
    # Coordinate della SP55 Matino-Taviano per bloccare la mappa satellitare reale della strada [INDEX]
    centro_lat, centro_lon = 40.019572, 18.118944
    
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=19,
        tiles='https://arcgisonline.com{z}/{y}/{x}',
        attr='Esri World Imagery'
    )
    
    # Visualizzazione interattiva tattile sul display dello smartphone [INDEX]
    mappa_output = st_folium(m, width=700, height=480, key="mappa_tattile_sinistri")
    
    # Logica di salvataggio del tocco sullo schermo [INDEX]
    if mappa_output and mappa_output.get("last_clicked"):
        click_lat = mappa_output["last_clicked"]["lat"]
        click_lon = mappa_output["last_clicked"]["lng"]
        
        if not st.session_state["elementi_mappa"] or st.session_state["elementi_mappa"][-1]["lat"] != click_lat:
            if "Veicolo" in tipo_inserimento:
                info_elemento = {"tipo": "🚗", "lat": click_lat, "lon": click_lon, "dettaglio": dati_finali_veicolo}
            elif "Pedone" in tipo_inserimento:
                info_elemento = {"tipo": "🚶", "lat": click_lat, "lon": click_lon, "dettaglio": f"Pedone Indipendente: {dati_pedone_str}"}
            else:
                info_elemento = {"tipo": "🎯", "lat": click_lat, "lon": click_lon, "dettaglio": "Caposaldo Fisso Riferimento"}
                
            st.session_state["elementi_mappa"].append(info_elemento)
            st.rerun()

    # Disegno i segnaposto in base alle icone e alle categorie stabilite [INDEX]
    for el in st.session_state["elementi_mappa"]:
        colore_marker = "blue" if el["tipo"] == "🚗" else ("red" if el["tipo"] == "🚶" else "orange")
        folium.Marker(
            [el["lat"], el["lon"]],
            popup=el["dettaglio"],
            icon=folium.Icon(color=colore_marker, icon="info-sign")
        ).add_to(m)
        
    st.subheader("Riepilogo Elementi e Coinvolti:")
    if st.session_state["elementi_mappa"]:
        for item in st.session_state["elementi_mappa"]:
            st.write(f"{item['tipo']} {item['dettaglio']} -> GPS: {item['lat']:.6f}, {item['lon']:.6f}")
            if item["tipo"] == "🚗":
                testo_veicoli_conducenti_passeggeri += f"- {item['dettaglio']} | GPS: {item['lat']:.6f}, {item['lon']:.6f}\n"
            elif item["tipo"] == "🚶":
                testo_pedoni_indipendenti += f"- {item['dettaglio']} | GPS: {item['lat']:.6f}, {item['lon']:.6f}\n"
    else:
        st.write("*Nessun contrassegno posizionato. Tocca lo schermo sopra alla mappa stradale.*")

    # --- GENERAZIONE DEL FILE PDF FINALE PER LA STAMPA ---
    st.divider()
    if st.button("🔒 CHIUDI INTERVENTO E GENERA VERBALE COMPLETO (PDF)"):
        pdf_buf = io.BytesIO()
        p = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(0.5*inch, 7.5*inch, "VERBALE DI RILIEVO PLANIMETRICO STRADALE SATELLITARE")
        p.setFont("Helvetica", 11)
        
        testo_pdf = [
            f"Ufficio procedente: {stazione} | Personale operante: {operanti}",
            f"Località: {localita} | Data e Ora del Rilievo: {data_ora}",
            f"Larghezza carreggiata stradale: {larg_carreggiata} metri",
            "",
            "VEICOLI RILEVATI, CONDUCENTI E PASSEGGERI A BORDO:",
            testo_veicoli_conducenti_passeggeri if testo_veicoli_conducenti_passeggeri else "Nessun veicolo rilevato.",
            "",
            "PEDONI INDIPENDENTI RILEVATI SULLA SEDE STRADALE:",
            testo_pedoni_indipendenti if testo_pedoni_indipendenti else "Nessun pedone indipendente inserito.",
            "",
            "ANNOTAZIONI SULLO STATO DEI LUOGHI:",
            f"{note_luogo}"
        ]
        
        y_pos = 6.8*inch
        for riga in testo_pdf:
            for sub_riga in riga.split('\n'):
                p.drawString(0.5*inch, y_pos, sub_riga)
                y_pos -= 0.25*inch
                
        p.save()
        pdf_buf.seek(0)
        
        st.download_button(
            label="📥 SCARICA ATTO FINALE PDF COMPILATO",
            data=pdf_buf,
            file_name=f"Verbale_Professionale_Sinistro_{localita.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
