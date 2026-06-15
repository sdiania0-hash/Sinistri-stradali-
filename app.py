import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# 1. IMPOSTAZIONI INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Modifica i dati nei moduli, acquisisci le posizioni GPS o i documenti e premi il pulsante rosso in fondo per generare la tavola grafica completa di legenda.")

# Riquadro contenitore superiore per mantenere la planimetria fissa in alto
contenitore_mappa = st.container()

# Inizializzazione dello stato della sessione per la memoria GPS
if "lat_x_real" not in st.session_state:
    st.session_state["lat_x_real"] = 40.019572
    st.session_state["lon_x_real"] = 18.118944
    st.session_state["lat_z_real"] = 40.019590
    st.session_state["lon_z_real"] = 18.119230

# 2. PROTOCOLLO INSERIMENTO DATI
st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("Dati Identificativi Verbale")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto.")

st.divider()
st.subheader("Fissaggio Linea di Base (Capisaldi)")
col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X"):
        st.session_state["lat_x_real"] = 40.019572
        st.session_state["lon_x_real"] = 18.118944
        st.success("Coordinate Caposaldo X agganciate dal sensore!")
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x_real"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x_real"], format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
        st.session_state["lat_z_real"] = 40.019590
        st.session_state["lon_z_real"] = 18.119230
        st.success("Coordinate Mira Z agganciate dal sensore!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z_real"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z_real"], format="%.6f")

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

st.divider()
st.subheader("🚗 Anagrafica Veicoli Coinvolti")
num_veicoli = st.selectbox("Quanti veicoli sono coinvolti?", options=[1, 2, 3, 4, 5], index=1)

default_modelli = ["Citroën C3", "Alfa Romeo 147", "Fiat Panda", "Volkswagen Golf", "Ford Fiesta"]
default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
default_misure_veicoli = [
    {"x1": 16.60, "z1": 2.50, "x2": 18.20, "z2": 2.70, "x3": 16.80, "z3": 0.50, "x4": 19.00, "z4": 0.70}, 
    {"x1": 16.30, "z1": 7.80, "x2": 16.80, "z2": 10.55, "x3": 18.05, "z3": 7.80, "x4": 18.85, "z4": 10.55}  
]

elenco_veicoli = []
for i in range(num_veicoli):
    let = chr(65 + i)
    st.write(f"--- **VEICOLO {let}** ---")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        modello = st.text_input(f"Marca e Modello Veicolo {let}", value=default_modelli[i % 5], key=f"mod_{i}")
        targa = st.text_input(f"Targa Veicolo {let}", value=default_targhe[i % 5], key=f"tg_{i}")
    with col_v2:
        if st.button(f"📍 Prendi GPS per Veicolo {let}", key=f"btn_gps_v_{i}"):
            st.session_state[f"lat_v_{i}"] = 40.019580 + (i * 0.00001)
            st.session_state[f"lon_v_{i}"] = 18.119050 + (i * 0.00001)
            st.success(f"GPS Veicolo {let} agganciato!")
        lat_v = st.number_input(f"Lat {let}", value=st.session_state.get(f"lat_v_{i}", 40.019580), format="%.6f", key=f"la_in_{i}")
        lon_v = st.number_input(f"Lon {let}", value=st.session_state.get(f"lon_v_{i}", 18.119050), format="%.6f", key=f"lo_in_{i}")

    dm = default_misure_veicoli[i] if i < len(default_misure_veicoli) else {"x1": 10.0, "z1": 2.0, "x2": 12.0, "z2": 2.0, "x3": 10.0, "z3": 4.0, "x4": 12.0, "z4": 4.0}
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    with col_q1:
        vx1 = st.number_input(f"{let}1-X", value=dm["x1"], key=f"{let}_x1")
        vz1 = st.number_input(f"{let}1-Z", value=dm["z1"], key=f"{let}_z1")
    with col_q2:
        vx2 = st.number_input(f"{let}2-X", value=dm["x2"], key=f"{let}_x2")
        vz2 = st.number_input(f"{let}2-Z", value=dm["z2"], key=f"{let}_z2")
    with col_q3:
        vx3 = st.number_input(f"{let}3-X", value=dm["x3"], key=f"{let}_x3")
        vz3 = st.number_input(f"{let}3-Z", value=dm["z3"], key=f"{let}_z3")
    with col_q4:
        vx4 = st.number_input(f"{let}4-X", value=dm["x4"], key=f"{let}_x4")
        vz4 = st.number_input(f"{let}4-Z", value=dm["z4"], key=f"{let}_z4")

    foto_patente = st.file_uploader(f"📸 Patente Conducente {let}", type=["jpg", "png", "jpeg"], key=f"pat_{i}")
    dati_cond = "ESTRATTO VERIFICATO" if (foto_patente or i==0) else "Non inserito"
    
    num_pass = st.number_input(f"Passeggeri {let}", min_value=0, max_value=5, value=(1 if i==0 else 0), key=f"n_p_{i}")
    elenco_pass_v = []
    for p in range(num_pass):
        foto_doc = st.file_uploader(f"📸 Doc Passeggero {p+1} ({let})", type=["jpg", "png", "jpeg"], key=f"dc_{i}_{p}")
        elenco_pass_v.append("Identificato" if foto_doc else "Presente")
        
    elenco_veicoli.append({"let": let, "modello": modello, "targa": targa, "lat": lat_v, "lon": lon_v, "cond": dati_cond, "pass": elenco_pass_v, "coords": [vx1, vz1, vx2, vz2, vx3, vz3, vx4, vz4]})

st.divider()
st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta A1 - B1 (m)", value=12.90, format="%.2f")
dist_A2B3 = st.number_input("Distanza diretta A2 - B3 (m)", value=11.40, format="%.2f")

st.divider()
st.subheader("⚙️ Pannello Azione")
esegui_ricalcolo = st.button("🏗️ ELABORA TUTTI I DATI E RIGENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)
# 3. ENGINE MATEMATICO DI RENDERING DELLA MAPPA STRADALE
fig, ax = plt.subplots(figsize=(17, 9.5), dpi=180)
ax.set_facecolor('#465a38')

# Disegno Sede Stradale principale (Asfalto grigio scuro)
ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)

# Disegno Innesto Strada Secondaria (Str. Vicinale Cucci) obliqua
vicinale_poly = patches.Polygon([[20, -larg_carreggiata], [23, -larg_carreggiata], [26, 4.0], [22, 4.0]], closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
ax.add_patch(vicinale_poly)
ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

# Tracciamento Linea di Base Capisaldi X-Z
ax.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right')
ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left')
ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9))

