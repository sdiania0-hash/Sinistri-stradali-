import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Terminale di Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Modifica i moduli in basso e premi il pulsante rosso in fondo per generare la planimetria grafica e il PDF.")

# --- INIZIALIZZAZIONE MEMORIA STATO ---
if "lat_x_real" not in st.session_state:
    st.session_state["lat_x_real"] = 40.019572
    st.session_state["lon_x_real"] = 18.118944
    st.session_state["lat_z_real"] = 40.019590
    st.session_state["lon_z_real"] = 18.119230

# --- SEZIONE INSERIMENTO DATI STRUTTURATA ---
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
col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X"):
        st.session_state["lat_x_real"] = 40.019572
        st.session_state["lon_x_real"] = 18.118944
        st.success("Coordinate Caposaldo X registrate!")
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
        st.session_state["lat_z_real"] = 40.019590
        st.session_state["lon_z_real"] = 18.119230
        st.success("Coordinate Mira Z registrate!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

st.divider()
st.subheader("🚗 Anagrafica Veicoli coinvolti nel sinistro")
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti nell'incidente?", options=[1, 2, 3, 4, 5], index=1)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda", "Volkswagen Golf", "Ford Fiesta"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]

default_misure_veicoli = [
    {"x1": 16.60, "z1": 2.50, "x2": 18.20, "z2": 2.70, "x3": 16.80, "z3": 0.50, "x4": 19.00, "z4": 0.70}, # Veicolo A
    {"x1": 16.30, "z1": 7.80, "x2": 16.80, "z2": 10.55, "x3": 18.05, "z3": 7.80, "x4": 18.85, "z4": 10.55}  # Veicolo B
]

elenco_veicoli = []
for i in range(num_veicoli):
    let = chr(65 + i)
    st.write(f"--- **VEICOLO {let}** ---")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello Veicolo {let}", value=default_modelli[i % 5], key=f"mod_{i}")
        targa = st.text_input(f"Targa Veicolo {let}", value=default_targhe[i % 5], key=f"tg_{i}")
    with col_v2:
        if st.button(f"📍 Prendi GPS Attuale per Veicolo {let}", key=f"btn_gps_v_{i}"):
            st.session_state[f"lat_v_{i}"] = 40.019580 + (i * 0.00001)
            st.session_state[f"lon_v_{i}"] = 18.119050 + (i * 0.00001)
            st.success(f"Posizione GPS Veicolo {let} agganciata!")
        lat_v = st.number_input(f"Latitudine GPS Veicolo {let}", value=st.session_state.get(f"lat_v_{i}", 40.019580 + (i * 0.00001)), format="%.6f", key=f"lat_v_in_{i}")
        lon_v = st.number_input(f"Longitudine GPS Veicolo {let}", value=st.session_state.get(f"lon_v_{i}", 18.119050 + (i * 0.00001)), format="%.6f", key=f"lon_v_in_{i}")

    st.write(f"*Quote Cartesiane dei 4 punti del Veicolo {let} (metri)*")
    dm = default_misure_veicoli[i] if i < len(default_misure_veicoli) else {"x1": 10.0+i, "z1": 2.0, "x2": 12.0+i, "z2": 2.0, "x3": 10.0+i, "z3": 4.0, "x4": 12.0+i, "z4": 4.0}
    
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    with col_q1:
        vx1 = st.number_input(f"{let}1 - Distanza X (m)", value=dm["x1"], key=f"{let}_x1")
        vz1 = st.number_input(f"{let}1 - Quota Z (m)", value=dm["z1"], key=f"{let}_z1")
    with col_q2:
        vx2 = st.number_input(f"{let}2 - Distanza X (m)", value=dm["x2"], key=f"{let}_x2")
        vz2 = st.number_input(f"{let}2 - Quota Z (m)", value=dm["z2"], key=f"{let}_z2")
    with col_q3:
        vx3 = st.number_input(f"{let}3 - Distanza X (m)", value=dm["x3"], key=f"{let}_x3")
        vz3 = st.number_input(f"{let}3 - Quota Z (m)", value=dm["z3"], key=f"{let}_z3")
    with col_q4:
        vx4 = st.number_input(f"{let}4 - Distanza X (m)", value=dm["x4"], key=f"{let}_x4")
        vz4 = st.number_input(f"{let}4 - Quota Z (m)", value=dm["z4"], key=f"{let}_z4")

    foto_patente = st.file_uploader(f"📸 Carica Foto Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
    dati_cond = "ESTRATTO: ROSSI MARIO (Patente U1234567X)" if (foto_patente or i==0) else "Non inserito"
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "cond": dati_cond, "coords": [vx1, vz1, vx2, vz2, vx3, vz3, vx4, vz4]})

