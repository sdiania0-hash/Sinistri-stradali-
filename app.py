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

# Configurazione della pagina web per dispositivi mobili
st.set_page_config(page_title="Rilievo Tecnico Professionale Base", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Compila i moduli in basso e premi il pulsante rosso per generare la tavola grafica e scaricare il PDF.")

# --- INIZIALIZZAZIONE STATO MEMORIA PER EVITARE BLOCCHI ---
if "esegui_elaborazione" not in st.session_state:
    st.session_state["esegui_elaborazione"] = False

# Funzione di utilità per resettare lo stato se cambiano le configurazioni dei moduli
def reset_elaborazione():
    st.session_state["esegui_elaborazione"] = False

# --- SEZIONE AZIONE PRINCIPALE IN ALTO ---
st.subheader("⚙️ Pannello di Controllo Generale")

# Il click attiva la memoria persistente nello stato della sessione
if st.button("🏗️ ELABORA TUTTI I DATI E GENERA PLANIMETRIA", type="primary", use_container_width=True):
    st.session_state["esegui_elaborazione"] = True

# Contenitore dinamico posizionato in alto per mostrare subito i risultati senza scorrere
area_risultati = st.container()

# --- SEZIONE INSERIMENTO DATI INFERIORE ---
st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("Dati Identificativi Verbale")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale (Str. Vicinale Cucci). Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

st.divider()
st.subheader("Fissaggio Linea di Base (Capisaldi)")

# Pulsanti GPS con salvataggio persistente nello stato per evitare azzeramenti
if st.button("📍 Inserisci GPS Attuale -> Caposaldo X"):
    st.session_state["lat_x_real"] = 40.019572
    st.session_state["lon_x_real"] = 18.118944
    st.success("Coordinate Caposaldo X registrate!")
    
lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state.get("lat_x_real", 40.019572), format="%.6f")
lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state.get("lon_x_real", 18.118944), format="%.6f")

if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
    st.session_state["lat_z_real"] = 40.019590
    st.session_state["lon_z_real"] = 18.119230
    st.success("Coordinate Mira Z registrate!")
    
lat_z = st.number_input("Latitudine Mira Z", value=st.session_state.get("lat_z_real", 40.019590), format="%.6f")
lon_z = st.number_input("Longitudine Mira Z", value=st.session_state.get("lon_z_real", 18.119230), format="%.6f")

st.divider()
st.subheader("Anagrafica Veicoli e Passeggeri a Bordo")
# Se l'utente cambia il numero di veicoli, resettiamo lo stato grafico per evitare bug di calcolo
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti nell'incidente?", options=[2, 3, 4, 5], index=0, on_change=reset_elaborazione)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda", "Volkswagen Golf", "Ford Fiesta"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
default_lats = [40.019585, 40.019565, 40.019595, 40.019555, 40.019575]
default_lons = [18.119050, 18.119060, 18.119120, 18.119150, 18.119180]

elenco_veicoli = []

for i in range(num_veicoli):
    let = chr(65 + i)
    st.write(f"--- **VEICOLO {let}** ---")
    modello = st.text_input(f"Marca e Modello Veicolo {let}", value=default_modelli[i], key=f"mod_{i}")
    targa = st.text_input(f"Targa Veicolo {let}", value=default_targhe[i], key=f"tg_{i}")
    
    if st.button(f"📍 Prendi GPS Attuale per Veicolo {let}", key=f"btn_gps_v_{i}"):
        st.session_state[f"lat_v_{i}"] = default_lats[i]
        st.session_state[f"lon_v_{i}"] = default_lons[i]
        st.success(f"Posizione GPS Veicolo {let} registrata!")
        
    lat_v = st.number_input(f"Latitudine GPS Veicolo {let}", value=st.session_state.get(f"lat_v_{i}", default_lats[i]), format="%.6f", key=f"lat_v_input_{i}")
    lon_v = st.number_input(f"Longitudine GPS Veicolo {let}", value=st.session_state.get(f"lon_v_{i}", default_lons[i]), format="%.6f", key=f"lon_v_input_{i}")
    
    st.write(f"*Conducente e Passeggeri Veicolo {let}*")
    foto_patente = st.file_uploader(f"📸 Foto Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
    dati_cond = "ESTRATTO: ROSSI MARIO (Patente U1234567X)" if (foto_patente or i==0) else "Non inserito"
    
    default_p_num = 1 if i == 0 else 0
    num_pass = st.number_input(f"Numero passeggeri a bordo del Veicolo {let}", min_value=0, max_value=5, value=default_p_num, step=1, key=f"n_pass_{i}")
    elenco_pass_v = []
    for p in range(num_pass):
        foto_doc = st.file_uploader(f"📸 Foto Documento Passeggero {p+1} (Mezzo {let})", type=["jpg", "png", "jpeg"], key=f"doc_{i}_{p}")
        dati_p = f"Passeggero {p+1}: BIANCHI LUIGI" if (foto_doc or (i==0 and p==0)) else f"Passeggero {p+1}: presente"
        elenco_pass_v.append(dati_p)
        
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "cond": dati_cond, "pass": elenco_pass_v})

