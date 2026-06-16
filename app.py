import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from streamlit_js_eval import streamlit_js_eval

# 1. IMPOSTAZIONI INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Modifica i dati nei moduli, attiva il sensore GPS del dispositivo per agganciare le coordinate reali sul campo e premi il pulsante in fondo per generare la tavola grafica.")

# Contenitore dinamico per la mappa (evita lo sfarfallio e la duplicazione)
contenitore_mappa = st.empty()

# Inizializzazione dello stato della sessione per la memoria GPS
if "lat_x_real" not in st.session_state:
    st.session_state["lat_x_real"] = 40.019572
    st.session_state["lon_x_real"] = 18.118944
if "lat_z_real" not in st.session_state:
    st.session_state["lat_z_real"] = 40.019590
    st.session_state["lon_z_real"] = 18.119230

# FUNZIONE GEODETICA: Calcola automaticamente la distanza in metri tra due coordinate GPS (Haversine)
def calcola_distanza_gps(lat1, lon1, lat2, lon2):
    R = 6371000.0  # Raggio della Terra in metri
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# 2. PROTOCOLLO INSERIMENTO DATI
st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("Dati Identificativi Verbale")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto.")

st.divider()
st.subheader("📡 Fissaggio Linea di Base tramite Hardware GPS")

# Attivazione del sensore del browser
ottieni_gps = st.checkbox("🔄 Attiva Antenna/Sensore GPS Dispositivo")
posizione_reale = None

if ottieni_gps:
    # Esegue il codice JavaScript nel browser del dispositivo per estrarre la posizione live
    posizione_reale = streamlit_js_eval(
        data_string="navigator.geolocation.getCurrentPosition(success => { return [success.coords.latitude, success.coords.longitude]; }, error => { return null; })", 
        key="gps_device_live"
    )
    if posizione_reale and len(posizione_reale) == 2:
        st.success(f"📡 Satelliti Agganciati! Posizione: {posizione_reale[0]:.6f}, {posizione_reale[1]:.6f}")
    else:
        st.warning("In attesa del segnale GPS... Assicurati di aver dato i permessi di localizzazione al browser.")

col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Copia GPS Live -> Caposaldo X") and posizione_reale:
        st.session_state["lat_x_real"] = posizione_reale[0]
        st.session_state["lon_x_real"] = posizione_reale[1]
        st.toast("Coordinate Caposaldo X registrate!")
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")

with col_cz:
    if st.button("📍 Copia GPS Live -> Mira Z") and posizione_reale:
        st.session_state["lat_z_real"] = posizione_reale[0]
        st.session_state["lon_z_real"] = posizione_reale[1]
        st.toast("Coordinate Mira Z registrate!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

# Calcolo automatico intelligente della distanza reale tra i due punti GPS
dist_calcolata = calcola_distanza_gps(lat_x, lon_x, lat_z, lon_z)
if dist_calcolata < 0.1:
    dist_calcolata = 25.05  # Valore di fallback se i punti coincidono o sono di test

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=float(round(dist_calcolata, 2)))
if ottieni_gps:
    st.caption(f"✨ Distanza X-Z calcolata geometricamente via GPS: {dist_calcolata:.2f} metri.")
    st.divider()
st.subheader("🚗 Anagrafica Veicoli Coinvolti")
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti?", options=[1, 2, 3, 4, 5], index=1)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda", "Volkswagen Golf", "Ford Fiesta"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
default_misure_veicoli = [
    {"x1": 16.60, "z1": 2.50, "x2": 18.20, "z2": 2.70, "x3": 16.80, "z3": 0.50, "x4": 19.00, "z4": 0.70}, 
    {"x1": 16.30, "z1": 7.80, "x2": 16.80, "z2": 10.55, "x3": 18.05, "z3": 7.80, "x4": 18.85, "z4": 10.55}  
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
        if st.button(f"📍 Prendi GPS per Veicolo {let}", key=f"btn_gps_v_{i}") and posizione_reale:
            st.session_state[f"lat_v_{i}"] = posizione_reale[0]
            st.session_state[f"lon_v_{i}"] = posizione_reale[1]
            st.toast(f"GPS Veicolo {let} registrato!")
        lat_v = st.number_input(f"Lat {let}", value=st.session_state.get(f"lat_v_{i}", 40.019580 + (i * 0.00001)), format="%.6f", key=f"la_in_{i}")
        lon_v = st.number_input(f"Lon {let}", value=st.session_state.get(f"lon_v_{i}", 18.119050 + (i * 0.00001)), format="%.6f", key=f"lo_in_{i}")

    dm = default_misure_veicoli[i] if i < len(default_misure_veicoli) else {"x1": 10.0, "z1": 2.0, "x2": 12.0, "z2": 2.0, "x3": 10.0, "z3": 4.0, "x4": 12.0, "z4": 4.0}
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    with col_q1:
        vx1 = st.number_input(f"{let}1-X", value=dm["x1"], key=f"{let}_x1")
        vz1 = st.number_input(f"{let}1-Z", value=dm["z1"], key=f"{let}_z1")
    with col_q2:
        vx2 = st.number_input(f"{let}2-X", value=dm["x2"], key=f"{let}_x2")
        vz2 = st.number_input(f"{let}2-Z", value=dm["z2"], key=f"{let}_z2")
    with col_q3:
        vx3 = st.number_input(f"{let}3-X", value=dm["x3"], key=f"{let}_x3")
        vz3 = st.number_input(f"{let}3-Z", value=dm["z3"], key=f"{let}_z3")
    with col_q4:
        vx4 = st.number_input(f"{let}4-X", value=dm["x4"], key=f"{let}_x4")
        vz4 = st.number_input(f"{let}4-Z", value=dm["z4"], key=f"{let}_z4")

    foto_patente = st.file_uploader(f"📸 Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
    dati_cond = "ESTRATTO VERIFICATO" if (foto_patente or i==0) else "Non inserito"
    
    num_pass = st.number_input(f"Passeggeri {let}", min_value=0, max_value=5, value=(1 if i==0 else 0), key=f"n_p_{i}")
    elenco_pass_v = []
    for p in range(num_pass):
        foto_doc = st.file_uploader(f"📸 Doc Passeggero {p+1} ({let})", type=["jpg", "png", "jpeg"], key=f"dc_{i}_{p}")
        elenco_pass_v.append("Identificato" if foto_doc else "Presente")
        
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "cond": dati_cond, "pass": elenco_pass_v, "coords": [vx1, vz1, vx2, vz2, vx3, vz3, vx4, vz4]})

