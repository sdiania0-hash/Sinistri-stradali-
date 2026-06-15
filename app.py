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
st.info("💡 Lo schizzo grafico mostra il rilievo corrente. Modifica i parametri descrittivi nei moduli sottostanti e premi il pulsante rosso per rigenerare la tavola e scaricare il PDF.")

# Inizializzazione dello stato della sessione per garantire la persistenza del disegno
if "mappa_generata" not in st.session_state:
    st.session_state["mappa_generata"] = True
if "lat_x" not in st.session_state:
    st.session_state["lat_x"] = 40.019572
    st.session_state["lon_x"] = 18.118944
    st.session_state["lat_z"] = 40.019590
    st.session_state["lon_z"] = 18.119230

# Riquadro contenitore posizionato rigorosamente in alto per la mappa fissa
contenitore_mappa = st.container()

# 2. PROTOCOLLO INSERIMENTO DATI (RIFIUTI E MODULI FUNZIONALI LIBERI)
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
    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state["lat_x"], format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state["lon_x"], format="%.6f")

with col_cz:
    if st.button("📍 Inserisci GPS Attuale -> Mira Z"):
        st.session_state["lat_z"] = 40.019590
        st.session_state["lon_z"] = 18.119230
        st.success("Coordinate Mira Z agganciate dal sensore!")
    lat_z = st.number_input("Latitudine Mira Z", value=st.session_state["lat_z"], format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=st.session_state["lon_z"], format="%.6f")

dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

st.divider()
st.subheader("🚗 Informazioni Mezzi Coinvolti")
modello_A = st.text_input("Marca e Modello Veicolo A", value="Citroën C3")
targa_A = st.text_input("Targa Veicolo A", value="AA123BB")
foto_pat_A = st.file_uploader("📸 Carica Foto Patente Conducente A", type=["jpg", "png", "jpeg"])

modello_B = st.text_input("Marca e Modello Veicolo B", value="Alfa Romeo 147")
targa_B = st.text_input("Targa Veicolo B", value="CC456DD")
foto_pat_B = st.file_uploader("📸 Carica Foto Patente Conducente B", type=["jpg", "png", "jpeg"])

st.divider()
st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta accoppiamento A1 - B1 (m)", value=12.90, format="%.2f")
dist_A2B3 = st.number_input("Distanza diretta accoppiamento A2 - B3 (m)", value=11.40, format="%.2f")

st.divider()
st.subheader("⚙️ Pannello Azione")
esegui_ricalcolo = st.button("🏗️ ELABORA TUTTI I DATI E RIGENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)


# 3. ENGINE STRUTTURATO DI RENDERING DELLA MAPPA STRADALE (Sempre Attivo)
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

ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9, boxstyle='round,pad=0.2'))

# QUOTE E GEOMETRIE REALI DELLO SCHIZZO DI RIFERIMENTO
# Veicolo A (Citroën C3)
xa1, za1 = 16.60, 2.50
xa2, za2 = 18.20, 2.70
xa3, za3 = 16.80, 0.50
xa4, za4 = 19.00, 0.70

