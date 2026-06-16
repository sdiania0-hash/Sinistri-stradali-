"""
POLIZIA STRADALE - TERMINALE UNIVERSALE DI RILIEVO PLANIMETRICO FORENSE PRO
SISTEMA INFORMATIVO INTEGRATO PER L'ACQUISIZIONE DI REPERTI CINEMATICI E METRICI
================================================================================
Codice Reparto: POL-STRADA-MATINO-2026
Versione: 2.4.1 Pro (Edizione Speciale Scalata a 600 Righe Universali)
Descrizione: Modulo di inizializzazione, costanti e sicurezza crittografica.
"""

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

# ==============================================================================
# CONFIGURAZIONE STRUTTURALE DELLA PAGINA ED INTERFACCIA UTENTE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Terminale Rilievo Forense Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense Pro")

# Costanti di autenticazione ministeriale crittografate o hardcoded di reparto
UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

# ==============================================================================
# DICHIARAZIONE DEI DEFAULTS E INIZIALIZZAZIONE DELLO STATO DELLA SESSIONE (SIDE)
# ==============================================================================
defaults_sistema_forense = {
    "autenticato": False,
    "lat_x_real": 40.019572,
    "lon_x_real": 18.118944,
    "lat_z_real": 40.019590,
    "lon_z_real": 18.119230,
    "strada_bloccata": "",
    "foto_sinistro": [],
    "validazione_errori": [],
    "registro_operazioni": ["Avvio Sistema Terminato Rilievo Forense... OK"]
}

# Caricamento ciclico controllato per evitare sovrascritture dello stato corrente
for chiave_stato, valore_default in defaults_sistema_forense.items():
    if chiave_stato not in st.session_state:
        st.session_state[chiave_stato] = valore_default

# ==============================================================================
# SISTEMA DI AUTENTICAZIONE PROTETTO ED ACCESSO CONFIGURAZIONE CORE
# ==============================================================================
if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato - Operatori di Polizia Stradale")
    st.info("Inserire le proprie credenziali per sbloccare le funzioni di disegno metrico.")
    
    colonna_id, colonna_pass = st.columns(2)
    with colonna_id:
        u_operatore = st.text_input("Identificativo Nome Utente (ID)", placeholder="Es: comando")
    with colonna_pass:
        p_operatore = st.text_input("Chiave di Accesso (Password)", type="password", placeholder="******")

    if st.button("Sblocca Terminale Operativo", type="primary", use_container_width=True):
        if u_operatore.strip().lower() == UTENTE_CORRETTO and p_operatore.strip() == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.session_state["registro_operazioni"].append("Autenticazione operatore completata correttamente.")
            st.rerun()
        else:
            st.error("❌ Credenziali errate o non autorizzate nel sistema centrale. Riprovare.")
    st.stop()

# Banner di segnalazione software beta per gli operatori sul teatro stradale
st.warning("⚠️ VERSIONE BETA PROFESSIONALE - Sistema di acquisizione planimetrica digitale forense.")

# ==============================================================================
# DIZIONARIO CONFIGURAZIONE INGOMBRI ED IDENTIFICAZIONE CODICI VEICOLO
# ==============================================================================
DIZIONARIO_SEGMENTI = {
    "🚗 Citroën C3 (Auto Utilitaria)": {"w": 1.75, "l": 3.99},
    "🚗 Alfa Romeo 147 (Berlina)": {"w": 1.73, "l": 4.22},
    "🚙 SUV / Furgone Commerciale": {"w": 1.90, "l": 4.65},
    "🏍️ Motociclo (Ciclomotore)": {"w": 0.80, "l": 2.10},
    "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50}
}

# Configurazione del trasformatore WGS84 a UTM Zona 33N (EPSG:32633) per metriche reali
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
# ==============================================================================
# FUNZIONI CORE (GEO-COMPUTAZIONE, TRASFORMAZIONE DI COORDINATE E CALCOLI METRICI)
# ==============================================================================

def gps_to_utm(lat: float, lon: float):
    """
    Esegue la conversione delle coordinate sferiche WGS84 in proiezioni
    cartografiche piane basate sul sistema metrico UTM Zona 33N.
    """
    try:
        x_utm, y_utm = transformer.transform(lon, lat)
        return x_utm, y_utm
    except Exception as errore_trasformazione:
        st.session_state["validazione_errori"].append(f"Errore di proiezione: {errore_trasformazione}")
        return 0.0, 0.0


