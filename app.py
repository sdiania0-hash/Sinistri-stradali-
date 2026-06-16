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

# =========================================================
# CONFIGURAZIONE GENERALE DELL'INTERFACCIA WEB FORENSE
# =========================================================
st.set_page_config(page_title="Terminale Rilievo Forense Pro", layout="wide")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense Pro")

UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

defaults = {
    "autenticato": False,
    "lat_x_real": 40.019572,
    "lon_x_real": 18.118944,
    "lat_z_real": 40.019590,
    "lon_z_real": 18.119230,
    "strada_bloccata": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# GATEWAY DI AUTENTICAZIONE PROTETTO (IMMUNE A ERRORI TASTIERA SMARTPHONE)
# =========================================================
if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato - Operatori di Polizia Stradale")
    u = st.text_input("Identificativo Nome Utente (ID)")
    p = st.text_input("Chiave di Accesso (Password)", type="password")

    if st.button("Sblocca Terminale Operativo", type="primary", use_container_width=True):
        if u.strip().lower() == UTENTE_CORRETTO and p.strip() == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("❌ Credenziali errate o non autorizzate nel sistema centrale.")
    st.stop()

st.warning("⚠️ VERSIONE BETA PROFESSIONALE - Sistema integrato per l'acquisizione planimetrica digitale forense.")

DIZIONARIO_SEGMENTI = {
    "🚗 Citroën C3 (Auto Utilitaria)": {"w": 1.75, "l": 3.99},
    "🚗 Alfa Romeo 147 (Berlina)": {"w": 1.73, "l": 4.22},
    "🚙 SUV / Furgone Commerciale": {"w": 1.90, "l": 4.65},
    "🏍️ Motociclo (Ciclomotore)": {"w": 0.80, "l": 2.10},
    "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50}
}

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

# =========================================================
# ENGINE LOGICO ED ESTRAZIONE SEGNALI/DOCUMENTI
# =========================================================
def gps_to_utm(lat, lon):
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
        return f"OCR non configurato sul server: {e}"

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
            "https://openstreetmap.org",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1},
            headers={"User-Agent": "RilievoForense/1.0"},
            timeout=8
        )
        r.raise_for_status()
        j = r.json()
        a = j.get("address", {})
        road = a.get("road") or a.get("pedestrian") or a.get("suburb") or "SP55 Matino-Taviano"
        comune = a.get("city") or a.get("town") or a.get("village") or "Matino"
        return f"{road}, {comune}"
    except:
        return "SP55 Matino-Taviano, Matino"
     def calcola_rettangolo_veicolo_utm(x_ant, z_ant, x_post, z_post, larghezza, lunghezza):
    dx = x_ant - x_post
    dz = z_ant - z_post
    lunghezza_vec = math.hypot(dx, dz)
    if lunghezza_vec == 0:
        return np.array([
            [x_ant - larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant - lunghezza],
            [x_ant - larghezza/2, z_ant - lunghezza]
        ])
    ux, uz = dx / lunghezza_vec, dz / lunghezza_vec
    nx, nz = -uz, ux
    p1 = np.array([x_ant - (larghezza/2)*nx, z_ant - (larghezza/2)*nz])
    p2 = np.array([x_ant + (larghezza/2)*nx, z_ant + (larghezza/2)*nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    return np.array([p1, p2, p3, p4])

# =========================================================
# FUNZIONE TAVOLA GRAFICA SU SCALA METRICA AVANZATA
# =========================================================
def tavola(veicoli, pedoni, localita, data_ora, operatori, andamento, tipo_c, larg_c, num_c, stato_a, dist_xz):
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(-15, 45)
    ax.set_ylim(-5, 35)
    ax.set_aspect('equal')
    ax.axis("on")
    ax.grid(True, linestyle=":", alpha=0.5)

    # Rendering strutturale della sede stradale (Asfalto scuro)
    strada_sfondo = patches.Rectangle((-15, -1), 60, larg_c + 2, facecolor="#333333", alpha=0.95, zorder=1)
    ax.add_patch(strada_sfondo)

    # Disegno dei margini esterni continui di carreggiata
    ax.plot([-15, 45], [0, 0], color="white", linewidth=3.5, zorder=2)
    ax.plot([-15, 45], [larg_c, larg_c], color="white", linewidth=3.5, zorder=2)

    # Disegno delle linee tratteggiate di corsia interne parametrizzate
    if num_c > 1:
        passo_corsia = larg_c / num_c
        for nc in range(1, num_c):
            ax.plot([-15, 45], [passo_corsia*nc, passo_corsia*nc], color="white", linestyle="--", linewidth=1.5, zorder=2)

    # Posizionamento e simbologia Forense dei due Capisaldi di Riferimento Metrico
    ax.plot(0, 0, "X", color="#f0ad4e", markersize=12, label="Caposaldo X (Origine)", zorder=5)
    ax.text(-1, -1.8, "Caposaldo X\n(Punto Fisso)", color="#f0ad4e", fontweight="bold", fontsize=9, ha="center")

    ax.plot(dist_xz, 0, "X", color="#f0ad4e", markersize=12, label="Mira Z", zorder=5)
    ax.text(dist_xz, -1.8, "Mira Z\n(Orientamento)", color="#f0ad4e", fontweight="bold", fontsize=9, ha="center")

    # Tracciamento dell'asse di misurazione metrica X-Z
    ax.plot([0, dist_xz], [0, 0], color="#f0ad4e", linestyle="-.", linewidth=1.5, alpha=0.9, zorder=2)
    ax.text(dist_xz/2, -0.8, f"Linea Base X-Z = {dist_xz:.2f} metri", color="#f0ad4e", fontsize=9, ha="center", fontweight="bold")

    # Rendering planimetrico dei veicoli con calcolo reale dei 4 vertici d'ingombro
    for v in veicoli:
        pts = v["punti_invallati"]
        polygon = patches.Polygon(pts, closed=True, facecolor=v["colore_faccia"], edgecolor=v["colore_bordo"], linewidth=2, alpha=0.85, zorder=4)
        ax.add_patch(polygon)
        
        cx = np.mean(pts[:, 0])
        cz = np.mean(pts[:, 1])
        ax.text(cx, cz, f"Veicolo {v['let']}\n({v['targa']})", color="white", fontweight="bold", fontsize=8, ha="center", va="center")
        
        # Plot dei punti di collisione (Es: A1, A2, B1, B2)
        for idx, pt in enumerate(pts[:2]):
            ax.plot(pt[0], pt[1], "o", color="cyan", markersize=6, zorder=5)
            ax.text(pt[0], pt[1]+0.4, f"{v['let']}{idx+1}", color="cyan", fontsize=8, fontweight="bold", ha="center")

    # Tracciamento planimetrico reale dei pedoni
    for p in pedoni:
        ax.plot(p["x"], p["z"], "ro", markersize=9, zorder=5)
        ax.text(p["x"], p["z"] + 0.8, p["nome"], color="red", fontweight="bold", fontsize=9, ha="center")

    ax.set_title(f"PLANIMETRIA FORENSE SCALATA - {localita.upper()}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Asse Metrico Longitudinale Z (metri Avanzamento da X)")
    ax.set_ylabel("Asse Metrico Ortogonale X (metri Scostamento da X)")
    return fig
     def build_report(localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata, larg_carreggiata, num_corsie, stato_asfalto, note_luogo, orientamento_nord, lat_x, lon_x, lat_z, lon_z, dist_XZ, elenco_veicoli, elenco_pedoni):
    testo = f"""==================================================================
VERBALE DI RILIEVO DESCRITTIVO E PLANIMETRICO STRADALE FORENSE
==================================================================
Organo Procedente: Polizia Stradale - Terminale Forense Digitale
Data / Ora Sopralluogo: {data_ora}
Località / Toponomastica: {localita}
Operatori verbalizzanti: {operatori_input}

CONDIZIONI AMBIENTALI E STATO DEI LUOGHI:
Andamento Planimetrico: {andamento_strada} | Struttura: {tipo_carreggiata}
Larghezza Sede Stradale: {larg_carreggiata} metri | Corsie disponibili: {num_corsie}
Stato del Fondo Stradale: {stato_asfalto} | Note tecniche: {note_luogo}

DATI STRUMENTALI E CAPISALDI METRICI DELLA LINEA DI BASE:
- Caposaldo d'Origine X (0,0): Latitud. {lat_x:.6f} | Longitud. {lon_x:.6f}
- Mira di Orientamento Z: Latitud. {lat_z:.6f} | Longitud. {lon_z:.6f}
- Distanza asse geoide X-Z: {dist_XZ:.2f} metri | Orientamento Base: {orientamento_nord}

CENSIMENTO DETTAGLIATO UNITÀ COINVOLTE, REPERTI E STATO SANITARIO:
"""
    for v in elenco_veicoli:
        testo += f"\n▶️ VEICOLO {v['let']} - Modello: {v['modello']} | Targa: {v['targa']}\n"
        testo += f"  - Localizzazione GPS: Lat: {v['lat']:.6f}, Lon: {v['lon']:.6f}\n"
        testo += f"  - Stato Post-Urto: {v['stato']}\n"
        testo += f"  - Metriche d'Ingombro Rilevate: XA1={v['misure']:.2f}m, ZA1={v['misure']:.2f}m | XA2={v['misure']:.2f}m, ZA2={v['misure']:.2f}m\n"
        testo += f"  - Conducente: Ferito: {'SÌ' if v['ferito'] else 'NO'} | Prognosi: {v['prognosi']} gg | Struttura: {v['ospedale']}\n"
        testo += f"  - Estrazione OCR Documenti: {v['estratto_auto']}\n"
        if v["passeggeri"]:
            testo += f"  - Passeggeri registrati a bordo ({len(v['passeggeri'])}):\n"
            for passg in v["passeggeri"]:
                testo += f"    * {passg['descr']} | Ferito: {'SÌ' if passg['ferito'] else 'NO'} | Prognosi: {passg['prognosi']} gg\n"

    if elenco_pedoni:
        testo += "\n▶️ PEDONI / OSTACOLI FISSI REGISTRATI:\n"
        for idx, ped in enumerate(elenco_pedoni):
            testo += f"  - Soggetto/Target P{idx+1}: {ped['nome']}\n"
            testo += f"    * Posizione Metrica sul campo: X = {ped['x']:.2f} m, Z = {ped['z']:.2f} m\n"
            testo += f"    * Stato Sanitario: Ferito: {'SÌ' if ped['ferito'] else 'NO'} | Prognosi: {ped['prognosi']} gg | Ospedale: {ped['ospedale']}\n"
    else:
        testo += "\n▶️ PEDONI / OSTACOLI FISSI REGISTRATI: Nessuno\n"
        
    testo += f"\nNOTE CONCLUSIVE DI CHIUSURA FASCICOLO:\nIl presente rapporto costituisce riproduzione informatica di dati digitali acquisiti sul campo. Firma operatore: {operatori_input}."
    return testo
# =========================================================
# SEZIONE 1: INTERFACCIA UTENTE - PARAMETRI AMBIENTALI
# =========================================================
st.header("1. Protocollo di Acquisizione Dati sul Campo")
location = streamlit_geolocation()

if location and location.get("latitude") is not None and location.get("longitude") is not None:
    if st.session_state["strada_bloccata"] in ["", "SP55 Matino-Taviano"]:
        st.session_state["strada_bloccata"] = reverse_geo(location["latitude"], location["longitude"])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano"

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
operatori_input = st.text_input("Operatori di Polizia Stradale", value="Brig. Rima G., V.B. Rizzo V.")

col_strada1, col_strada2 = st.columns(2)
with col_strada1:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata", options=["Carreggiata unica a doppio senso", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata (Spartitraffico Centrale)"])
    larg_carreggiata = st.number_input("Larghezza della carreggiata stradale (m)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero corsie totali della carreggiata", options=[1, 2, 3, 4], index=1)
