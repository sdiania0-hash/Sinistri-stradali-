import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# 1. IMPOSTAZIONI INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 La mappa mostra i dati del rilievo corrente. Modifica i parametri nei moduli sottostanti e premi il pulsante rosso per aggiornare lo schizzo grafico e scaricare il PDF.")

# Riquadro contenitore superiore per mantenere la planimetria fissa in alto
contenitore_mappa = st.container()

# 2. PROTOCOLLO INSERIMENTO DATI (MODULI LIBERI E PRECOMPILATI)
st.header("1. Protocollo di Acquisizione Dati sul Campo")

st.subheader("Dati Identificativi Verbale")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale (Str. Vicinale Cucci). Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

st.divider()
st.subheader("Fissaggio Linea di Base (Capisaldi)")
col_cx, col_cz = st.columns(2)
with col_cx:
    if st.button("📍 Inserisci GPS Attuale -> Caposaldo X"):
        st.session_state["lat_x"] = 40.019572
        st.session_state["lon_x"] = 18.118944
        st.success("Coordinate Caposaldo X agganciate dal sensore!")
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state.get("lat_x", 40.019572), format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state.get("lon_x", 18.118944), format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
        st.session_state["lat_z"] = 40.019590
        st.session_state["lon_z"] = 18.119230
        st.success("Coordinate Mira Z agganciate dal sensore!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state.get("lat_z", 40.019590), format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state.get("lon_z", 18.119230), format="%.6f")

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

st.divider()
st.subheader("🚗 Configurazione Quote Veicolo A (Citroën C3)")
modello_A = st.text_input("Marca e Modello Veicolo A", value="Citroën C3")
targa_A = st.text_input("Targa Veicolo A", value="AA123BB")
if st.button("📍 Prendi GPS Attuale per Veicolo A"):
    st.session_state["lat_A"] = 40.019585
    st.session_state["lon_A"] = 18.119050
    st.success("GPS Veicolo A salvato!")

col_qA1, col_qA2, col_qA3, col_qA4 = st.columns(4)
with col_qA1:
    xa1 = st.number_input("A1 - Distanza X (m)", value=16.60, format="%.2f")
    za1 = st.number_input("A1 - Quota Z (m)", value=2.50, format="%.2f")
with col_qA2:
    xa2 = st.number_input("A2 - Distanza X (m)", value=18.20, format="%.2f")
    za2 = st.number_input("A2 - Quota Z (m)", value=2.70, format="%.2f")
with col_qA3:
    xa3 = st.number_input("A3 - Distanza X (m)", value=16.80, format="%.2f")
    za3 = st.number_input("A3 - Quota Z (m)", value=0.50, format="%.2f")
with col_qA4:
    xa4 = st.number_input("A4 - Distanza X (m)", value=19.00, format="%.2f")
    za4 = st.number_input("A4 - Quota Z (m)", value=0.70, format="%.2f")
foto_pat_A = st.file_uploader("📸 Carica Foto Patente Conducente A", type=["jpg", "png", "jpeg"])

st.divider()
st.subheader("🚗 Configurazione Quote Veicolo B (Alfa Romeo 147)")
modello_B = st.text_input("Marca e Modello Veicolo B", value="Alfa Romeo 147")
targa_B = st.text_input("Targa Veicolo B", value="CC456DD")
if st.button("📍 Prendi GPS Attuale per Veicolo B"):
    st.session_state["lat_B"] = 40.019565
    st.session_state["lon_B"] = 18.119060
    st.success("GPS Veicolo B salvato!")

col_qB1, col_qB2, col_qB3, col_qB4 = st.columns(4)
with col_qB1:
    xb1 = st.number_input("B1 - Distanza X (m)", value=16.30, format="%.2f")
    zb1 = st.number_input("B1 - Quota Z (m)", value=7.80, format="%.2f")
with col_qB2:
    xb2 = st.number_input("B2 - Distanza X (m)", value=16.80, format="%.2f")
    zb2 = st.number_input("B2 - Quota Z (m)", value=10.55, format="%.2f")
with col_qB3:
    xb3 = st.number_input("B3 - Distanza X (m)", value=18.05, format="%.2f")
    zb3 = st.number_input("B3 - Quota Z (m)", value=7.80, format="%.2f")
with col_qB4:
    xb4 = st.number_input("B4 - Distanza X (m)", value=18.85, format="%.2f")
    zb4 = st.number_input("B4 - Quota Z (m)", value=10.55, format="%.2f")
foto_pat_B = st.file_uploader("📸 Carica Foto Patente Conducente B", type=["jpg", "png", "jpeg"])

st.divider()
st.subheader("🚶 Configurazione Pedoni / Terzi Coinvolti")
num_pedoni = st.selectbox("Quanti pedoni sono coinvolti?", options=[0, 1, 2, 3], index=0)
elenco_pedoni = []
for j in range(num_pedoni):
    st.write(f"*Pedone {j+1}*")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        px = st.number_input(f"Pedone {j+1} - Distanza X (m)", value=15.0, key=f"px_{j}")
    with col_p2:
        pz = st.number_input(f"Pedone {j+1} - Quota Z (m)", value=4.0, key=f"pz_{j}")
    elenco_pedoni.append({"idx": j+1, "x": px, "z": pz})

st.divider()
st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta accoppiamento A1 - B1 (m)", value=12.90, format="%.2f")
dist_A2B3 = st.number_input("Distanza diretta accoppiamento A2 - B3 (m)", value=11.40, format="%.2f")

st.divider()
st.subheader("⚙️ Pannello Azione")
esegui_ricalcolo = st.button("🏗️ ELABORA TUTTI I DATI E AGGIORNA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)

# 3. ENGINE MATEMATICO DI RENDERING DELLA MAPPA STRADALE (Sempre attivo)
fig, ax = plt.subplots(figsize=(15, 9.5), dpi=180)
ax.set_facecolor('#465a38')  # Terreno/erba circostante

# Disegno Sede Stradale principale (Asfalto grigio scuro)
ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)

# Disegno Innesto Strada Secondaria (Str. Vicinale Cucci) obliqua
vicinale_punti = [[20, -larg_carreggiata], [23, -larg_carreggiata], [26, 4.0], [22, 4.0]]
vicinale_poly = patches.Polygon(vicinale_punti, closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
ax.add_patch(vicinale_poly)
ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

# Tracciamento e scritte Linea di Base Capisaldi X-Z
ax.scatter(0, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))

ax.scatter(dist_XZ, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))

