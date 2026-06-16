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

# 1. IMPOSTAZIONI INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Forense", layout="wide")
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

st.warning("⚠️ **VERSIONE BETA IN VIA DI SVILUPPO** — Prototipo industriale per il rilievo stradale. I calcoli geometrici, le stime cinematiche e le acquisizioni hardware devono essere verificate dall'operatore prima dell'inserimento negli atti ufficiali.")
st.caption("© 2026 Tutti i diritti riservati. Proprietà intellettuale depositata. Modulo di geocoding OSM Nominatim e localizzazione hardware nativa integrati.")

# Inizializzazione della memoria di stato per i capisaldi e la via automatica
if "lat_x_real" not in st.session_state: st.session_state["lat_x_real"] = 40.019572
if "lon_x_real" not in st.session_state: st.session_state["lon_x_real"] = 18.118944
if "lat_z_real" not in st.session_state: st.session_state["lat_z_real"] = 40.019590
if "lon_z_real" not in st.session_state: st.session_state["lon_z_real"] = 18.119230
if "strada_bloccata" not in st.session_state: st.session_state["strada_bloccata"] = ""

DIZIONARIO_SEGMENTI = {
    "🚗 Autovettura Utilitaria / Media": {"w": 1.65, "l": 3.85, "t": "auto"}, 
    "🚙 SUV / Berlina Lunga / Furgone": {"w": 1.90, "l": 4.65, "t": "auto"}, 
    "🏍️ Motociclo / Ciclomotore (Mozzo Ant./Post.)": {"w": 0.80, "l": 2.10, "t": "moto"}, 
    "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50, "t": "auto"}
}

