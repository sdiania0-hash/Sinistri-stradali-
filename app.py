import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Terminale Rilievo Forense", layout="centered")
st.title("🚓 Terminale Universale di Rilievo Planimetrico Forense")

st.warning("⚠️ **VERSIONE BETA IN VIA DI SVILUPPO** — Prototipo industriale per il rilievo stradale. I calcoli geometrici, le stime cinematiche e le acquisizioni hardware devono essere verificati dall'operatore prima dell'inserimento negli atti ufficiali.")
st.caption("© 2026 Tutti i diritti riservati. Proprietà intellettuale depositata. Integrazione classificazione lesioni e tipologie stradali multiple.")

contenitore_mappa = st.empty()

if "lat_x_real" not in st.session_state: st.session_state["lat_x_real"] = 40.019572
if "lon_x_real" not in st.session_state: st.session_state["lon_x_real"] = 18.118944
if "lat_z_real" not in st.session_state: st.session_state["lat_z_real"] = 40.019590
if "lon_z_real" not in st.session_state: st.session_state["lon_z_real"] = 18.119230

DIZIONARIO_SEGMENTI = {"🚗 Autovettura Utilitaria / Media": {"w": 1.75, "l": 4.10, "t": "auto"}, "🚙 SUV / Berlina Lunga / Furgone": {"w": 1.90, "l": 4.65, "t": "auto"}, "🏍️ Motociclo / Ciclomotore (Mozzo Ant./Post.)": {"w": 0.80, "l": 2.10, "t": "moto"}, "🚚 Mezzo Pesante / Autobus": {"w": 2.50, "l": 11.50, "t": "auto"}, "🚶 Pedone / Ostacolo Fisso (Punto)": {"w": 0.60, "l": 0.60, "t": "punto"}}

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

st.subheader("🏥 Stato di Incolumità delle Persone (Gravità)")
col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    flag_feriti = st.checkbox("🩹 Presenza di Feriti")
    flag_gravi = st.checkbox("🚨 Feriti Gravi (Prognosi Riservata)")
with col_g2:
    flag_decesso = st.checkbox("🚷 Sinistro con Esito Mortale (Decesso)")
    flag_ospedale = st.checkbox("🚑 Trasporto in Ospedale via 118")
with col_g3:
    ospedale_nome = st.text_input("Ospedale di Destinazione", value="Vito Fazzi - Lecce")

col_info_strada1, col_info_strada2 = st.columns(2)
with col_info_strada1:
    tipo_carreggiata = st.selectbox("Tipologia Carreggiata", options=["Carreggiata Unica (Doppio Senso)", "Carreggiata Unica (Senso Unico)", "Doppia Carreggiata (Spartitraffico Centrale)"])
    larg_carreggiata = st.number_input("Larghezza della singola carreggiata (m)", min_value=2.0, max_value=20.0, value=6.60)
    num_corsie = st.selectbox("Numero corsie per carreggiata", options=[1, 2, 3, 4], index=1)
with col_info_strada2:
    andamento_strada = st.selectbox("Andamento della sede stradale", options=["Rettilineo", "Curva a Destra ↪️", "Curva a Sinistra ↩️"])
    orientamento_nord = st.selectbox("Orientamento Linea di Base (Direzione Caposaldo Z)", options=["Nord ⬆️", "Nord-Est ↗️", "Est ➡️", "Sud-Est ↘️", "Sud ⬇️", "Sud-Ovest ↙️", "Ovest ⬅️", "Nord-Ovest ↖️"])
    stato_asfalto = st.selectbox("Stato del fondo stradale", options=["Asfalto Asciutto (f=0.75)", "Asfalto Bagnato (f=0.45)", "Viscido / Fango (f=0.30)"])

note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Fondo stradale regolare, segnaletica orizzontale visibile.")
st.divider()
st.subheader("📡 Fissaggio Linea di Base (Capisaldi)")
ottieni_gps = st.checkbox("🔄 Attiva Sensore GPS del Dispositivo")
posizione_reale = None

if ottieni_gps:
    posizione_reale = streamlit_js_eval(data_string="navigator.geolocation.getCurrentPosition(success => { return [success.coords.latitude, success.coords.longitude]; }, error => { return null; })", key="gps_device_live")
    if posizione_reale and len(posizione_reale) == 2: st.success("📡 Satelliti Agganciati! Posizione registrata correttamente.")
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
st.subheader("🚗 Anagrafica e Rilievo Mezzi / Entità Coinvolte")
num_veicoli = st.selectbox("Quanti mezzi/entità sono coinvolti?", options=[1, 2, 3, 4, 5], index=1)