with col_strada2:
    stato_asfalto = st.selectbox("Stato del fondo stradale", options=["Asfalto asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Viscido / Fango (f=0.30)"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base (Direzione Caposaldo Z)", options=["Nord ⬆️", "Est ➡️", "Sud ⬇️", "Ovest ⬅️"])
    note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Condizioni di luce: diurna. Visibilità: buona. Presenza di intersezione.")

st.subheader("📐 Definizione dei Capisaldi di Riferimento Strumentale")
col_cx, col_cz = st.columns(2)
with col_cx:
    lat_x = st.number_input("Latitudine Caposaldo X (Origine 0,0)", format="%.6f", value=st.session_state["lat_x_real"])
    lon_x = st.number_input("Longitudine Caposaldo X (Origine 0,0)", format="%.6f", value=st.session_state["lon_x_real"])
with col_cz:
    lat_z = st.number_input("Latitudine Caposaldo Z (Asse Metrico)", format="%.6f", value=st.session_state["lat_z_real"])
    lon_z = st.number_input("Longitudine Caposaldo Z (Asse Metrico)", format="%.6f", value=st.session_state["lon_z_real"])

dist_XZ = distanza(lat_x, lon_x, lat_z, lon_z)
st.write("Distanza base calcolata:", round(dist_XZ, 2), "m")

# =========================================================
# SEZIONE 2: ACQUISIZIONE DINAMICA VEICOLI COINVOLTI
# =========================================================
st.header("2. Veicoli")
n = st.selectbox("Numero veicoli coinvolti", [1, 2, 3, 4, 5], index=1)
veicoli = []

for i in range(n):
    let = chr(65 + i)
    st.subheader(f"📦 Configurazione Avanzata Veicolo {let}")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        cat = st.selectbox("Categoria e Modello Strutturale", list(DIZIONARIO_SEGMENTI.keys()), key=f"cat_{i}", index=i if i < 2 else 0)
        mod = st.text_input("Marca e Modello Esteso", value="Citroën C3" if i==0 else "Alfa Romeo 147", key=f"mod_{i}")
        targa = st.text_input("Targa del Veicolo", value="AA123BB" if i==0 else "CC456DD", key=f"targa_{i}").upper()
        stato_v = st.text_input("Stato Post-Urto", value="Gravi danni anteriori", key=f"stato_{i}")
    with col_v2:
        latv = st.number_input("Latitudine Quiete GPS", key=f"latv_{i}", value=lat_x, format="%.6f")
        lonv = st.number_input("Longitudine Quiete GPS", key=f"lonv_{i}", value=lon_x, format="%.6f")
        doc = st.file_uploader("Carica Patente / Libretto (Analisi OCR)", key=f"doc_{i}")
    with col_v3:
        ferito_v = st.checkbox("Conducente Ospedalizzato", key=f"fer_{i}")
        prog_v = st.number_input("Prognosi Riscontrata (giorni)", min_value=0, value=0, key=f"prog_{i}")
        ospedale_v = st.text_input("Struttura Sanitaria", value="Nessuno", key=f"osp_{i}")

    st.markdown(f"**📐 Rilevamenti Metrici dal Campo (Misure Veicolo {let})**")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: xa = st.number_input("XA1 (Avanzamento Ant.)", value=16.60 if i==0 else 16.30, key=f"xa_{i}")
    with col_m2: za = st.number_input("ZA1 (Scostamento Ant.)", value=11.55 if i==0 else 10.55, key=f"za_{i}")
    with col_m3: xp = st.number_input("XA2 (Avanzamento Post.)", value=18.20 if i==0 else 18.05, key=f"xp_{i}")
    with col_m4: zp = st.number_input("ZA2 (Scostamento Post.)", value=11.00 if i==0 else 8.70, key=f"zp_{i}")

    ocr_txt = ocr(doc)
    parsed = parse_doc(ocr_txt)

    if parsed.get("targa"): st.success(f"🔍 Targa rilevata OCR per {let}: {parsed['targa']}")
    if parsed.get("nome"): st.success(f"🔍 Nominativo rilevato OCR per {let}: {parsed['nome']}")

    dim = DIZIONARIO_SEGMENTI[cat]
    punti_invallati = calcola_rettangolo_veicolo_utm(xa, za, xp, zp, dim["w"], dim["l"])
    col_faccia = "#add8e6" if i==0 else "#d3d3d3"
    col_bordo = "blue" if i==0 else "black"

    st.markdown(f"*Registro Passeggeri Trasportati a bordo del Veicolo {let}*")
    num_pass = st.number_input(f"Numero di passeggeri - Veicolo {let}", min_value=0, max_value=4, value=0, key=f"npass_{i}")
    passeggeri_lista = []
    for p_idx in range(int(num_pass)):
        col_ps1, col_ps2, col_ps3 = st.columns(3)
        with col_ps1: descr_p = st.text_input("Generalità Passeggero", value=f"Passeggero {p_idx+1}", key=f"dps_{i}_{p_idx}")
        with col_ps2: ferito_p = st.checkbox("Ferito", key=f"fps_{i}_{p_idx}")
        with col_ps3: prog_p = st.number_input("Prognosi", min_value=0, value=0, key=f"pps_{i}_{p_idx}")
        passeggeri_lista.append({"descr": descr_p, "ferito": ferito_p, "prognosi": prog_p})

    veicoli.append({
        "let": let, "modello": mod, "targa": targa, "categoria": cat, "lat": latv, "lon": lonv,
        "stato": stato_v, "ferito": ferito_v, "prognosi": prog_v, "ospedale": ospedale_v, "misure": [xa, za, xp, zp],
        "punti_invallati": punti_invallati, "colore_faccia": col_faccia, "colore_bordo": col_bordo,
        "estratto_auto": parsed if parsed else "Nessuno", "passeggeri": passeggeri_lista
    })
# =========================================================
# SEZIONE 3: ACQUISIZIONE DINAMICA PEDONI ED OSTACOLI FISSI
# =========================================================
st.header("3. Pedoni / Strutture / Terzi Coinvolti")
pnum = st.selectbox("Numero pedoni o ostacoli fissi da censire", [0, 1, 2, 3, 4, 5], index=0)
pedoni = []

for i in range(pnum):
    st.markdown(f"##### 🚶 Target Pedone/Ostacolo P{i+1}")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        nome_p = st.text_input("Identificativo / Nome", value=f"Soggetto P{i+1}", key=f"pn_{i}")
        ferito_p = st.checkbox("Soggetto Infortunato", key=f"fped_{i}")
    with col_p2:
        x_p = st.number_input("Distanza Ortogonale X (m)", value=1.50, format="%.2f", key=f"px_{i}")
    with col_p3:
        z_p = st.number_input("Avanzamento Base Z (m)", value=12.00, format="%.2f", key=f"pz_{i}")
    with col_p4:
        prog_p = st.number_input("Prognosi (gg)", min_value=0, value=0, key=f"pped_{i}")
        osp_p = st.text_input("Struttura Sanitaria Ricovero", value="Nessuno", key=f"osped_{i}")
        
    pedoni.append({"nome": nome_p, "x": x_p, "z": z_p, "ferito": ferito_p, "prognosi": prog_p, "ospedale": osp_p})

# =========================================================
# MODULO CINEMATICO-FORENSE (ANALISI AVANZATA DELLA VELOCITÀ)
# =========================================================
st.header("💥 Analisi Cinematica Forense (Stima Velocità Pre-Urto)")
st.markdown("*Calcolo ricostruttivo basato sulla formula di Searle per la dissipazione dell'energia cinetica:*")

col_cine1, col_cine2 = st.columns(2)
with col_cine1:
    usa_frenata = st.checkbox("Presenza di tracce di frenata / scarrocciamento sul fondo asfaltato")
    lunghezza_traccia = st.number_input("Lunghezza della traccia di frenata rilevata L (m)", min_value=0.0, max_value=200.0, value=15.50)
with col_cine2:
    pendenza_strada = st.number_input("Pendenza longitudinale della strada p (%) (+ salita, - discesa)", min_value=-20.0, max_value=20.0, value=0.0)
    velocita_impatto = st.number_input("Stima della velocità residua al momento dell'urto V_URTO (km/h)", min_value=0.0, max_value=200.0, value=30.0)

# Mappatura sicura ed esente da NameError per l'aderenza stradale f
aderenza_mappa = {
    "Asfalto asciutto (f=0.75)": 0.75, 
    "Asfalto Bagnato (f=0.45)": 0.45, 
    "Viscido / Fango (f=0.30)": 0.30
}
stringa_stato = stato_asfalto if 'stato_asfalto' in locals() else "Asfalto asciutto (f=0.75)"
f_aderenza = aderenza_mappa.get(stringa_stato, 0.75)

v_stimata_kmh = 0.0
if usa_frenata and lunghezza_traccia > 0:
    p_dec = pendenza_strada / 100.0
    g_costante = 9.81
    v_urto_ms = velocita_impatto / 3.6
    quadrato_v = (v_urto_ms ** 2) + (2 * g_costante * lunghezza_traccia * (f_aderenza + p_dec))
    if quadrato_v > 0:
        v_stimata_kmh = math.sqrt(quadrato_v) * 3.6
    st.success(f"🧮 Velocità iniziale stimata alle tracce di frenata: **{v_stimata_kmh:.1f} km/h**")
    if v_stimata_kmh > 50.0:
         st.error("⚠️ Il veicolo analizzato superava il limite di velocità standard urbano (50 km/h).")

# =========================================================
# 4. ELABORAZIONE E RENDERING TAVOLA PLANIMETRICA SCALATA
# =========================================================
st.header("4. Elaborazione e Generazione Tavola Planimetrica")

fig = tavola(
    veicoli=veicoli, pedoni=pedoni, localita=localita, data_ora=data_ora, operatori=operatori_input,
    andamento=andamento_strada, tipo_c=tipo_carreggiata, larg_c=larg_carreggiata, num_c=num_corsie,
    stato_a=stringa_stato, dist_xz=dist_XZ
)

st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
st.download_button(
    "📥 Scarica Elaborato Grafico Planimetrico (PNG HD 300 DPI)",
    data=buf.getvalue(),
    file_name=f"SCHIZZO_PLANIMETRICO_{localita.replace(' ', '_')}.png",
    mime="image/png",
    use_container_width=True
)

# =========================================================
# 5. GENERAZIONE RELAZIONE TECNICA DESCRITTIVA EXPORT ATTI
# =========================================================
st.header("5. Relazione Tecnica Descrittiva Ufficiale di Reparto")

note_luogo_aggiornate = note_luogo if 'note_luogo' in locals() else "Fondo stradale regolare."
if usa_frenata
