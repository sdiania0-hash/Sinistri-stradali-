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

st.set_page_config(page_title="Terminale Rilievo Forense", layout="wide")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense")

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

if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato")
    u = st.text_input("Nome Utente")
    p = st.text_input("Password", type="password")

    if st.button("Sblocca Terminale"):
        if u == UTENTE_CORRETTO and p == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Credenziali errate")

    st.stop()

st.warning("⚠️ VERSIONE BETA")
st.caption("© 2026")

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
    targa = re.search(r"\b[A-Z]{2}d{3}[A-Z]{2}\b", t)
    if targa:
        out["targa"] = targa.group()
    nome = re.search(r"(NOME|COGNOME)s*[:-]?s*([A-ZÀ-Ü' ]{3,})", t)
    if nome:
        out["nome"] = nome.group(2).strip()
    return out

def reverse_geo(lat, lon):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
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
    ax.add_patch(patches.Rectangle((2, 2), 96, 96, fill=False))
    ax.text(50, 95, "TAVOLA RILIEVO FORENSE", ha="center", fontsize=14, fontweight="bold")
    ax.plot([10, 90], [50, 50], color="black")
    for i, v in enumerate(veicoli):
        x = 20 + i * 15
        y = 40 if i % 2 == 0 else 60
        ax.add_patch(patches.Rectangle((x, y), 8, 4, color="lightblue"))
        ax.text(x + 4, y + 2, v["let"], ha="center")
    for i, p in enumerate(pedoni):
        ax.plot(20 + i * 3, 30, "ro")
    ax.text(5, 85, localita)
    return fig

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
- Distanza misurata sulla linea di base strumentale X - Z: {dist_XZ} metri
- Orientamento Linea Base: {orientamento_nord}

