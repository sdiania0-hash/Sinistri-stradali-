import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# 1. INTERFACCIA WEB
st.set_page_config(page_title="Terminale Rilievo Planimetrico", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("💡 Mappa attiva all'avvio. Modifica i dati sotto e premi il pulsante rosso per aggiornare.")

contenitore_mappa = st.container()

# 2. INPUT DATI FIELD
st.header("1. Protocollo di Acquisizione Dati sul Campo")
stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)
note_luogo = st.text_area("Stato dei luoghi", value="Strada Provinciale SP55, carreggiata a doppio senso. Fondo stradale asfalto asciutto.")

st.subheader("Fissaggio Linea di Base (Capisaldi)")
lat_x = st.number_input("Latitudine Caposaldo X", value=40.019572, format="%.6f")
lon_x = st.number_input("Longitudine Caposaldo X", value=18.118944, format="%.6f")
lat_z = st.number_input("Latitudine Mira Z", value=40.019590, format="%.6f")
lon_z = st.number_input("Longitudine Mira Z", value=18.119230, format="%.6f")
dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

st.subheader("🚗 Informazioni Mezzi Coinvolti")
modello_A = st.text_input("Marca/Modello Veicolo A", value="Citroën C3")
targa_A = st.text_input("Targa Veicolo A", value="AA123BB")
modello_B = st.text_input("Marca/Modello Veicolo B", value="Alfa Romeo 147")
targa_B = st.text_input("Targa Veicolo B", value="CC456DD")

st.subheader("📏 Misure Dirette di Riscontro")
dist_A1B1 = st.number_input("Distanza diretta A1 - B1 (m)", value=12.90)
dist_A2B3 = st.number_input("Distanza diretta A2 - B3 (m)", value=11.40)

esegui_ricalcolo = st.button("🏗️ ELABORA TUTTI I DATI E RIGENERA PLANIMETRIA TAVOLA GRAFICA", type="primary", use_container_width=True)

# 3. ENGINE MATPLOTLIB RENDERING
fig, ax = plt.subplots(figsize=(14, 9), dpi=150)
ax.set_facecolor('#465a38')

# Sede stradale principale
ax.fill_between([-10, dist_XZ + 15], -larg_carreggiata, 0, facecolor='#2f3542', alpha=0.95, zorder=1)
ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)

# Strada secondaria Cucci
vicinale_poly = patches.Polygon([[20, -larg_carreggiata], [23, -larg_carreggiata], [26, 4.0], [22, 4.0]], closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
ax.add_patch(vicinale_poly)
ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

# Capisaldi fissi X e Z
ax.scatter([0, dist_XZ], [0, 0], color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right')
ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left')
ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9))

