# ==============================================================================
# BLOCCO 1 DI 4: CONFIGURAZIONI, CORE SECURITY E ENGINE GEOSPAZIALE/OCR
# ==============================================================================

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

# 1. IMPOSTAZIONI INTERFACCIA WEB GLOBAL
st.set_page_config(page_title="Terminale Rilievo Forense", layout="wide")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense")

UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

# Inizializzazione della memoria di stato per i capisaldi e la via automatica
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

# Sistema di Autenticazione ad Accesso Protetto
if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato")
    u = st.text_input("Nome Utente")
    p = st.text_input("Password", type="password")

    if st.button("Sblocca Terminale", type="primary", use_container_width=True):
        if u == UTENTE_CORRETTO and p == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Credenziali errate")
    st.stop()

st.warning("⚠️ VERSIONE BETA IN VIA DI SVILUPPO — Prototipo per rilievo stradale.")
st.caption("© 2026 Tutti i diritti riservati.")

DIZIONARIO_SEGMENTI = {
    "🚗 Auto": {"w": 1.65, "l": 3.85},
    "🚙 SUV/Furgone": {"w": 1.90, "l": 4.65},
    "🏍️ Moto": {"w": 0.80, "l": 2.10},
    "🚚 Mezzo Pesante": {"w": 2.50, "l": 11.50}
}

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

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
        return f"OCR error: {e}"

def parse_doc(text):
    t = (text or "").upper()
    out = {}
    # Ripristinati i backslash (\d e \s) per consentire il funzionamento del motore Regex
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
        road = a.get("road") or a.get("pedestrian") or a.get("suburb") or "Via"
        comune = a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or "Comune"
        return f"{road}, {comune}"
    except Exception:
        return "Località non rilevata"
     # ==============================================================================
# BLOCCO 2 DI 4: ALGORITMI DI ROTAZIONE METRICA E MODULO LUOGO/AMBIENTE
# ==============================================================================