punti_A = [(xa1, -za1), (xa2, -za2), (xa4, -za4), (xa3, -za3)]
poly_A = patches.Polygon(punti_A, closed=True, facecolor='#1b9cfc', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
ax.add_patch(poly_A)

cx_A = sum(p for p, _ in punti_A) / 4
cy_A = sum(p for _, p in punti_A) / 4
ax.text(cx_A, cy_A, f"Veicolo A\n({modello_A})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

color_A = '#25ccf7'
ax.plot([xa1, xa1], [0, -za1], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xa1, -za1/2, f"{xa1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.text(xa1 - 1.2, -za1, f"{za1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.plot([xa2, xa2], [0, -za2], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xa2, -za2/2, f"{xa2:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')

nomi_A = ["A1", "A2", "A4", "A3"]
for idx, p in enumerate(punti_A):
    ax.scatter(p[0], p[1], color=color_A, s=35, zorder=7, edgecolor='black')
    ax.text(p[0], p[1] - 0.35, nomi_A[idx], color='white', fontsize=8, fontweight='bold', ha='center')

# Veicolo B (Alfa Romeo 147)
xb1, zb1 = 16.30, 7.80
xb2, zb2 = 16.80, 10.55
xb3, zb3 = 18.05, 7.80
xb4, zb4 = 18.85, 10.55

punti_B = [(xb1, -zb1), (xb3, -zb3), (xb4, -zb4), (xb2, -zb2)]
poly_B = patches.Polygon(punti_B, closed=True, facecolor='#718093', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
ax.add_patch(poly_B)

cx_B = sum(p for p, _ in punti_B) / 4
cy_B = sum(p for _, p in punti_B) / 4
ax.text(cx_B, cy_B, f"Veicolo B\n({modello_B})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

color_B = '#ff4757'
ax.plot([xb1, xb1], [0, -zb1], color=color_B, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xb1 - 0.8, -zb1 + 1.2, f"{xb1:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.text(xb1 - 0.8, -zb1 + 2.5, f"{zb1:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.plot([xb3, xb3], [0, -zb3], color=color_B, linestyle=':', linewidth=1.2, zorder=4)
ax.text(xb3 + 0.8, -zb3 + 1.2, f"{xb3:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')
ax.text(xb3 + 0.8, -zb3 + 2.5, f"{zb3:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center', weight='bold')

nomi_B = ["B1", "B3", "B4", "B2"]
for idx, p in enumerate(punti_B):
    ax.scatter(p[0], p[1], color=color_B, s=35, zorder=7, edgecolor='black')
    ax.text(p[0], p[1] + 0.35, nomi_B[idx], color='white', fontsize=8, fontweight='bold', ha='center')

# Linee di riscontro d'impatto dirette
ax.plot([xa1, xb1], [-za1, -zb1], color='#2ecc71', linestyle='-', linewidth=2, zorder=5)
ax.text((xa1+xb1)/2, (-za1-zb1)/2, f"A1 - B1 = {dist_A1B1:.2f} m", color='#2ecc71', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.8, boxstyle='round,pad=0.15'), ha='center')

ax.plot([xa2, xb3], [-za2, -zb3], color='#db00d4', linestyle='-', linewidth=2, zorder=5)
ax.text((xa2+xb3)/2, (-za2-zb3)/2, f"A2 - B3 = {dist_A2B3:.2f} m", color='#db00d4', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.8, boxstyle='round,pad=0.15'), ha='center')

# Diciture di Provenienza e Frecce stradali
ax.annotate("Provenienza TAVIANO (Direzione Matino)", xy=(-3, -1), xytext=(2, -1), color='white', weight='bold', fontsize=9, arrowprops=dict(arrowstyle="<-", color="white", linewidth=1.5))
# Completa il disegno

ax.annotate(
"Provenienza TAVIANO (Direzione Matino)",
xy=(-3, -1),
xytext=(2, -1),
color='white',
weight='bold',
fontsize=9,
arrowprops=dict(
arrowstyle="<-",
color="white",
linewidth=1.5
)
)

ax.set_aspect('equal')
ax.set_xlim(-10, dist_XZ + 15)
ax.set_ylim(-15, 8)
ax.set_title(
f"Rilievo Planimetrico - {localita}",
fontsize=14,
fontweight="bold"
)

ax.axis("off")

# VISUALIZZA LA MAPPA NELLA PAGINA STREAMLIT

with contenitore_mappa:
st.pyplot(fig, use_container_width=True)

# CREA PNG

buffer_png = io.BytesIO()
fig.savefig(
buffer_png,
format="png",
bbox_inches="tight",
dpi=300
)
buffer_png.seek(0)

st.download_button(
"📸 Scarica rilievo PNG",
data=buffer_png,
file_name="rilievo_planimetrico.png",
mime="image/png"
)

plt.close(fig)