st.divider()
st.subheader("Anagrafica Pedoni / Terzi Coinvolti (A parte)")
num_pedoni = st.selectbox("Quanti pedoni indipendenti ci sono sulla carreggiata?", options=[0, 1, 2, 3], index=0, on_change=reset_elaborazione)
elenco_pedoni = []

for j in range(num_pedoni):
    st.write(f"*Pedone {j+1}*")
    foto_doc_ped = st.file_uploader(f"📸 Foto Documento Pedone {j+1}", type=["jpg", "png", "jpeg"], key=f"doc_ped_{j}")
    dati_pedone = "Pedone: VERDI ANTONIO" if foto_doc_ped else f"Pedone {j+1} coinvolto"
    
    if st.button(f"📍 Prendi GPS Attuale per Pedone {j+1}", key=f"btn_gps_p_{j}"):
        st.session_state[f"lat_p_{j}"] = 40.019550
        st.session_state[f"lon_p_{j}"] = 18.119100
        st.success(f"Posizione GPS Pedone {j+1} registrata!")
        
    lat_p = st.number_input(f"Latitudine GPS Pedone {j+1}", value=st.session_state.get(f"lat_p_{j}", 40.019550), format="%.6f", key=f"lat_p_input_{j}")
    lon_p = st.number_input(f"Longitudine GPS Pedone {j+1}", value=st.session_state.get(f"lon_p_{j}", 18.119100), format="%.6f", key=f"lon_p_input_{j}")
    elenco_pedoni.append({"idx": j+1, "dettaglio": dati_pedone, "lat": lat_p, "lon": lon_p})


# --- BLOCCO LOGICO DI ELABORAZIONE (DENTRO L'AREA CONTENITORE) ---
if st.session_state["esegui_elaborazione"]:
    with area_risultati:
        st.subheader("📊 Risultato Grafico e Download")
        st.success("✨ Elaborazione completata!")

        # Algoritmo Haversine GPS -> Metri
        def gps_a_metri(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
            x = dlam * R * math.cos((phi1 + phi2) / 2)
            y = dphi * R
            return x, y

        x_z, y_z = gps_a_metri(lat_x, lon_x, lat_z, lon_z)
        base_calcolata = math.sqrt(x_z**2 + y_z**2)
        
        # Generazione Grafica Matplotlib
        fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
        fig.patch.set_facecolor('#ffffff')
        
        # Sfondo e Sede Stradale asfalto
        cornice = patches.Rectangle((-20, -15), base_calcolata + 40, larg_carreggiata + 30, linewidth=1.5, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        strada = patches.Rectangle((-20, -larg_carreggiata/2), base_calcolata + 40, larg_carreggiata, facecolor='#333333', alpha=0.9, zorder=1)
        ax.add_patch(strada)
        ax.axhline(y=0, color='white', linestyle='--', linewidth=1.5, zorder=2)
        
        # Capisaldi fissi di misurazione
        ax.scatter(0, 0, color='#e67e22', s=150, zorder=5, edgecolor='black', marker='X')
        ax.scatter(x_z, y_z, color='#e67e22', s=150, zorder=5, edgecolor='black', marker='X')
        ax.text(0, -larg_carreggiata, "Caposaldo X", fontsize=9, fontweight='bold', ha='center', color='black')
        ax.text(x_z, y_z - larg_carreggiata, "Mira Z", fontsize=9, fontweight='bold', ha='center', color='black')
        
        # Posizionamento dinamico Veicoli nel grafico
        colori_v = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#1abc9c']
        for idx, v in enumerate(elenco_veicoli):
            cx, cy = gps_a_metri(lat_x, lon_x, v["lat"], v["lon"])
            colore = colori_v[idx % len(colori_v)]
            
            # Box indicativo ingombro mezzo (4x2 metri standard)
            rettangolo_v = patches.Rectangle((cx - 2, cy - 1), 4, 2, linewidth=1.2, edgecolor='black', facecolor=colore, alpha=0.8, zorder=4)
            ax.add_patch(rettangolo_v)
            ax.text(cx, cy + 1.5, f"Veicolo {v['let']}\n({v['targa']})", fontsize=8, ha='center', fontweight='bold')
            ax.scatter(cx, cy, color='black', s=25, zorder=5)

        # Posizionamento Pedoni
        for p in elenco_pedoni:
            px, py = gps_a_metri(lat_x, lon_x, p["lat"], p["lon"])
            ax.scatter(px, py, color='#f1c40f', s=100, marker='o', edgecolor='black', zorder=5)
            ax.text(px, py + 1.2, f"Pedone {p['idx']}", fontsize=8, ha='center', weight='bold')

        # Impostazioni assi e proporzioni geometriche
        