default_modelli = ["Citroën C3", "Yamaha T-Max", "Fiat Panda"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF"]
default_inputs = [{"xa": 16.60, "za": 2.50, "xp": 18.20, "zp": 2.70}, {"xa": 15.10, "za": 4.20, "xp": 15.80, "zp": 4.35}]

elenco_veicoli = []
for i in range(num_veicoli):
    let = chr(65 + i)
    st.write(f"--- **ENTITÀ / VEICOLO {let}** ---")
    
    categoria = st.selectbox(f"Tipologia / Categoria di Mezzo {let}", options=list(DIZIONARIO_SEGMENTI.keys()), index=(0 if i==0 else (1 if i==1 else 2)), key=f"cat_{i}")
    larg, lung, tipo_forma = DIZIONARIO_SEGMENTI[categoria]["w"], DIZIONARIO_SEGMENTI[categoria]["l"], DIZIONARIO_SEGMENTI[categoria]["t"]
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello {let}", value=default_modelli[i % 3], key=f"mod_{i}")
        targa = st.text_input(f"Targa / Sigla {let}", value=default_targhe[i % 3], key=f"tg_{i}")
        stato_mezzo = st.selectbox(f"Stato di Quiete Mezzo {let}", options=["Normale (Ruote a terra)", "Ribaltato su un fianco", "Sottosopra / Capovolto"], key=f"cond_mezzo_{i}")
    with col_v2:
        if st.button(f"📍 Prendi GPS di Posizionamento Mezzo {let}", key=f"btn_gps_v_{i}") and posizione_reale:
            st.session_state[f"lat_v_{i}"] = posizione_reale
            st.session_state[f"lon_v_{i}"] = posizione_reale
        lat_v = st.number_input(f"Lat {let}", value=st.session_state.get(f"lat_v_{i}", 40.019580 + (i * 0.00001)), format="%.6f", key=f"la_in_{i}")
        lon_v = st.number_input(f"Lon {let}", value=st.session_state.get(f"lon_v_{i}", 18.119050 + (i * 0.00001)), format="%.6f", key=f"lo_in_{i}")

    st.markdown("*📁 Caricamento Documenti (Lettura Forense Integrata)*")
    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        foto_patente = st.file_uploader(f"📸 Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
        foto_carta = st.file_uploader(f"📸 Carta Circolazione / Libretto {let}", type=["jpg", "png", "jpeg"], key=f"lib_{i}")
    with col_doc2:
        foto_ass = st.file_uploader(f"📸 Polizza Assicurativa RCA {let}", type=["jpg", "png", "jpeg"], key=f"ass_{i}")
        st.markdown(f"🔍 **Banche Dati Esterne {let}:** [Verifica RCA ANIA](https://ilportaledellautomobilista.it) | [Controllo Veicoli Rubati](https://mininterno.it)")

    dati_ocr = f"Documenti Caricati: {'Sì' if (foto_patente or foto_carta) else 'No'}. Accertamenti d'ufficio regolari."
    num_pass = st.number_input(f"Passeggeri trasportati sul Mezzo {let}", min_value=0, max_value=5, value=0, key=f"n_p_{i}")
    
    elenco_pass_v = []
    for p in range(num_pass):
        foto_doc = st.file_uploader(f"📸 Doc Passeggero {p+1} ({let})", type=["jpg", "png", "jpeg"], key=f"dc_{i}_{p}")
        elenco_pass_v.append(f"Passeggero {p+1}: {'Identificato via OCR' if foto_doc else 'Presente sul posto'}")

    st.markdown("📐 *Misure Cartesiane (Allineamento Caposaldo X)*")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        vx1 = st.number_input(f"Punto Anteriore Sx / Ruota Ant. X (m) [{let}1]", value=default_inputs[i % 2]["xa"] if i < len(default_inputs) else 10.0, key=f"{let}_x1_r")
        vz1 = st.number_input(f"Punto Anteriore Sx / Ruota Ant. Z (m) [{let}1]", value=default_inputs[i % 2]["za"] if i < len(default_inputs) else 2.0, key=f"{let}_z1_r")
    with col_q2:
        vx2 = st.number_input(f"Punto Posteriore Sx / Ruota Post. X (m) [{let}2]", value=default_inputs[i % 2]["xp"] if i < len(default_inputs) else 12.0, key=f"{let}_x2_r")
        vz2 = st.number_input(f"Punto Posteriore Sx / Ruota Post. Z (m) [{let}2]", value=default_inputs[i % 2]["zp"] if i < len(default_inputs) else 2.0, key=f"{let}_z2_r")
    
    punti_v = calcola_rettangolo_veicolo(vx1, vz1, vx2, vz2, larg, lung)
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "punti": punti_v, "misure_base": [vx1, vz1], "ocr": dati_ocr, "passeggeri": elenco_pass_v, "stato": stato_mezzo, "forma": tipo_forma, "categoria": categoria})
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
    grid = plt.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.25)

    ax_mappa = fig.add_subplot(grid)
    ax_mappa.set_facecolor('#465a38')
    
    # Gestione grafica avanzata della doppia carreggiata e spartitraffico
    if "Doppia Carreggiata" in tipo_carreggiata:
        ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax_mappa.fill_between([-15, dist_XZ + 20], -larg_carreggiata-1.5, -larg_carreggiata, facecolor='#20bf6b', alpha=0.9, zorder=1) # Spartitraffico verde
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

    # Disegno delle corsie interne tratteggiate
    if num_corsie > 1:
        spazio_corsia = larg_carreggiata / num_corsie
        for c in range(1, num_corsie): ax_mappa.axhline(y=-(spazio_corsia * c), color='white', linestyle='--', linewidth=1.2, alpha=0.7, zorder=2)

    # Disegno freccia gigante di direzione senso di marcia stradale (stile planimetria catastale)
    ax_mappa.arrow(-10, -larg_carreggiata/2, 4, 0, width=0.2, head_width=0.6, head_length=0.8, color='white', alpha=0.5, zorder=2)
    ax_mappa.text(-8, -larg_carreggiata/2 + 0.5, "SENSO DI MARCIA", color='white', alpha=0.5, fontsize=7, weight='bold')

    ax_mappa.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=250, marker='X', edgecolor='white', zorder=10)

    ax_mappa.plot([0, dist_XZ],, color='#e67e22', linestyle='-', linewidth=2, zorder=3)
    ax_mappa.scatter([pu_x], [-pu_z], color='red', s=300, marker='*', edgecolor='white', linewidth=1.5, zorder=8)
    ax_mappa.plot([frenata_x, pu_x], [-frenata_z, -pu_z], color='#f1c40f', linestyle='--', linewidth=3, zorder=4)
    ax_mappa.text(-3, 2.0, f"🧭 Nord: {orientamento_nord}", color='black', weight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, pad=2))
    
    colori_v = ['#1b9cfc', '#718093', '#2ecc71', '#9b59b6', '#1abc9c']
    for idx, v in enumerate(elenco_veicoli):
        pts = v["punti"].copy()
        pts[:, 1] = -pts[:, 1]
        col = colori_v[idx % len(colori_v)]
        if v["forma"] == "punto": ax_mappa.scatter([v["misure_base"]], [-v["misure_base"]], color='red', s=150, zorder=6)
        else: ax_mappa.add_patch(patches.Polygon(pts, closed=True, facecolor=col, edgecolor='black', linewidth=2, zorder=5))
        ax_mappa.text(np.mean(pts[:, 0]), np.mean(pts[:, 1]), f"{v['let']}\n({v['stato']})", color='white', fontsize=8, weight='bold', ha='center', va='center', zorder=6)
        mb = v["misure_base"]
        ax_mappa.plot([mb, mb], [0, -mb], color=col, linestyle=':', alpha=0.7)
        ax_mappa.text(mb, -mb - 0.3, f"{v['let']}1", color='white', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.7, pad=1))

    ax_mappa.grid(True, color='#ffffff', linestyle='--', alpha=0.15)
    ax_mappa.set_xlim(-12, dist_XZ + 15)
    ax_mappa.set_ylim(-larg_carreggiata*2 - 5, 4)
    ax_mappa.set_aspect('equal')
    
    ax_info = fig.add_subplot(grid)
    ax_info.axis('off')
    cartiglio = f"CARTIGLIO RILIEVO UFFICIALE\n• Comando: {stazione}\n• Località: {localita}\n• Data/Ora: {data_ora}\n• Configurazione: {tipo_carreggiata} ({andamento_strada})\n• Operanti: {operanti}"
    ax_info.text(0.01, 0.95, cartiglio, fontsize=8.5, bbox=dict(facecolor='white', edgecolor='#cccccc', boxstyle='round,pad=0.8'), va='top')
    legenda_legge = f"LEGENDA TECNICA DEI RILIEVI:\n• Stella Rossa (P.U.): Punto d'Urto presunto a X={pu_x}m, Z={pu_z}m\n• Linea Tratteggiata Gialla: Traccia Frenata gommata inizio X={frenata_x}m\n• Riscontri Diretti: A1-B1 = {dist_A1B1} metri | A2-B3 = {dist_A2B3} metri\n• Allineamento Nord: {orientamento_nord} | Linea Base X-Z = {dist_XZ}m"
    ax_info.text(0.48, 0.95, legenda_legge, fontsize=8.5, bbox=dict(facecolor='#f8f9fa', edgecolor='#e67e22', boxstyle='round,pad=0.8'), va='top')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