# Geometrie Veicolo A (Carreggiata)
xa1, za1, xa2, za2, xa3, za3, xa4, za4 = 16.60, 2.50, 18.20, 2.70, 16.80, 0.50, 19.00, 0.70
punti_A = [(xa1, -za1), (xa2, -za2), (xa4, -za4), (xa3, -za3)]
ax.add_patch(patches.Polygon(punti_A, closed=True, facecolor='#1b9cfc', edgecolor='white', linewidth=1.5, zorder=6))
ax.text((xa1+xa4)/2, (-za1-za3)/2, f"Veicolo A\n({modello_A})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

color_A = '#25ccf7'
ax.plot([xa1, xa1], [0, -za1], color=color_A, linestyle=':', linewidth=1.2)
ax.text(xa1, -za1/2, f"{xa1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
ax.text(xa1 - 1.2, -za1, f"{za1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
ax.plot([xa2, xa2], [0, -za2], color=color_A, linestyle=':')
ax.text(xa2, -za2/2, f"{xa2:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')

nomi_A = ["A1", "A2", "A4", "A3"]
for idx, p in enumerate(punti_A):
    ax.scatter(p[0], p[1], color=color_A, s=35, zorder=7, edgecolor='black')
    ax.text(p[0], p[1] - 0.35, nomi_A[idx], color='white', fontsize=8, fontweight='bold', ha='center')

# Geometrie Veicolo B (Terreno/Erba)
xb1, zb1, xb2, zb2, xb3, zb3, xb4, zb4 = 16.30, 7.80, 16.80, 10.55, 18.05, 7.80, 18.85, 10.55
punti_B = [(xb1, -zb1), (xb3, -zb3), (xb4, -zb4), (xb2, -zb2)]
ax.add_patch(patches.Polygon(punti_B, closed=True, facecolor='#718093', edgecolor='white', linewidth=1.5, zorder=6))
ax.text((xb1+xb4)/2, (-zb1-zb2)/2, f"Veicolo B\n({modello_B})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

color_B = '#ff4757'
ax.plot([xb1, xb1], [0, -zb1], color=color_B, linestyle=':', linewidth=1.2)
ax.text(xb1 - 0.8, -zb1 + 1.2, f"{xb1:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
ax.text(xb1 - 0.8, -zb1 + 2.5, f"{zb1:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')
ax.plot([xb3, xb3], [0, -zb3], color=color_B, linestyle=':')
ax.text(xb3 + 0.8, -zb3 + 1.2, f"{xb3:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='square,pad=0.15'), fontsize=7.5, ha='center')

nomi_B = ["B1", "B3", "B4", "B2"]
for idx, p in enumerate(punti_B):
    ax.scatter(p[0], p[1], color=color_B, s=35, zorder=7, edgecolor='black')
    ax.text(p[0], p[1] + 0.35, nomi_B[idx], color='white', fontsize=8, fontweight='bold', ha='center')

# Linee dirette d'urto
ax.plot([xa1, xb1], [-za1, -zb1], color='#2ecc71', linewidth=2)
ax.text((xa1+xb1)/2, (-za1-zb1)/2, f"A1-B1={dist_A1B1:.2f}m", color='#2ecc71', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.8))
ax.plot([xa2, xb3], [-za2, -zb3], color='#db00d4', linewidth=2)
ax.text((xa2+xb3)/2, (-za2-zb3)/2, f"A2-B3={dist_A2B3:.2f}m", color='#db00d4', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.8))

# Diciture di provenienza stradale e margini
ax.annotate("Provenienza TAVIANO", xy=(-3, -1), xytext=(2, -1), color='white', weight='bold', fontsize=9, arrowprops=dict(arrowstyle="<-", color="white"))
ax.annotate("Provenienza MATINO", xy=(-3, -larg_carreggiata + 1), xytext=(2, -larg_carreggiata + 1), color='white', weight='bold', fontsize=9, arrowprops=dict(arrowstyle="->", color="white"))

ax.plot([-4, -4], [0, -larg_carreggiata], color='white', linewidth=1.2)
ax.text(-4.5, -larg_carreggiata/2, f"cd = {larg_carreggiata:.2f} m", color='white', rotation=90, fontsize=9, weight='bold', va='center')

# PARTE RICHIESTA NELLO SCREENSHOT (Parametri e inquadratura limiti)
info_strada_testo = f"PARAMETRI STRADA:\nLarghezza carreggiata: {larg_carreggiata:.2f} m\nBase X-Z: {dist_XZ:.2f} m"
ax.text(-4, -larg_carreggiata - 2.5, info_strada_testo, color='white', fontsize=8, weight='bold', bbox=dict(facecolor='black', alpha=0.5, boxstyle='round,pad=0.3'))

tutti_x = [0, dist_XZ, -5, dist_XZ + 5, xa1, xa2, xb1, xb3]
tutti_y = [0, -larg_carreggiata, -larg_carreggiata - 3, 3, -za1, -za2, -zb1, -zb3]
ax.set_xlim(min(tutti_x) - 2, max(tutti_x) + 2)
ax.set_ylim(min(tutti_y) - 2, max(tutti_y) + 2)
ax.set_aspect('equal')
ax.axis('off')

with contenitore_mappa:
    st.pyplot(fig)

# 4. GENERAZIONE FILE PDF
img_buf = io.BytesIO()
plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=180)
img_buf.seek(0)
plt.close(fig)

pdf_buf = io.BytesIO()
p_canvas = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
larg_p, alt_p = landscape(letter)

p_canvas.rect(15, 15, larg_p - 30, alt_p - 30)
p_canvas.setFont("Helvetica-Bold", 13)
p_canvas.drawString(30, alt_p - 35, "RELAZIONE PLANIMETRICA ILLUSTRAZIONE SINISTRO STRADALE")
p_canvas.line(30, alt_p - 42, larg_p - 30, alt_p - 42)
p_canvas.drawImage(img_buf, 25, 140, width=larg_p - 50, height=265, preserveAspectRatio=True)
p_canvas.line(30, 132, larg_p - 30, 132)

p_canvas.setFont("Helvetica-Bold", 9)
p_canvas.drawString(30, 115, "CARTIGLIO ED ACCERTAMENTI:")
p_canvas.setFont("Helvetica", 8)
p_canvas.drawString(30, 100, f"Ufficio: {stazione}  ||  Operatori: {operanti}")
p_canvas.drawString(30, 85, f"Località: {localita}  ||  Data/Ora: {data_ora}")
p_canvas.drawString(30, 70, f"Larghezza Sede: {larg_carreggiata:.2f} m  ||  Linea Base X-Z: {dist_XZ:.2f} m")

p_canvas.setFont("Helvetica-Bold", 9)
p_canvas.drawString(350, 115, "MEZZI COINVOLTI:")
p_canvas.setFont("Helvetica", 8)
p_canvas.drawString(350, 100, f"Veicolo A: {modello_A} ({targa_A})")
p_canvas.drawString(350, 87, f"Veicolo B: {modello_B} ({targa_B})")

p_canvas.showPage()
p_canvas.save()
pdf_buf.seek(0)

if esegui_ricalcolo:
    st.success("✨ Tavola grafica aggiornata con successo!")

st.download_button(
    label="📥 SCARICA TAVOLA PLANIMETRICA AGGIORNATA IN FORMATO PDF VETTORIALE",
    data=pdf_buf,
    file_name="Tavola_Planimetrica_Sinistro.pdf",
    mime="application/pdf",
    use_container_width=True
)