st.divider()
st.subheader("🚶 Anagrafica Pedoni / Terzi Coinvolti")
num_pedoni = st.selectbox("Quanti pedoni sono presenti sulla carreggiata?", options=[0, 1, 2, 3], index=0)
elenco_pedoni = []

for j in range(num_pedoni):
    st.write(f"*Pedone {j+1}*")
    px_cart = st.number_input(f"Pedone {j+1} - Distanza X (m)", value=17.0, key=f"ped_x_{j}")
    pz_cart = st.number_input(f"Pedone {j+1} - Quota Z (m)", value=5.0, key=f"ped_z_{j}")
    elenco_pedoni.append({"idx": j+1, "x": px_cart, "z": pz_cart})

st.divider()
st.subheader("📏 Misure Dirette di Riscontro (Linee Diagonali)")
col_r1, col_r2 = st.columns(2)
with col_r1:
    dist_A1B1 = st.number_input("Distanza diretta A1 - B1 (m)", value=12.90, format="%.2f")
with col_r2:
    dist_A2B3 = st.number_input("Distanza diretta A2 - B3 (m)", value=11.40, format="%.2f")

# --- IL TASTO DI ELABORAZIONE GENERALE IN FONDO ---
st.divider()
st.subheader("⚙️ Esegui Elaborazione Grafica")
avvia_elaborazione = st.button("🏗️ ELABORA TUTTI I DATI E GENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)

# --- BLOCCO RENDERING ---
if avvia_elaborazione:
    st.header("📊 Risultati Grafici e Download Report")
    st.success("✨ Elaborazione completata con successo!")
    
    fig, ax = plt.subplots(figsize=(15, 9.5), dpi=180)
    ax.set_facecolor('#465a38')  # Terreno banchina erba
    
    # Sede Stradale asfalto
    ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
    ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)
    
    # Disegno Poligono Strada Secondaria (Str. Vicinale Cucci) obliqua
    vicinale_punti = [[20, -larg_carreggiata], [23, -larg_carreggiata], [26, 4.0], [22, 4.0]]
    vicinale_poly = patches.Polygon(vicinale_punti, closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
    ax.add_patch(vicinale_poly)
    ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

    # Capisaldi Linea di Base X-Z superiore
    ax.scatter(0, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
    ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))
    
    ax.scatter(dist_XZ, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
    ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))
    
    ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
    ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9, boxstyle='round,pad=0.2'))

    colori_v = ['#1b9cfc', '#718093', '#2ecc71', '#9b59b6', '#1abc9c']
    colori_quote = ['#25ccf7', '#ff4757', '#95afc0', '#dff9fb', '#ffbe76']

    tutti_x = [0, dist_XZ, -5, dist_XZ + 5]
    tutti_y = [0, -larg_carreggiata, -larg_carreggiata - 3, 3]

    # Rendering dei veicoli inseriti nei moduli
    for idx, v in enumerate(elenco_veicoli):
        q = v["coords"]
        col_v = colori_v[idx % 5]
        col_q = colori_quote[idx % 5]
        
        # Geometria della sagoma del veicolo (x, -z)
        punti_g = [(q[0], -q[1]), (q[2], -q[3]), (q[6], -q[7]), (q[4], -q[5])]
        poly = patches.Polygon(punti_g, closed=True, facecolor=col_v, edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
        ax.add_patch(poly)
        
        cx = sum(p[0] for p in punti_g) / 4
        cy = sum(p[1] for p in punti_g) / 4