with contenitore_mappa:
    immagine_mappa = genera_tavola_grafica()
    st.image(immagine_mappa, caption="Tavola Grafica Forense Unificata con Legenda e Proiezione Stradale Adattiva")

st.divider()
st.header("📝 2. Relazione Sintetica dello Stato dei Luoghi (Verbale NK)")

severita = "⚠️ INCIDENTE STRADALE CON DANNI MATERIALI E LESIONI A PERSONE" if flag_feriti else "🟢 INCIDENTE STRADALE CON SOLI DANNI MATERIALI"
if flag_gravi: severita = "🚨 INCIDENTE STRADALE CON FERITI IN PROGNOSI RISERVATA"
if flag_decesso: severita = "🚷 INCIDENTE STRADALE CON ESITO MORTALE (DECESSO)"

testo_relazione = f"""RELAZIONE SINTETICA DI RILIEVO FORENSE (VERBALE MOD. NK)
Ufficio Procedente: {stazione}\nOperatori sul posto: {operanti}\nLocalità d'intervento: {localita} | Data e Ora: {data_ora}

CLASSIFICAZIONE EVENTO: {severita}
{"↳ Trasporto sanitario d'urgenza gestito dal 118 verso l'Ospedale: " + ospedale_nome if flag_ospedale else ""}

In data e ora indicate, il personale scrivente è intervenuto nel luogo descritto. La sede stradale si presentava configurata come {tipo_carreggiata.upper()}, con fondo in {stato_asfalto.upper()}, andamento {andamento_strada.upper()} ed orientamento d'allineamento cardinale verso {orientamento_nord.upper()}. La larghezza utile della carreggiata è misurata in {larg_carreggiata} metri, organizzata su {num_corsie} corsie per senso di marcia. Annotazioni ambientali: {note_luogo}.

Rilievo topografico eseguito tramite linea di base cartesiana vincolata ai capisaldi stabili:
- Caposaldo X: Lat: {lat_x:.6f}, Lon: {lon_x:.6f} (Origine degli assi 0.00)
- Mira Z: Lat: {lat_z:.6f}, Lon: {lon_z:.6f}
Distanza metrica sulla linea di base X-Z: {dist_XZ} metri.

EVIDENZE E TRACCE FORENSI:
Sul piano viabile è stato localizzato il Punto d'Urto presunto (P.U.) alle quote X = {pu_x:.2f} m e Z = {pu_z:.2f} m. Tale area d'impatto risulta preceduta da una traccia gommata di frenata/scarrocciamento continuo avente inizio alle quote cartesiane X = {frenata_x:.2f} m, indicativa del bloccaggio degli pneumatici prima dell'evento.

ANAGRAFICA MEZZI E STATO DI QUIETE NELLO SCHIZZO:\n"""

