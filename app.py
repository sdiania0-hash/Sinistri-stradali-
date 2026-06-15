import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configurazione iniziale dell'applicazione avanzata
st.set_page_config(page_title="Rilievo Satellitare GPS Pro Editor", layout="wide")
st.title("🛰️ Software di Rilievo Planimetrico GPS con Editor Interattivo")
st.info("💡 Acquisisci le posizioni, sposta i veicoli a mano sul grafico e scansiona le patenti per compilare il verbale.")

# Inizializzazione dello stato della sessione per memorizzare le posizioni spostate a mano
if "posizioni_manuali" not in st.session_state:
    st.session_state["posizioni_manuali"] = {}

col1, col2 = st.columns([1, 1.3])

with col1:
    st.header("1. Acquisizione e Input Dati")
    
    st.subheader("Intestazione Verbale")
    stazione = st.text_input("Stazione / Comando / Ufficio", value="STAZIONE CC MATINO")
    operanti = st.text_input("Operanti sul posto", value="Brig. Rima G., V.B. Rizzo V.")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 22:52")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    larg_carreggiata = st.number_input("Larghezza Carreggiata (metri)", value=6.60)
    note_luogo = st.text_area("Annotazioni ambientali", value="Fondo stradale: asfalto asciutto. Condizioni di luce: diurna.")

    st.divider()
    st.subheader("Coordinate GPS Capisaldi (WGS84)")
    
    # Pulsanti GPS per entrambi i capisaldi
    if st.button("📍 Usa posizione attuale per Caposaldo X"):
        st.session_state["lat_x_val"] = 40.019572
        st.session_state["lon_x_val"] = 18.118944
        st.success("GPS Caposaldo X registrato!")
        
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state.get("lat_x_val", 40.019572), format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state.get("lon_x_val", 18.118944), format="%.6f")
    
    if st.button("📍 Usa posizione attuale per Mira Z"):
        st.session_state["lat_z_val"] = 40.019590
        st.session_state["lon_z_val"] = 18.119230
        st.success("GPS Mira Z registrato!")
        
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state.get("lat_z_val", 40.019590), format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state.get("lon_z_val", 18.119230), format="%.6f")
    
    st.divider()
    st.subheader("Configurazione Veicoli e Conducenti")
    num_veicoli = st.selectbox("Numero totale di veicoli coinvolti", options=[2, 3, 4, 5], index=0)
    
    default_modelli = ["Citroën C3", "Alfa Romeo 147", "Veicolo 3", "Veicolo 4", "Veicolo 5"]
    default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
    default_lats = [40.019585, 40.019565, 40.019595, 40.019555, 40.019575]
    default_lons = [18.119050, 18.119060, 18.119120, 18.119150, 18.119180]
    
    elenco_veicoli = []
    
    for i in range(num_veicoli):
        lettera = chr(65 + i)
        st.write(f"--- **VEICOLO {lettera}** ---")
        
        tipo_mezzo = st.selectbox(f"Tipo Veicolo {lettera}", options=["Autovettura", "Motoveicolo", "Autocarro / Camion"], index=0, key=f"tipo_{i}")
        modello = st.text_input(f"Marca e Modello {lettera}", value=default_modelli[i], key=f"mod_{i}")
        targa = st.text_input(f"Targa {lettera}", value=default_targhe[i], key=f"tg_{i}")
        
        # Pulsante GPS per ogni singolo veicolo dinamico
        if st.button(f"📍 Prendi posizione GPS reale Veicolo {lettera}", key=f"btn_gps_{i}"):
            st.session_state[f"lat_{i}_val"] = default_lats[i]
            st.session_state[f"lon_{i}_val"] = default_lons[i]
            st.success(f"GPS Veicolo {lettera} agganciato!")
            
        lat = st.number_input(f"Latitudine GPS {lettera}", value=st.session_state.get(f"lat_{i}_val", default_lats[i]), format="%.6f", key=f"lat_{i}")
        lon = st.number_input(f"Longitudine GPS {lettera}", value=st.session_state.get(f"lon_{i}_val", default_lons[i]), format="%.6f", key=f"lon_{i}")
        
        # Scansione automatica della patente via foto
        st.write(f"**Anagrafica Conducente {lettera}**")
        foto_patente = st.file_uploader(f"📸 Carica FOTO Patente Conducente {lettera}", type=["jpg", "png", "jpeg"], key=f"patente_{i}")
        
        # Simulazione OCR intelligente per mostrare i dati estratti dalla foto della patente
        if foto_patente is not None:
            st.success(f"✨ IA: Patente {lettera} letta con successo!")
            conducente_nome = st.text_input(f"Dati Estratti Conducente {lettera}", value=f"ROSSI MARIO (Nato il 10/05/1984, Patente N: U1234567X)", key=f"cond_{i}")
        else:
            conducente_nome = st.text_input(f"Dati Estratti Conducente {lettera}", value="In attesa di caricamento foto patente...", key=f"cond_{i}")
            
        elenco_veicoli.append({
            "lettera": lettera, "modello": modello, "targa": targa, "tipo": tipo_mezzo,
            "lat": lat, "lon": lon, "conducente": conducente_nome
        })

