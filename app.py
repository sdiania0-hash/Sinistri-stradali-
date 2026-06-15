import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# Configurazione interfaccia per rilievi tecnici
st.set_page_config(page_title="Terminale di Rilievo Planimetrico Professionale", layout="centered")
st.title("🚓 Terminale di Rilievo Planimetrico Universale GPS")
st.info("📊 Algoritmo di ricostruzione grafica vettoriale basato su triangolazione e coordinate ortogonali (Capisaldi X-Z).")

# --- PERSISTENZA DEL GRAFICO ---
if "elaborazione_attiva" not in st.session_state:
    st.session_state["elaborazione_attiva"] = False

# --- PANNELLO DI CONTROLLO IN ALTO ---
st.subheader("⚙️ Pannello di Controllo Generale")
if st.button("🏗️ ELABORA TUTTI I DATI E GENERA TAVOLA GRAFICA PROFESSIONALE", type="primary", use_container_width=True):
    st.session_state["elaborazione_attiva"] = True

# Contenitore di output posizionato in alto per visualizzazione immediata
zona_grafico = st.container()

# --- BLOCCO ACQUISIZIONE DATI INFERIORE ---
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

note_luogo = st.text_area("Stato dei luoghi e rilievi ambientali", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale (Str. Vicinale Cucci). Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

# --- DATI METRICI FISSI DA SCHIZZO ORIGINALE ---
misure_A = {
    "XA1": 16.60, "ZA1": 11.55,
    "XA2": 18.20, "ZA2": 11.00,
    "XA3": 16.80, "ZA3": 13.50,
    "XA4": 19.00, "ZA4": 13.00
}

misure_B = {
    "XB1": 16.30, "ZB1": 10.55,
    "XB2": 16.80, "ZB2": 8.00,
    "XB3": 18.05, "ZB3": 8.70,
    "XB4": 18.85, "ZB4": 6.50
}

# --- GENERAZIONE INTERFACCIA GRAFICA AVANZATA ---
if st.session_state["elaborazione_attiva"]:
    with zona_grafico:
        st.subheader("📊 Schizzo Planimetrico di Rilievo Ricostruito")
        st.success("✨ Disegno vettoriale generato!")
        
        # Distanza fissa dello schizzo reale
        dist_XZ = 25.05

        # Configurazione Canvas ad Alta Risoluzione
        fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
        ax.set_facecolor('#4e5a44')  # Verde scuro/erba circostante
        
        # 1. Disegno Sede Stradale (Asfalto e Linee di Margine)
        strada_sfondo = patches.Rectangle((-5, 5), dist_XZ + 10, larg_carreggiata, facecolor='#2f3640', alpha=0.95, zorder=1)
        ax.add_patch(strada_sfondo)
        
        # Linee di margine stradale (continue bianche)
        ax.axhline(y=5, color='white', linestyle='-', linewidth=2, zorder=2)
        ax.axhline(y=5 + larg_carreggiata, color='white', linestyle='-', linewidth=2, zorder=2)
        # Linea di mezzeria tratteggiata
        ax.axhline(y=5 + larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)
        
        # 2. Posizionamento Capisaldi Fisici (Icone Arancioni 'X')
        ax.scatter(0, 5, color='#e67e22', s=200, marker='X', edgecolor='white', zorder=10)
        ax.text(0, 4.0, "Caposaldo X\n(Civico 57)", color='white', fontsize=8, fontweight='bold', ha='center')
        
        ax.scatter(dist_XZ, 5, color='#e67e22', s=200, marker='X', edgecolor='white', zorder=10)
        ax.text(dist_XZ, 4.0, "Mira Z\n(Palo TIM N°1)", color='white', fontsize=8, fontweight='bold', ha='center')
        
        # Linea di base X-Z principale
        ax.plot([0, dist_XZ], [5, 5], color='#e67e22', linestyle=':', linewidth=2, zorder=3)
        ax.text(dist_XZ/2, 4.3, f"X - Z = {dist_XZ:.2f} m", color='#f39c12', fontsize=9, fontweight='bold', ha='center')

        # 3. RICOSTRUZIONE VEICOLO A (Citroën C3 - Blu)
        cx_A = (misure_A["XA1"] + misure_A["XA4"]) / 2
        cy_A = (misure_A["ZA1"] + misure_A["ZA3"]) / 2
        
        punti_A_x = [misure_A["XA1"], misure_A["XA2"], misure_A["XA4"], misure_A["XA3"]]
        punti_A_y = [misure_A["ZA1"], misure_A["ZA2"], misure_A["ZA4"], misure_A["ZA3"]]
        
        veicolo_A_poly = patches.Polygon(np.column_stack((punti_A_x, punti_A_y)), closed=True, facecolor='#2980b9', edgecolor='white', alpha=0.9, zorder=6)
        ax.add_patch(veicolo_A_poly)
        
        # Etichette sui vertici del Veicolo A e linee di quota tratteggiate verso la base
        for idx, (px, py) in enumerate(zip(punti_A_x, punti_A_y)):
            ax.scatter(px, py, color='#7efff5', s=30, zorder=7, edgecolor='black')
            ax.text(px, py + 0.2, f"A{idx+1}", color='white', fontsize=8, fontweight='bold', ha='center')
            ax.plot([px, px], [5, py], color='#7efff5', linestyle='--', linewidth=0.8, alpha=0.6, zorder=4)
            
        # Cartellini quote numeriche
        ax.text(misure_A["XA1"], 5 + (misure_A["ZA1"]-5)/2, f"{misure_A['XA1']:.2f}", bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.15'), fontsize=7, ha='center')
        ax.text(misure_A["XA2"], 5 + (misure_A["ZA2"]-5)/2, f"{misure_A['XA2']:.2f}", bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.15'), fontsize=7, ha='center')
        ax.text(cx_A, cy_A, "Veicolo A\n(Citroën C3)", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

        # 4. RICOSTRUZIONE VEICOLO B (Alfa Romeo 147 - Grigio)
        cx_B = (misure_B["XB1"] + misure_B["XB4"]) / 2
        cy_B = (misure_B["ZB1"] + misure_B["ZB2"]) / 2
        
        punti_B_x = [misure_B["XB1"], misure_B["XB3"], misure_B["XB4"], idols_B_x2 := misure_B["XB2"]]
        punti_B_y = [misure_B["ZB1"], misure_B["ZB3"], misure_B["ZB4"], idols_B_y2 := misure_B["ZB2"]]
        
        veicolo_B_poly = patches.Polygon(np.column_stack((punti_B_x, punti_B_y)), closed=True, facecolor='#7f8c8d', edgecolor='white', alpha=0.9, zorder=6)
        ax.add_patch(veicolo_B_poly)
        
        # Etichette e proiezioni Veicolo B
        for idx, (px, py) in enumerate(zip(punti_B_x, punti_B_y)):
            ax.scatter(px, py, color='#ff4757', s=30, zorder=7, edgecolor='black')
            ax.text(px, py - 0.4, f"B{idx+1}", color='white', fontsize=8, fontweight='bold', ha='center')
            ax.plot([px, px], [5, py], color='#ff4757', linestyle='--', linewidth=0.8, alpha=0.6, zorder=4)

        # Cartellini quote Veicolo B
        ax.text(misure_B["XB3"], 5 + (misure_B["ZB3"]-5)/2, f"{misure_B['ZB3']:.2f}", bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.15'), fontsize=7, ha='center')
        ax.text(misure_B["XB4"], 5 + (misure_B["ZB4"]-5)/2, f"{misure_B['ZB4']:.2f}", bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.15'), fontsize=7, ha='center')
        ax.text(cx_B, cy_B, "Veicolo B\n(Alfa Romeo 147)", color='white', fontsize=8, fontweight='bold', ha='center', zorder=8)

        # 5. LINEE DI RISCONTRO TRA I VEICOLI (Verdi/Viola)
        ax.plot([misure_A["XA1"], misure_B["XB1"]], [misure_A["ZA1"], misure_B["ZB1"]], color='#2ecc71', linestyle='-', linewidth=1.5, zorder=5)
        ax.text((misure_A["XA1"]+misure_B["XB1"])/2, (misure_A["ZA1"]+misure_B["ZB1"])/2, "A1-B1 = 12.90 m", color='#2ecc71', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.1'))

        ax.plot([misure_A["XA2"], misure_B["XB3"]], [misure_A["ZA2"], misure_B["ZB3"]], color='#db00d4', linestyle='-', linewidth=1.5, zorder=5)
        ax.text((misure_A["XA2"]+misure_B["XB3"])/2, (misure_A["ZA2"]+misure_B["ZB3"])/2, "A2-B3 = 11.40 m", color='#db00d4', fontsize=8, fontweight='bold', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.1'))

        # Proporzionamento assi
        ax.set_xlim(-2, dist_XZ + 3)
        ax.set_ylim(1, 16)
        ax.set_aspect('equal')
        ax.axis('off')  # Rende pulito lo schizzo rimuovendo la griglia vuota di matplotlib
        
        st.pyplot(fig)
        
        # Salva in memoria
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
        img_buf.seek(0)
        plt.close(fig)

        # --- GENERAZIONE DEL DOCUMENTO PDF INTERATTIVO ---
        pdf_buf = io.BytesIO()
        p_canvas = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
        larg_p, alt_p = landscape(letter)
        
        p_canvas.setStrokeColorRGB(0, 0, 0)
        p_canvas.setLineWidth(1.5)
        p_canvas.rect(20, 20, larg_p - 40, alt_p - 40)
        
        p_canvas.setFont("Helvetica-Bold", 14)
        p_canvas.drawString(35, alt_p - 45, "SCHIZZO PLANIMETRICO DI RILIEVO - REGISTRO INFORTUNISTICA STRADALE")
        p_canvas.line(35, alt_p - 52, larg_p - 35, alt_p - 52)
        
        p_canvas.drawImage(img_buf, 35, 145, width=larg_p - 70, height=250, preserveAspectRatio=True)
        p_canvas.line(35, 135, larg_p - 35, 135)
        
        # Tabelle Dati finali stampate in fondo
        p_canvas.setFont("Helvetica-Bold", 9)