# Trasformatore WGS84 -> UTM Zona 33N (Italia centro-meridionale)
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
    if lunghezza_vec == 0: 
        return np.array([[x_ant, z_ant], [x_ant + larghezza, z_ant], [x_ant + larghezza, z_ant + lunghezza], [x_ant, z_ant + lunghezza]])
    ux, uz = dx / lunghezza_vec, dz / lunghezza_vec
    nx, nz = -uz, ux
    p1 = np.array([x_ant, z_ant])
    p2 = p1 + larghezza * np.array([nx, nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    return np.array([p1, p2, p3, p4])

def estrai_testo_ocr(file):
    if file is None:
        return ""
    try:
        img = Image.open(file)
        return pytesseract.image_to_string(img, lang="ita+eng")
    except Exception as e:
        return f"OCR non disponibile: {e}"

def pulisci_testo_documento(testo):
    t = testo.upper()
    out = {}
    targa = re.search(r"\b[A-Z]{2}\d{3}[A-Z]{2}\b", t)
    if targa:
        out["targa"] = targa.group(0)
    nome = re.search(r"(NOME|COGNOME)\s*[:-]?\s*([A-ZÀ-Ü' ]{3,})", t)
    if nome:
        out["nome"] = nome.group(2).strip()
    return out

def recupera_toponomastica_reale(lat, lon):
    url = "https://openstreetmap.org"
    params = {"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1}
    headers = {"User-Agent": "TerminaleRilievoForense/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        dati = r.json()
        addr = dati.get("address", {})
        via = addr.get("road") or addr.get("pedestrian") or addr.get("suburb") or "Via non classificata"
        comune = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or "Comune non rilevato"
        return f"{via}, {comune}"
    except Exception:
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
    if st.session_state["strada_bloccata"] == "" or st.session_state["strada_bloccata"] == "SP55 Matino-Taviano":
        st.session_state["strada_bloccata"] = recupera_toponomastica_reale(posizione_reale[0], posizione_reale[1])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano"

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
operatori_input = st.text_input("Operatori di Polizia Stradale", value="Ass. Capo Rossi, Ag. Scelti Bianchi")

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
        st.session_state["strada_bloccata"] = recupera_toponomastica_reale(posizione_reale[0], posizione_reale[1])
        st.rerun()
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")
with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z") and posizione_reale:
        st.session_state["lat_z_real"] = posizione_reale[0]
        st.session_state["lon_z_real"] = posizione_reale[1]
        st.session_state["strada_bloccata"] = recupera_toponomastica_reale(posizione_reale[0], posizione_reale[1])
        st.rerun()
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_calcolata = calcola_distanza_utm(lat_x, lon_x, lat_z, lon_z)
if dist_calcolata < 0.1: dist_calcolata = 25.05
dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, value=float(round(dist_calcolata, 2)))
st.header("2. Censimento Unità Coinvolte e Rilievi Metrici")

num_veicoli = st.selectbox("Numero totale veicoli da censire", options=[1, 2, 3, 4, 5], index=1)

elenco_veicoli = []
for k in range(num_veicoli):
    let = chr(65 + k)  # Genera A, B, C...
    st.markdown(f"### 🚗 Unità Veicolare {let}")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        categoria = st.selectbox(f"Categoria Mezzo {let}", options=list(DIZIONARIO_SEGMENTI.keys()), key=f"cat_{k}")
        modello = st.text_input(f"Marca e Modello {let}", value=f"Veicolo {let}", key=f"mod_{k}")
        targa = st.text_input(f"Targa / Telaio {let}", value=f"{let}{let}123{let}{let}", key=f"targ_{k}").upper()
        stato_mezzo = st.selectbox(f"Stato Mezzo {let}", options=["Fermo / Incolume", "Incarrozzato / Distrutto", "Proiettato fuori sede stradale"], key=f"stat_{k}")
    
    with col_v2:
        lat_v = st.number_input(f"Latitudine Posizione Finale {let}", value=lat_x + (k * 0.0001), format="%.6f", key=f"lat_v_{k}")
        lon_v = st.number_input(f"Longitudine Posizione Finale {let}", value=lon_x + (k * 0.0001), format="%.6f", key=f"lon_v_{k}")
        tipo_forma = st.radio(f"Rappresentazione Grafica {let}", options=["Rettangolo", "Punto"], key=f"form_{k}")
    
    st.markdown(f"#### 📐 Rilievi Metrici (Metodo delle Coordinate Ortogonali) per Veicolo {let}")
    st.write("Inserire le distanze misurate partendo dal Caposaldo X (0,0) lungo la linea di base X-Z.")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        vx1 = st.number_input(f"Punto A (Anteriore) - Distanza Asse X (m) {let}", value=5.2 + (k * 6), key=f"vx1_{k}")
        vz1_in = st.number_input(f"Punto A (Anteriore) - Scostamento Asse Z (m) {let}", value=1.8, key=f"vz1_{k}")
        vlato1 = st.radio(f"Lato Punto A {let}", ["Destra", "Sinistra '-'"], key=f"vlat1_{k}")
        vz1 = -vz1_in if "Sinistra" in vlato1 else vz1_in
        
    with col_m2:
        vx2 = st.number_input(f"Punto B (Posteriore) - Distanza Asse X (m) {let}", value=2.1 + (k * 6), key=f"vx2_{k}")
        vz2_in = st.number_input(f"Punto B (Posteriore) - Scostamento Asse Z (m) {let}", value=1.5, key=f"vz2_{k}")
        vlato2 = st.radio(f"Lato Punto B {let}", ["Destra", "Sinistra '-'"], key=f"vlat2_{k}")
        vz2 = -vz2_in if "Sinistra" in vlato2 else vz2_in

    punti_v = np.array([[vx1, vz1], [vx2, vz2]])

    # 📁 Sezione Documenti e OCR Veicolo
    st.markdown("##### 📁 Caricamento Documenti Conducente e Veicolo (OCR)")
    doc_patente = st.file_uploader(f"Patente conducente {let}", type=["jpg", "jpeg", "png"], key=f"pat_{k}")
    doc_carta = st.file_uploader(f"Carta circolazione {let}", type=["jpg", "jpeg", "png"], key=f"lib_{k}")
    doc_ass = st.file_uploader(f"Assicurazione RCA {let}", type=["jpg", "jpeg", "png"], key=f"ass_{k}")

    if f"ocr_veicolo_{k}" not in st.session_state:
        st.session_state[f"ocr_veicolo_{k}"] = {"patente": "", "carta": "", "assicurazione": "", "estratto": {}}

    if st.button(f"🔎 Leggi documenti Veicolo {let}", key=f"ocr_btn_{k}", use_container_width=True):
        with st.spinner("Estrazione testo in corso..."):
            testo_pat = estrai_testo_ocr(doc_patente)
            testo_lib = estrai_testo_ocr(doc_carta)
            testo_ass = estrai_testo_ocr(doc_ass)
            testo_tot = "\n".join([testo_pat, testo_lib, testo_ass])
            st.session_state[f"ocr_veicolo_{k}"] = {
                "patente": testo_pat,
                "carta": testo_lib,
                "assicurazione": testo_ass,
                "estratto": pulisci_testo_documento(testo_tot)
            }

    ocr_v = st.session_state[f"ocr_veicolo_{k}"]
    col_ocr_txt = st.columns(3)
    with col_ocr_txt[0]:
        st.text_area(f"Testo OCR patente {let}", value=ocr_v["patente"], height=100, key=f"ocr_pat_txt_{k}")
    with col_ocr_txt[1]:
        st.text_area(f"Testo OCR carta circolazione {let}", value=ocr_v["carta"], height=100, key=f"ocr_lib_txt_{k}")
    with col_ocr_txt[2]:
        st.text_area(f"Testo OCR assicurazione {let}", value=ocr_v["assicurazione"], height=100, key=f"ocr_ass_txt_{k}")
        
    st.write("**Dati rilevati da analisi semantica:**")
    st.json(ocr_v["estratto"])

    # 🩹 Stato Sanitario Conducente
    st.markdown("##### 🩹 Stato del Conducente")
    col_cond_s1, col_cond_s2 = st.columns(2)
    with col_cond_s1:
        flag_cond_ferito = st.checkbox(f"Il Conducente {let} ha riportato lesioni (Ferito)", key=f"c_fer_{k}")
        prognosi_cond = st.number_input(f"Prognosi Conducente {let} (giorni)", min_value=0, max_value=365, value=0, key=f"c_prog_{k}")
    with col_cond_s2:
        ospedale_cond = st.text_input(f"Ospedale trasporto Conducente {let}", value="Vito Fazzi - Lecce" if flag_cond_ferito else "Nessuno", key=f"osp_c_{k}")

    # 👥 Passeggeri del Veicolo
    st.markdown(f"##### 👥 Passeggeri Trasportati (Veicolo {let})")
    num_pass = st.number_input(f"Numero passeggeri su Veicolo {let}", min_value=0, max_value=10, value=0, key=f"n_p_{k}")
    elenco_pass_v = []
    
    for p in range(num_pass):
        st.write(f"↳ *Passeggero {p+1} (Mezzo {let})*")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            foto_doc = st.file_uploader(f"📸 Documento Pass. {p+1}", type=["jpg", "png", "jpeg"], key=f"dc_{k}_{p}")
            f_p = st.checkbox(f"🩹 Ferito", key=f"p_fer_{k}_{p}")
        with col_p2:
            o_p = st.text_input(f"Ospedale trasporto Pass. {p+1}", value="Vito Fazzi - Lecce" if f_p else "Nessuno", key=f"osp_p_{k}_{p}")
            prog_p = st.number_input(f"Prognosi (giorni) Pass. {p+1}", min_value=0, max_value=365, value=0, key=f"p_prog_{k}_{p}")

        if f"ocr_pass_{k}_{p}" not in st.session_state:
            st.session_state[f"ocr_pass_{k}_{p}"] = ""
        if st.button(f"🔎 Leggi documento Pass. {p+1}", key=f"ocr_pass_btn_{k}_{p}"):
            st.session_state[f"ocr_pass_{k}_{p}"] = estrai_testo_ocr(foto_doc)

        st.text_area(f"Testo OCR Pass. {p+1}", value=st.session_state[f"ocr_pass_{k}_{p}"], height=80, key=f"ocr_pass_txt_{k}_{p}")

        elenco_pass_v.append({
            "descr": f"Passeggero {p+1}",
            "ferito": f_p,
            "prognosi": prog_p,
            "ospedale": o_p,
            "ocr": st.session_state[f"ocr_pass_{k}_{p}"]
        })

    elenco_veicoli.append({
        "let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "punti": punti_v,
        "misure_base": [vx1, vz1], "ocr": ocr_v, "passeggeri": elenco_pass_v, "stato": stato_mezzo,
        "forma": tipo_forma, "categoria": categoria, "ferito": flag_cond_ferito, "prognosi": prognosi_cond,
        "ospedale": ospedale_cond, "estratto_auto": ocr_v["estratto"]
    })
    st.divider()

# 🚶 Sezione Pedoni e Ostacoli Fissi
st.header("3. Censimento Pedoni / Ostacoli Fissi")
num_pedoni = st.selectbox("Quanti pedoni o ostacoli fissi vuoi registrare?", options=[0, 1, 2, 3, 4, 5], index=0)
elenco_pedoni = []

for kp in range(num_pedoni):
    st.write(f"🔹 **Pedone / Ostacolo {kp + 1}**")
    col_pe1, col_pe2 = st.columns(2)
    with col_pe1:
        ped_nome = st.text_input(f"Nome Pedone / Tipo Ostacolo {kp+1}", value=f"Pedone {kp+1}", key=f"p_nom_{kp}")
        ped_doc = st.file_uploader(f"📸 Documento Pedone {kp+1}", type=["jpg", "png", "jpeg"], key=f"ped_doc_{kp}")
        ped_ferito = st.checkbox(f"🩹 Ferito / Danneggiato", value=False, key=f"p_fr_{kp}")
    with col_pe2:
        ped_prog = st.number_input(f"Prognosi (giorni) Pedone {kp+1}", min_value=0, max_value=365, value=0, key=f"p_prog_{kp}")
        ped_osp = st.text_input(f"Ospedale trasporto Pedone {kp+1}", value="Vito Fazzi - Lecce" if ped_ferito else "Nessuno", key=f"p_osp_{kp}")
        ped_x = st.number_input(f"Distanza Asse X (m) Ostacolo {kp+1}", value=10.0 + (kp * 2), key=f"p_x_{kp}")
        ped_z_in = st.number_input(f"Scostamento Asse Z (m) Ostacolo {kp+1}", value=2.5, key=f"p_z_{kp}")
        ped_lato = st.radio(f"Lato Ostacolo {kp+1}", ["Destra", "Sinistra '-'"], key=f"p_lt_{kp}")
        ped_z = -ped_z_in if "Sinistra" in ped_lato else ped_z_in

    if f"ocr_ped_{kp}" not in st.session_state:
        st.session_state[f"ocr_ped_{kp}"] = ""
    if st.button(f"🔎 Leggi documento Pedone {kp+1}", key=f"ocr_ped_btn_{kp}"):
        st.session_state[f"ocr_ped_{kp}"] = estrai_testo_ocr(ped_doc)

    st.text_area(f"Testo OCR Pedone {kp+1}", value=st.session_state[f"ocr_ped_{kp}"], height=80, key=f"ocr_ped_txt_{kp}")

    elenco_pedoni.append({
        "nome": ped_nome, "x": ped_x, "z": ped_z, "ferito": ped_ferito,
        "prognosi": ped_prog, "ospedale": ped_osp, "ocr": st.session_state[f"ocr_ped_{kp}"]
    })
     # =========================================================
# 🎨 4. MOTORE GRAFICO PLANIMETRICO E RELAZIONE FORENSE
# =========================================================
st.header("4. Elaborazione Grafica e Relazione Descrittiva Ufficiale")

def genera_tavola_grafica(elenco_veicoli, elenco_pedoni, localita, data_ora, operatori, note_luogo, larg_carreggiata, dist_XZ):
    fig, ax = plt.subplots(figsize=(15, 8))
    plt.subplots_adjust(right=0.72, left=0.06, top=0.94, bottom=0.10)
    
    ax.set_facecolor("#F2F2F2")
    ax.grid(True, which="both", color="#D3D3D3", linestyle="--", linewidth=0.5)
    
    # Rappresentazione dei Capisaldi Metrici Strumentali
    ax.plot(0, 0, "ro", markersize=10, markeredgecolor="black", label="Caposaldo Origine X (0,0)")
    ax.text(-0.5, -0.6, "X (0,0)", color="red", fontweight="bold", fontsize=10)
    
    ax.plot(dist_XZ, 0, "bo", markersize=10, markeredgecolor="black", label=f"Mira Linea Base Z ({dist_XZ}m)")
    ax.text(dist_XZ - 1.0, -0.6, f"Z ({dist_XZ}m)", color="blue", fontweight="bold", fontsize=10)
    
    # Tracciamento della Linea di Base Fondamentale del Rilievo
    ax.plot([0, dist_XZ], [0, 0], "k--", linewidth=1.5, alpha=0.7)
    
    # Rappresentazione della Sede Stradale (Carreggiata Simulata)
    limite_superiore = larg_carreggiata
    limite_inferiore = -larg_carreggiata
    ax.axhline(y=limite_superiore, color="#404040", linestyle="-", linewidth=2.5, label="Margini Carreggiata")
    ax.axhline(y=limite_inferiore, color="#404040", linestyle="-", linewidth=2.5)
    ax.axhline(y=0, color="#808080", linestyle=":", linewidth=1.0)
    
    # 🚗 DISEGNO DELLE UNITÀ VEICOLARI IN SCALA
    for v in elenco_veicoli:
        p_ant = v["punti"][0] # [x, z] anteriore
        p_post = v["punti"][1] # [x, z] posteriore
        let = v["let"]
        
        dim = DIZIONARIO_SEGMENTI.get(v["categoria"], {"w": 1.80, "l": 4.20})
        w, l = dim["w"], dim["l"]
        
        ax.plot(p_ant[0], p_ant[1], "go", markersize=6, markeredgecolor="black")
        ax.plot(p_post[0], p_post[1], "go", markersize=6, markeredgecolor="black")
        ax.text(p_ant[0], p_ant[1] + 0.2, f"{let}1", color="green", fontweight="bold", fontsize=9)
        ax.text(p_post[0], p_post[1] + 0.2, f"{let}2", color="green", fontweight="bold", fontsize=9)
        
        # Linee di quota
        ax.plot([p_ant[0], p_ant[0]], [0, p_ant[1]], color="green", linestyle=":", alpha=0.5)
        ax.plot([p_post[0], p_post[0]], [0, p_post[1]], color="green", linestyle=":", alpha=0.5)
        
        ax.text(p_ant[0], p_ant[1]/2, f"{abs(p_ant[1]):.2f}m", color="darkgreen", fontsize=8
                
