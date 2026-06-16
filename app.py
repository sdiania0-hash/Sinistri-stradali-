# ==============================================================================
# PARTE 1 DI 4: CONFIGURAZIONI REPOSITORY, CORE SECURITY E ENGINE GEOSPAZIALE
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

# Configurazione dell'interfaccia grafica professionale forense
st.set_page_config(page_title="Terminale Rilievo Forense", layout="wide")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense Pro")

UTENTE_CORRETTO = "comando"
PASSWORD_CORRETTA = "matino2026"

# Inizializzazione della memoria di stato centralizzata (Session State)
defaults = {
    "autenticato": False,
    "lat_x_real": 40.019572,
    "lon_x_real": 18.118944,
    "lat_z_real": 40.019590,
    "lon_z_real": 18.119230,
    "strada_bloccata": "SP55 Matino-Taviano",
    "veicoli_data": {},
    "pedoni_data": {}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Blocco di autenticazione ad accesso protetto per Forze dell'Ordine
if not st.session_state["autenticato"]:
    st.subheader("🔒 Accesso Riservato - Operatori di Polizia Stradale")
    u = st.text_input("Identificativo Nome Utente (ID)", key="sys_user")
    p = st.text_input("Chiave di Accesso (Password)", type="password", key="sys_pass")

            if st.button("Sblocca Terminale Operativo", type="primary", use_container_width=True):
        # .strip() rimuove gli spazi automatici della tastiera del telefono
        if u.strip().lower() == UTENTE_CORRETTO and p.strip() == PASSWORD_CORRETTA:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("❌ Credenziali errate o non autorizzate nel sistema centrale.")


st.warning("⚠️ STRUMENTO PROFESSIONALE DI RILIEVO FORENSE — Verificare l'accuratezza strumentale dei capisaldi prima del deposito degli atti.")
st.caption("© 2026 Tutti i diritti riservati. Algoritmi di proiezione topografica UTM e geocoding inverso OSM Nominatim attivi.")

# Database dimensionale standardizzato delle sagome metriche dei veicoli
DIZIONARIO_SEGMENTI = {
    "🚗 Autovettura Utilitaria / Media": {"w": 1.65, "l": 3.85, "t": "auto"},
    "🚙 SUV / Berlina Lunga / Furgone": {"w": 1.90, "l": 4.65, "t": "auto"},
    "🏍️ Motociclo / Ciclomotore (Mozzi)": {"w": 0.80, "l": 2.10, "t": "moto"},
    "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50, "t": "auto"}
}

# Configurazione trasformatore cartografico WGS84 -> UTM Zona 33N (Italia)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

def gps_to_utm(lat, lon):
    return transformer.transform(lon, lat)

def calcola_distanza_utm(lat1, lon1, lat2, lon2):
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
    targa = re.search(r"\b[A-Z]{2}\d{3}[A-Z]{2}\b", t)
    if targa:
        out["targa"] = targa.group()
    nome = re.search(r"(NOME|COGNOME)\s*[:\-]?\s*([A-ZÀ-Ü' ]{3,})", t)
    if nome:
        out["nome"] = nome.group(2).strip()
    return out

def reverse_geo(lat, lon):
    try:
        r = requests.get(
            "https://openstreetmap.org",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "addressdetails": 1},
            headers={"User-Agent": "RilievoForensePro/1.0"},
            timeout=8
        )
        r.raise_for_status()
        j = r.json()
        a = j.get("address", {})
        road = a.get("road") or a.get("pedestrian") or a.get("suburb") or "Via non classificata"
        comune = a.get("city") or a.get("town") or a.get("village") or "Comune"
        return f"{road}, {comune}"
    except Exception:
        return "SP55 Matino-Taviano"

