import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Terminale Rilievo Planimetrico Forense", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")

st.warning("⚠️ **VERSIONE BETA IN VIA DI SVILUPPO** — Questo software è un prototipo sperimentale per il rilievo stradale. I calcoli geometrici e le acquisizioni hardware devono essere verificati dall'operatore procedente prima dell'inserimento negli atti ufficiali.")
st.caption("© 2026 Tutti i diritti riservati. Proprietà intellettuale e codice sorgente depositati. Vietata la riproduzione e la ridistribuzione non autorizzata.")

st.info("💡 Interfaccia professionale per il rilievo dei sinistri. Permette la scelta del metodo di misura, l'acquisizione GPS e la generazione istantanea della relazione tecnica d'ufficio.")

contenitore_mappa = st.empty()

if "lat_x_real" not in st.session_state: st.session_state["lat_x_real"] = 40.019572
if "lon_x_real" not in st.session_state: st.session_state["lon_x_real"] = 18.118944
if "lat_z_real" not in st.session_state: st.session_state["lat_z_real"] = 40.019590
if "lon_z_real" not in st.session_state: st.session_state["lon_z_real"] = 18.119230

DIZIONARIO_SEGMENTI = {"🚗 Piccola / Utilitaria (Panda, Ypsilon, C3)": {"w": 1.65, "l": 3.85}, "🚗 Compatta / Media (Golf, Giulietta, Focus)": {"w": 1.80, "l": 4.30}, "SUV Compatto / Crossover (Jeep Renegade, 500X)": {"w": 1.80, "l": 4.25}, "🚙 SUV Grande / Berlina Lunga (Stelvio, Audi A6)": {"w": 1.90, "l": 4.70}, "🚚 Furgone Commerciale Light (Ducato, Daily)": {"w": 2.05, "l": 5.40}}

def calcola_distanza_gps(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calcola_rettangolo_veicolo(x_ant, z_ant, x_post, z_post, larghezza=1.80, lunghezza=4.20):
    dx = x_ant - x_post
    dz = z_ant - z_post
    lunghezza_rilevata = math.hypot(dx, dz)
    if lunghezza_rilevata == 0: return np.array([[x_ant, z_ant], [x_ant+1, z_ant], [x_ant+1, z_ant+1], [x_ant, z_ant+1]])
    ux, uz = dx / lunghezza_rilevata, dz / lunghezza_rilevata
    nx, nz = -uz, ux
    p1 = np.array([x_ant, z_ant])
    p2 = np.array([x_ant + larghezza * nx, z_ant + larghezza * nz])
    p3 = p2 - lunghezza * np.array([ux, uz])
    p4 = p1 - lunghezza * np.array([ux, uz])
    return np.array([p1, p2, p3, p4])

st.header("1. Protocollo di Acquisizione Dati sul Campo")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")

col_info_strada1, col_info_strada2 = st.columns(2)
with col_info_strada1:
    larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero totale di corsie", options=[1, 2, 3, 4], index=1)
with col_info_strada2:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base (Direzione Caposaldo Z)", options=["Nord ⬆️", "Nord-Est ↗️", "Est ➡️", "Sud-Est ↘️", "Sud ⬇️", "Sud-Ovest ↙️", "Ovest ⬅️", "Nord-Ovest ↖️"])

note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Visibilità buona.")
st.divider()
st.subheader("📡 Fissaggio Linea di Base (Capisaldi)")
ottieni_gps = st.checkbox("🔄 Attiva Sensore GPS del Dispositivo")
posizione_reale = None

if ottieni_gps:
    posizione_reale = streamlit_js_eval(data_string="navigator.geolocation.getCurrentPosition(success => { return [success.coords.latitude, success.coords.longitude]; }, error => { return null; })", key="gps_device_live")
    if i == 0 or (posizione_reale and len(posizione_reale) == 2): st.success("📡 Satelliti Agganciati! Posizione registrata correttamente.")
    else: st.warning("Ricerca del fix GPS in corso... Assicurati di aver concesso i permessi.")

st.markdown("##### 🗺️ Ispezione Stradale Google Maps")
url_maps = f"https://google.com{st.session_state['lat_x_real']},{st.session_state['lon_x_real']}"
st.link_button("🌐 Apri coordinate su Google Maps (Verifica Corsie e Curve)", url_maps, use_container_width=True)

col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X") and posizione_reale:
        st.session_state["lat_x_real"] = posizione_reale
        st.session_state["lon_x_real"] = posizione_reale
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z") and posizione_reale:
        st.session_state["lat_z_real"] = posizione_reale
        st.session_state["lon_z_real"] = posizione_reale
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_calcolata = calcola_distanza_gps(lat_x, lon_x, lat_z, lon_z)
if dist_calcolata < 0.1: dist_calcolata = 25.05
dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, value=float(round(dist_calcolata, 2)))