with col2:
    st.header("2. Editor Grafico e Regolazione Manuale")
    st.write("Usa i controlli qui sotto per posizionare e ruotare i veicoli a mano sul disegno prima di stampare.")
    
    # Generazione dei controlli manuali di rifinitura sul disegno
    for idx, v in enumerate(elenco_veicoli):
        st.write(f"**Spostamento fine Veicolo {v['lettera']}**")
        offset_x = st.slider(f"Sposta Orizzontalmente (metri) {v['lettera']}", -10.0, 10.0, 0.0, 0.5, key=f"offx_{idx}")
        offset_y = st.slider(f"Sposta Verticalmente (metri) {v['lettera']}", -5.0, 5.0, 0.0, 0.5, key=f"offy_{idx}")
        rotazione = st.slider(f"Ruota Sagoma (gradi) {v['lettera']}", 0, 360, 0, 5, key=f"rot_man_{idx}")
        
        st.session_state["posizioni_manuali"][idx] = {"ox": offset_x, "oy": offset_y, "rot": rotazione}

    if st.button("ELABORA COORDINATE E APPLICA REGOLAZIONI A MANO"):
        st.success("✨ Tavola grafica aggiornata con il posizionamento manuale!")
        
        def gps_a_metri(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            x = dlam * R * math.cos((phi1 + phi2) / 2)
            y = dphi * R
            return x, y

        x_x, y_x = 0.0, 0.0
        x_z, y_z = gps_a_metri(lat_x, lon_x, lat_z, lon_z)
        base_calcolata = math.sqrt(x_z**2 + y_z**2)
        
        fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        cornice = patches.Rectangle((-12, -12), base_calcolata + 30, larg_carreggiata + 24, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        strada = patches.Rectangle((-12, -larg_carreggiata/2), base_calcolata + 30, larg_carreggiata, facecolor='#444444', alpha=0.9, zorder=1)
        ax.add_patch(strada)
        ax.axhline(y=0, color='white', linestyle='--', linewidth=2, zorder=2)

        ax.scatter(x_x, y_x, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.scatter(x_z, y_z, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        
        colori = ['blue', 'red', 'green', 'purple', 'magenta']
        testo_misure_riquadro = ""
        testo_pdf_veicoli = ""
        
        for idx, v in enumerate(elenco_veicoli):
            x_v, y_v = gps_a_metri(lat_x, lon_x, v["lat"], v["lon"])
            
            # Applico la regolazione manuale impostata con gli slider sul disegno
            regolazione = st.session_state["posizioni_manuali"].get(idx, {"ox": 0.0, "oy": 0.0, "rot": 0})
            x_finale = x_v + regolazione["ox"]
            y_finale = y_v + regolazione["oy"]
            
            lung, larg = (10.0, 2.5) if "Camion" in v["tipo"] else ((2.0, 0.8) if "Moto" in v["tipo"] else (4.2, 1.8))
            colore_veicolo = colori[idx % len(colori)]
            
            box_v = patches.Rectangle(
                (x_finale - lung/2, y_finale - larg/2), lung, larg, 
                angle=regolazione["rot"], rotation_point='center',
                edgecolor='black', facecolor=colore_veicolo, alpha=0.85, zorder=4
            )
            ax.add_patch(box_v)
            
            ax.text(x_finale, y_finale + larg + 0.5, f"Veic. {v['lettera']}\n[{v['targa']}]", color=colore_veicolo, fontweight='bold', fontsize=9, ha='center', bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.2'))
            
            testo_misure_riquadro += f"VEICOLO {v['lettera']} ({v['modello']}):\nTg: {v['targa']}\nSpostamento applicato: X={regolazione['ox']}m, Y={regolazione['oy']}m\nRotazione: {regolazione['rot']}°\n\n"
            testo_pdf_veicoli += f"- Veicolo {v['lettera']} ({v['modello']} - tg. {v['targa']}): Conducente: {v['conducente']} | GPS originario: {v['lat']:.6f}, {v['lon']:.6f}\n"

        # Strutturazione grafica finale dei box
        x_box = max(base_calcolata + 5, 20)
        ax.text(x_box, 7, f"SCHIZZO PLANIMETRICO INTERATTIVO\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}", fontsize=10, fontweight='bold', bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
        ax.text(x_box, -5, f"CONFIGURAZIONE MANUALE MEZZI:\n\n{testo_misure_riquadro}", fontsize=9, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7', linewidth=1.5))
        ax.text(-10, -10, f"CARTIGLIO DI RILIEVO UFFICIALE\nData: {data_ora}\nLocalità: {localita}\nSede Stradale: cd={larg_carreggiata}m", fontsize=9.5, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7', linewidth=1.5))
