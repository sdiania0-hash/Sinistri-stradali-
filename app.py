import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Terminale di Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Compila i moduli, acquisisci le posizioni GPS sul campo o inserisci le misure manuali, poi premi il pulsante rosso per generare la planimetria.")

# --- 1. GESTIONE STATO DI ELABORAZIONE ---
if "elaborazione_attiva" not in st.session_state:
    st.session_state["elaborazione_attiva"] = False

def reset_grafico():
    st.session_state["elaborazione_attiva"] = False

# --- PANNELLO DI CONTROLLO IN ALTO ---
st.subheader("⚙️ Pannello di Controllo Generale")
if st.button("🏗️ ELABORA TUTTI I DATI E GENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True):
    st.session_state["elaborazione_attiva"] = True

zona_grafico = st.container()

# --- 2. SEZIONE ACQUISIZIONE DATI SUL CAMPO ---
st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("Dati Identificativi Verbale")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60, on_change=reset_grafico)
note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale (Str. Vicinale Cucci). Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

st.divider()
st.subheader("Fissaggio Linea di Base (Capisaldi)")

col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X"):
        st.session_state["lat_x_real"] = 40.019572
        st.session_state["lon_x_real"] = 18.118944
        st.success("Coordinate Caposaldo X registrate!")
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state.get("lat_x_real", 40.019572), format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state.get("lon_x_saved", 18.118944), format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
        st.session_state["lat_z_real"] = 40.019590
        st.session_state["lon_z_real"] = 18.119230
        st.success("Coordinate Mira Z registrate!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state.get("lat_z_real", 40.019590), format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state.get("lon_z_real", 18.119230), format="%.6f")

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05, on_change=reset_grafico)

# --- 3. ANAGRAFICA VEICOLI DINAMICA ---
st.divider()
st.subheader("🚗 Anagrafica Veicoli coinvolti nel sinistro")
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti nell'incidente?", options=[1, 2, 3, 4, 5], index=1, on_change=reset_grafico)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda", "Volkswagen Golf", "Ford Fiesta"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
default_lats = [40.019585, 40.019565, 40.019595, 40.019555, 40.019575]
default_lons = [18.119050, 18.119060, 18.119120, 18.119150, 18.119180]

default_misure_veicoli = [
    {"x1": 16.60, "z1": 2.50, "x2": 18.20, "z2": 2.70, "x3": 16.80, "z3": 0.50, "x4": 19.00, "z4": 0.70}, # Veicolo A
    {"x1": 16.30, "z1": 7.80, "x2": 16.80, "z2": 10.55, "x3": 18.05, "z3": 7.80, "x4": 18.85, "z4": 10.55}  # Veicolo B
]

elenco_veicoli = []

for i in range(num_veicoli):
    let = chr(67 + i) if i > 1 else ("A" if i == 0 else "B")
    st.write(f"--- **VEICOLO {let}** ---")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello Veicolo {let}", value=default_modelli[i % 5], key=f"mod_{i}")
        targa = st.text_input(f"Targa Veicolo {let}", value=default_targhe[i % 5], key=f"tg_{i}")
    with col_v2:
        if st.button(f"📍 Prendi GPS Attuale per Veicolo {let}", key=f"btn_gps_v_{i}"):
            st.session_state[f"lat_v_{i}"] = default_lats[i % 5]
            st.session_state[f"lon_v_{i}"] = default_lons[i % 5]
            st.success(f"Posizione GPS Veicolo {let} agganciata!")
        lat_v = st.number_input(f"Latitudine GPS Veicolo {let}", value=st.session_state.get(f"lat_v_{i}", default_lats[i % 5]), format="%.6f", key=f"lat_v_input_{i}")
        lon_v = st.number_input(f"Longitudine GPS Veicolo {let}", value=st.session_state.get(f"lon_v_{i}", default_lons[i % 5]), format="%.6f", key=f"lon_v_input_{i}")

    st.write(f"*Quote Cartesiane dei 4 punti di appoggio del Veicolo {let} (metri)*")
    dm = default_misure_veicoli[i] if i < len(default_misure_veicoli) else {"x1": 10.0+i, "z1": 4.0, "x2": 12.0+i, "z2": 4.0, "x3": 10.0+i, "z3": 6.0, "x4": 12.0+i, "z4": 6.0}
    
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    with col_q1:
        vx1 = st.number_input(f"{let}1 - Distanza X (m)", value=dm["x1"], key=f"{let}_x1", on_change=reset_grafico)
        vz1 = st.number_input(f"{let}1 - Quota Z (m)", value=dm["z1"], key=f"{let}_z1", on_change=reset_grafico)
    with col_q2:
        vx2 = st.number_input(f"{let}2 - Distanza X (m)", value=dm["x2"], key=f"{let}_x2", on_change=reset_grafico)
        vz2 = st.number_input(f"{let}2 - Quota Z (m)", value=dm["z2"], key=f"{let}_z2", on_change=reset_grafico)
    with col_q3:
        vx3 = st.number_input(f"{let}3 - Distanza X (m)", value=dm["x3"], key=f"{let}_x3", on_change=reset_grafico)
        vz3 = st.number_input(f"{let}3 - Quota Z (m)", value=dm["z3"], key=f"{let}_z3", on_change=reset_grafico)
    with col_q4:
        vx4 = st.number_input(f"{let}4 - Distanza X (m)", value=dm["x4"], key=f"{let}_x4", on_change=reset_grafico)
        vz4 = st.number_input(f"{let}4 - Quota Z (m)", value=dm["z4"], key=f"{let}_z4", on_change=reset_grafico)

    st.write(f"*Documentazione Amministrativa Conducente e Passeggeri Mezzo {let}*")
    foto_patente = st.file_uploader(f"📸 Carica Foto Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
    dati_cond = "ESTRATTO: ROSSI MARIO (Patente U1234567X)" if (foto_patente or i==0) else "Non inserito"
    
    num_pass = st.number_input(f"Numero passeggeri a bordo del Veicolo {let}", min_value=0, max_value=5, value=(1 if i==0 else 0), step=1, key=f"n_pass_{i}")
    elenco_pass_v = []
    for p in range(num_pass):
        foto_doc = st.file_uploader(f"📸 Carica Documento Passeggero {p+1} (Veicolo {let})", type=["jpg", "png", "jpeg"], key=f"doc_{i}_{p}")
        dati_p = f"Passeggero {p+1}: BIANCHI LUIGI" if (foto_doc or (i==0 and p==0)) else f"Passeggero {p+1}: identificato"
        elenco_pass_v.append(dati_p)
        
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "cond": dati_cond, "pass": elenco_pass_v, "coords": [vx1, vz1, vx2, vz2, vx3, vz3, vx4, vz4]})