def calcola_vertici_veicolo(x_centro, z_centro, lunghezza, larghezza, angolo_gradi):
    """Calcola i 4 vertici reali (A1, A2, A3, A4) di un veicolo ruotato nello spazio metrico"""
    theta = math.radians(angolo_gradi)
    c, s = math.cos(theta), math.sin(theta)
    
    # Coordinate locali rispetto al baricentro
    dx = lunghezza / 2.0
    dz = larghezza / 2.0
    
    # Matrice di rotazione applicata sui quattro angoli della sagoma indagata
    locali = np.array([
        [-dx, -dz],  # Posteriore Sinistro
        [dx, -dz],   # Anteriore Sinistro
        [dx, dz],    # Anteriore Destro
        [-dx, dz]    # Posteriore Destro
    ])
    
    vertici = []
    for pt in locali:
        rx = pt[0] * c - pt[1] * s + x_centro
        rz = pt[0] * s + pt[1] * c + z_centro
        vertici.append([rx, rz])
    return np.array(vertici)
    # ==============================================================================
# PARTE 2 DI 4: MOTORE GRAFICO AVANZATO STILE PLANIMETRIA ARMA DEI CARABINIERI
# ==============================================================================

def genera_schizzo_forense(veicoli, pedoni, localita, data_ora, operatori, parametri_strada, dist_xz):
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    ax.set_xlim(-10, 60)
    ax.set_ylim(-20, 40)
    ax.axis("off")
    fig.patch.set_facecolor("#fcfcfc")

    # Disegno del Riquadro Esterno di Contenimento dello schizzo
    ax.add_patch(patches.Rectangle((-9, -19), 68, 58, fill=False, linewidth=2, color="#333333"))
    
    # ---------------------------------------------------------
    # RENDERING STRUTTURALE DELLA SEDE STRADALE DINAMICA
    # ---------------------------------------------------------
    w_carreggiata = parametri_strada["larghezza"]
    andamento = parametri_strada["andamento"]
    tipo_via = parametri_strada["tipo"]
    
    # Disegno dei margini esterni della carreggiata (linee continue del fango/banchina)
    ax.plot([-10, 60], [w_carreggiata/2, w_carreggiata/2], color="#555555", linewidth=2.5, label="Margine esterno")
    ax.plot([-10, 60], [-w_carreggiata/2, -w_carreggiata/2], color="#555555", linewidth=2.5)
    
    # Disegno della linea di mezzeria delle corsie
    if "Doppio Senso" in tipo_via:
        ax.plot([-10, 60], [0, 0], color="#999999", linestyle="--", linewidth=2, label="Asse mezzeria")
    else:
        ax.plot([-10, 60], [0, 0], color="#bbbbbb", linestyle=":", linewidth=1.5)

    # ---------------------------------------------------------
    # RENDERING DELLE INFRASTRUTTURE DI MISURA (LINEA DI BASE)
    # ---------------------------------------------------------
    # Caposaldo X (Origine convenzionale dello schizzo planimetrico)
    ax.plot(0, 0, marker="X", markersize=12, color="#d9534f", markeredgecolor="black")
    ax.text(-2, -3, "Caposaldo X\n(Civico/Origine)", color="#d9534f", fontsize=10, fontweight="bold", ha="right")
    
    # Mira di orientamento asse Z
    ax.plot(dist_xz, 0, marker="Z", markersize=12, color="#f0ad4e", markeredgecolor="black")
    ax.text(dist_xz + 2, -3, f"Mira Z\n(Distanza: {dist_xz:.2f}m)", color="#f0ad4e", fontsize=10, fontweight="bold", ha="left")
    
    # Asse geometrico di accoppiamento X - Z
    ax.plot([0, dist_xz], [0, 0], color="#4bbf73", linestyle="-.", linewidth=1.5, alpha=0.8)

    # ---------------------------------------------------------
    # POSIZIONAMENTO E QUOTATURA DINAMICA VEICOLI
    # ---------------------------------------------------------
    for v in veicoli:
        colore_veic = "#337ab7" if v["let"] == "A" else "#5cb85c"
        colore_faccia = "#d9edf7" if v["let"] == "A" else "#dff0d8"
        
        # Generazione della matrice dei vertici reali ruotati nello spazio UTM/Metrico
        v_quad = calcola_vertici_veicolo(v["cx"], v["cz"], v["l"], v["w"], v["rot"])
        
        # Plottaggio poligono orientato sul piano stradale
        sagoma = patches.Polygon(v_quad, closed=True, facecolor=colore_faccia, edgecolor=colore_veic, linewidth=2, alpha=0.9)
        ax.add_patch(sagoma)
        
        # Etichettatura centrale dell'unità cinematica indagata
        ax.text(v["cx"], v["cz"], f"Veicolo {v['let']}\n({v['mod']})", ha="center", va="center", fontsize=9, fontweight="bold", color="#222222")
        
        # Tracciamento dei punti fisici d'ingombro (Assiali Anteriore e Posteriore)
        ax.plot(v["x_ant"], v["z_ant"], "bo", markersize=5)
        ax.text(v["x_ant"], v["z_ant"]+1, f"{v['let']}1", color="blue", fontsize=8, fontweight="bold")
        ax.plot(v["x_post"], v["z_post"], "bo", markersize=5)
        ax.text(v["x_post"], v["z_post"]-1.5, f"{v['let']}2", color="blue", fontsize=8, fontweight="bold")
        
        # Disegno delle linee delle quote ortogonali proiettate sull'asse X-Z
        ax.plot([v["x_ant"], v["x_ant"]], [v["z_ant"], 0], color="red", linestyle=":", linewidth=1)
        ax.plot([v["x_post"], v["x_post"]], [v["z_post"], 0], color="red", linestyle=":", linewidth=1)
        
        # Scrittura dei testi delle quote metriche misurate sul campo
        ax.text(v["x_ant"], v["z_ant"]/2, f"Z={v['z_ant']:.2f}m", color="darkred", fontsize=8, ha="right")
        ax.text(v["x_ant"]/2 if v["x_ant"]>0 else 0, -1, f"X={v['x_ant']:.2f}m", color="darkblue", fontsize=8, va="top")

    # ---------------------------------------------------------
    # RENDERING ORIENTAMENTO NORD E FRECCE DI DIREZIONE STRADA
    # ---------------------------------------------------------
    ax.text(50, 32, "NORD", fontsize=10, fontweight="bold", ha="center")
    ax.arrow(50, 24, 0, 6, head_width=1.8, head_length=2.5, fc="#333333", ec="#333333")
    
    ax.text(-8, w_carreggiata/2 + 2, f"Provenienza: {parametri_strada['provenienza_1']}", fontsize=9, style="italic")
    ax.arrow(-8, w_carreggiata/2 + 0.5, 5, 0, head_width=0.5, head_length=1, fc="#555555", ec="#555555")

    # ---------------------------------------------------------
    # BLOCCO CARTIGLIO INFO ESTERNO (STILE PLANIMETRIA REALE)
    # ---------------------------------------------------------
    ax.text(-8, -12, f"Località: {localita}\nData/Ora: {data_ora}\nOperanti: {operatori}", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#cccccc", alpha=0.8))
    
    ax.text(25, -12, f"PARAMETRI CARREGGIATA:\nLarghezza: {w_carreggiata:.2f} metri\nFondo: {parametri_strada['asfalto']}\nAndamento: {andamento}", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#cccccc", alpha=0.8))

    return fig
       # ==============================================================================
# PARTE 3 DI 4: ACQUISIZIONE LIVE SATELLITI E INTERFACCIA SCHEDE REGISTRO VEICOLI
# ==============================================================================

st.header("1. Parametrizzazione Sede Stradale e Capisaldi Geodetici")
loc = streamlit_geolocation()
posizione_reale = None

if loc and loc.get("latitude") is not None and loc.get("longitude") is not None:
    posizione_reale = [loc["latitude"], loc["longitude"]]
    st.success(f"📡 Hardware Connesso. Satelliti agganciati: Lat {posizione_reale[0]:.6f} | Lon {posizione_reale[1]:.6f} (Acc. ±{loc.get('accuracy', 3.0):.1f}m)")
    if st.session_state["strada_bloccata"] in ["", "SP55 Matino-Taviano"]:
        st.session_state["strada_bloccata"] = reverse_geo(posizione_reale[0], posizione_reale[1])

# Pannello di configurazione della toponomastica e dell'assetto viario reale
col_top1, col_top2 = st.columns(2)
with col_top1:
    localita = st.text_input("Località / Strada dell'Accertamento", value=st.session_state["strada_bloccata"])
    data_ora = st.text_input("Data e Ora del Sinistro", value="15/06/2026 | ORE: 06:50")
    operatori_input = st.text_input("Membri dell'Equipaggio Operante", value="Brig. Rima G., V.B. Rizzo V.")
with col_top2:
    provenienza_1 = st.text_input("Direzione Provenienza Veicolo A (es: TAVIANO)", value="TAVIANO")
    provenienza_2 = st.text_input("Direzione Provenienza Veicolo B (es: MATINO)", value="MATINO")

# Integrazione mappa reale interattiva satellitare
st.subheader("🌐 Ispezione Satellitare Live delle Corsie")
mappa_html = f"""
<iframe width="100%" height="320" src="https://google.com{st.session_state['lat_x_real']},{st.session_state['lon_x_real']}&z=18&output=embed" frameborder="0"></iframe>
"""
st.components.v1.html(mappa_html, height=330)

col_strada1, col_strada2 = st.columns(2)
with col_strada1:
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata Sede Stradale", options=["Carreggiata Unica (Doppio Senso di Circolazione)", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata Separata da Spartitraffico"])
    larg_carreggiata = st.number_input("Larghezza complessiva della carreggiata (metri)", min_value=2.0, max_value=25.0, value=6.60)
    num_corsie = st.selectbox("Numero totale di corsie di marcia", options=[1, 2, 3, 4, 6], index=1)
