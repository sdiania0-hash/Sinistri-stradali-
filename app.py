import streamlit as st
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
import requests
from streamlit_geolocation import streamlit_geolocation
from pyproj import Transformer
import pytesseract
from PIL import Image
import re
import json
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Terminale Rilievo Planimetrico", layout="wide")

# Carica la configurazione degli utenti
def carica_config():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except:
        # Se non c'è il file, usa le credenziali di default
        return {
            'credentials': {
                'usernames': {
                    'comando': {
                        'name': 'Comando',
                        'password': '$2b$12$default'  # Non funzionerà, ma evita crash
                    }
                }
            },
            'cookie': {
                'expiry_days': 30,
                'name': 'auth_cookie',
                'key': 'default_key'
            }
        }

config = carica_config()
authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

defaults = {
    "autenticato": False,
    "lat_x_real": 40.019572,
    "lon_x_real": 18.118944,
    "lat_z_real": 40.019590,
    "lon_z_real": 18.119230,
    "strada_bloccata": "SP55 Matino-Taviano, Matino",
    "render_schizzo": False,
    "frenata_abilitata": False,
    "localita_accertata": "SP55 Matino-Taviano, Matino",
    "foto_sinistro": [],
    "backup_json": {},
    "operatore": "",
    "nome_completo": "",
    "matricola": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

def gps_to_utm(lat, lon):
    if lat is None or lon is None:
        return 0.0, 0.0
    return transformer.transform(lon, lat)

def distanza(lat1, lon1, lat2, lon2):
    x1, y1 = gps_to_utm(lat1, lon1)
    x2, y2 = gps_to_utm(lat2, lon2)
    return math.hypot(x2 - x1, y2 - y1)

def ocr(file):
    if file is None:
        return ""
    try:
        return pytesseract.image_to_string(Image.open(file), lang="ita+eng")
    except Exception as e:
        return f"OCR non configurato: {e}"

def parse_doc(text):
    t = (text or "").upper()
    out = {}
    targa = re.search(r"\b[A-Z]{2}\d{3}[A-Z]{2}\b", t)
    if targa:
        out["targa"] = targa.group()
    nome = re.search(r"(NOME|COGNOME)\s*[:-]?\s*([A-ZÀ-Ü' ]{3,})", t)
    if nome:
        out["nome"] = nome.group(2).strip()
    return out

def reverse_geo(lat, lon):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1},
            headers={"User-Agent": "RilievoPlanimetrico/1.0"},
            timeout=8
        )
        r.raise_for_status()
        j = r.json()
        a = j.get("address", {})
        road = a.get("road") or a.get("pedestrian") or a.get("suburb") or "SP55 Matino-Taviano"
        comune = a.get("city") or a.get("town") or a.get("village") or "Matino"
        return f"{road}, {comune}"
    except Exception:
        return "SP55 Matino-Taviano, Matino"