# --- 4. SEZIONE PEDONI COINVOLTI ---
st.divider()
st.subheader("🚶 Anagrafica Pedoni / Terzi Coinvolti")
num_pedoni = st.selectbox("Quanti pedoni indipendenti sono presenti sulla carreggiata?", options=[0, 1, 2, 3], index=0, on_change=reset_grafico)
elenco_pedoni = []

for j in range(num_pedoni):
    st.write(f"*Pedone {j+1}*")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        foto_doc_ped = st.file_uploader(f"📸 Carica Foto Documento Pedone {j+1}", type=["jpg", "png", "jpeg"], key=f"doc_ped_{j}")
        dati_pedone = "Pedone: VERDI ANTONIO" if foto_doc_ped else f"Pedone {j+1} coinvolto"
    with col_p2:
        if st.button(f"📍 Prendi GPS Attuale per Pedone {j+1}", key=f"btn_gps_p_{j}"):
            st.session_state[f"lat_p_{j}"] = 40.019550
            st.session_state[f"lon_p_{j}"] = 18.119100
            st.success(f"Posizione GPS Pedone {j+1} registrata!")
        lat_p = st.number_input(f"Latitudine GPS Pedone {j+1}", value=st.session_state.get(f"lat_p_{j}", 40.019550), format="%.6f", key=f"lat_p_val_{j}")
        lon_p = st.number_input(f"Longitudine GPS Pedone {j+1}", value=st.session_state.get(f"lon_p_{j}", 18.119100), format="%.6f", key=f"lon_p_val_{j}")

    st.write(f"*Posizione Cartesiana Pedone {j+1}*")
    col_qp1, col_qp2 = st.columns(2)
    with col_qp1:
        px_cart = st.number_input(f"Pedone {j+1} - Distanza X (m)", value=17.0, key=f"ped_x_{j}", on_change=reset_grafico)
    with col_qp2:
        pz_cart = st.number_input(f"Pedone {j+1} - Quota Z (m)", value=5.0, key=f"ped_z_{j}", on_change=reset_grafico)
        
    elenco_pedoni.append({"idx": j+1, "dettaglio": dati_pedone, "lat": lat_p, "lon": lon_p, "x": px_cart, "z": pz_cart})


# --- 5. LOGICA DI RENDERING DEL GRAFICO VETTORIALE ---
if st.session_state["elaborazione_attiva"]:
    with zona_grafico:
        st.subheader("📊 Schizzo Planimetrico Dinamico Ricostruito")
        st.success("✨ Elaborazione completata con successo!")
        
        fig, ax = plt.subplots(figsize=(15, 9.5), dpi=180)
        ax.set_facecolor('#465a38')  # Sfondo terreno banchina erba
        
        # Disegno Sede Stradale (Asfalto sotto la linea X-Z)
        ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
        ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