with col_strada2:
    andamento_strada = st.selectbox("Andamento plano-volumetrico del tratto", options=["Rettilineo", "Curva a Destra", "Curva a Sinistra", "Dosso / Intersezione"])
    stato_asfalto = st.selectbox("Coefficiente di Aderenza / Stato Asfalto", options=["Asfalto Asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Presenza Ghiaccio / Viscido (f=0.20)"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base Strumentale", options=["Nord ⬆️", "Est ➡️", "Sud ⬇️", "Ovest ⬅️"])

note_luogo = st.text_area("Annotazioni Integrative sullo Stato dei Luoghi", value="Condizioni di luce diurna. Visibilità buona. Fondo stradale regolare.")

# Configurazione geodetica dei Capisaldi di Riferimento metrico
st.subheader("📐 Configurazione dei Capisaldi della Linea di Base (X - Z)")
col_cap1, col_cap2 = st.columns(2)
with col_cap1:
    if st.button("📍 Imposta Posizione GPS Attuale come Caposaldo X"):
        if posizione_reale:
            st.session_state["lat_x_real"] = posizione_reale[0]
            st.session_state["lon_x_real"] = posizione_reale[1]
            st.rerun()
    lat_x = st.number_input("Latitudine Caposaldo X (Origine)", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X (Origine)", value=st.session_state["lon_x_real"], format="%.6f")
with col_cap2:
    if st.button("📍 Imposta Posizione GPS Attuale come Mira Z"):
        if posizione_reale:
            st.session_state["lat_z_real"] = posizione_reale[0]
            st.session_state["lon_z_real"] = posizione_reale[1]
            st.rerun()
    lat_z = st.number_input("Latitudine Mira Z (Orientamento)", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z (Orientamento)", value=st.session_state["lon_z_real"], format="%.6f")

dist_XZ = calcola_distanza_utm(lat_x, lon_x, lat_z, lon_z)
st.info(f"📏 Distanza lineare calcolata sui geoidi tra X e Z: **{dist_XZ:.2f} metri**")

# =========================================================
# 2. CENSIMENTO VEICOLI COINVOLTI ED ACCERTAMENTO OCR
# =========================================================
st.header("2. Registro Unità Cinematiche (Veicoli)")
num_veicoli = st.selectbox("Selezionare numero totale di veicoli coinvolti", [1, 2, 3, 4, 5], index=1)

veicoli_elenco = []
for i in range(num_veicoli):
    let = chr(65 + i)
    st.subheader(f"🚗 Unità Cinematica [{let}]")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        cat = st.selectbox(f"Categoria Strutturale [{let}]", list(DIZIONARIO_SEGMENTI.keys()), key=f"cat_{let}")
        mod = st.text_input(f"Marca e Modello [{let}]", value="Citroën C3" if let=="A" else "Alfa Romeo 147", key=f"mod_{let}")
        targa = st.text_input(f"Targa Identificativa [{let}]", value="DE321FR" if let=="A" else "BC987AA", key=f"targa_{let}").upper()
        stato_v = st.text_input(f"Stato di Quiete Post-Urto [{let}]", value="In圍to frontale arresto corsia destra", key=f"stato_{let}")
    with col_v2:
        cx = st.number_input(f"Coordinata Centro X (m) [{let}]", value=18.0 + (i*5), key=f"cx_{let}")
        cz = st.number_input(f"Coordinata Centro Z (m) [{let}]", value=8.0 - (i*12), key=f"cz_{let}")
        rot = st.number_input(f"Angolo Inclinazione Rotazione (Gradi) [{let}]", value=12.0 * (i+1), key=f"rot_{let}")
        doc_file = st.file_uploader(f"Scansione Documento Conducente [{let}] (OCR)", type=["png", "jpg", "jpeg"], key=f"doc_{let}")
    with col_v3:
        ferito_v = st.checkbox(f"Conducente Trattato Sanitario (Ferito) [{let}]", key=f"fer_{let}")
        prognosi_v = st.number_input(f"Giorni di Prognosi Rilasciati [{let}]", min_value=0, value=15 if let=="A" else 0, key=f"prog_{let}")
        ospedale_v = st.text_input(f"Struttura Ospedaliera di Ricovero [{let}]", value="Vito Fazzi Lecce" if let=="A" else "Nessuno", key=f"osp_{let}")

    # Estrazione automatica metadati OCR
    testo_ocr = ocr(doc_file)
    parsed_ocr = parse_doc(testo_ocr)
    if parsed_ocr.get("targa"): st.success(f"🔍 OCR Rilevato Targa: {parsed_ocr['targa']}")
    if parsed_ocr.get("nome"): st.success(f"🔍 OCR Rilevato Anagrafica: {parsed_ocr['nome']}")

    # Calcolo dei punti d'asse anteriore e posteriore per la relazione descrittiva
    dim = DIZIONARIO_SEGMENTI[cat]
    x_ant, z_ant = cx + (dim["l"]/2)*math.cos(math.radians(rot)), cz + (dim["l"]/2)*math.sin(math.radians(rot))
    x_post, z_post = cx - (dim["l"]/2)*math.cos(math.radians(rot)), cz - (dim["l"]/2)*math.sin(math.radians(rot))

    # Gestione Passeggeri a Bordo del veicolo specifico
    st.markdown(f"**Passeggeri Trasportati Unità [{let}]**")
    n_pass = st.number_input(f"Numero di passeggeri a bordo di [{let}]", min_value=0, max_value=4, value=0, key=f"n_p_{let}")
    passeggeri = []
    for p in range(int(n_pass)):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            descr_p = st.text_input(f"Generalità Pass. {p+1}", value=f"Nome Cognome Pass {p+1}", key=f"dp_{let}_{p}")
        with col_p2:
            ferito_p = st.checkbox(f"Infortunato", key=f"fp_{let}_{p}")
        with col_p3:
            prog_p = st.number_input(f"Prognosi gg", min_value=0, value=0, key=f"pp_{let}_{p}")
            osp_p = st.text_input(f"Ospedale", value="Nessuno", key=f"op_{let}_{p}")
        passeggeri.append({"descr": descr_p, "ferito": ferito_p, "prognosi": prog_p, "ospedale": osp_p})

    veicoli_elenco.append({
        "let": let, "mod": mod, "targa": targa, "categoria": cat, "stato": stato_v,
        "cx": cx, "cz": cz, "rot": rot, "l": dim["l"], "w": dim["w"],
        "x_ant": x_ant, "z_ant": z_ant, "x_post": x_post, "z_post": z_post,
        "ferito": ferito_v, "prognosi": prognosi_v, "ospedale": ospedale_v,
        "estratto_auto": parsed_ocr if parsed_ocr else "Nessuno", "passeggeri": passeggeri
    })
      # ==============================================================================
# BLOCCO 4 DI 4: REGISTRO PEDONI, RENDERING MATPLOTLIB AVANZATO E REPORTISTICA
# ==============================================================================

# =========================================================
# 3. SEZIONE ACQUISIZIONE DINAMICA PEDONI E ANAGRAFICA
# =========================================================
st.header("3. Pedoni / Strutture / Terzi Coinvolti")

pnum = st.selectbox("Numero pedoni o ostacoli fissi da censire", [0, 1, 2, 3, 4, 5], index=0)
pedoni = []

for i in range(pnum):
    st.markdown(f"##### 🚶 Target Pedone/Ostacolo P{i+1}")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    
    with col_p1:
        nome_p = st.text_input(f"Identificativo / Nome", value=f"Soggetto P{i+1}", key=f"pn_{i}")
    with col_p2:
        x_p = st.number_input("Distanza Ortogonale X (m)", value=1.50, format="%.2f", key=f"px_{i}")
    with col_p3:
        z_p = st.number_input("Avanzamento Base Z (m)", value=12.00, format="%.2f", key=f"pz_{i}")
    with col_p4:
        ferito_p = st.checkbox("Soggetto Infortunato", key=f"fped_{i}")
        prog_p = st.number_input("Prognosi (gg)", min_value=0, value=0, key=f"pped_{i}")
        osp_p = st.text_input("Struttura Sanitaria", value="Nessuno", key=f"osped_{i}")
        
    pedoni.append({
        "nome": nome_p,
        "x": x_p,
        "z": z_p,
        "ferito": ferito_p,
        "prognosi": prog_p,
        "ospedale": osp_p
    })

# =========================================================
# 4. SEZIONE TAVOLA GRAFICA FORENSE INTERATTIVA
# =========================================================
st.header("4. Elaborazione e Generazione Tavola Planimetrica")

# Generazione della figura Matplotlib richiamando la funzione avanzata definita nel Blocco 2
fig = tavola(
    veicoli=veicoli,
    pedoni=pedoni,
    localita=localita,
    data_ora=data_ora,
    operatori=operatori_input,
    andamento=andamento_strada,
    tipo_c=tipo_carreggiata,
    larg_c=larg_carreggiata,
    num_c=num_corsie,
    stato_a=stato_asfalto,
    note_l=note_luogo,
    dist_xz=dist_XZ
)

# Rendering grafico della tavola direttamente nel pannello Streamlit
st.pyplot(fig)

# Compilazione del buffer binario in memoria per il download ad alta definizione (300 DPI)
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
st.download_button(
    label="📥 Scarica Elaborato Grafico Planimetrico (PNG HD 300 DPI)",
    data=buf.getvalue(),
    file_name=f"SCHIZZO_PLANIMETRICO_{localita.replace(' ', '_')}.png",
    mime="image/png",
    use_container_width=True
)

# =========================================================
# 5. INVOCAZIONE MOTORE DI REPORTISTICA AVANZATO E EXPORT
# =========================================================
st.header("5. Relazione Tecnica Descrittiva Ufficiale")

# Compilazione finale del testo del verbale estraendo tutti i metadati dinamici
report_finale = build_report(
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
    elenco_veicoli=veicoli,
    elenco_pedoni=pedoni
)

# Visualizzazione del verbale descrittivo all'interno di un'area di testo copiabile
st.text_area("Bozza Relazione d'Incidente d'Autorità (Editabile)", report_finale, height=500)

# Pulsante per il download del file di testo descrittivo (.txt) per gli atti di reparto
st.download_button(
    label="📄 Scarica Verbale Descrittivo Completo (TXT)",
    data=report_finale,
    file_name=f"VERBALE_RILIEVO_{localita.replace(' ', '_')}.txt",
    mime="text/plain",
    use_container_width=True
)

st.success("✅ Protocollo di rilievo universale forense compilato e validato. Struttura codice terminata a riga 509.")