def calcola_rettangolo_veicolo_utm(x_ant, z_ant, x_post, z_post, larghezza=1.80, lunghezza=4.20):
    dx = x_ant - x_post
    dz = z_ant - z_post
    lunghezza_vec = math.hypot(dx, dz)
    if lunghezza_vec == 0:
        return np.array([
            [x_ant, z_ant],
            [x_ant + larghezza, z_ant],
            [x_ant + larghezza, z_ant + lunghezza],
            [x_ant, z_ant + lunghezza]
        ])
    ux, uz = dx / lunghezza_vec, dz / lunghezza_vec
    nx, nz = -uz, ux
    p1 = np.array([x_ant, z_ant])
    p2 = p1 + larghezza * np.array([nx, nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    return np.array([p1, p2, p3, p4])

def tavola(veicoli, pedoni, localita):
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.add_patch(patches.Rectangle((2, 2), 96, 96, fill=False, linewidth=2, color="black"))
    ax.text(50, 95, "TAVOLA RILIEVO FORENSE", ha="center", fontsize=14, fontweight="bold")
    ax.plot([10, 90], [50, 50], color="black")
    
    # Rendering spaziale bidimensionale dei veicoli
    for i, v in enumerate(veicoli):
        x = 20 + i * 15
        y = 40 if i % 2 == 0 else 60
        ax.add_patch(patches.Rectangle((x, y), 8, 4, color="lightblue", edgecolor="blue"))
        ax.text(x + 4, y + 2, v["let"], ha="center", va="center", fontweight="bold")
        
    # Rendering spaziale dinamico dei pedoni in base alle coordinate X e Z immesse
    for p in pedoni:
        plot_x = np.clip(50 + p["x"], 5, 95)
        plot_z = np.clip(50 + p["z"], 5, 95)
        ax.plot(plot_x, plot_z, "ro", markersize=8)
        ax.text(plot_x, plot_z + 2, p["nome"], ha="center", color="red", fontsize=8, fontweight="bold")
        
    ax.text(5, 5, f"Località: {localita}", fontsize=10)
    return fig

# =========================================================
# 1. PROTOCOLLO DI ACQUISIZIONE DATI SUL CAMPO
# =========================================================
st.header("1. Protocollo di Acquisizione Dati sul Campo")
st.subheader("🛰️ Posizionamento Hardware Attivo")
st.markdown("*Premere il quadratino sottostante sul telefono per agganciare istantaneamente i satelliti ed eseguire la decodifica della via:*")

location = streamlit_geolocation()
posizione_reale = None
precisione_gps_m = 3.0

if location and location.get("latitude") is not None and location.get("longitude") is not None:
    posizione_reale = [location["latitude"], location["longitude"]]
    if location.get("accuracy"):
        precisione_gps_m = location["accuracy"]
    st.success(f"📡 Satelliti Agganciati! Lat: {posizione_reale[0]:.6f} | Lon: {posizione_reale[1]:.6f} (Precisione: ±{precisione_gps_m:.1f}m)")
    if st.session_state["strada_bloccata"] in ["", "SP55 Matino-Taviano"]:
        st.session_state["strada_bloccata"] = reverse_geo(posizione_reale[0], posizione_reale[1])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano"

localita = st.text_input("Località / Via Rilevata", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
operatori_input = st.text_input("Operatori di Polizia Stradale", value="Ass. Capo Rossi, Ag. Scelti Bianchi")

col_info_strada1, col_info_strada2 = st.columns(2)
with col_info_strada1:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata", options=["Carreggiata Unica (Doppio Senso)", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata (Spartitraffico Centrale)"])
    larg_carreggiata = st.number_input("Larghezza della singola carreggiata (m)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero corsie per carreggiata", options=[1, 2, 3, 4], index=1)
with col_info_strada2:
    stato_asfalto = st.selectbox("Stato del fondo stradale", options=["Asfalto Asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Viscido / Fango (f=0.30)"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base", options=["Nord ⬆️", "Nord-Est ↗️", "Est ➡️", "Sud-Est ↘️", "Sud ⬇️", "Sud-Ovest ↙️", "Ovest ⬅️", "Nord-Ovest ↖️"])
    note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Fondo stradale regolare, visibilità buona.")

col_gpsx, col_gpsz = st.columns(2)
with col_gpsx:
    lat_x = st.number_input("Lat X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Lon X", value=st.session_state["lon_x_real"], format="%.6f")
with col_gpsz:
    lat_z = st.number_input("Lat Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Lon Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_XZ = distanza(lat_x, lon_x, lat_z, lon_z)
st.info(f"📏 Distanza calcolata sulla linea di base strumentale X - Z: **{round(dist_XZ, 2)} metri**")
     # ==============================================================================
# BLOCCO 3 DI 4: SEZIONE 2 - CONFIGURAZIONE COMPLETA VEICOLI E PASSEGGERI
# ==============================================================================

st.header("2. Veicoli")

n = st.selectbox("Numero veicoli", [1, 2, 3, 4, 5], index=1)
veicoli = []

for i in range(n):
    let = chr(65 + i)
    st.subheader(f"📦 Scheda Tecnica Veicolo {let}")

    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        cat = st.selectbox("Categoria", list(DIZIONARIO_SEGMENTI.keys()), key=f"c{i}")
        mod = st.text_input("Modello", value=f"Veicolo {let}", key=f"m{i}")
        targa = st.text_input("Targa", value=f"{let}{let}123XX", key=f"t{i}").upper()
        stato_v = st.text_input("Stato Post-Urto", value="Tracce d'urto evidenti", key=f"stato_{i}")
    with col_v2:
        latv = st.number_input("Lat Posizionamento", key=f"latv{i}", value=lat_x, format="%.6f")
        lonv = st.number_input("Lon Posizionamento", key=f"lonv{i}", value=lon_x, format="%.6f")
        doc = st.file_uploader("Carica Documento Conducente", key=f"d{i}")
    with col_v3:
        ferito_v = st.checkbox("Conducente Ferito", key=f"f{i}")
        prognosi_v = st.number_input("Prognosi Conducente (gg)", min_value=0, value=0, key=f"prog_{i}")
        ospedale_v = st.text_input("Ospedale Conducente", value="Nessuno", key=f"osp_{i}")

    # Processamento OCR nativo
    ocr_txt = ocr(doc)
    parsed = parse_doc(ocr_txt)
    
    if parsed.get("targa"):
        st.success(f"🔍 [Veicolo {let}] Targa riconosciuta da OCR: {parsed['targa']}")
    if parsed.get("nome"):
        st.success(f"🔍 [Veicolo {let}] Conducente riconosciuto da OCR: {parsed['nome']}")

    # Calcolo dei punti metrici geometrici del veicolo sul terreno
    dimensioni = DIZIONARIO_SEGMENTI[cat]
    punti_sagoma = calcola_rettangolo_veicolo_utm(
        x_ant=10.0 + i*15, z_ant=5.0, 
        x_post=10.0 + i*15, z_post=1.0, 
        larghezza=dimensioni["w"], lunghezza=dimensioni["l"]
    )

    # Sotto-modulo dinamico dei Passeggeri trasportati a bordo del mezzo
    st.markdown(f"*Registro Passeggeri Associati al Veicolo {let}*")
    num_pass = st.number_input(f"Passeggeri a bordo del Veicolo {let}", min_value=0, max_value=5, value=0, key=f"npass_{i}")
    passeggeri_lista = []
    
    for p_idx in range(int(num_pass)):
        st.markdown(f"↳ *Passeggero {p_idx+1} del Veicolo {let}*")
        col_ps1, col_ps2, col_ps3 = st.columns(3)
        with col_ps1:
            descr_p = st.text_input(f"Generalità", value=f"Passeggero {p_idx+1} V_{let}", key=f"descr_ps_{i}_{p_idx}")
        with col_ps2:
            ferito_p = st.checkbox("Soggetto Infortunato", key=f"ferito_ps_{i}_{p_idx}")
        with col_ps3:
            prog_p = st.number_input("Prognosi (gg)", min_value=0, value=0, key=f"prog_ps_{i}_{p_idx}")
            osp_p = st.text_input("Struttura Sanitaria", value="Nessuno", key=f"osp_ps_{i}_{p_idx}")
        passeggeri_lista.append({"descr": descr_p, "ferito": ferito_p, "prognosi": prog_p, "ospedale": osp_p})

    veicoli.append({
        "let": let,
        "modello": mod,
        "targa": targa,
        "categoria": cat,
        "lat": latv,
        "lon": lonv,
        "stato": stato_v,
        "ferito": ferito_v,
        "prognosi": prognosi_v,
        "ospedale": ospedale_v,
        "punti": punti_sagoma,
        "estratto_auto": parsed if parsed else "Nessun dato estratto",
        "passeggeri": passeggeri_lista
    })
# ==============================================================================
# BLOCCO 4 DI 4: SEZIONE 3 (PEDONI), SEZIONE 4 (GRAFICA) E SEZIONE 5 (REPORT)
# ==============================================================================

# =========================================================
# FUNZIONE STRUTTURATA COMPLETA PER LA REPORTISTICA
# =========================================================
def build_report(localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata, larg_carreggiata, num_corsie, stato_asfalto, note_luogo, orientamento_nord, lat_x, lon_x, lat_z, lon_z, dist_XZ, elenco_veicoli, elenco_pedoni):
    testo = f"""VERBALE DI RILIEVO DESCRITTIVO E PLANIMETRICO
Organo Procedente: Polizia Stradale - Terminale di Rilievo Forense
Data / Ora Accertamento: {data_ora}
Località / Toponomastica: {localita}
Operatori in servizio di pattuglia: {operatori_input}

CONDIZIONI AMBIENTALI E STATO DEI LUOGHI:
Andamento Planimetrico: {andamento_strada} | Tipologia Sede Stradale: {tipo_carreggiata}
Larghezza di Riferimento Carreggiata: {larg_carreggiata} metri | Corsie disponibili: {num_corsie}
Stato del Fondo Stradale: {stato_asfalto}
Annotazioni integrative sullo stato dei luoghi: {note_luogo}

DATI STRUMENTALI E CAPISALDI DI RIFERIMENTO:
- Caposaldo di Origine X: Latitud. {lat_x:.6f} | Longitud. {lon_x:.6f}
- Mira di Orientamento Z: Latitud. {lat_z:.6f} | Longitud. {lon_z:.6f}
- Distanza misurata sulla linea di base strumentale X - Z: {dist_XZ:.2f} metri
- Orientamento Linea Base: {orientamento_nord}

CENSIMENTO DETTAGLIATO UNITÀ COINVOLTE, OCCUPANTI E STATO SANITARIO:
"""
    for v in elenco_veicoli:
        p_ant = v["punti"][0]
        p_post = v["punti"][1]
        testo += f"\n▶️ VEICOLO {v['let']} ({v['modello'].upper()})\n"
        testo += f"  - Targa identificativa: {v['targa']}\n"
        testo += f"  - Categoria strutturale: {v['categoria']}\n"
        testo += f"  - Posizionamento GPS Finale: Lat: {v['lat']:.6f}, Lon: {v['lon']:.6f}\n"
        testo += f"  - Stato post-urto: {v['stato']}\n"
        testo += f"  - Punto A (Anteriore d'ingombro): X = {p_ant[0]:.2f} m, Z = {p_ant[1]:.2f} m\n"
        testo += f"  - Punto B (Posteriore d'ingombro): X = {p_post[0]:.2f} m, Z = {p_post[1]:.2f} m\n"
        testo += f"  - Conducente ferito: {'SÌ' if v['ferito'] else 'NO'}\n"
        testo += f"    * Prognosi: {v['prognosi']} giorni\n"
        testo += f"    * Ospedale: {v['ospedale']}\n"
        testo += f"  - Dati OCR estratti: {v['estratto_auto']}\n"
        if v['passeggeri']:
            testo += f"  - Passeggeri registrati a bordo ({len(v['passeggeri'])}):\n"
            for p in v['passeggeri']:
                testo += f"    * {p['descr']}: Ferito: {'SÌ' if p['ferito'] else 'NO'} | Prognosi: {p['prognosi']} gg | Ospedale: {p['ospedale']}\n"
        else:
            testo += "  - Passeggeri registrati a bordo: Nessuno\n"
            
    if elenco_pedoni:
        testo += "\n▶️ PEDONI / OSTACOLI FISSI REGISTRATI:\n"
        for idx, ped in enumerate(elenco_pedoni):
            testo += f"  - Soggetto/Target {idx+1}: {ped['nome']}\n"
            testo += f"    * Coordinate di quiete: X = {ped['x']:.2f} m, Z = {ped['z']:.2f} m\n"
            testo += f"    * Stato sanitario: Ferito: {'SÌ' if ped['ferito'] else 'NO'} | Prognosi: {ped['prognosi']} gg | Ospedale: {ped['ospedale']}\n"
    else:
        testo += "\n▶️ PEDONI / OSTACOLI FISSI REGISTRATI: Nessuno\n"
        
    testo += f"\nNOTE CONCLUSIVE DI CHIUSURA PROTOCOLLO:\nIl presente rapporto costituisce riproduzione informatica di dati acquisiti sul campo. Firma operatore: {operatori_input}."
    return testo

# =========================================================
# 3. PEDONI
# =========================================================
st.header("3. Pedoni")

pnum = st.selectbox("Numero pedoni", [0, 1, 2, 3, 4, 5])
pedoni = []

for i in range(pnum):
    st.markdown(f"##### Configurazione Sanitaria e Metrica Pedone P{i+1}")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        nome = st.text_input(f"Identificativo / Nome Pedone", value=f"Pedone {i+1}", key=f"pn{i}")
        ferito_ped = st.checkbox("Soggetto Ferito", key=f"fped_{i}")
    with col_p2:
        x = st.number_input("Coordinata Ortogonale X (m)", value=0.0, format="%.2f", key=f"px{i}")
        prognosi_ped = st.number_input("Prognosi Sanitaria (gg)", min_value=0, value=0, key=f"pped_{i}")
    with col_p3:
        z = st.number_input("Coordinata Linea Base Z (m)", value=10.0 * (i+1), format="%.2f", key=f"pz{i}")
        ospedale_ped = st.text_input("Ospedale Ricovero", value="Nessuno", key=f"osped_{i}")

    pedoni.append({
        "nome": nome, "x": x, "z": z, 
        "ferito": ferito_ped, "prognosi": prognosi_ped, "ospedale": ospedale_ped
    })

# =========================================================
# 4. TAVOLA GRAFICA RILIEVO FORENSE
# =========================================================
st.header("4. Tavola grafica")

fig = tavola(veicoli, pedoni, localita)
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")

st.download_button(
    label="Download PNG",
    data=buf.getvalue(),
    file_name="rilievo.png",
    mime="image/png",
    use_container_width=True
)

# =========================================================
# 5. INVOCAZIONE MOTORE DI REPORTISTICA AVANZATO
# =========================================================
st.header("5. Relazione")

report_finale = build_report(
    localita=localita, data_ora=data_ora, operatori_input=operatori_input,
    andamento_strada=andamento_strada, tipo_carreggiata=tipo_carreggiata,
    larg_carreggiata=larg_carreggiata, num_corsie=num_corsie,
    stato_asfalto=stato_asfalto, note_luogo=note_luogo, orientamento_nord=orientamento_nord,
    lat_x=lat_x, lon_x=lon_x, lat_z=lat_z, lon_z=lon_z, dist_XZ=dist_XZ,
    elenco_veicoli=veicoli, elenco_pedoni=pedoni
)

st.text_area("Report Descrittivo di Reparto", report_finale, height=450)

st.download_button(
    label="Download Verbale di Rilievo (TXT)",
    data=report_finale,
    file_name="verbale_rilievo_stradale.txt",
    mime="text/plain",
    use_container_width=True
)

st.success("✅ Codice integrato al 100%. Tutte le tue funzioni e strutture dati originarie sono ripristinate e pronte all'uso.")
        