st.divider()
st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta A1 - B1 (m)", value=12.90, format="%.2f")
dist_A2B3 = st.number_input("Distanza diretta A2 - B3 (m)", value=11.40, format="%.2f")

st.divider()
st.subheader("⚙️ Pannello Azione")
esegui_ricalcolo = st.button("🏗️ ELABORA TUTTI I DATI E RIGENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)

# 3. ENGINE MATEMATICO DI RENDERING DELLA MAPPA STRADALE
def genera_mappa():
    fig, ax = plt.subplots(figsize=(17, 9.5), dpi=180)
    ax.set_facecolor('#465a38')

    # Disegno Sede Stradale principale (Asfalto grigio scuro)
    ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
    ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)

    # Disegno Innesto Strada Secondaria obliqua
    vicinale_poly = patches.Polygon([[20, -larg_carreggiata], [23, -larg_carreggiata], [26, 4.0], [22, 4.0]], closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
    ax.add_patch(vicinale_poly)
    ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

    # Tracciamento Linea di Base Capisaldi X-Z
    ax.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
    ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right')
    ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left')
    ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
    ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9))

    colori_v = ['#1b9cfc', '#718093', '#2ecc71', '#9b59b6', '#1abc9c']
    colori_quote = ['#25ccf7', '#ff4757', '#95afc0', '#dff9fb', '#ffbe76']

    tutti_x = [0, dist_XZ, -5, dist_XZ + 10]
    tutti_z = [0, 0, 5, -larg_carreggiata - 3]

    # Rendering dei veicoli
    for idx, v in enumerate(elenco_veicoli):
        c = v["coords"]
        col = colori_v[idx % len(colori_v)]
        col_q = colori_quote[idx % len(colori_quote)]
        
        # Spigoli vettoriali
        punti_v = np.array([[c[0], -c[1]], [c[2], -c[3]], [c[6], -c[7]], [c[4], -c[5]]])
        poly_v = patches.Polygon(punti_v, closed=True, facecolor=col, edgecolor='black', linewidth=2, alpha=0.9, zorder=5)
        ax.add_patch(poly_v)
        
        center_x = np.mean(punti_v[:, 0])
        center_z = np.mean(punti_v[:, 1])
        ax.text(center_x, center_z, f"VEICOLO {v['let']}\n{v['modello']}", color='white', fontsize=9, weight='bold', ha='center', va='center', zorder=6)

        # Tracciamento quote cartesiane dai capisaldi sugli spigoli indicati
        for pt_idx, (px, pz) in enumerate([(c[0], c[1]), (c[2], c[3])]):
            ax.plot([px, px], [0, -pz], color=col_q, linestyle=':', linewidth=1.5, zorder=4)
            ax.plot([0, px], [0, 0], color=col_q, linestyle=':', linewidth=1.5, zorder=4)
            ax.scatter([px], [-pz], color=col_q, s=50, zorder=6)
            ax.text(px, -pz - 0.3, f"{v['let']}{pt_idx+1}", color='white', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.6, pad=1))

        tutti_x.extend([c[0], c[2], c[4], c[6]])
        tutti_z.extend([-c[1], -c[3], -c[5], -c[7]])

    ax.grid(True, color='#ffffff', linestyle='--', alpha=0.15, zorder=0)
    ax.set_xlim(min(tutti_x) - 3, max(tutti_x) + 3)
    ax.set_ylim(min(tutti_z) - 3, max(tutti_z) + 3)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel("Asse X (Metri) - Allineamento Linea di Base Capisaldi", fontsize=10, weight='bold')
    ax.set_ylabel("Asse Z (Metri) - Scostamento Ortogonale", fontsize=10, weight='bold')
    ax.set_title("PLANIMETRIA RILIEVO STATO DEI LUOGHI (SCALA METRICA REGOLARE)", fontsize=14, weight='bold', pad=15)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180)
    buf.seek(0)
    plt.close(fig)  # Libera la RAM impedendo il crash dell'app
    return buf

# Renderizza la mappa aggiornata nel contenitore fisso superiore
with contenitore_mappa:
    mappa_img = genera_mappa()
    st.image(mappa_img, caption="Planimetria Tecnica Dinamica generata in tempo reale")

if esegui_ricalcolo:
    st.success("✅ Elaborazione geometrica completata e mappa aggiornata con le coordinate GPS!")
    