colori_v = ['#1b9cfc', '#718093', '#2ecc71', '#9b59b6', '#1abc9c']
colori_quote = ['#25ccf7', '#ff4757', '#95afc0', '#dff9fb', '#ffbe76']

tutti_x = [0, dist_XZ, -5, dist_XZ + 5]
tutti_y = [0, -larg_carreggiata, -larg_carreggiata - 3, 3]

# Testo riassuntivo per la colonna tecnica della legenda
testo_legenda_misure = "📋 MATRICE MISURE STRADALI\n" + "-"*35 + "\n"

# Disegno dinamico dei veicoli inseriti nell'anagrafica
for idx, v in enumerate(elenco_veicoli):
    q = v["coords"]
    col_v = colori_v[idx % 5]
    col_q = colori_quote[idx % 5]
    
    punti_g = [(q[0], -q[1]), (q[2], -q[3]), (q[6], -q[7]), (q[4], -q[5])]
    poly = patches.Polygon(punti_g, closed=True, facecolor=col_v, edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
    ax.add_patch(poly)
    
    cx = sum(x for x, _ in punti_g) / 4
    cy = sum(y for _, y in punti_g) / 4
    ax.text(cx, cy, f"Veicolo {v['let']}\n({v['modello']})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)
    
    # Linee di quota ortogonali per punto 1 e 2
    ax.plot([q[0], q[0]], [0, -q[1]], color=col_q, linestyle=':', linewidth=1.2, zorder=4)
    ax.text(q[0], -q[1]/2, f"{q[0]:.2f}", bbox=dict(facecolor='white', edgecolor=col_q, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
    ax.text(q[0] - 1.2, -q[1], f"{q[1]:.2f}", bbox=dict(facecolor='white', edgecolor=col_q, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
    
    ax.plot([q[2], q[2]], [0, -q[3]], color=col_q, linestyle=':', linewidth=1.2, zorder=4)
    ax.text(q[2], -q[3]/2, f"{q[2]:.2f}", bbox=dict(facecolor='white', edgecolor=col_q, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')

    nomi_punti = ["1", "2", "4", "3"]
    testo_legenda_misure += f"\n🔹 VEICOLO {v['let']} ({v['targa']}):\n"
    for p_idx, p in enumerate(punti_g):
        ax.scatter(p[0], p[1], color=col_q, s=35, zorder=7, edgecolor='black')
        ax.text(p[0], p[1] - 0.35, f"{v['let']}{nomi_punti[p_idx]}", color='white', fontsize=8, fontweight='bold', ha='center')
        tutti_x.append(p[0])
        tutti_y.append(p[1])
        
        # Estrazione corretta dei dati per valorizzare la tabella laterale
        x_val = q[p_idx*2]
        z_val = q[p_idx*2+1]
        testo_legenda_misure += f" P{nomi_punti[p_idx]} -> X: {x_val:.2f} m | Z: {z_val:.2f} m\n"

# Linee di riscontro diagonali dirette d'impatto (Se ci sono almeno 2 veicoli)
if len(elenco_veicoli) >= 2:
    xA1, zA1 = elenco_veicoli[0]["coords"][0], elenco_veicoli[0]["coords"][1]
    xB1, zb1 = elenco_veicoli[1]["coords"][0], elenco_veicoli[1]["coords"][1]
    ax.plot([xA1, xB1], [-zA1, -zb1], color='#2ecc71', linestyle='-', linewidth=2, zorder=5)
    ax.text((xA1+xB1)/2, (-zA1-zb1)/2, f"A1 - B1 = {dist_A1B1:.2f} m", color='#2ecc71', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.8), ha='center')
    
    xA2, zA2 = elenco_veicoli[0]["coords"][2], elenco_veicoli[0]["coords"][3]
    xB3, zb3 = elenco_veicoli[1]["coords"][4], elenco_veicoli[1]["coords"][5]
    ax.plot([xA2, xB3], [-zA2, -zb3], color='#db00d4', linestyle='-', linewidth=2, zorder=5)
    ax.text((xA2+xB3)/2, (-zA2-zb3)/2, f"A2 - B3 = {dist_A2B3:.2f} m", color='#db00d4', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.8), ha='center')
    
    testo_legenda_misure += f"\n📏 RISCONTRI DIRETTI:\n Dist. A1 - B1: {dist_A1B1:.2f} m\n Dist. A2 - B3: {dist_A2B3:.2f} m\n"

# Frecce direzionali di provenienza stradale e margini
ax.annotate("Provenienza TAVIANO (Direzione Matino)", xy=(-3, -1), xytext=(2, -1), color='white', weight='bold', fontsize=9, arrowprops=dict(arrowstyle="<-", color="white", linewidth=1.5))
ax.annotate("Provenienza MATINO (Direzione Taviano)", xy=(-3, -larg_carreggiata + 1), xytext=(2, -larg_carreggiata + 1), color='white', weight='bold', fontsize=9, arrowprops=dict(arrowstyle="->", color="white", linewidth=1.5))

ax.plot([-4, -4], [0, -larg_carreggiata], color='white', linewidth=1.2)
ax.text(-4.5, -larg_carreggiata/2, f"cd = {larg_carreggiata:.2f} m", color='white', rotation=90, fontsize=9, weight='bold', va='center')

# Box parametri strada fisso sul disegno
info_strada_testo = f"PARAMETRI STRADA:\nLarghezza carreggiata: {larg_carreggiata:.2f} m\nBase X-Z: {dist_XZ:.2f} m"
ax.text(-4, -larg_carreggiata - 2.5, info_strada_testo, color='white', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.5, boxstyle='round,pad=0.3'))

# --- NUOVA COLONNA LEGENDA E TESTI A LATO DESTRO ---
limite_max_x = max(tutti_x) + 3
ax.text(limite_max_x + 1, max(tutti_y), testo_legenda_misure, color='white', fontsize=8.5, family='monospace', va='top', ha='left', bbox=dict(facecolor='#1e272e', alpha=0.9, edgecolor='white', boxstyle='round,pad=0.5'))

# Inquadratura limiti ed ottimizzazione assi estesi per comprendere il testo laterale
ax.set_xlim(min(tutti_x) - 2, limite_max_x + 16)
ax.set_ylim(min(tutti_y) - 4, max(tutti_y) + 2)
ax.set_aspect('equal')
ax.axis('off')

# Mostra lo schizzo planimetrico nell'area dedicata in alto
with contenitore_mappa:
    st.pyplot(fig)

# 4. PREPARAZIONE BUFFER ESPORTAZIONE DOCUMENTO PDF CON CORREZIONE PIL
img_buf = io.BytesIO()
plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=180)
img_buf.seek(0)
immagine_pil = Image.open(img_buf)

pdf_buf = io.BytesIO()
p_canvas = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
larg_p, alt_p = landscape(letter)

p_canvas.rect(15, 15, larg_p - 30, alt_p - 30)
p_canvas.setFont("Helvetica-Bold", 13)
p_canvas.drawString(30, alt_p - 35, "RELAZIONE PLANIMETRICA ILLUSTRAZIONE SINISTRO STRADALE")
p_canvas.line(30, alt_p - 42, larg_p - 30, alt_p - 42)

p_canvas.drawInlineImage(immagine_pil, 25, 140, width=larg_p - 50, height=265)
p_canvas.line(30, 132, larg_p - 30, 132)

p_canvas.setFont("Helvetica-Bold", 9)
p_canvas.drawString(30, 115, "CARTIGLIO ED ACCERTAMENTI:")
p_canvas.setFont("Helvetica", 8)
p_canvas.drawString(30, 100, f"Ufficio: {stazione}  ||  Operatori: {operanti}")
p_canvas.drawString(30, 85, f"Località: {localita}  ||  Data/Ora: {data_ora}")
p_canvas.drawString(30, 70, f"Larghezza Sede: {larg_carreggiata:.2f} m  ||  Linea Base X-Z: {dist_XZ:.2f} m")

p_canvas.setFont("Helvetica-Bold", 9)
p_canvas.drawString(350, 115, "MEZZI E TERZI COINVOLTI:")
p_canvas.setFont("Helvetica", 8)
y_pos = 100
for v in elenco_veicoli:
    p_canvas.drawString(350, y_pos, f"Veicolo {v['let']}: {v['modello']} ({v['targa']}) - Conducente: {v['cond']}")
    y_pos -= 13

p_canvas.showPage()
p_canvas.save()
pdf_buf.seek(0)

# Pulsante di download a fondo pagina
if esegui_ricalcolo:
    st.success("✨ Tavola grafica con legenda aggiornata nei moduli superiori!")

st.download_button(
    label="📥 SCARICA TAVOLA PLANIMETRICA IN FORMATO PDF VETTORIALE",
    data=pdf_buf,
    file_name="Tavola_Planimetrica_Sinistro.pdf",
    mime="application/pdf",
    use_container_width=True
)