st.divider()
st.subheader("🚗 Anagrafica e Rilievo Veicoli")
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti?", options=, index=1)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF"]
default_inputs = [{"xa": 16.60, "za": 2.50, "xp": 18.20, "zp": 2.70, "default_seg": 0}, {"xa": 16.30, "za": 7.80, "xp": 16.80, "zp": 10.55, "default_seg": 1}]

elenco_veicoli = []
for i in range(num_veicoli):
    let = chr(65 + i)
    st.write(f"--- **VEICOLO {let}** ---")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello Veicolo {let}", value=default_modelli[i % 3], key=f"mod_{i}")
        targa = st.text_input(f"Targa Veicolo {let}", value=default_targhe[i % 3], key=f"tg_{i}")
    with col_v2:
        if st.button(f"📍 Prendi GPS di Posizionamento per Veicolo {let}", key=f"btn_gps_v_{i}") and posizione_reale:
            st.session_state[f"lat_v_{i}"] = posizione_reale
            st.session_state[f"lon_v_{i}"] = posizione_reale
        lat_v = st.number_input(f"Lat {let}", value=st.session_state.get(f"lat_v_{i}", 40.019580 + (i * 0.00001)), format="%.6f", key=f"la_in_{i}")
        lon_v = st.number_input(f"Lon {let}", value=st.session_state.get(f"lon_v_{i}", 18.119050 + (i * 0.00001)), format="%.6f", key=f"lo_in_{i}")

    metodo_rilievo = st.radio(f"Metodo Rilievo Misure per Veicolo {let}:", ["📐 Rapido (Solo Ruota Ant. e Post. Sinistra)", "📏 Avanzato (Inserisci tutti e 4 i punti a mano)"], key=f"metodo_{i}")

    if "Rapido" in metodo_rilievo:
        def_idx = default_inputs[i % 2]["default_seg"] if i < len(default_inputs) else 0
        categoria = st.selectbox(f"Categoria Sagoma Standard {let}", options=list(DIZIONARIO_SEGMENTI.keys()), index=def_idx, key=f"cat_{i}")
        larg, lung = DIZIONARIO_SEGMENTI[categoria]["w"], DIZIONARIO_SEGMENTI[categoria]["l"]
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            vx1 = st.number_input(f"Ruota Ant. Sx X (m) [{let}1]", value=default_inputs[i % 2]["xa"] if i < len(default_inputs) else 10.0, key=f"{let}_x1_r")
            vz1 = st.number_input(f"Ruota Ant. Sx Z (m) [{let}1]", value=default_inputs[i % 2]["za"] if i < len(default_inputs) else 2.0, key=f"{let}_z1_r")
        with col_q2:
            vx2 = st.number_input(f"Ruota Post. Sx X (m) [{let}2]", value=default_inputs[i % 2]["xp"] if i < len(default_inputs) else 12.0, key=f"{let}_x2_r")
            vz2 = st.number_input(f"Ruota Post. Sx Z (m) [{let}2]", value=default_inputs[i % 2]["zp"] if i < len(default_inputs) else 2.0, key=f"{let}_z2_r")
        punti_v = calcola_rettangolo_veicolo(vx1, vz1, vx2, vz2, larg, lung)
        tipo_misure = f"Metodo Rapido: R1=({vx1}m, {vz1}m), R2=({vx2}m, {vz2}m) su sagoma {lung}x{larg}m"
    else:
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            vx1 = st.number_input(f"{let}1-X (Ant Sx)", value=16.60 if i==0 else 16.30, key=f"{let}_x1_f")
            vz1 = st.number_input(f"{let}1-Z", value=2.50 if i==0 else 7.80, key=f"{let}_z1_f")
        with col_q2:
            vx2 = st.number_input(f"{let}2-X (Ant Dx)", value=18.20 if i==0 else 16.80, key=f"{let}_x2_f")
            vz2 = st.number_input(f"{let}2-Z", value=2.70 if i==0 else 10.55, key=f"{let}_z2_f")
        with col_q3:
            vx3 = st.number_input(f"{let}3-X (Post Dx)", value=19.00 if i==0 else 18.85, key=f"{let}_x3_f")
            vz3 = st.number_input(f"{let}3-Z", value=0.70 if i==0 else 10.55, key=f"{let}_z3_f")
        with col_q4:
            vx4 = st.number_input(f"{let}4-X (Post Sx)", value=16.80 if i==0 else 18.05, key=f"{let}_x4_f")
            vz4 = st.number_input(f"{let}4-Z", value=0.50 if i==0 else 7.80, key=f"{let}_z4_f")
        punti_v = np.array([[vx1, vz1], [vx2, vz2], [vx3, vz3], [vx4, vz4]])
        tipo_misure = f"Metodo Avanzato a 4 spigoli inseriti manualmente."

    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "punti": punti_v, "descr_misure": tipo_misure, "misure_base": [vx1, vz1, vx2, vz2]})
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
st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta d'intersezione A1 - B1 (m)", value=12.90, format="%.2f")
dist_A2B3 = st.number_input("Distanza diretta d'intersezione A2 - B3 (m)", value=11.40, format="%.2f")