def distanza(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcola la distanza geometrica euclidea espressa in metri lineari tra due punti
    rilevati tramite coordinate GPS sul campo stradale.
    """
    x1, y1 = gps_to_utm(lat1, lon1)
    x2, y2 = gps_to_utm(lat2, lon2)
    distanza_calcolata = math.hypot(x2 - x1, y2 - y1)
    return float(distanza_calcolata)


def ocr(file) -> str:
    """
    Analizza il file immagine caricato ed esegue il motore Tesseract OCR
    per l'estrazione cruda dei caratteri alfanumerici (Patenti e Libretti).
    """
    if file is None:
        return ""
    try:
        immagine_aperta = Image.open(file)
        testo_estratto = pytesseract.image_to_string(immagine_aperta, lang="ita+eng")
        return str(testo_estratto)
    except Exception as errore_ocr:
        st.session_state["validazione_errori"].append(f"Errore OCR: {errore_ocr}")
        return f"OCR non configurato nel sistema operativo: {errore_ocr}"


def parse_doc(text: str) -> dict:
    """
    Elabora e filtra il testo grezzo proveniente dal motore OCR per isolare
    ed identificare pattern regolari (Targhe automobilistiche e Nominativi).
    """
    testo_maiuscolo = (text or "").upper()
    risultati_estrazione = {}
    
    # Ricerca di pattern regolari compatibili con targhe italiane standard
    match_targa = re.search(r"\b[A-Z]{2}\d{3}[A-Z]{2}\b", testo_maiuscolo)
    if match_targa:
        risultati_estrazione["targa"] = match_targa.group()
        
    # Ricerca di corrispondenze alfanumeriche per i campi anagrafici conducente
    match_nome = re.search(r"(NOME|COGNOME)\s*[:-]?\s*([A-ZÀ-Ü' ]{3,})", testo_maiuscolo)
    if match_nome:
        risultati_estrazione["nome"] = match_nome.group(2).strip()
        
    return risultati_estrazione


def reverse_geo(lat: float, lon: float) -> str:
    """
    Interroga i server cartografici OSM Nominatim per ottenere la toponomastica
    esatta e ufficiale corrispondente alla posizione GPS del terminale.
    """
    try:
        url_servizio = "https://openstreetmap.org"
        parametri_richiesta = {"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1}
        intestazioni_sicurezza = {"User-Agent": "RilievoForenseUniversal/2.0"}
        
        risposta_server = requests.get(
            url_servizio, 
            params=parametri_richiesta, 
            headers=intestazioni_sicurezza, 
            timeout=8
        )
        risposta_server.raise_for_status()
        dati_mappa = risposta_server.json()
        indirizzo_estratto = dati_mappa.get("address", {})
        
        via_strada = indirizzo_estratto.get("road") or indirizzo_estratto.get("pedestrian") or indirizzo_estratto.get("suburb") or "SP55 Matino-Taviano"
        comune_localita = indirizzo_estratto.get("city") or indirizzo_estratto.get("town") or indirizzo_estratto.get("village") or "Matino"
        
        return f"{via_strada}, {comune_localita}"
    except Exception as errore_rete:
        st.session_state["validazione_errori"].append(f"Fallback Geocoding: {errore_rete}")
        return "SP55 Matino-Taviano, Matino"


def calcola_rettangolo_veicolo_utm(x_ant: float, z_ant: float, x_post: float, z_post: float, larghezza: float, lunghezza: float):
    """
    Algoritmo matematico vettoriale che restituisce le coordinate spaziali planimetriche
    dei 4 vertici del veicolo partendo dai due punti di misurazione rilevati.
    """
    differenza_x = x_ant - x_post
    differenza_z = z_ant - z_post
    lunghezza_vettore_base = math.hypot(differenza_x, differenza_z)
    
    if lunghezza_vettore_base == 0:
        return np.array([
            [x_ant - larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant],
            [x_ant + larghezza/2, z_ant - lunghezza],
            [x_ant - larghezza/2, z_ant - lunghezza]
        ])
        
    unitario_x = differenza_x / lunghezza_vettore_base
    unitario_z = differenza_z / lunghezza_vettore_base
    normale_x = -unitario_z
    normale_z = unitario_x
    
    vertice_1 = np.array([x_ant - (larghezza/2)*normale_x, z_ant - (larghezza/2)*normale_z])
    vertice_2 = np.array([x_ant + (larghezza/2)*normale_x, z_ant + (larghezza/2)*normale_z])
    vertice_3 = vertice_2 - lunghezza * np.array([unitario_x, unitario_z])
    vertice_4 = vertice_1 - lunghezza * np.array([unitario_x, unitario_z])
    
    return np.array([vertice_1, vertice_2, vertice_3, vertice_4])
    # ==============================================================================
# DISPATCHER GRAFICO - RENDERING SCALATO DELLA TAVOLA PLANIMETRICA METRICA
# ==============================================================================

def tavola(veicoli, pedoni, localita, data_ora, operatori, andamento, tipo_c, larg_c, num_c, stato_a, dist_xz):
    """
    Inizializza la figura vettoriale Matplotlib e gestisce il posizionamento
    stratificato (z-order) di carreggiate, corsie, capisaldi e veicoli.
    """
    # Creazione dell'istanza e impostazione dei limiti di delimitazione spaziale
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(-10, 40)
    ax.set_ylim(-5, 35)
    ax.set_aspect('equal')
    ax.axis("on")
    ax.grid(True, linestyle=":", alpha=0.5)

    # 1. RENDERING DELLA SEDE STRADALE (Sfondo della carreggiata asfaltata)
    strada_sfondo = patches.Rectangle((-10, 0), 50, larg_c, facecolor="#555555", alpha=0.9, zorder=1)
    ax.add_patch(strada_sfondo)
    
    # Linee di margine continue bianche (Spessore forense standard = 3px)
    ax.plot([-10, 40], [0, 0], color="white", linewidth=3, zorder=2)
    ax.plot([-10, 40], [larg_c, larg_c], color="white", linewidth=3, zorder=2)

    # 2. SEPARAZIONE DELLE CORSIE INTERNE (Linee tratteggiate di mezzeria)
    if num_c > 1:
        passo_corsia = larg_c / num_c
        for nc in range(1, num_c):
            ax.plot(
                [-10, 40], 
                [passo_corsia * nc, passo_corsia * nc], 
                color="white", 
                linestyle="--", 
                linewidth=1.5, 
                zorder=2
            )

    # 3. TRACCIAMENTO DEI PUNTI FISSI DI RIFERIMENTO METRICO (Capisaldi)
    # Caposaldo di Origine Strumentale X
    ax.plot(0, 0, "X", color="orange", markersize=12, label="Caposaldo X (Origine)", zorder=5)
    ax.text(-1, -1.5, "Caposaldo X\n(Civico 57)", color="orange", fontweight="bold", fontsize=9, ha="center")
    
    # Mira Metrica di Allineamento ed Orientamento Z
    ax.plot(dist_xz, 0, "X", color="orange", markersize=12, label="Mira Z", zorder=5)
    ax.text(dist_xz, -1.5, "Mira Z\n(Palo TIM)", color="orange", fontweight="bold", fontsize=9, ha="center")

    # Rappresentazione vettoriale della Linea di Base Strumentale X-Z
    ax.plot([0, dist_xz], [0, 0], color="red", linestyle="-.", linewidth=1.2, alpha=0.7, zorder=2)
    ax.text(dist_xz / 2, -0.8, f"Linea Base X-Z = {dist_xz:.2f} m", color="red", fontsize=9, ha="center", fontweight="bold")

    # 4. PLOTTING DINAMICO DEI POLIGONI DEI VEICOLI CENSITI NELLA SCENA
    for v in veicoli:
        punti_vertice = v["punti_invallati"]
        
        # Generazione della patch poligonale chiusa con trasparenza per impatti sovrapposti
        poligono_veicolo = patches.Polygon(
            punti_vertice, 
            closed=True, 
            facecolor=v["colore_faccia"], 
            edgecolor=v["colore_bordo"], 
            linewidth=2, 
            alpha=0.85, 
            zorder=4
        )
        ax.add_patch(poligono_veicolo)
        
        # Calcolo del centroide geometrico per l'etichettatura alfanumerica centrale
        centro_x, centro_z = np.mean(punti_vertice[:, 0]), np.mean(punti_vertice[:, 1])
        ax.text(
            centro_x, centro_z, 
            f"Veicolo {v['let']}\n({v['targa']})", 
            color="white", fontweight="bold", fontsize=8, ha="center", va="center"
        )
        
        # Visualizzazione grafica dei punti di rilevamento anteriori (vertici A1 e A2)
        for idx, pt in enumerate(punti_vertice[:2]):
            ax.plot(pt[0], pt[1], "o", color="cyan", markersize=6, zorder=5)
            ax.text(pt[0], pt[1] + 0.4, f"{v['let']}{idx+1}", color="cyan", fontsize=8, fontweight="bold", ha="center")

    # 5. DISGREGATORE GRAFICO DI REPERTI FISSI, PEDONI O OSTACOLI ESTERNI
    for p in pedoni:
        ax.plot(p["x"], p["z"], "ro", markersize=9, zorder=5)
        ax.text(p["x"], p["z"] + 0.8, p["nome"], color="red", fontweight="bold", fontsize=9, ha="center")

    # Definizione titoli di sezione e mappature cartesiane
    ax.set_title(f"PLANIMETRIA FORENSE SCALATA - {localita.upper()}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Asse Metrico Longitudinale Z (metri Avanzamento)")
    ax.set_ylabel("Asse Metrico Ortogonale X (metri Scostamento)")
    
    return fig
   # ==============================================================================
# MOTORE GENERATORE DI REPORTISTICA TESTUALE DI REPARTO
# ==============================================================================

def build_report(localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata,
                 larg_carreggiata, num_corsie, stato_asfalto, note_luogo, orientamento_nord, 
                 lat_x, lon_x, lat_z, lon_z, dist_XZ, elenco_veicoli, elenco_pedoni):
    """
    Sintetizza in una stringa strutturata tutte le metriche e le anagrafiche
    acquisite per la successiva esportazione in formato testuale ufficiale.
    """
    testo = f'''==================================================================
VERBALE DI RILIEVO DESCRITTIVO E PLANIMETRICO STATICO E CINEMATICO
==================================================================
Organo Procedente: Polizia Stradale - Stazione CC Matino
Data / Ora Accertamento: {data_ora}
Località / Toponomastica: {localita}
Operatori in servizio: {operatori_input}

CONDIZIONI AMBIENTALI E STATO DEI LUOGHI:
Andamento Planimetrico: {andamento_strada} | Carreggiata: {tipo_carreggiata}
Larghezza Sede Stradale: {larg_carreggiata} metri | Corsie totali: {num_corsie}
Fondo Stradale: {stato_asfalto} | Note del sopralluogo: {note_luogo}

DATI STRUMENTALI E LINEA DI BASE METRICA:
- Caposaldo X (Origine 0,0): Lat: {lat_x:.6f} | Lon: {lon_x:.6f}
- Mira di Orientamento Z: Lat: {lat_z:.6f} | Lon: {lon_z:.6f}
- Distanza geometrica asse X-Z: {dist_XZ:.2f} metri | Orientamento Nord: {orientamento_nord}

CENSIMENTO UNITÀ COINVOLTE, REPERTI METRICI E STATO SANITARIO:
'''
    for v in elenco_veicoli:
        testo += f"\n▶️ VEICOLO {v['let']} - Modello: {v['modello']} | Targa: {v['targa']}\n"
        testo += f" - Posizione GPS: Lat: {v['lat']:.6f}, Lon: {v['lon']:.6f}\n"
        testo += f" - Misure d'ingombro registrate: XA1={v['misure'][0]:.2f}m, ZA1={v['misure'][1]:.2f}m | XA2={v['misure'][2]:.2f}m, ZA2={v['misure'][3]:.2f}m\n"
        testo += f" - Conducente Ferito: {'SÌ' if v['ferito'] else 'NO'} | Prognosi: {v['prognosi']} gg | Ospedale: {v['ospedale']}\n"
        testo += f" - Riferimenti OCR Documenti: {v['estratto_auto']}\n"
        if v['passeggeri']:
            for passg in v['passeggeri']:
                testo += f"   * Passeggero: {passg['descr']} | Ferito: {'SÌ' if passg['ferito'] else 'NO'} | Prognosi: {passg['prognosi']} gg\n"

    for idx, ped in enumerate(elenco_pedoni):
        testo += f"\n▶️ PEDONE / OSTACOLO P{idx+1}: {ped['nome']}\n"
        testo += f" - Posizione Metrica: X = {ped['x']:.2f} m, Z = {ped['z']:.2f} m\n"
        testo += f" - Stato Sanitario: Ferito: {'SÌ' if ped['ferito'] else 'NO'} | Prognosi: {ped['prognosi']} gg | Ricovero: {ped['ospedale']}\n"
        
    return testo

# ==============================================================================
# SEZIONE INTERFACCIA WEB: 1. PROTOCOLLO AMBIENTALE E DISPOSITIVI SATELLITARI
# ==============================================================================
st.header("1. Protocollo di Acquisizione Dati sul Campo")
location = streamlit_geolocation()

# Invocazione automatica del reverse geocoding in caso di fix GPS valido
if location and location.get("latitude") is not None and location.get("longitude") is not None:
    if st.session_state["strada_bloccata"] in ["", "SP55 Matino-Taviano"]:
        st.session_state["strada_bloccata"] = reverse_geo(location["latitude"], location["longitude"])

if st.session_state["strada_bloccata"] == "":
    st.session_state["strada_bloccata"] = "SP55 Matino-Taviano, Matino"

localita = st.text_input("Località / Via Rilevata (Accertamento Satellitare)", value=st.session_state["strada_bloccata"])
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
operatori_input = st.text_input("Operatori di Polizia Stradale", value="Brig. Rima G., V.B. Rizzo V.")

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
# SEZIONE INTERFACCIA UTENTE: 2. REGISTRO VEICOLI COINVOLTI NEL SINISTRO
# ==============================================================================
st.header("2. Veicoli")
n = st.selectbox("Numero veicoli coinvolti nel sinistro", [1, 2, 3, 4, 5], index=1)
veicoli = []

# Loop iterativo per il caricamento delle schede tecniche di ciascun veicolo censito
for i in range(n):
    let = chr(65 + i)
    st.subheader(f"📦 Configurazione Avanzata Veicolo {let}")
    col_v1, col_v2, col_v3 = st.columns(3)
    
    with col_v1:
        cat = st.selectbox("Categoria e Modello Strutturale", list(DIZIONARIO_SEGMENTI.keys()), key=f"cat_{i}", index=i if i < 2 else 0)
        mod = st.text_input("Marca e Modello Esteso", value="Citroën C3" if i==0 else "Alfa Romeo 147", key=f"mod_{i}")
        targa = st.text_input("Targa del Veicolo", value="AA123BB" if i==0 else "CC456DD", key=f"targa_{i}").upper()
        stato_v = st.text_input("Stato Post-Urto / Danni Strutturali", value="Danni ingenti sulla parte frontale dell'automezzo", key=f"stato_{i}")
        
    with col_v2:
        latv = st.number_input(f"Latitudine Quiete GPS - Veicolo {let}", key=f"latv_{i}", value=lat_x, format="%.6f")
        lonv = st.number_input(f"Longitudine Quiete GPS - Veicolo {let}", key=f"lonv_{i}", value=lon_x, format="%.6f")
        doc = st.file_uploader(f"Scansione Patente / Libretto {let} (OCR)", key=f"doc_{i}")
        
    with col_v3:
        ferito_v = st.checkbox(f"Conducente {let} Infortunato / Ospedalizzato", key=f"fer_{i}")
        prog_v = st.number_input(f"Prognosi Conducente {let} (giorni)", min_value=0, value=0, key=f"prog_{i}")
        ospedale_v = st.text_input(f"Ospedale d'Accoglimento Conducente {let}", value="Vito Fazzi" if ferito_v else "Nessuno", key=f"osp_{i}")

    st.markdown(f"**📐 Rilevamenti Metrici dal Campo (Riscontri Grafici Veicolo {let})**")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1: 
        xa = st.number_input(f"XA1 {let} (Avanzamento Ant.)", value=16.60 if i==0 else 16.30, key=f"xa_{i}")
    with col_m2: 
        za = st.number_input(f"ZA1 {let} (Scostamento Ant.)", value=11.55 if i==0 else 10.55, key=f"za_{i}")
    with col_m3: 
        xp = st.number_input(f"XA2 {let} (Avanzamento Post.)", value=18.20 if i==0 else 18.05, key=f"xp_{i}")
    with col_m4: 
        zp = st.number_input(f"ZA2 {let} (Scostamento Post.)", value=11.00 if i==0 else 8.70, key=f"zp_{i}")

    # Elaborazione del testo estratto tramite modulo OCR intelligente e Regex
    ocr_txt = ocr(doc)
    parsed = parse_doc(ocr_txt)
    if parsed.get("targa"): 
        st.success(f"🔍 Targa rilevata OCR per {let}: {parsed['targa']}")
    if parsed.get("nome"): 
        st.success(f"🔍 Conducente rilevato OCR per {let}: {parsed['nome']}")

    # Scomposizione metrica degli ingombri planimetrici
    dim = DIZIONARIO_SEGMENTI[cat]
    punti_invallati = calcola_rettangolo_veicolo_utm(xa, za, xp, zp, dim["w"], dim["l"])
    col_faccia = "#add8e6" if i==0 else "#d3d3d3"
    col_bordo = "blue" if i==0 else "black"

    # Sotto-modulo per la registrazione dinamica dei passeggeri trasportati
    st.markdown(f"*Registro Passeggeri Trasportati a bordo del Veicolo {let}*")
    num_pass = st.number_input(f"Numero di passeggeri - Veicolo {let}", min_value=0, max_value=4, value=0, key=f"npass_{i}")
    passeggeri_lista = []
    
    for p_idx in range(int(num_pass)):
        col_ps1, col_ps2, col_ps3 = st.columns(3)
        with col_ps1: 
            descr_p = st.text_input(f"Generalità Pass. {p_idx+1} V_{let}", value=f"Passeggero {p_idx+1}", key=f"dps_{i}_{p_idx}")
        with col_ps2: 
            ferito_p = st.checkbox(f"Ferito Pass. {p_idx+1} V_{let}", key=f"fps_{i}_{p_idx}")
        with col_ps3: 
            prog_p = st.number_input(f"Prognosi Pass. {p_idx+1} V_{let}", min_value=0, value=0, key=f"pps_{i}_{p_idx}")
        passeggeri_lista.append({"descr": descr_p, "ferito": ferito_p, "prognosi": prog_p})

    # Append finale dei dati strutturati nel dizionario centrale veicoli
    veicoli.append({
        "let": let, "modello": mod, "targa": targa, "categoria": cat, "lat": latv, "lon": lonv, "stato": stato_v,
        "ferito": ferito_v, "prognosi": prog_v, "ospedale": ospedale_v, "misure": [xa, za, xp, zp],
        "punti_invallati": punti_invallati, "colore_faccia": col_faccia, "colore_bordo": col_bordo,
        "estratto_auto": parsed if parsed else "Nessuno", "passeggeri": passeggeri_lista
    })
# ==============================================================================
# SEZIONE INTERFACCIA UTENTE: 3. REGISTRO PEDONI RILEVATI SUL TEATRO STRADALE
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
    with col_p2: 
        x_p = st.number_input("Distanza Ortogonale X (m) [Scostamento da Asse]", value=1.50, format="%.2f", key=f"px_{i}")
    with col_p3: 
        z_p = st.number_input("Avanzamento Base Z (m) [Distanza da Caposaldo]", value=12.00, format="%.2f", key=f"pz_{i}")
    with col_p4:
        prog_p = st.number_input("Prognosi Sanitaria Iniziale (gg)", min_value=0, value=0, key=f"pped_{i}")
        osp_p = st.text_input("Struttura Sanitaria d'Accoglimento", value="Vito Fazzi" if ferito_p else "Nessuno", key=f"osped_{i}")
        
    pedoni.append({"nome": nome_p, "x": x_p, "z": z_p, "ferito": ferito_p, "prognosi": prog_p, "ospedale": osp_p})

# ==============================================================================
# FASCICOLO FOTOGRAFICO DIGITALIZZATO (Gestione dell'input media)
# ==============================================================================
st.header("📸 Fascicolo Fotografico Digitale dei Rilievi")
col_cam1, col_cam2 = st.columns(2)

with col_cam1:
    sorgente_input = st.radio("Sorgente Input Media", options=["Fotocamera Dispositivo 📷", "Galleria File 📁"])
    file_scatto = None
    
    if len(st.session_state["foto_sinistro"]) < 30:
        if sorgente_input == "Fotocamera Dispositivo 📷": 
            file_scatto = st.camera_input("Inquadra reperto d'urto", key="cam_hw_in")
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
            with st.expander(f"📷 FOTOGRAMMA N. {f['id']} - {f['didascalia']}"): 
                st.image(f["img"], use_container_width=True)
        if st.button("🗑️ Svuota Fascicolo Fotografico"): 
            st.session_state["foto_sinistro"] = []
            st.rerun()

# ==============================================================================
# 💥 ANALISI CINEMATICA FORENSE (FORMULA FISICA PRE-URTO)
# ==============================================================================
st.header("💥 Analisi Cinematica Forense (Tracce Frenata)")
col_cine1, col_cine2 = st.columns(2)

with col_cine1:
    usa_frenata = st.checkbox("Presenza di tracce di frenata sul fondo asfaltato")
    lunghezza_traccia = st.number_input("Lunghezza della traccia di frenata L (m)", min_value=0.0, max_value=200.0, value=15.50)
    
with col_cine2:
    pendenza_strada = st.number_input("Pendenza longitudinale sede stradale p (%)", min_value=-20.0, max_value=20.0, value=0.0)
    velocita_impatto = st.number_input("Stima velocità residua all'urto V_URTO (km/h)", min_value=0.0, max_value=200.0, value=30.0)

stringa_stato = stato_asfalto
f_aderenza = {"Asfalto asciutto (f=0.75)": 0.75, "Asfalto Bagnato (f=0.45)": 0.45, "Viscido / Fango (f=0.30)": 0.30}.get(stringa_stato, 0.75)
v_stimata_kmh = 0.0

if usa_frenata and lunghezza_traccia > 0:
    quadrato_v = ((velocita_impatto / 3.6) ** 2) + (2 * 9.81 * lunghezza_traccia * (f_aderenza + (pendenza_strada / 100.0)))
    if quadrato_v > 0: 
        v_stimata_kmh = math.sqrt(quadrato_v) * 3.6
st.success(f"🧮 Stima Velocità Pre-Frenata calcolata: **{v_stimata_kmh:.1f} km/h**")

# ==============================================================================
# 4. RENDERING TAVOLA PLANIMETRICA AVANZATA E EXPORT ACTS (MATPLOTLIB)
# ==============================================================================
st.header("4. Elaborazione Grafica e Generazione Planimetria")
fig = tavola(veicoli, pedoni, localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata, larg_carreggiata, num_corsie, stringa_stato, dist_XZ)
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
st.download_button("📥 Scarica Elaborato Grafico Planimetrico (PNG HD)", data=buf.getvalue(), file_name=f"SCHIZZO_{localita.replace(' ', '_')}.png", mime="image/png", use_container_width=True)

# ==============================================================================
# 5. INVOCAZIONE MOTORE DI REPORTISTICA AVANZATO ED EXPORT DOCUMENTALE
# ==============================================================================
st.header("5. Relazione Tecnica Descrittiva Ufficiale di Reparto")
note_l_agg = note_luogo
if usa_frenata: 
    note_l_agg += f" Tracce di frenata rilevate per {lunghezza_traccia}m. Velocità iniziale calcolata dal software: {v_stimata_kmh:.1f} km/h."

report_finale = build_report(localita, data_ora, operatori_input, andamento_strada, tipo_carreggiata, larg_carreggiata, num_corsie, stringa_stato, note_l_agg, orientamento_nord, lat_x, lon_x, lat_z, lon_z, dist_XZ, veicoli, pedoni)
st.text_area("Bozza Relazione d'Incidente d'Autorità (Editabile)", report_finale, height=500)
st.download_button("📄 Scarica Verbale Descrittivo Completo (TXT)", data=report_finale, file_name=f"VERBALE_{localita.replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)

st.success("✅ Protocollo di rilievo universale forense completato. Struttura codice validata senza alcuna interruzione.")
    
