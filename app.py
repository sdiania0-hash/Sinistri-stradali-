import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# Configurazione interfaccia grafica professionale modulare
st.set_page_config(page_title="Terminale di Rilievo Planimetrico Universale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("📊 Inserisci le quote cartesiane (X, Z) misurate rispetto alla linea di base per ricostruire qualsiasi sinistro stradale.")

# --- MEMORIA DI STATO STREAMLIT ---
if "elaborazione_attiva" not in st.session_state:
    st.session_state["elaborazione_attiva"] = False

# --- PANNELLO DI CONTROLLO SUPERIORE ---
st.subheader("⚙️ Pannello di Controllo Generale")
if st.button("🏗️ ELABORA I DATI E GENERA LA TAVOLA GRAFICA", type="primary", use_container_width=True):
    st.session_state["elaborazione_attiva"] = True

zona_grafico = st.container()

# --- BLOCCO INPUT DATI ---
st.header("1. Protocollo di Acquisizione Dati sul Campo")
col_A, col_B = st.columns(2)

with col_A:
    st.subheader("Dati Identificativi Verbale")
    stazione = st.text_input("Ufficio / Comando Procedente", value="STAZIONE CC MATINO")
    operanti = st.text_input("Personale Operante", value="Brig. Rima G., V.B. Rizzo V.")
    localita = st.text_input("Località / Via / Progressiva Km", value="SP55 Matino-Taviano")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
    larg_carreggiata = st.number_input("Larghezza Sede Stradale cd (metri)", min_value=2.0, max_value=20.0, value=6.60)

with col_B:
    st.subheader("Fissaggio Linea di Base (Capisaldi)")
    lat_x = st.number_input("Latitudine Caposaldo X (Civico 57)", value=40.019572, format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X (Civico 57)", value=18.118944, format="%.6f")
    lat_z = st.number_input("Latitudine Mira Z (Palo TIM)", value=40.019590, format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z (Palo TIM)", value=18.119230, format="%.6f")
    dist_XZ = st.number_input("Distanza Linea di Base X - Z (metri)", min_value=1.0, max_value=500.0, value=25.05)

note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale (Str. Vicinale Cucci). Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

# --- SEZIONE QUOTE DINAMICHE VEICOLO A ---
st.divider()
st.subheader("🚗 Configurazione Misure Veicolo A (es. Citroën C3)")
modello_A = st.text_input("Marca e Modello Veicolo A", value="Citroën C3")
targa_A = st.text_input("Targa Veicolo A", value="AA123BB")

col_a1, col_a2, col_a3, col_a4 = st.columns(4)
with col_a1:
    xa1 = st.number_input("Punto A1 - Distanza X (m)", value=16.60, format="%.2f")
    za1 = st.number_input("Punto A1 - Quota Z (m)", value=11.55, format="%.2f")
with col_a2:
    xa2 = st.number_input("Punto A2 - Distanza X (m)", value=18.20, format="%.2f")
    za2 = st.number_input("Punto A2 - Quota Z (m)", value=11.00, format="%.2f")
with col_a3:
    xa3 = st.number_input("Punto A3 - Distanza X (m)", value=16.80, format="%.2f")
    za3 = st.number_input("Punto A3 - Quota Z (m)", value=13.50, format="%.2f")
with col_a4:
    xa4 = st.number_input("Punto A4 - Distanza X (m)", value=19.00, format="%.2f")
    za4 = st.number_input("Punto A4 - Quota Z (m)", value=13.00, format="%.2f")

# --- SEZIONE QUOTE DINAMICHE VEICOLO B ---
st.divider()
st.subheader("🚗 Configurazione Misure Veicolo B (es. Alfa Romeo 147)")
modello_B = st.text_input("Marca e Modello Veicolo B", value="Alfa Romeo 147")
targa_B = st.text_input("Targa Veicolo B", value="CC456DD")

col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    xb1 = st.number_input("Punto B1 - Distanza X (m)", value=16.30, format="%.2f")
    zb1 = st.number_input("Punto B1 - Quota Z (m)", value=10.55, format="%.2f")
with col_b2:
    xb2 = st.number_input("Punto B2 - Distanza X (m)", value=16.80, format="%.2f")
    zb2 = st.number_input("Punto B2 - Quota Z (m)", value=8.00, format="%.2f")
with col_b3:
    xb3 = st.number_input("Punto B3 - Distanza X (m)", value=18.05, format="%.2f")
    zb3 = st.number_input("Punto B3 - Quota Z (m)", value=8.70, format="%.2f")
with col_b4:
    xb4 = st.number_input("Punto B4 - Distanza X (m)", value=18.85, format="%.2f")
    zb4 = st.number_input("Punto B4 - Quota Z (m)", value=6.50, format="%.2f")

# --- SEZIONE QUOTE DINAMICHE DI RISCONTRO INTER-VEICOLARE ---
st.divider()
st.subheader("📏 Misure Dirette di Riscontro (Linee Diagonali)")
col_r1, col_r2 = st.columns(2)
with col_r1:
    dist_A1B1 = st.number_input("Distanza diretta d'accoppiamento A1 - B1 (m)", value=12.90, format="%.2f")
with col_r2:
    dist_A2B3 = st.number_input("Distanza diretta d'accoppiamento A2 - B3 (m)", value=11.40, format="%.2f")


# --- PROCESSO DI RENDERING DINAMICO ---
if st.session_state["elaborazione_attiva"]:
    with zona_grafico:
        st.subheader("📊 Schizzo Planimetrico Generato Dinamicamente")
        
        # Creazione della figura
        fig, ax = plt.subplots(figsize=(15, 9.5), dpi=180)
        ax.set_facecolor('#465a38')  # Sfondo terreno verde scuro
        
        # 1. Disegno Sede Stradale (Asfalto basato sulla larghezza inserita dall'utente)
        strada = patches.Rectangle((-5, -larg_carreggiata), dist_XZ + 10, larg_carreggiata, facecolor='#2f3542', alpha=0.95, zorder=1)
        ax.add_patch(strada)
        
        # Linee di margine stradale e mezzeria
        ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
        ax.axhline(y=-larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
        ax.axhline(y=-larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)
        
        # Strada secondaria (intersezione)
        vicinale_punti = [[20, -larg_carreggiata], [23, -larg_carreggiata], [32, 4], [29, 4]]
        vicinale_poly = patches.Polygon(vicinale_punti, closed=True, facecolor='#2f3542', alpha=0.9, zorder=1)
        ax.add_patch(vicinale_poly)
        ax.text(24.5, 2.5, "Str. Vicinale Cucci", color='white', fontsize=8, rotation=50, weight='bold', alpha=0.8)

        # 2. Capisaldi della Linea di Base (X e Z)
        ax.scatter(0, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
        ax.text(-0.5, 0.5, "Caposaldo X\n(Civico 57)", color='black', fontsize=9, fontweight='bold', ha='right', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))
        
        ax.scatter(dist_XZ, 0, color='#e67e22', s=220, marker='X', edgecolor='white', zorder=10)
        ax.text(dist_XZ + 0.5, 0.5, "Mira Z\n(Palo TIM N°)", color='black', fontsize=9, fontweight='bold', ha='left', bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.1'))
        
        ax.plot([0, dist_XZ], [0, 0], color='#e67e22', linestyle='-', linewidth=2.5, zorder=3)
        ax.text(dist_XZ/2, 0.3, f"X - Z = {dist_XZ:.2f} m", color='#e67e22', fontsize=11, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9, boxstyle='round,pad=0.2'))

        # 3. DISEGNO DINAMICO VEICOLO A (Utilizza le variabili degli input numerici)
        punti_A_grafico = [(xa1, -za1), (xa2, -za2), (xa4, -za4), (xa3, -za3)]
        veicolo_A_poly = patches.Polygon(punti_A_grafico, closed=True, facecolor='#1b9cfc', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
        ax.add_patch(veicolo_A_poly)
        
        cx_A = sum(p[0] for p in punti_A_grafico) / 4
        cy_A = sum(p[1] for p in punti_A_grafico) / 4
        ax.text(cx_A, cy_A, f"Veicolo A\n({modello_A})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)
        
        color_A = '#25ccf7'
        # Quota dinamica A1
        ax.plot([xa1, xa1], [0, -za1], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
        ax.text(xa1, -za1/2, f"{xa1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='round,pad=0.15'), fontsize=8, ha='center', weight='bold')
        ax.text(xa1 - 1.2, -za1, f"{za1:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='round,pad=0.15'), fontsize=8, ha='center', weight='bold')
        
        # Quota dinamica A2
        ax.plot([xa2, xa2], [0, -za2], color=color_A, linestyle=':', linewidth=1.2, zorder=4)
        ax.text(xa2, -za2/2, f"{xa2:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='round,pad=0.15'), fontsize=8, ha='center', weight='bold')
        ax.text(xa2 + 1.2, -za2, f"{za2:.2f}", bbox=dict(facecolor='white', edgecolor=color_A, boxstyle='round,pad=0.15'), fontsize=8, ha='center', weight='bold')

        for idx, p in enumerate(punti_A_grafico):
            ax.scatter(p[0], p[1], color=color_A, s=40, zorder=7, edgecolor='black')
            ax.text(p[0], p[1] - 0.3, f"A{idx+1}", color='white', fontsize=8, fontweight='bold', ha='center')

        # 4. DISEGNO DINAMICO VEICOLO B
        punti_B_grafico = [(xb1, -zb1), (xb3, -zb3), (xb4, -zb4), (xb2, -zb2)]
        veicolo_B_poly = patches.Polygon(punti_B_grafico, closed=True, facecolor='#57606f', edgecolor='white', linewidth=1.5, alpha=0.95, zorder=6)
        ax.add_patch(veicolo_B_poly)
        
        cx_B = sum(p[0] for p in punti_B_grafico) / 4
        cy_B = sum(p[1] for p in punti_B_grafico) / 4
        ax.text(cx_B, cy_B, f"Veicolo B\n({modello_B})", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)
        
        color_B = '#ff4757'
        # Quota dinamica B1
        ax.plot([xb1, xb1], [0, -zb1], color=color_B, linestyle=':', linewidth=1.2, zorder=4)
        ax.text(xb1 - 0.7, -zb1 + 1.5, f"{xb1:.2f}", bbox=dict(facecolor='white', edgecolor=color_B, boxstyle='round,pad=0.15'), fontsize=8, ha='center', weight='bold')