def genera_tavola_grafica():
    fig = plt.figure(figsize=(16, 10), dpi=150)
    grid = plt.GridSpec(2, 1, height_ratios=[7, 3], hspace=0.25)
    ax_mappa = fig.add_subplot(grid[0])
    ax_mappa.set_facecolor('#465a38')
    ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
    ax_mappa.axhline(y=0, color='white', linestyle='-', linewidth=3, zorder=2)
    ax_mappa.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=3, zorder=2)
    if num_corsie > 1:
        spazio_corsia = larg_carreggiata / num_corsie
        for c in range(1, num_corsie):
            quota_linea = - (spazio_corsia * c)
            ax_mappa.axhline(y=quota_linea, color='white', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    if "Curva" in andamento_strada:
        ax_mappa.text((dist_XZ/2), 2.2, f"⚠️ ASSE STRADALE RETTIFICATO - GEOMETRIA IN {andamento_strada.upper()}", color='darkred', weight='bold', ha='center', fontsize=9)
    ax_mappa.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=250, marker='X', edgecolor='white', zorder=10)
    ax_mappa.text(-0.5, 0.5, "Caposaldo X\n(Civico)", color='black', fontsize=9, fontweight='bold', ha='right')
    ax_mappa.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo)", color='black', fontsize=9, fontweight='bold', ha='left')
    ax_mappa.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2, zorder=3)
    ax_mappa.scatter([pu_x], [-pu_z], color='red', s=300, marker='*', edgecolor='white', linewidth=1.5, zorder=8)
    ax_mappa.text(pu_x + 0.5, -pu_z, "P.U.", color='red', weight='bold', fontsize=10, zorder=8)
    ax_mappa.plot([frenata_x, pu_x], [-frenata_z, -pu_z], color='#f1c40f', linestyle='--', linewidth=3, zorder=4)
    ax_mappa.text(frenata_x, -frenata_z + 0.3, "Traccia Frenata", color='#f1c40f', fontsize=8, weight='bold')
    ax_mappa.text(-3, 2.0, f"🧭 Orientamento: {orientamento_nord}", color='black', weight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, pad=2))
    colori_v = ['#1b9cfc', '#718093', '#2ecc71']
    for idx, v in enumerate(elenco_veicoli):
        pts = v["punti"].copy()
        pts[:, 1] = -pts[:, 1]
        col = colori_v[idx % len(colori_v)]
        poly = patches.Polygon(pts, closed=True, facecolor=col, edgecolor='black', linewidth=2, zorder=5)
        ax_mappa.add_patch(poly)
        cx, cz = np.mean(pts[:, 0]), np.mean(pts[:, 1])
        ax_mappa.text(cx, cz, f"Veicolo {v['let']}\n({v['modello']})", color='white', fontsize=9, weight='bold', ha='center', va='center', zorder=6)
        mb = v["misure_base"]
        ax_mappa.plot([mb[0], mb[0]], [0, -mb[1]], color=col, linestyle=':', alpha=0.7)
        ax_mappa.plot([mb[2], mb[2]], [0, -mb[3]], color=col, linestyle=':', alpha=0.7)
    ax_mappa.grid(True, color='#ffffff', linestyle='--', alpha=0.15)
    ax_mappa.set_xlim(-5, dist_XZ + 10)
    ax_mappa.set_ylim(-larg_carreggiata - 4, 3)
    ax_mappa.set_aspect('equal')
    ax_mappa.set_title("SCHIZZO PLANIMETRICO DI RILIEVO - TAVOLA GRAFICA COMPLETA", fontsize=12, weight='bold')
    ax_info = fig.add_subplot(grid[1])
    ax_info.axis('off')
    cartiglio = f"CARTIGLIO DI RILIEVO PROCEDENTE\n• Comando: {stazione}\n• Località: {localita}\n• Data/Ora: {data_ora}\n• Tratto: {andamento_strada} | Orientazione: {orientamento_nord}\n• Operatori: {operanti}"
    ax_info.text(0.01, 0.95, cartiglio, fontsize=8.5, bbox=dict(facecolor='white', edgecolor='#cccccc', boxstyle='round,pad=0.8'), va='top')
    legenda_legge = "LEGENDA E PARAMETRI REGISTRATI:\n"
    for v in elenco_veicoli: legenda_legge += f"• Veicolo {v['let']}: {v['modello']} ({v['targa']}) | GPS: {v['lat']:.5f}, {v['lon']:.5f}\n"
    legenda_legge += f"• Evidenze: Punto d'Urto (P.U.) a X={pu_x}m, Z={pu_z}m | Traccia Frenata inizio X={frenata_x}m\n• Riscontri: A1-B1 = {dist_A1B1}m | A2-B3 = {dist_A2B3}m"
    ax_info.text(0.48, 0.95, legenda_legge, fontsize=8.5, bbox=dict(facecolor='#f8f9fa', edgecolor='#e67e22', boxstyle='round,pad=0.8'), va='top')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

