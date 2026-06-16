import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
import requests
from streamlit_geolocation import streamlit_geolocation
from pyproj import Transformer

# 1. IMPOSTAZIONI INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Forense", layout="centered")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense")

# =========================================================
# 🔐 SISTEMA DI AUTENTICAZIONE (ACCESSO PROTETTO)
# =========================================================
UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato - Operatori di Polizia Stradale")
    st.write("Inserire le credenziali fornite dall'amministratore per sbloccare i moduli di rilievo forense.")
    utente_input = st.text_input("Nome Utente", value="", key="login_user")
    password_input = st.text_input("Password", type="password", value="", key="login_pass")
    if st.button("Sblocca Terminale", type="primary", use_container_width=True, key="login_btn"):
        if utente_input == UTENTE_CORRETTO and password_input == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("❌ Credenziali errate. Accesso negato.")
    st.stop()
# =========================================================

st.warning("⚠️ **VERSIONE BETA IN VIA DI SVILUPPO** — Prototipo industriale per il rilievo stradale. I calcoli geometrici, le stime cinematiche e le acquisizioni hardware devono essere verificati dall'operatore prima dell'inserimento negli atti ufficiali.")
st.caption("© 2026 Tutti i diritti riservati. Proprietà intellettuale depositata. Modulo di geocoding OSM Nominatim e localizzazione hardware nativa integrati.")

contenitore_mappa = st.empty()

# Inizializzazione della memoria di stato per i capisaldi e la via automatica
if "lat_x_real" not in st.session_state: st.session_state["lat_x_real"] = 40.019572
if "lon_x_real" not in st.session_state: st.session_state["lon_x_real"] = 18.118944
if "lat_z_real" not in st.session_state: st.session_state["lat_z_real"] = 40.019590
if "lon_z_real" not in st.session_state: st.session_state["lon_z_real"] = 18.119230
if "strada_bloccata" not in st.session_state: st.session_state["strada_bloccata"] = ""

