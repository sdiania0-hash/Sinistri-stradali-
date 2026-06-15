import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configurazione della pagina
st.set_page_config(page_title="Rilievo Satellitare GPS Professional", layout="wide")
st.title("🛰️ Sistema di Rilievo Planimetrico su Base GPS")
st.info("💡 Inserisci le coordinate GPS dei capisaldi e dei veicoli per generare la tavola formattata.")

col1, col2 = st.columns([1, 1.4])

with col1:
    st.header("1. Inserimento Coordinate GPS")
    
    st.subheader("Intestazione")
    stazione = st.text_input("Stazione / Comando / Ufficio", value="STAZIONE CC MATINO")
    operanti = st.text_input("Operanti", value="Brig. Rima G., V.B. Rizzo V.")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    larg_carreggiata = st.number_input("Larghezza Carreggiata (metri)", value=6.60)
    note_luogo = st.text_area("Caratteristiche del luogo", value="Fondo stradale: asfalto asciutto. Condizioni di luce: diurna.")

    st.divider()
    st.subheader("Coordinate GPS Capisaldi (Lat, Lon)")
    lat_x = st.number_input("Latitudine Caposaldo X (Civico 57)", value=40.019572, format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X (Civico 57)", value=18.118944, format="%.6f")
    
    lat_z = st.number_input("Latitudine Mira Z (Palo TIM)", value=40.019590, format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z (Palo TIM)", value=18.119230, format="%.6f")
    
    st.divider()
    st.subheader("Coordinate GPS Veicoli")
    st.write("**VEICOLO A**")
    modello_a = st.text_input("Modello Veicolo A", value="Citroën C3")
    targa_a = st.text_input("Targa Veicolo A", value="AA123BB")
    lat_a1 = st.number_input("Latitudine Punto A1 (Front)", value=40.019585, format="%.6f")
    lon_a1 = st.number_input("Longitudine Punto A1 (Front)", value=18.119050, format="%.6f")
    lat_a2 = st.number_input("Latitudine Punto A2 (Rear)", value=40.019582, format="%.6f")
    lon_a2 = st.number_input("Longitudine Punto A2 (Rear)", value=18.119100, format="%.6f")
    
    st.write("**VEICOLO B**")
    modello_b = st.text_input("Modello Veicolo B", value="Alfa Romeo 147")
    targa_b = st.text_input("Targa Veicolo B", value="CC456DD")
    lat_b1 = st.number_input("Latitudine Punto B1 (Front)", value=40.019565, format="%.6f")
    lon_b1 = st.number_input("Longitudine Punto B1 (Front)", value=18.119060, format="%.6f")
    lat_b3 = st.number_input("Latitudine Punto B3 (Rear)", value=40.019560, format="%.6f")
    lon_b3 = st.number_input("Longitudine Punto B3 (Rear)", value=18.119110, format="%.6f")

with col2:
    st.header("2. Tavola Planimetrica Calcolata")
    
    if st.button("ELABORA COORDINATE GPS E GENERA TAVOLA"):
        # Funzione matematica di Haversine per convertire gradi GPS in metri reali
        def gps_a_metri(lat1, lon1, lat2, lon2):
            R = 6371000  # Raggio della Terra in metri
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            # Proiezioni piane relative approssimate
            x = dlam * R * math.cos((phi1 + phi2) / 2)
            y = dphi * R
            return x, y

        # Impostiamo Caposaldo X come origine cartesiana (0,0)
        x_x, y_x = 0.0, 0.0
        x_z, y_z = gps_a_metri(lat_x, lon_x, lat_z, lon_z)
        base_calcolata = math.sqrt(x_z**2 + y_z**2)
        
        # Calcolo posizioni veicoli rispetto a Caposaldo X
        x_a1, y_a1 = gps_a_metri(lat_x, lon_x, lat_a1, lon_a1)
        x_a2, y_a2 = gps_a_metri(lat_x, lon_x, lat_a2, lon_a2)
        x_b1, y_b1 = gps_a_metri(lat_x, lon_x, lat_b1, lon_b1)
        x_b3, y_b3 = gps_a_metri(lat_x, lon_x, lat_b3, lon_b3)
        
        # Creazione del foglio grafico
        fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        cornice = patches.Rectangle((-10, -10), base_calcolata + 25, larg_carreggiata + 20, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        # Disegno la carreggiata orientata sull'asse calcolato dei capisaldi
        strada = patches.Rectangle((-10, -larg_carreggiata/2), base_calcolata + 25, larg_carreggiata, facecolor='#444444', alpha=0.9, zorder=1)
        ax.add_patch(strada)
        ax.axhline(y=0, color='white', linestyle='--', linewidth=1.5, zorder=2) # Mezzeria
        
        # Capisaldi fisici ricavati da GPS
        ax.scatter(x_x, y_x, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.scatter(x_z, y_z, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.text(x_x, y_x - 1.5, "Caposaldo X\n(Rilevato GPS)", fontsize=10, fontweight='bold', ha='center')
        ax.text(x_z, y_z - 1.5, "Mira Z\n(Rilevato GPS)", fontsize=10, fontweight='bold', ha='center')
        
        # Sagoma Veicolo A
        angolo_a = math.atan2(y_a2 - y_a1, x_a2 - x_a1) * 180 / math.pi
        box_a = patches.Rectangle((x_a1, y_a1 - 0.9), 4.0, 1.8, angle=angolo_a, edgecolor='black', facecolor='#1b3a4b', alpha=0.9, zorder=4)
        ax.add_patch(box_a)
        ax.text(x_a1, y_a1 + 0.5, f"A1\n{modello_a}", color='blue', fontweight='bold', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        
        # Sagoma Veicolo B
        angolo_b = math.atan2(y_b3 - y_b1, x_b3 - x_b1) * 180 / math.pi
        box_b = patches.Rectangle((x_b1, y_b1 - 0.9), 4.0, 1.8, angle=angolo_b, edgecolor='black', facecolor='#780000', alpha=0.9, zorder=4)
        ax.add_patch(box_b)
        ax.text(x_b1, y_b1 - 1.5, f"B1\n{modello_b}", color='red', fontweight='bold', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        
        # Allineamento Box Informazioni
        x_box = base_calcolata + 4
        ax.text(x_box, 6, f"SCHIZZO PLANIMETRICO GPS\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}", fontsize=10, fontweight='bold', bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.8'))
        ax.text(x_box, -1, f"POSIZIONI GPS ESTRATTE:\n\nBase X-Z Calcolata: {base_calcolata:.2f} m\n\n{modello_a} ({targa_a}):\nLat A1: {lat_a1:.6f}\nLon A1: {lon_a1:.6f}\n\n{modello_b} ({targa_b}):\nLat B1: {lat_b1:.6f}\nLon B1: {lon_b1:.6f}", fontsize=9.5, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        ax.text(-8, -8, f"CARTIGLIO DI RILIEVO\nData: {data_ora}\nLocalità: {localita}\nSede Stradale: {larg_carreggiata} m", fontsize=10, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        ax.text(7, -8, f"NOTE TECNICHE AMBIENTALI\n\n{note_luogo}", fontsize=9.5, wrap=True, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        
        ax.set_xlim(-10, base_calcolata + 16)
        ax.set_ylim(-10, larg_carreggiata + 10)
        ax.set_aspect('equal')
        ax.axis('off')
        st.pyplot(fig)
        
        # Compilazione PDF
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
        img_buf.seek(0)
        plt.close()
        
        immagine_pil = Image.open(img_buf)
        pdf_buf = io.BytesIO()
        p = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
        p.drawInlineImage(immagine_pil, 0.25*inch, 0.25*inch, width=10.5*inch, height=8*inch)
        p.showPage()
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(0.5*inch, 7.5*inch, "VERBALE DI RILIEVO TOPOGRAFICO GPS")
        p.setFont("Helvetica", 11)
        testo_pdf = [
            f"Comando procedente: {stazione} | Operanti: {operanti}",
            f"Località: {localita} | Data e Ora: {data_ora}",
            f"Distanza calcolata tra i Capisaldi X e Z: {base_calcolata:.2f} metri",
            "",
            "COORDINATE GEOGRAFICHE REALI ACQUISITE (WGS84):",
            f"- Caposaldo X -> Lat: {lat_x:.6f}, Lon: {lon_x:.6f}",
            f"- Mira Z      -> Lat: {lat_z:.6f}, Lon: {lon_z:.6f}",
            f"- {modello_a} ({targa_a}) -> Lat A1: {lat_a1:.6f}, Lon: {lon_a1:.6f}",
            f"- {modello_b} ({targa_b}) -> Lat B1: {lat_b1:.6f}, Lon: {lon_b1:.6f}",
            "",
            "ANNOTAZIONI SULLO STATO DEI LUOGHI:",
            f"{note_luogo}"
        ]
        y_pos = 6.8*inch
        for riga in testo_pdf:
            p.drawString(0.5*inch, y_pos, riga)
            y_pos -= 0.25*inch
        p.save()
        pdf_buf.seek(0)
        
        st.divider()
        st.download_button(
            label="📥 SCARICA TAVOLA E VERBALE TOPOGRAFICO GPS (PDF)",
            data=pdf_buf,
            file_name=f"Rilievo_GPS_{localita.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        