with contenitore_mappa:
    immagine_mappa = genera_tavola_grafica()
    st.image(immagine_mappa, caption="Tavola Grafica Forense Distribuita con Legenda, Corsie, P.U. e Cartiglio Integrato")

st.divider()
st.header("📝 2. Relazione Sintetica dello Stato dei Luoghi")

testo_relazione = f"""RELAZIONE SINTETICA DI RILIEVO STRADALE
Ufficio Procedente: {stazione}\nOperatori sul posto: {operanti}\nLocalità e data: {localita} | Data e Ora: {data_ora}

In data e ora sopra indicate, il personale scrivente è intervenuto nel luogo descritto a causa di un sinistro stradale. I luoghi si presentavano come segue: {note_luogo}. La sede stradale presenta una configurazione in tratto {andamento_strada.upper()} con orientamento cardinale d'allineamento verso {orientamento_nord.upper()}. La carreggiata misura una larghezza complessiva di {larg_carreggiata} metri ed è suddivisa in {num_corsie} corsie di marcia.

Per la determinazione geometrico-topografica dello stato delle cose, si è proceduto a istituire una linea di base d'allineamento legata a due capisaldi geografici stabili:
- Caposaldo X (Origine degli assi cartesiani 0.00): Lat: {lat_x:.6f}, Lon: {lon_x:.6f}
- Mira Z (Fine della linea di orientamento): Lat: {lat_z:.6f}, Lon: {lon_z:.6f}
Distanza metrica rilevata sulla linea di base X-Z: {dist_XZ} metri.

Nel corso dei rilievi è stato individuato il Punto d'Urto presunto (P.U.) individuato alle quote cartesiane X = {pu_x:.2f} m e Z = {pu_z:.2f} m, preceduto da una traccia di frenata/scarrocciamento gommata sull'asfalto avente inizio alla quota X = {frenata_x:.2f} m e Z = {frenata_z:.2f} m.

Sulla scorta di tale allineamento, sono state cristallizzate le posizioni statiche di quiete dei seguenti veicoli coinvolti:\n"""

for v in elenco_veicoli: testo_relazione += f"- Veicolo {v['let']}: {v['modello']}, targa {v['targa']}. Posizionamento GPS registrato: {v['lat']:.6f}, {v['lon']:.6f}. {v['descr_misure']}.\n"

testo_relazione += f"\nA riscontro incrociato delle misure di rilievo ortogonale e a garanzia della precisione millimetrica della tavola grafica, sono state misurate le seguenti distanze dirette di intersecazione tra i mezzi sul campo:\n"
testo_relazione += f"- Distanza diretta registrata tra lo spigolo A1 ed il punto B1: {dist_A1B1} metri.\n"
testo_relazione += f"- Distanza diretta registrata tra lo spigolo A2 ed il punto B3: {dist_A2B3} metri.\n"
testo_relazione += f"\nI rilievi si sono conclusi regolarmente, con successivo sgombero della carreggiata per il ripristino della viabilità."

st.text_area("Copia il testo della relazione per il verbale d'ufficio:", value=testo_relazione, height=350)

if st.button("🏗️ RIGENERA INTERO ELABORATO E MAPPA", type="primary", use_container_width=True): st.success("Planimetria, cartiglio e relazione scritta aggiornati in base ai nuovi parametri inseriti!")
    