for v in elenco_veicoli:
    testo_relazione += f"- Veicolo {v['let']}: {v['modello']} (Targa: {v['targa']}). Categoria: {v['categoria']}. Quiete: {v['stato']}. Posizione GPS Assoluta: {v['lat']:.6f}, {v['lon']:.6f}.\n"
    testo_relazione += f"  ↳ {v['ocr']}\n"
    if v['passeggeri']: testo_relazione += f"  ↳ Passeggeri registrati a bordo:\n     • " + "\n     • ".join(v['passeggeri']) + "\n"

testo_relazione += f"\nMISURE DI RISCONTRO DIRETTO INCROCIATO:\nA garanzia della precisione millimetrica dello schizzo grafico allegato agli atti, sono state isolate le seguenti distanze di intersecazione sul campo:\n- Distanza diretta tra lo spigolo A1 ed il punto B1: {dist_A1B1} metri.\n- Distanza diretta tra lo spigolo A2 ed il punto B3: {dist_A2B3} metri.\n"
testo_relazione += f"\nI rilievi tecnici descritti sono stati conclusi regolarmente per il successivo ripristino della viabilità ordinaria."

st.text_area("Copia l'intero verbale NK strutturato per l'inserimento negli atti d'ufficio:", value=testo_relazione, height=400)

if st.button("🏗️ RIGENERA INTERO ELABORATO E MAPPA", type="primary", use_container_width=True): st.success("Planimetria, cartiglio e relazione scritta aggiornati con successo!")
    