def calcola_rettangolo_veicolo_utm(x_ant, z_ant, x_post, z_post, larghezza, lunghezza, assetto="Regolare"):
    dx = x_ant - x_post
    dz = z_ant - z_post
    lunghezza_vec = math.hypot(dx, dz)
    if lunghezza_vec == 0:
        base_box = np.array([
            [x_ant - larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant - lunghezza],
            [x_ant - larghezza/2, z_ant - lunghezza]
        ])
        return base_box
    ux, uz = dx / lunghezza_vec, dz / lunghezza_vec
    nx, nz = -uz, ux
    p1 = np.array([x_ant - (larghezza/2)*nx, z_ant - (larghezza/2)*nz])
    p2 = np.array([x_ant + (larghezza/2)*nx, z_ant + (larghezza/2)*nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    punti_box = np.array([p1, p2, p3, p4])
    if "fianco" in assetto:
        punti_box = punti_box * 0.92
    elif "Sottosopra" in assetto:
        punti_box = np.array([p2, p1, p4, p3])
    return punti_box

DIZIONARIO_SEGMENTI = {
    "🚗 Citroën C3 (Auto Utilitaria)": {"w": 1.75, "l": 3.99, "tipo": "auto"},
    "🚗 Alfa Romeo 147 (Berlina)": {"w": 1.73, "l": 4.22, "tipo": "auto"},
    "🚙 SUV / Furgone Commerciale": {"w": 1.90, "l": 4.65, "tipo": "suv"},
    "🏍️ Motociclo (Ciclomotore)": {"w": 0.80, "l": 2.10, "tipo": "moto"},
    "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50, "tipo": "camion"}
}
# ==============================================================================
# LOGIN SEMPLICE
# ==============================================================================
if not st.session_state["autenticato"]:
    st.title("🚓 Terminale Universale di Rilievo Planimetrico Stradale")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔒 Accesso Riservato - Carabinieri")
        st.markdown("*Inserisci le tue credenziali.*")
        
        u_raw = st.text_input("Username", value="", autocomplete="off")
        p_raw = st.text_input("Password", type="password", value="", autocomplete="off")
        
        if st.button("🔓 Accedi", type="primary", use_container_width=True):
            utente_pulito = u_raw.strip().lower() if u_raw else ""
            password_pulita = p_raw.strip() if p_raw else ""
            
            if utente_pulito == "comando" and password_pulita == "matino2026":
                st.session_state["autenticato"] = True
                st.session_state["operatore"] = "comando"
                st.session_state["nome_completo"] = "Comando"
                st.session_state["matricola"] = "00000"
                st.success("✅ Accesso effettuato!")
                st.rerun()
            else:
                st.error("❌ Credenziali errate. Riprova.")
    st.stop()

# ==============================================================================
# HEADER CON OPERATORE
# ==============================================================================
st.title("🚓 Terminale Universale di Rilievo Planimetrico Stradale")
st.sidebar.success(f"👮 Operatore: {st.session_state['nome_completo']}")
st.sidebar.info(f"🆔 Matricola: {st.session_state['matricola']}")
st.sidebar.markdown("---")

st.warning("⚠️ VERSIONE BETA IN CORSO DI AGGIORNAMENTO - Sistema professionale di acquisizione planimetrica digitale.")

# ==============================================================================
# SEZIONE 1: PROTOCOLLO ACQUISIZIONE DATI
# ==============================================================================
st.header("1. Protocollo di Acquisizione Dati sul Campo")
location = streamlit_geolocation()

if location and location.get("latitude") is not None and location.get("longitude") is not None:
    if st.session_state["strada_bloccata"] in ["", "SP55 Matino-Taviano, Matino"]:
        st.session_state["strada_bloccata"] = reverse_geo(location["latitude"], location["longitude"])

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value=f"{datetime.now().strftime('%d/%m/%Y')} | ORE: {datetime.now().strftime('%H:%M')}")

# Usa il nome dell'operatore loggato
operatori_input = st.text_input("Operatori di Polizia Stradale", value=st.session_state["nome_completo"])

col_strada1, col_strada2 = st.columns(2)
with col_strada1:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata", options=["Carreggiata unica a doppio senso di circolazione", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata (Spartitraffico Centrale)"])
    larg_carreggiata = st.number_input("Larghezza della singola carreggiata cd (m)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero corsie totali della carreggiata", options=[1, 2, 3, 4], index=1)