CENSIMENTO DETTAGLIATO UNITÀ COINVOLTE, OCCUPANTI E STATO SANITARIO:
"""
    for v in elenco_veicoli:
        p_ant = v["punti"][0]
        p_post = v["punti"][1]
        testo += f"
▶️ VEICOLO {v['let']} ({v['modello'].upper()})
"
        testo += f"  - Targa identificativa: {v['targa']}
"
        testo += f"  - Categoria strutturale: {v['categoria']}
"
        testo += f"  - Posizionamento GPS Finale: Lat: {v['lat']:.6f}, Lon: {v['lon']:.6f}
"
        testo += f"  - Stato post-urto: {v['stato']}
"
        testo += f"  - Punto A: X = {p_ant[0]:.2f} m, Z = {p_ant[1]:.2f} m
"
        testo += f"  - Punto B: X = {p_post[0]:.2f} m, Z = {p_post[1]:.2f} m
"
        testo += f"  - Conducente ferito: {'SÌ' if v['ferito'] else 'NO'}
"
        testo += f"    * Prognosi: {v['prognosi']} giorni
"
        testo += f"    * Ospedale: {v['ospedale']}
"
        testo += f"  - Dati OCR estratti: {v['estratto_auto']}
"
        if v['passeggeri']:
            testo += f"  - Passeggeri registrati a bordo ({len(v['passeggeri'])}):
"
            for p in v['passeggeri']:
                testo += f"    * {p['descr']}: Ferito: {'SÌ' if p['ferito'] else 'NO'} | Prognosi: {p['prognosi']} gg | Ospedale: {p['ospedale']}
"
        else:
            testo += "  - Passeggeri registrati a bordo: Nessuno
"
    if elenco_pedoni:
        testo += "
▶️ PEDONI / OSTACOLI FISSI REGISTRATI:
"
        for idx, ped in enumerate(elenco_pedoni):
            testo += f"  - Soggetto/Target {idx+1}: {ped['nome']}
"
            testo += f"    * Coordinate di quiete: X = {ped['x']:.2f} m, Z = {ped['z']:.2f} m
"
            testo += f"    * Stato sanitario: Ferito: {'SÌ' if ped['ferito'] else 'NO'} | Prognosi: {ped['prognosi']} gg | Ospedale: {ped['ospedale']}
"
    else:
        testo += "
▶️ PEDONI / OSTACOLI FISSI REGISTRATI: Nessuno
"
    testo += f"
NOTE CONCLUSIVE DI CHIUSURA PROTOCOLLO:
Il presente rapporto costituisce riproduzione informatica di dati acquisiti sul campo. Firma operatore: {operatori_input}."
    return testo
# GPS
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
    if st.session_state["strada_bloccata"] == "" or st.session_state["strada_bloccata"] == "SP55 Matino-Taviano":
        st.session_state["strada_bloccata"] = reverse_geo(posizione_reale[0], posizione_reale[1])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano"

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
operatori_input = st.text_input("Operatori di Polizia Stradale", value="Ass. Capo Rossi, Ag. Scelti Bianchi")

url_maps = f"https://www.google.com/maps?q={st.session_state['lat_x_real']},{st.session_state['lon_x_real']}"
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
        st.session_state["strada_bloccata"] = reverse_geo(posizione_reale[0], posizione_reale[1])
        st.rerun()
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")
with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z") and posizione_reale:
        st.session_state["lat_z_real"] = posizione_reale[0]
        st.session_state["lon_z_real"] = posizione_reale[1]
        st.session_state["strada_bloccata"] = reverse_geo(posizione_reale[0], posizione_reale[1])
        st.rerun()
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_calcolata = distanza(lat_x, lon_x, lat_z, lon_z)
if dist_calcolata < 0.1:
    dist_calcolata = 25.05

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, value=float(round(dist_calcolata, 2)))

# VEICOLI
st.header("2. Censimento Unità Coinvolte e Rilievi Metrici")
num_veicoli = st.selectbox("Numero totale veicoli da censire", options=[1, 2, 3, 4, 5], index=1)
elenco_veicoli = []

for k in range(num_veicoli):
    let = chr(65 + k)
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

    st.markdown("##### 📁 Caricamento Documenti Conducente e Veicolo (OCR)")
    doc_patente = st.file_uploader(f"Patente conducente {let}", type=["jpg", "jpeg", "png"], key=f"pat_{k}")
    doc_carta = st.file_uploader(f"Carta circolazione {let}", type=["jpg", "jpeg", "png"], key=f"lib_{k}")
    doc_ass = st.file_uploader(f"Assicurazione RCA {let}", type=["jpg", "jpeg", "png"], key=f"ass_{k}")

    if f"ocr_veicolo_{k}" not in st.session_state:
        st.session_state[f"ocr_veicolo_{k}"] = {"patente": "", "carta": "", "assicurazione": "", "estratto": {}}

    if st.button(f"🔎 Leggi documenti Veicolo {let}", key=f"ocr_btn_{k}", use_container_width=True):
        with st.spinner("Estrazione testo in corso..."):
            testo_pat = ocr(doc_patente)
            testo_lib = ocr(doc_carta)
            testo_ass = ocr(doc_ass)
            testo_tot = "
".join([testo_pat, testo_lib, testo_ass])
            st.session_state[f"ocr_veicolo_{k}"] = {
                "patente": testo_pat,
                "carta": testo_lib,
                "assicurazione": testo_ass,
                "estratto": parse_doc(testo_tot)
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

    st.markdown("##### 🩹 Stato del Conducente")
    col_cond_s1, col_cond_s2 = st.columns(2)
    with col_cond_s1:
        flag_cond_ferito = st.checkbox(f"Il Conducente {let} ha riportato lesioni (Ferito)", key=f"c_fer_{k}")
        prognosi_cond = st.number_input(f"Prognosi Conducente {let} (giorni)", min_value=0, max_value=365, value=0, key=f"c_prog_{k}")
    with col_cond_s2:
        ospedale_cond = st.text_input(f"Ospedale trasporto Conducente {let}", value="Vito Fazzi - Lecce" if flag_cond_ferito else "Nessuno", key=f"osp_c_{k}")

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
            st.session_state[f"ocr_pass_{k}_{p}"] = ocr(foto_doc)

        st.text_area(f"Testo OCR Pass. {p+1}", value=st.session_state[f"ocr_pass_{k}_{p}"], height=80, key=f"ocr_pass_txt_{k}_{p}")

        elenco_pass_v.append({
            "descr": f"Passeggero {p+1}",
            "ferito": f_p,
            "prognosi": prog_p,
            "ospedale": o_p,
            "ocr": st.session_state[f"ocr_pass_{k}_{p}"]
        })

    elenco_veicoli.append({
        "let": let,
        "modello": modello,
        "targa": targa,
        "lat": lat_v,
        "lon": lon_v,
        "punti": punti_v,
        "misure_base": [vx1, vz1],
        "ocr": ocr_v,
        "passeggeri": elenco_pass_v,
        "stato": stato_mezzo,
        "forma": tipo_forma,
        "categoria": categoria,
        "ferito": flag_cond_ferito,
        "prognosi": prognosi_cond,
        "ospedale": ospedale_cond,
        "estratto_auto": ocr_v["estratto"]
    })
    st.divider()
# PEDONI
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
        st.session_state[f"ocr_ped_{kp}"] = ocr(ped_doc)

    st.text_area(f"Testo OCR Pedone {kp+1}", value=st.session_state[f"ocr_ped_{kp}"], height=80, key=f"ocr_ped_txt_{kp}")

    elenco_pedoni.append({
        "nome": ped_nome,
        "x": ped_x,
        "z": ped_z,
        "ferito": ped_ferito,
        "prognosi": ped_prog,
        "ospedale": ped_osp,
        "ocr": st.session_state[f"ocr_ped_{kp}"]
    })
    st.divider()

# TAVOLA
st.header("4. Tavola grafica")
fig = tavola(elenco_veicoli, elenco_pedoni, localita)
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")

st.download_button(
    "Download PNG",
    data=buf.getvalue(),
    file_name="rilievo.png",
    mime="image/png"
)

# RELAZIONE
st.header("5. Relazione")
report = build_report(
    localita=localita,
    data_ora=data_ora,
    operatori_input=operatori_input,
    andamento_strada=andamento_strada,
    tipo_carreggiata=tipo_carreggiata,
    larg_carreggiata=larg_carreggiata,
    num_corsie=num_corsie,
    stato_asfalto=stato_asfalto,
    note_luogo=note_luogo,
    orientamento_nord=orientamento_nord,
    lat_x=lat_x,
    lon_x=lon_x,
    lat_z=lat_z,
    lon_z=lon_z,
    dist_XZ=dist_XZ,
    elenco_veicoli=elenco_veicoli,
    elenco_pedoni=elenco_pedoni
)

st.text_area("Report", report, height=400)

# EXTRA
st.header("6. Sintesi Tecnica")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.metric("Veicoli censiti", len(elenco_veicoli))
with col_s2:
    st.metric("Pedoni/Ostacoli censiti", len(elenco_pedoni))
with col_s3:
    st.metric("Distanza base X-Z", f"{dist_XZ:.2f} m")

if elenco_veicoli:
    st.subheader("Dettaglio veicoli")
    for v in elenco_veicoli:
        st.write(f"{v['let']} - {v['modello']} - {v['targa']} - {v['categoria']} - {v['stato']}")
        st.write(f"Posizione: {v['lat']:.6f}, {v['lon']:.6f}")
        st.write(f"OCR estratto: {v['estratto_auto']}")
        st.divider()

if elenco_pedoni:
    st.subheader("Dettaglio pedoni / ostacoli")
    for p in elenco_pedoni:
        st.write(f"{p['nome']} - X: {p['x']:.2f} m - Z: {p['z']:.2f} m")
        st.write(f"Ferito: {'SÌ' if p['ferito'] else 'NO'} | Prognosi: {p['prognosi']} gg | Ospedale: {p['ospedale']}")
        st.divider()

st.download_button(
    "Scarica relazione TXT",
    data=report,
    file_name="relazione_rilievo.txt",
    mime="text/plain"
)

st.info("File completo pronto per esecuzione in Streamlit.")