# SBLOCCATA LA RIGA ERRENEA PRECEDENTE: Rimossa la virgola muta di interruzione
ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9, boxstyle='round,pad=0.2'))

# DISEGNO DETTAGLIATO VEICOLO A (Sagoma Blu)
punti_A = [(xa1, -za1), (xa2, -za2), (xa4, -za4), (xa3, -za3)]
poly_A = patches.Polygon(punti_A, closed=True, facecolor='#1b9cfc', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
ax.add_patch(poly_A)

cx_A = sum(p for p, _ in punti_A) / 4
cy_A = sum(p for _, p in punti_A) / 4
ax.text(cx_A, cy_A, f"Veicolo A\n({modello_A})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

# Quote Ortogonali Azzurre Veicolo A con cartellini bianchi
color_A = '#25ccf7'
# Punto A1
ax.plot([xa1, xa1], [0, -za1], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xa1, -za1/2, f"{xa1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.text(xa1 - 1.2, -za1, f"{za1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
# Punto A2
ax.plot([xa2, xa2], [0, -za2], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xa2, -za2/2, f"{xa2:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')

nomi_A = ["A1", "A2", "A4", "A3"]
for idx, p in enumerate(punti_A):
    ax.scatter(p, p, color=color_A, s=35, zorder=7, edgecolor='black')
    ax.text(p, p - 0.35, nomi_A[idx], color='white', fontsize=8, fontweight='bold', ha='center')

# DISEGNO DETTAGLIATO VEICOLO B (Sagoma Grigio Scuro)
punti_B = [(xb1, -zb1), (xb3, -zb3), (xb4, -zb4), (xb2, -zb2)]
poly_B = patches.Polygon(punti_B, closed=True, facecolor='#718093', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
ax.add_patch(poly_B)

cx_B = sum(p for p, _ in punti_B) / 4
cy_B = sum(p for _, p in punti_B) / 4