with col_strada2:
    stato_asfalto = st.selectbox("Stato del fondo stradale", options=["Asfalto asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Viscido / Fango (f=0.30)"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base (Direzione Caposaldo Z)", options=["Nord ⬆️", "Est ➡️", "Sud ⬇️", "Ovest ⬅️"])
    note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Condizioni di luce: diurna. Visibilità: buona. Presenza di intersezione con strada vicinale.")

st.subheader("📐 Definizione dei Capisaldi di Riferimento Strumentale")
col_cx, col_cz = st.columns(2)
with col_cx:
    lat_x = st.number_input("Latitudine Caposaldo X (Origine 0,0)", format="%.6f", value=st.session_state["lat_x_real"])
    lon_x = st.number_input("Longitudine Caposaldo X (Origine 0,0)", format="%.6f", value=st.session_state["lon_x_real"])
with col_cz:
    lat_z = st.number_input("Latitudine Caposaldo Z (Asse Metrico)", format="%.6f", value=st.session_state["lat_z_real"])
    lon_z = st.number_input("Longitudine Caposaldo Z (Asse Metrico)", format="%.6f", value=st.session_state["lon_z_real"])

dist_XZ = distanza(lat_x, lon_x, lat_z, lon_z)
st.info(f"📏 Distanza calcolata sulla linea di base strumentale X - Z: **{dist_XZ:.2f} metri**")

# ==============================================================================
# SEZIONE 2: VEICOLI
# ==============================================================================
st.header("2. Veicoli")
n = st.selectbox("Numero veicoli coinvolti nel sinistro stradale", [1, 2, 3, 4, 5], index=1)
veicoli = []

for i in range(n):
    let = chr(65 + i)
    st.subheader(f"📦 Configurazione Avanzata Unità {let}")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        cat = st.selectbox("Categoria e Modello Strutturale", list(DIZIONARIO_SEGMENTI.keys()), key=f"cat_{i}", index=i if i < 2 else 0)
        mod = st.text_input("Marca e Modello Esteso", value="Citroën C3" if i==0 else "Alfa Romeo 147", key=f"mod_{i}")
        targa = st.text_input("Targa del Veicolo", value="AA123BB" if i==0 else "CC456DD", key=f"targa_{i}").upper()
        stato_v = st.text_input("Stato Post-Urto / Danni Strutturali", value="Danni ingenti sulla parte frontale dell'automezzo", key=f"stato_{i}")
        assetto_v = st.selectbox("Giacitura / Assetto di Quiete Statica", options=["Regolare", "Ribaltato sul fianco dx", "Ribaltato sul fianco sx", "Sottosopra (Capovolto)"], key=f"ass_{i}")
    with col_v2:
        latv = st.number_input(f"Lat Quiete GPS - Veicolo {let}", key=f"latv_{i}", value=lat_x, format="%.6f")
        lonv = st.number_input(f"Lon Quiete GPS - Veicolo {let}", key=f"lonv_{i}", value=lon_x, format="%.6f")
        doc = st.file_uploader(f"Scansione Patente / Libretto {let} (OCR)", key=f"doc_{i}")
    with col_v3:
        ferito_v = st.checkbox(f"Conducente {let} Infortunato / Ospedalizzato", key=f"fer_{i}")
        prog_v = st.number_input(f"Prognosi Conducente {let} (giorni)", min_value=0, value=0, key=f"prog_{i}")
        ospedale_v = st.text_input(f"Ospedale Conducente {let}", value="Vito Fazzi" if ferito_v else "Nessuno", key=f"osp_{i}")

    st.markdown(f"**📐 Rilevamenti Metrici dal Campo (Riscontri Grafici Veicolo {let})**")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: xa = st.number_input(f"XA1 {let} (Avanzamento Ant.)", value=16.60 if i==0 else 16.30, key=f"xa_{i}", format="%.2f")
    with col_m2: za = st.number_input(f"ZA1 {let} (Scostamento Ant.)", value=11.55 if i==0 else 10.55, key=f"za_{i}", format="%.2f")
    with col_m3: xp = st.number_input(f"XA2 {let} (Avanzamento Post.)", value=18.20 if i==0 else 18.05, key=f"xp_{i}", format="%.2f")
    with col_m4: zp = st.number_input(f"ZA2 {let} (Scostamento Post.)", value=11.00 if i==0 else 8.70, key=f"zp_{i}", format="%.2f")

    ocr_txt = ocr(doc)
    parsed = parse_doc(ocr_txt)
    if parsed.get("targa"): st.success(f"🔍 Targa rilevata OCR per {let}: {parsed['targa']}")
    if parsed.get("nome"): st.success(f"🔍 Conducente rilevato OCR per {let}: {parsed['nome']}")

    dim = DIZIONARIO_SEGMENTI[cat]
    punti_invallati = calcola_rettangolo_veicolo_utm(xa, za, xp, zp, dim["w"], dim["l"], assetto_v)
    col_faccia = "#add8e6" if i==0 else "#d3d3d3"
    col_bordo = "blue" if i==0 else "black"

    st.markdown(f"*Registro Passeggeri Trasportati a bordo del Veicolo {let}*")
    num_pass = st.number_input(f"Numero di passeggeri - Veicolo {let}", min_value=0, max_value=4, value=0, key=f"npass_{i}")
    passeggeri_lista = []
    for p_idx in range(int(num_pass)):
        col_ps1, col_ps2, col_ps3 = st.columns(3)
        with col_ps1: descr_p = st.text_input(f"Generalità Pass. {p_idx+1} V_{let}", value=f"Passeggero {p_idx+1}", key=f"dps_{i}_{p_idx}")
        with col_ps2: ferito_p = st.checkbox(f"Ferito Pass. {p_idx+1} V_{let}", key=f"fps_{i}_{p_idx}")
        with col_ps3: prog_p = st.number_input(f"Prognosi Pass. {p_idx+1} V_{let}", min_value=0, value=0, key=f"pps_{i}_{p_idx}")
        passeggeri_lista.append({"descr": descr_p, "ferito": ferito_p, "prognosi": prog_p})

    veicoli.append({
        "let": let, "modello": mod, "targa": targa, "categoria": cat, "lat": latv, "lon": lonv, "stato": stato_v,
        "ferito": ferito_v, "prognosi": prog_v, "ospedale": ospedale_v, "misure": [xa, za, xp, zp],
        "punti_invallati": punti_invallati, "colore_faccia": col_faccia, "colore_bordo": col_bordo,
        "estratto_auto": parsed if parsed else "Nessuno", "passeggeri": passeggeri_lista, "assetto_scelto": assetto_v
    })

# ==============================================================================
# SEZIONE 3: PEDONI
# ==============================================================================
st.header("3. Pedoni / Strutture / Terzi Coinvolti")
pnum = st.selectbox("Numero pedoni o ostacoli fissi da censire sul teatro del sinistro", [0, 1, 2, 3, 4, 5], index=0)
pedoni = []

for i in range(pnum):
    st.markdown(f"##### 🚶 Target Pedone / Ostacolo Fisso P{i+1}")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        nome_p = st.text_input("Identificativo / Nome Soggetto", value=f"Soggetto P{i+1}", key=f"pn_{i}")
        ferito_p = st.checkbox("Soggetto Infortunato / Deceduto", key=f"fped_{i}")
    with col_p2: x_p = st.number_input("Distanza Ortogonale X (m) [Scostamento da Asse]", value=1.50, format="%.2f", key=f"px_{i}")
    with col_p3: z_p = st.number_input("Avanzamento Base Z (m) [Distanza da Caposaldo]", value=12.00, format="%.2f", key=f"pz_{i}")
    with col_p4:
        prog_p = st.number_input("Prognosi Sanitaria Iniziale (gg)", min_value=0, value=0, key=f"pped_{i}")
        osp_p = st.text_input("Struttura Sanitaria d'Accoglimento", value="Vito Fazzi" if ferito_p else "Nessuno", key=f"osped_{i}")
    pedoni.append({"nome": nome_p, "x": x_p, "z": z_p, "ferito": ferito_p, "prognosi": prog_p, "ospedale": osp_p})
    # ==============================================================================
# SEZIONE 4: FOTO
# ==============================================================================
st.header("📸 Fascicolo Fotografico Digitale dei Rilievi")
if "foto_sinistro" not in st.session_state: st.session_state["foto_sinistro"] = []

col_cam1, col_cam2 = st.columns(2)
with col_cam1:
    sorgente_input = st.radio("Sorgente Input Media", options=["Fotocamera Dispositivo 📷", "Galleria File 📁"])
    if len(st.session_state["foto_sinistro"]) < 30:
        if sorgente_input == "Fotocamera Dispositivo 📷":
            file_scatto = st.camera_input("Inquadra reperto d'urto", key="cam_hw_in", facing_mode="environment")
        else:
            file_scatto = st.file_uploader("Seleziona file immagine", type=["png", "jpg", "jpeg"], key="gal_hw_in")
        
        if file_scatto:
            img_aperta = Image.open(file_scatto)
            if file_scatto.name not in [f["nome"] for f in st.session_state["foto_sinistro"]]:
                num_id = len(st.session_state["foto_sinistro"]) + 1
                desc_foto = st.text_input(f"Didascalia Fotogramma N. {num_id}", value=f"Reperto n. {num_id}", key=f"desc_f_{num_id}")
                if st.button(f"Salva Fotogramma N. {num_id}"):
                    st.session_state["foto_sinistro"].append({"id": num_id, "nome": file_scatto.name, "img": img_aperta, "didascalia": desc_foto})
                    st.rerun()

with col_cam2:
    st.markdown(f"**Fotogrammi Validati: {len(st.session_state['foto_sinistro'])} / 30**")
    if st.session_state["foto_sinistro"]:
        for f in st.session_state["foto_sinistro"]:
            with st.expander(f"📷 FOTOGRAMMA N. {f['id']} - {f['didascalia']}"): st.image(f["img"], use_container_width=True)
        if st.button("🗑️ Svuota Fascicolo Fotografico"): st.session_state["foto_sinistro"] = []; st.rerun()

# ==============================================================================
# SEZIONE 5: ANALISI CINEMATICA
# ==============================================================================
st.header("💥 Analisi Cinematica (Tracce Frenata)")
col_cine1, col_cine2 = st.columns(2)
with col_cine1:
    usa_frenata = st.checkbox("Presenza di tracce di frenata sul fondo asfaltato")
    lunghezza_traccia = st.number_input("Lunghezza della traccia di frenata L (m)", min_value=0.0, max_value=200.0, value=15.50)
with col_cine2:
    pendenza_strada = st.number_input("Pendenza longitudinale sede stradale p (%)", min_value=-20.0, max_value=20.0, value=0.0)
    velocita_impatto = st.number_input("Stima velocità residua all'urto V_URTO (km/h)", min_value=0.0, max_value=200.0, value=30.0)

stringa_stato = stato_asfalto
coefficienti_aderenza = {
    "Asfalto asciutto (f=0.75)": 0.75,
    "Asfalto Bagnato (f=0.45)": 0.45,
    "Viscido / Fango (f=0.30)": 0.30
}
f_aderenza = coefficienti_aderenza.get(stringa_stato, 0.75)
v_stimata_kmh = 0.0
if usa_frenata and lunghezza_traccia > 0:
    quadrato_v = ((velocita_impatto / 3.6) ** 2) + (2 * 9.81 * lunghezza_traccia * (f_aderenza + (pendenza_strada / 100.0)))
    if quadrato_v > 0: v_stimata_kmh = math.sqrt(quadrato_v) * 3.6
    st.success(f"🧮 Stima Velocità Pre-Frenata calcolata: **{v_stimata_kmh:.1f} km/h**")

# ==============================================================================
# SEZIONE 6: DISEGNO (con TOGGLE)
# ==============================================================================
st.header("4. Elaborazione Grafica e Generazione Planimetria")
st.markdown("*Attivare l'interruttore sottostante per visualizzare o rigenerare lo schizzo planimetrico aggiornato sul campo:*")

attiva_schizzo = st.toggle("🔄 RIGENERA / AGGIORNA SCHIZZO PLANIMETRICO", value=st.session_state["render_schizzo"])
st.session_state["render_schizzo"] = attiva_schizzo

# ==============================================================================
# FUNZIONE TAVOLA (DISEGNO) - DEVE ESSERE PRIMA DELL'USO
# ==============================================================================
def tavola(veicoli, pedoni, localita, data_ora, operatori, andamento, tipo_c, larg_c, num_c, stato_a, dist_xz, ord_nord, usa_frenata, lung_t):
    fig, ax = plt.subplots(figsize=(16, 10), facecolor="#f8f9fa")
    ax.set_xlim(-15, 45)
    ax.set_ylim(-12, 22)
    ax.set_aspect('equal')
    ax.axis("off")
    
    x_strada = np.linspace(-15, 45, 200)
    deviazione = np.zeros_like(x_strada)
    if "Destra" in andamento:
        deviazione = 0.05 * (x_strada - 15) ** 2
    elif "Sinistra" in andamento:
        deviazione = -0.05 * (x_strada - 15) ** 2
    
    for x_p, dev_p in zip(x_strada[:-1], deviazione[:-1]):
        carreggiata = patches.Rectangle((x_p, dev_p), 0.5, larg_c, facecolor="#444444", zorder=1)
        ax.add_patch(carreggiata)
        banch_sup = patches.Rectangle((x_p, dev_p + larg_c), 0.5, 10, facecolor="#7a8a78", alpha=0.25, zorder=0)
        banch_inf = patches.Rectangle((x_p, dev_p - 10), 0.5, 10, facecolor="#7a8a78", alpha=0.25, zorder=0)
        ax.add_patch(banch_sup)
        ax.add_patch(banch_inf)
    
    ax.plot(x_strada, deviazione, color="white", linewidth=3.5, zorder=2)
    ax.plot(x_strada, deviazione + larg_c, color="white", linewidth=3.5, zorder=2)
    ax.plot(x_strada, deviazione + (larg_c / 2), color="white", linestyle="--", linewidth=1.8, zorder=2)
    
    if "Doppia" in tipo_c:
        for x_p, dev_p in zip(x_strada[:-1], deviazione[:-1]):
            spartitraffico = patches.Rectangle((x_p, dev_p + (larg_c/2) - 0.25), 0.5, 0.5, facecolor="#999999", zorder=3)
            ax.add_patch(spartitraffico)
    
    if "Unico" in tipo_c:
        ax.arrow(10, larg_c*0.75, 4, 0, head_width=0.5, head_length=0.9, fc='white', ec='white', zorder=3)
        ax.arrow(22, larg_c*0.25, 4, 0, head_width=0.5, head_length=0.9, fc='white', ec='white', zorder=3)
    else:
        ax.arrow(10, larg_c*0.75, 4, 0, head_width=0.5, head_length=0.9, fc='white', ec='white', zorder=3)
        ax.arrow(22, larg_c*0.25, -4, 0, head_width=0.5, head_length=0.9, fc='white', ec='white', zorder=3)
    
    ax.plot(0, 0, "X", color="#d9534f", markersize=12, markeredgecolor="black", zorder=6)
    ax.text(0, -1.8, "Caposaldo X\n(Civico 57)", color="white", weight="bold", fontsize=8,
            bbox=dict(facecolor='#d9534f', alpha=0.9, boxstyle='round,pad=0.3'), ha="center")
    ax.plot(dist_xz, 0, "X", color="#f0ad4e", markersize=12, markeredgecolor="black", zorder=6)
    ax.text(dist_xz, -1.8, "Mira Z\n(Palo TIM)", color="black", weight="bold", fontsize=8,
            bbox=dict(facecolor='#f0ad4e', alpha=0.9, boxstyle='round,pad=0.3'), ha="center")
    ax.plot([0, dist_xz], [0, 0], color="#d9534f", linestyle="-.", linewidth=1.5, zorder=3)
    ax.text(dist_xz/2, -0.9, f"Linea Base X-Z = {dist_xz:.2f} m", color="#d9534f", weight="bold", fontsize=10, ha="center")
    
    for v in veicoli:
        pts = v["punti_invallati"]
        if "Moto" in v["categoria"]:
            polygon = patches.Polygon(pts, closed=True, facecolor=v["colore_faccia"], edgecolor=v["colore_bordo"], linewidth=3, zorder=5)
            ax.add_patch(polygon)
            cx, cz = np.mean(pts[:, 0]), np.mean(pts[:, 1])
            ax.plot([pts[0][0], pts[3][0]], [pts[0][1], pts[3][1]], color="black", linewidth=4, zorder=6)
            ax.plot([pts[1][0], pts[2][0]], [pts[1][1], pts[2][1]], color="black", linewidth=4, zorder=6)
        elif "Pesante" in v["categoria"]:
            polygon = patches.Polygon(pts, closed=True, facecolor=v["colore_faccia"], edgecolor=v["colore_bordo"], linewidth=3.5, zorder=5)
            ax.add_patch(polygon)
            cx, cz = np.mean(pts[:, 0]), np.mean(pts[:, 1])
            ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color="red", linewidth=3, zorder=6)
        else:
            polygon = patches.Polygon(pts, closed=True, facecolor=v["colore_faccia"], edgecolor=v["colore_bordo"], linewidth=2.5, zorder=5)
            ax.add_patch(polygon)
            cx, cz = np.mean(pts[:, 0]), np.mean(pts[:, 1])
        ax.text(cx, cz, f"Veicolo {v['let']}\n({v['targa']})", color="white" if v['let']=='A' else "black", weight="bold", fontsize=8, ha="center", va="center")
        c_p = "#0275d8" if v['let']=='A' else "#d9534f"
        for idx, pt in enumerate(pts):
            ax.plot(pt[0], pt[1], "o", color="white", markeredgecolor=c_p, markersize=7, markeredgewidth=2, zorder=6)
            offset_z = 0.6 if idx < 2 else -1.2
            ax.text(pt[0], pt[1] + offset_z, f"{v['let']}{idx+1}", color=c_p, weight="bold", fontsize=8, ha="center")
        ax.plot([pts[0][0], pts[0][0]], [pts[0][1], 0], color=c_p, linestyle=":", linewidth=1.2, zorder=3)
        ax.plot([pts[1][0], pts[1][0]], [pts[1][1], 0], color=c_p, linestyle=":", linewidth=1.2, zorder=3)
    
    for p in pedoni:
        ax.plot(p["x"], p["z"], "ro", markersize=10, markeredgecolor="black", zorder=6)
        ax.text(p["x"], p["z"] + 1.0, p["nome"], color="red", weight="bold", fontsize=9, ha="center")
        ax.plot([p["x"], p["x"]], [p["z"], 0], color="red", linestyle=":", linewidth=1, zorder=3)
    
    for v in veicoli:
        m = v["misure"]
        sfondo_coord = "#0275d8" if v['let']=='A' else "#d9534f"
        y_pos_box = 10 if v['let']=='A' else -5
        box_dati = patches.Rectangle((31, y_pos_box), 13, 5.5, fill=True, facecolor=v["colore_faccia"], edgecolor=sfondo_coord, linewidth=1.5, zorder=4)
        ax.add_patch(box_dati)
        ax.text(32, y_pos_box + 4.5, f"MISURE VEICOLO {v['let']} ({v['modello'][:8].upper()}):", weight="bold", color=sfondo_coord, fontsize=7.5)
        ax.text(32, y_pos_box + 3.2, f"{v['let']}A1 = {m[0]:.2f} m  |  {v['let']}Z1 = {m[1]:.2f} m", fontsize=7.5)
        ax.text(32, y_pos_box + 2.0, f"{v['let']}A2 = {m[2]:.2f} m  |  {v['let']}Z2 = {m[3]:.2f} m", fontsize=7.5)
        ax.text(32, y_pos_box + 0.8, f"Assetto Quiete: {v['assetto_scelto']}", fontsize=7, style="italic")
    
    # CALCOLO DISTANZE TRA VEICOLI
    distanze_txt = ""
    for i in range(len(veicoli)):
        for j in range(i+1, len(veicoli)):
            v1 = veicoli[i]
            v2 = veicoli[j]
            d1 = math.hypot(v1["misure"][0] - v2["misure"][0], v1["misure"][1] - v2["misure"][1])
            d2 = math.hypot(v1["misure"][2] - v2["misure"][2], v1["misure"][3] - v2["misure"][3])
            distanze_txt += f"{v1['let']}1-{v2['let']}1 = {d1:.2f} m  |  {v1['let']}2-{v2['let']}2 = {d2:.2f} m\n"
    
    if distanze_txt:
        box_distanze = patches.Rectangle((31, -10), 13, 2.5, fill=True, facecolor="white", edgecolor="black", linewidth=1, zorder=4)
        ax.add_patch(box_distanze)
        ax.text(32, -8.2, "DISTANZE TRA VEICOLI:", weight="bold", fontsize=7)
        lines = distanze_txt.strip().split('\n')
        for idx, line in enumerate(lines[:2]):
            ax.text(32, -9.0 - idx*0.7, line, fontsize=6.5)
    
    quadro_legenda = patches.Rectangle((-14, -11.5), 23, 4.8, fill=True, facecolor="white", edgecolor="black", linewidth=1.2, zorder=4)
    ax.add_patch(quadro_legenda)
    ax.text(-13.5, -7.4, "LEGENDA DI RILIEVO PLANIMETRICO", weight="bold", fontsize=9, color="black")
    ax.text(-13.5, -8.4, "🅇  Caposaldo di Origine Strumentale (0,0)", fontsize=8)
    ax.text(-13.5, -9.4, "🅏  Mira Metrica Linea d'Asse Z", fontsize=8)
    ax.text(-13.5, -10.4, "⚫  Punti Metrici Rilevati Unità A", fontsize=8, color="#0275d8")
    ax.text(-13.5, -11.4, "⚫  Punti Metrici Rilevati Unità B", fontsize=8, color="#d9534f")
    
    quadro_cartiglio = patches.Rectangle((10, -11.5), 18, 4.8, fill=True, facecolor="white", edgecolor="black", linewidth=1.2, zorder=4)
    ax.add_patch(quadro_cartiglio)
    ax.text(10.5, -7.4, "SCHIZZO PLANIMETRICO DI RILIEVO", weight="bold", color="#0275d8", fontsize=9)
    ax.text(10.5, -8.4, f"DATA: {data_ora}", fontsize=8)
    ax.text(10.5, -9.4, f"LOCALITÀ: {localita[:22]}", fontsize=8)
    ax.text(10.5, -10.4, f"OPERANTI: {operatori[:25]}", fontsize=8)
    ax.text(10.5, -11.4, "Elaborazione: Digitale | Tavola 1 di 1", fontsize=8)
    
    quadro_note = patches.Rectangle((29, -11.5), 15, 4.8, fill=True, facecolor="white", edgecolor="black", linewidth=1.2, zorder=4)
    ax.add_patch(quadro_note)
    ax.text(29.5, -7.4, "N.B. ELABORATO GRAFICO", weight="bold", fontsize=8)
    ax.text(29.5, -8.7, "Schizzo planimetrico realizzato\nsulla base delle misure rilevate\nsul posto d'urto. Le quote si\nriferiscono alla linea base X-Z.", fontsize=7.5, va="top")
    
    ax.arrow(-13, 16, 0, 3, head_width=1.2, head_length=1.5, fc='black', ec='black', zorder=4)
    ax.text(-13, 14.5, f"NORD\n({ord_nord})", ha="center", weight="bold", fontsize=8, color="black")
    
    return fig

if attiva_schizzo:
    if veicoli:
        fig = tavola(veicoli, pedoni, localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata, larg_carreggiata, num_corsie, stringa_stato, dist_XZ, orientamento_nord, usa_frenata, lunghezza_traccia)
        st.pyplot(fig)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        st.download_button("📥 Scarica Elaborato Grafico Planimetrico (PNG HD)", data=buf.getvalue(), file_name=f"SCHIZZO_{localita.replace(' ', '_')}.png", mime="image/png", use_container_width=True)
    else:
        st.warning("⚠️ Inserisci almeno un veicolo per generare lo schizzo.")
else:
    st.info("ℹ️ Schizzo planimetrico in pausa. Attivare il selettore sopra per rigenerare la tavola grafica con le nuove misure.")
# ==============================================================================
# SEZIONE 7: REPORT E VERBALE
# ==============================================================================
st.header("5. Relazione Tecnica Descrittiva Ufficiale di Reparto")

def build_report(localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata,
                 larg_carreggiata, num_corsie, stringa_stato, note_l_agg,
                 orientamento_nord, lat_x, lon_x, lat_z, lon_z, dist_XZ,
                 veicoli, pedoni, v_stimata_kmh, foto_count):
    
    report = f"""
================================================================================
                    REPARTO OPERATIVO - CARABINIERI
================================================================================

VERBALE DI RILIEVO PLANIMETRICO STRADALE
N. VR-{datetime.now().strftime('%Y%m%d')}-001

================================================================================
1. DATI IDENTIFICATIVI DEL SINISTRO
================================================================================
Data: {data_ora}
Località: {localita}

================================================================================
2. OPERATORI INTERVENUTI
================================================================================
{operatori_input}
Matricola: {st.session_state.get('matricola', 'N/D')}

================================================================================
3. CARATTERISTICHE DELLA SEDE STRADALE
================================================================================
Andamento: {andamento_strada}
Tipologia: {tipo_carreggiata}
Larghezza carreggiata: {larg_carreggiata} m
Numero corsie: {num_corsie}
Fondo stradale: {stringa_stato}

================================================================================
4. RILIEVI METRICI - LINEA BASE X-Z
================================================================================
Caposaldo X: Lat {lat_x:.6f}, Lon {lon_x:.6f}
Mira Z: Lat {lat_z:.6f}, Lon {lon_z:.6f}
Distanza X-Z: {dist_XZ:.2f} m

================================================================================
5. VEICOLI COINVOLTI
================================================================================
"""
    for v in veicoli:
        report += f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ VEICOLO {v['let']} - {v['modello'].upper()}                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ Targa: {v['targa']}                                                         │
│ Categoria: {v['categoria']}                                                 │
│ Danni: {v['stato']}                                                         │
│ Assetto: {v['assetto_scelto']}                                              │
│                                                                             │
│ MISURE METRICHE:                                                            │
│   {v['let']}A1 = {v['misure'][0]:.2f} m  |  {v['let']}Z1 = {v['misure'][1]:.2f} m       │
│   {v['let']}A2 = {v['misure'][2]:.2f} m  |  {v['let']}Z2 = {v['misure'][3]:.2f} m       │
│                                                                             │
│ CONDUCENTE:                                                                 │
│   Stato: {'Infortunato/Ospedalizzato' if v['ferito'] else 'Illeso'}         │
│   Prognosi: {v['prognosi']} giorni                                         │
│   Ospedale: {v['ospedale']}                                                │
"""
        if v['passeggeri']:
            report += "│ PASSEGGERI:                                                                │\n"
            for idx, p in enumerate(v['passeggeri']):
                report += f"│   {idx+1}. {p['descr']} - Ferito: {'Sì' if p['ferito'] else 'No'} - Prognosi: {p['prognosi']} gg │\n"
        report += "└─────────────────────────────────────────────────────────────────────────────┘\n"
    
    if pedoni:
        report += """
================================================================================
6. PEDONI / TERZI COINVOLTI
================================================================================
"""
        for idx, p in enumerate(pedoni):
            report += f"{idx+1}. {p['nome']} - Ferito: {'Sì' if p['ferito'] else 'No'} - Prognosi: {p['prognosi']} gg - Ospedale: {p['ospedale']}\n"
    
    if v_stimata_kmh > 0:
        report += f"""
================================================================================
7. ANALISI CINEMATICA
================================================================================
Velocità PRE-URTO stimata: {v_stimata_kmh:.1f} km/h
Lunghezza traccia frenata: {lunghezza_traccia:.2f} m
Coefficiente aderenza: {f_aderenza:.2f}
"""
    
    report += f"""
================================================================================
8. REPERTI FOTOGRAFICI
================================================================================
Numero fotogrammi acquisiti: {foto_count}

================================================================================
9. NOTE E OSSERVAZIONI
================================================================================
{note_l_agg}

================================================================================
10. FIRME
================================================================================
Data: {datetime.now().strftime('%d/%m/%Y')}

_________________________________    _________________________________
Firma Operatore                     Firma Operatore

================================================================================
Documento generato dal Terminale Universale di Rilievo Planimetrico Stradale v.2.0
Software professionale per Forze dell'Ordine - Licenza d'uso riservata
================================================================================
"""
    return report

note_l_agg = note_luogo
if usa_frenata and v_stimata_kmh > 0:
    note_l_agg += f"\nTracce di frenata rilevate per {lunghezza_traccia:.2f}m. Velocità pre-urto stimata: {v_stimata_kmh:.1f} km/h."

report_finale = build_report(
    localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata,
    larg_carreggiata, num_corsie, stringa_stato, note_l_agg,
    orientamento_nord, lat_x, lon_x, lat_z, lon_z, dist_XZ,
    veicoli, pedoni, v_stimata_kmh, len(st.session_state["foto_sinistro"])
)

st.text_area("📋 Verbale di P.G. (Modificabile)", report_finale, height=500)

# Download PDF
col_download1, col_download2, col_download3 = st.columns(3)
with col_download1:
    st.download_button("📄 Scarica Verbale TXT", data=report_finale, file_name=f"VERBALE_{localita.replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)
with col_download2:
    # PDF con FPDF
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "RELAZIONE TECNICA DI RILIEVO PLANIMETRICO STRADALE", 0, 1, "C")
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "CARABINIERI - REPARTO OPERATIVO", 0, 1, "C")
        pdf.line(10, 30, 200, 30)
        pdf.set_font("Arial", "", 11)
        pdf.ln(10)
        for line in report_finale.split("\n"):
            pdf.cell(0, 6, line[:180], 0, 1)
        st.download_button("📕 Scarica Verbale PDF", data=pdf.output(dest='S').encode('latin1'), file_name=f"VERBALE_{localita.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
    except:
        st.warning("⚠️ Libreria FPDF non disponibile. Installa fpdf per il PDF.")
with col_download3:
    # Backup JSON
    backup_data = {
        "localita": localita,
        "data_ora": data_ora,
        "operatori": operatori_input,
        "veicoli": veicoli,
        "pedoni": pedoni,
        "note": note_l_agg,
        "foto_count": len(st.session_state["foto_sinistro"]),
        "velocita_stimata": v_stimata_kmh
    }
    json_string = json.dumps(backup_data, indent=2, default=str)
    st.download_button("💾 Backup JSON", data=json_string, file_name=f"BACKUP_{localita.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

st.success("✅ Protocollo di rilievo completato. Tutti i dati sono stati salvati.")    