DIZIONARIO_SEGMENTI = {"🚗 Autovettura Utilitaria / Media": {"w": 1.65, "l": 3.85, "t": "auto"}, "🚙 SUV / Berlina Lunga / Furgone": {"w": 1.90, "l": 4.65, "t": "auto"}, "🏍️ Motociclo / Ciclomotore (Mozzo Ant./Post.)": {"w": 0.80, "l": 2.10, "t": "moto"}, "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50, "t": "auto"}}

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

def gps_to_utm(lat, lon):
    x, y = transformer.transform(lon, lat)
    return x, y

def calcola_distanza_utm(lat1, lon1, lat2, lon2):
    x1, y1 = gps_to_utm(lat1, lon1)
    x2, y2 = gps_to_utm(lat2, lon2)
    return math.hypot(x2 - x1, y2 - y1)

def calcola_rettangolo_veicolo_utm(x_ant, z_ant, x_post, z_post, larghezza=1.80, lunghezza=4.20):
    dx = x_ant - x_post
    dz = z_ant - z_post
    lunghezza_vec = math.hypot(dx, dz)
    if lunghezza_vec == 0: return np.array([[x_ant, z_ant], [x_ant + larghezza, z_ant], [x_ant + larghezza, z_ant + lunghezza], [x_ant, z_ant + lunghezza]])
    ux, uz = dx / lunghezza_vec, dz / lunghezza_vec
    nx, nz = -uz, ux
    p1 = np.array([x_ant, z_ant])
    p2 = p1 + larghezza * np.array([nx, nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    return np.array([p1, p2, p3, p4])

def recupera_toponomastica_reale(lat, lon):
    url = f"https://openstreetmap.org{lat}&lon={lon}&addressdetails=1"
    headers = {"User-Agent": "TerminaleRilievoForense/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            dati = response.json()
            via = dati.get("address", {}).get("road", dati.get("address", {}).get("suburb", "Via non classificata"))
            comune = dati.get("address", {}).get("city", dati.get("address", {}).get("town", dati.get("address", {}).get("village", "Comune non rilevato")))
            return f"{via}, {comune}"
    except Exception: pass
    return "SP55 Matino-Taviano"
    st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("🛰️ Posizionamento Hardware Attivo")
st.markdown("*Premere il quadratino sottostante sul telefono per agganciare istantaneamente i satelliti ed eseguire la decodifica della via:*")
location = streamlit_geolocation()
posizione_reale = None
precisione_gps_m = 3.0

if location and location.get("latitude") and location.get("longitude"):
    posizione_reale = [location["latitude"], location["longitude"]]
    if location.get("accuracy"): precisione_gps_m = location["accuracy"]
    st.success(f"📡 Satelliti Agganciati! Lat: {posizione_reale[0]:.6f} | Lon: {posizione_reale[1]:.6f} (Precisione: ±{precisione_gps_m:.1f}m)")
    # BLOCCO DELLA VIA IN SESSIONE (Risolve lo sfarfallio e il reset automatico dello schermo)
    if st.session_state["strada_bloccata"] == "":
        st.session_state["strada_bloccata"] = recupera_toponomastica_reale(posizione_reale[0], posizione_reale[1])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano"

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")

url_maps = f"https://google.com{st.session_state['lat_x_real']},{st.session_state['lon_x_real']}"
st.link_button("🌐 Apri Localizzazione su Google Maps (Ispezione Corsie e Curve)", url_maps, use_container_width=True)

col_info_strada1, col_info_strada2 = st.columns(2)
with col_info_strada1:
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata", options=["Carreggiata Unica (Doppio Senso)", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata (Spartitraffico Centrale)"])
    larg_carreggiata = st.number_input("Larghezza della singola carreggiata (m)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero corsie per carreggiata", options=[1, 2, 3, 4], index=1)
with col_info_strada2:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base (Direzione Caposaldo Z)", options=["Nord ⬆️", "Nord-Est ↗️", "Est ➡️", "Sud-Est ↘️", "Sud ⬇️", "Sud-Ovest ↙️", "Ovest ⬅️", "Nord-Ovest ↖️"])
    stato_asfalto = st.selectbox("Stato del fondo stradale", options=["Asfalto Asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Viscido / Fango (f=0.30)"])

note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Fondo stradale regolare, visibilità buona.")

col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X") and posizione_reale:
        st.session_state["lat_x_real"] = posizione_reale[0]
        st.session_state["lon_x_real"] = posizione_reale[1]
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")
with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z") and posizione_reale:
        st.session_state["lat_z_real"] = posizione_reale[0]
        st.session_state["lon_z_real"] = posizione_reale[1]
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_calcolata = calcola_distanza_utm(lat_x, lon_x, lat_z, lon_z)
if dist_calcolata < 0.1: dist_calcolata = 25.05
dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, value=float(round(dist_calcolata, 2)))

st.divider()
st.subheader("🚗 Anagrafica, Documenti e Rilievo Veicoli")
num_veicoli = st.selectbox("Quanti veicoli/mezzi sono coinvolti?", options=[1, 2, 3, 4, 5], index=1)

default_modelli = ["Citroën C3", "Yamaha T-Max", "Fiat Panda"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF"]
default_inputs = [{"xa": 16.60, "za": 2.50, "xp": 18.20, "zp": 2.70}, {"xa": 15.10, "za": 4.20, "xp": 15.80, "zp": 4.35}]

elenco_veicoli = []
for k in range(num_veicoli):
    let = chr(65 + k)
    st.write(f"--- **VEICOLO {let}** ---")
    categoria = st.selectbox(f"Tipologia Mezzo {let}", options=list(DIZIONARIO_SEGMENTI.keys()), index=(0 if k==0 else (1 if k==1 else 2)), key=f"cat_{k}")
    larg, lung, tipo_forma = DIZIONARIO_SEGMENTI[categoria]["w"], DIZIONARIO_SEGMENTI[categoria]["l"], DIZIONARIO_SEGMENTI[categoria]["t"]
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello {let}", value=default_modelli[k % 3], key=f"mod_{k}")
        targa = st.text_input(f"Targa / Sigla {let}", value=default_targhe[k % 3], key=f"tg_{k}")
        stato_mezzo = st.selectbox(f"Stato di Quiete Mezzo {let}", options=["Normale (Ruote a terra)", "Ribaltato su un fianco", "Sottosopra / Capovolto"], key=f"cond_mezzo_{k}")
    with col_v2:
        if st.button(f"📍 Prendi GPS Veicolo {let}", key=f"btn_gps_v_{k}") and posizione_reale:
            st.session_state[f"lat_v_{k}"] = posizione_reale[0]
            st.session_state[f"lon_v_{k}"] = posizione_reale[1]
        lat_v = st.number_input(f"Lat {let}", value=st.session_state.get(f"lat_v_{k}", 40.019580 + (k * 0.00001)), format="%.6f", key=f"la_in_{k}")
        lon_v = st.number_input(f"Lon {let}", value=st.session_state.get(f"lon_v_{k}", 18.119050 + (k * 0.00001)), format="%.6f", key=f"lo_in_{k}")

    st.markdown("*📁 Caricamento Documenti (Simulazione Lettura OCR)*")
    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        foto_patente = st.file_uploader(f"📸 Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{k}")
        foto_carta = st.file_uploader(f"📸 Carta Circolazione / Libretto {let}", type=["jpg", "png", "jpeg"], key=f"lib_{k}")
    with col_doc2:
        foto_ass = st.file_uploader(f"📸 Polizza RCA {let}", type=["jpg", "png", "jpeg"], key=f"ass_{k}")
        flag_cond_ferito = st.checkbox(f"🩹 Il Conducente {let} ha riportato lesioni (Ferito)", key=f"c_fer_{k}")
        ospedale_cond = st.text_input(f"Ospedale trasporto Conducente {let}", value="Vito Fazzi - Lecce" if flag_cond_ferito else "Nessuno", key=f"osp_c_{k}")

    dati_ocr = f"Documenti Caricati: {'Sì' if (foto_patente or foto_carta or foto_ass) else 'No'}. Accertamenti d'ufficio regolari via ANIA/Sinf."
    num_pass = st.number_input(f"Passeggeri trasportati sul Veicolo {let}", min_value=0, max_value=5, value=0, key=f"n_p_{k}")
    elenco_pass_v = []
    for p in range(num_pass):
        st.write(f"↳ *Passeggero {p+1} (Mezzo {let})*")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            foto_doc = st.file_uploader(f"📸 Documento Pass. {p+1}", type=["jpg", "png", "jpeg"], key=f"dc_{k}_{p}")
            f_p = st.checkbox(f"🩹 Ferito", key=f"p_fer_{k}_{p}")
        with col_p2:
            o_p = st.text_input(f"Ospedale trasporto Pass. {p+1}", value="Vito Fazzi" if f_p else "Nessuno", key=f"osp_p_{k}_{p}")
        elenco_pass_v.append({"descr": f"Passeggero {p+1}: {'Documentato via OCR' if foto_doc else 'Presente sul posto'}", "ferito": f_p, "ospedale": o_p})

    st.markdown("📐 *Misure Ortogonali di Posizionamento (Asse X-Z)*")
    lato_carreggiata = st.radio(f"Posizionamento del Veicolo {let} rispetto alla linea di mezzeria:", ["Corsia Principale (Destra / Valori Standard)", "Corsia Opposta (Sinistra / Valori Invertiti '-')"], key=f"lato_{k}")
    molt = -1.0 if "Opposta" in lato_carreggiata else 1.0

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        vx1 = st.number_input(f"Ruota Ant. X (m) [{let}1]", value=default_inputs[k % 2]["xa"] if k < len(default_inputs) else 10.0, key=f"{let}_x1_r")
        vz1_in = st.number_input(f"Ruota Ant. Z (m) [{let}1]", value=default_inputs[k % 2]["za"] if k < len(default_inputs) else 2.0, key=f"{let}_z1_r")
    with col_q2:
        vx2 = st.number_input(f"Ruota Post. X (m) [{let}2]", value=default_inputs[k % 2]["xp"] if k < len(default_inputs) else 12.0, key=f"{let}_x2_r")
        vz2_in = st.number_input(f"Ruota Post. Z (m) [{let}2]", value=default_inputs[k % 2]["zp"] if k < len(default_inputs) else 2.0, key=f"{let}_z2_r")
    
    vz1, vz2 = vz1_in * molt, vz2_in * molt
    punti_v = calcola_rettangolo_veicolo_utm(vx1, vz1, vx2, vz2, larg, lung)
    elenco_veicoli.append({"let": let, "modello": modelo, "targa": targa, "lat": lat_v, "lon": lon_v, "punti": punti_v, "misure_base": [vx1, vz1], "ocr": dati_ocr, "passeggeri": elenco_pass_v, "stato": stato_mezzo, "forma": tipo_forma, "categoria": categoria, "ferito": flag_cond_ferito, "ospedale": ospedale_cond})
    st.divider()
st.subheader("🚶 Rilievo Pedoni / Ostacoli sulla Carreggiata")
num_pedoni = st.selectbox("Quanti pedoni o ostacoli fissi vuoi registrare?", options=[0, 1, 2, 3], index=0)
elenco_pedoni = []

for kp in range(num_pedoni):
    st.write(f"🔹 **Pedone / Ostacolo {kp + 1}**")
    col_pe1, col_pe2 = st.columns(2)
    with col_pe1:
        ped_nome = st.text_input(f"Nome Pedone / Tipo Ostacolo {kp+1}", value=f"Pedone {kp+1}", key=f"p_nom_{kp}")
        ped_ferito = st.checkbox(f"🩹 Ferito", value=True, key=f"p_fr_{kp}")
        ped_osp = st.text_input(f"Ospedale trasporto Pedone {kp+1}", value="Vito Fazzi" if ped_ferito else "Nessuno", key=f"p_osp_{kp}")
    with col_pe2:
        ped_x = st.number_input(f"Distanza Asse X (m)", value=14.0, key=f"p_x_{kp}")
        ped_z_in = st.number_input(f"Scostamento Asse Z (m)", value=3.2, key=f"p_z_{kp}")
        ped_lato = st.radio(f"Lato", ["Destra", "Sinistra '-'"], key=f"p_lt_{kp}")
        ped_z = -ped_z_in if "Sinistra" in ped_lato else ped_z_in
    elenco_pedoni.append({"nome": ped_nome, "x": ped_x, "z": ped_z, "ferito": ped_ferito, "ospedale": ped_osp})

st.divider()
st.subheader("💥 Rilievo Tracce Forensi e Punto d'Urto")
col_pu1, col_pu2 = st.columns(2)
with col_pu1:
    pu_x = st.number_input("Punto d'Urto Presunto (P.U.) - Asse X (m)", value=17.00)
    frenata_x = st.number_input("Inizio Traccia Frenata - Asse X (m)", value=12.00)
with col_pu2:
    pu_z = st.number_input("Punto d'Urto Presunto (P.U.) - Asse Z (m)", value=4.50)
    frenata_z = st.number_input("Inizio Traccia Frenata - Asse Z (m)", value=4.50)

st.divider()
st.subheader("📏 Misure Dirette di Riscontro Incrociato Libero")
num_riscontri = st.selectbox("Quanti riscontri metrici vuoi registrare?", options=[1, 2, 3, 4, 5], index=1, key="num_risc")
elenco_riscontri = []

for idx_r in range(num_riscontri):
    st.write(f"🔹 **Riscontro Metrico N° {idx_r + 1}**")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        p_da = st.text_input(f"Dal Punto / Spigolo", value="A1" if idx_r==0 else "B2", key=f"p_da_{idx_r}")
    with col_r2:
        p_a = st.text_input(f"Al Punto / Spigolo", value="B1" if idx_r==0 else "P.U.", key=f"p_a_{idx_r}")
    with col_r3:
        dist_val = st.number_input(f"Distanza (m)", value=12.90 if idx_r==0 else 4.20, format="%.2f", key=f"d_val_{idx_r}")
    elenco_riscontri.append({"da": p_da, "a": p_a, "dist": dist_val})

def genera_tavola_grafica():
    fig, ax_mappa = plt.subplots(figsize=(16, 7), dpi=150)
    ax_mappa.set_facecolor('#465a38')
    
    if "Doppia Carreggiata" in tipo_carreggiata:
        ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata-1.5, -larg_carreggiata, facecolor='#20bf6b', alpha=0.9, zorder=1)
        ax_mappa.fill_between([-15, dist_XZ + 20], -2*larg_carreggiata-1.5, -larg_carreggiata-1.5, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax_mappa.axhline(y=0, color='white', linestyle='-', linewidth=3, zorder=2)
        ax_mappa.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2, zorder=2)
        ax_mappa.axhline(y=-larg_carreggiata-1.5, color='white', linestyle='-', linewidth=2, zorder=2)
        ax_mappa.axhline(y=-2*larg_carreggiata-1.5, color='white', linestyle='-', linewidth=3, zorder=2)
    else:
        ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax_mappa.axhline(y=0, color='white', linestyle='-', linewidth=3, zorder=2)
        ax_mappa.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=3, zorder=2)
        if "Doppio Senso" in tipo_carreggiata: ax_mappa.axhline(y=-larg_carreggiata/2, color='white', linestyle='-', linewidth=2, alpha=0.9, zorder=2)

    if num_corsie > 1:
        spazio_corsia = larg_carreggiata / num_corsie
        for c in range(1, num_corsie): ax_mappa.axhline(y=-(spazio_corsia * c), color='white', linestyle='--', linewidth=1.2, alpha=0.7, zorder=2)

    ax_mappa.arrow(-10, -larg_carreggiata/2, 4, 0, width=0.2, head_width=0.6, head_length=0.8, color='white', alpha=0.5, zorder=2)
    ax_mappa.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=250, marker='X', edgecolor='white', zorder=10)
    ax_mappa.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2, zorder=3)
    ax_mappa.scatter([pu_x], [-pu_z], color='red', s=300, marker='*', edgecolor='white', linewidth=1.5, zorder=8)
    ax_mappa.text(pu_x + 0.3, -pu_z + 0.3, "P.U.", color='red', weight='bold', fontsize=11)
    ax_mappa.plot([frenata_x, pu_x], [-frenata_z, -pu_z], color='#f1c40f', linestyle='--', linewidth=3, zorder=4)
    ax_mappa.text(-3, 1.8, f"🧭 Nord: {orientamento_nord}", color='black', weight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, pad=2))
    
    colori_v = ['#1b9cfc', '#718093', '#2ecc71', '#9b59b6', '#1abc9c']
    for idx_m, v in enumerate(elenco_veicoli):
        pts_plot = v["punti"].copy()
        pts_plot[:, 1] = -pts_plot[:, 1]
        col = colori_v[idx_m % len(colori_v)]
        ax_mappa.add_patch(patches.Polygon(pts_plot, closed=True, facecolor=col, edgecolor='black', linewidth=2, zorder=5))
        ax_mappa.text(np.mean(pts_plot[:, 0]), np.mean(pts_plot[:, 1]), f"{v['let']}\n({v['stato']})", color='white', fontsize=8, weight='bold', ha='center', va='center', zorder=6)
        mb_x, mb_z = v["misure_base"][0], v["misure_base"][1]
        ax_mappa.plot([mb_x, mb_x], [0, -mb_z], color=col, linestyle=':', alpha=0.7)
        ax_mappa.text(mb_x, -mb_z - 0.3, f"{v['let']}1", color='white', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.7, pad=1))

    for p in elenco_pedoni:
        ax_mappa.scatter([p["x"]], [-p["z"]], color='#e74c3c', s=160, marker='o', edgecolor='white', linewidth=1.5, zorder=7)
        ax_mappa.text(p["x"] + 0.3, -p["z"] + 0.3, p["nome"], color='yellow', weight='bold', fontsize=9)

    # 📊 LEGENDA INCORPORATA DIRETTAMENTE DENTRO IL FILE DELLA MAPPA (Requisito di stampa Forense)
    testo_legenda_fig = f"🌟 P.U. Presunto: X={pu_x:.2f}m, Z={pu_z:.2f}m\n🟡 Inizio Frenata: X={frenata_x:.2f}m\n🛰️ Precisione GPS: ±{precisione_gps_m:.1f}m\n📏 Base X-Z: {dist_XZ}m"
    ax_mappa.text(0.98, 0.95, testo_legenda_fig, transform=ax_mappa.transAxes, fontsize=8, verticalalignment='top', horizontalalignment='right', color='black', weight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', alpha=0.9, edgecolor='#e67e22'))

    ax_mappa.grid(True, color='#ffffff', linestyle='--', alpha=0.15)
    ax_mappa.set_xlim(-12, dist_XZ + 15)
    ax
    
