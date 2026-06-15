import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from PIL import Image
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configurazione della pagina dell'applicazione web
st.set_page_config(page_title="Generatore Planimetrico Professionale", layout="wide")
st.title("🚓 Sistema di Generazione e Stampa Rilievi")
st.info("💡 Inserisci i dati e premi il tasto in fondo per scaricare la tavola ufficiale pronta in PDF.")

col1, col2 = st.columns([1, 1.4])

with col1:
    st.header("1. Inserimento Dati")
    stazione = st.text_input("Stazione / Comando / Ufficio", value="STAZIONE CC MATINO")
    operanti = st.text_input("Operanti (es. Brig. Rima G., V.B. Rizzo V.)", value="Brig. Rima G., V.B. Rizzo V.")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 06:50")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    gps = st.text_input("Coordinate GPS", value="40.019572, 18.118944")
    base_xz = st.number_input("Distanza Base Capisaldi X-Z (metri)", value=25.05)
    larg_carreggiata = st.number_input("Larghezza Carreggiata (metri)", value=6.60)
    note_luogo = st.text_area("Caratteristiche del luogo", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale. Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

    st.divider()
    st.subheader("Misure Veicoli")
    modello_a = st.text_input("Modello Veicolo A", value="Citroën C3")
    targa_a = st.text_input("Targa Veicolo A", value="AA123BB")
    xa1 = st.number_input("Distanza XA1", value=16.60)
    za1 = st.number_input("Distanza ZA1", value=11.55)
    xa2 = st.number_input("Distanza XA2", value=18.20)
    za2 = st.number_input("Distanza ZA2", value=11.00)
    
    modello_b = st.text_input("Modello Veicolo B", value="Alfa Romeo 147")
    targa_b = st.text_input("Targa Veicolo B", value="CC456DD")
    xb1 = st.number_input("Distanza XB1", value=16.30)
    zb1 = st.number_input("Distanza ZB1", value=10.55)
    xb3 = st.number_input("Distanza XB3", value=18.05)
    zb3 = st.number_input("Distanza ZB3", value=8.70)

with col2:
    st.header("2. Anteprima della Tavola Grafica")
    
    # Algoritmo di trilaterazione geometrica
    def calcola_punto(rx, rz, d):
        a = (rx**2 - rz**2 + d**2) / (2 * d)
        h = np.sqrt(max(0, rx**2 - a**2))
        return a, h
    
    xa, ya = calcola_punto(xa1, za1, base_xz)
    xa2_c, ya2_c = calcola_punto(xa2, za2, base_xz)
    xb, yb = calcola_punto(xb1, zb1, base_xz)
    xb3_c, yb3_c = calcola_punto(xb3, zb3, base_xz)
    
    fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
    fig.patch.set_facecolor('#ffffff')
    
    cornice = patches.Rectangle((-5, -6), base_xz + 25, larg_carreggiata + 13, linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(cornice)
    
    strada_sfondo = patches.Rectangle((-5, 0), base_xz + 25, larg_carreggiata, facecolor='#555555', alpha=0.9, zorder=1)
    ax.add_patch(strada_sfondo)
    
    ax.axhline(y=0, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=larg_carreggiata, color='white', linestyle='-', linewidth=2.5, zorder=2)
    ax.axhline(y=larg_carreggiata/2, color='white', linestyle='--', linewidth=1.5, zorder=2)
    ax.text(-4, larg_carreggiata - 0.7, f"cd = {larg_carreggiata} m", fontsize=11, color='white', style='italic', fontweight='bold', zorder=3)
    
    ax.scatter(0, 0, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
    ax.scatter(base_xz, 0, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
    ax.text(0, -1.2, "Caposaldo X\n(Civico 57)", fontsize=11, fontweight='bold', ha='center', color='#d35400')
    ax.text(base_xz, -1.2, "Mira Z\n(Palo TIM N°)", fontsize=11, fontweight='bold', ha='center', color='#d35400')
    
    angolo_a = np.arctan2(ya2_c - ya, xa2_c - xa) * 180 / np.pi
    veicolo_a_box = patches.Rectangle((xa, ya - 0.7), 4.2, 1.8, angle=angolo_a, linewidth=1, edgecolor='black', facecolor='#1b3a4b', alpha=0.9, zorder=4)
    ax.add_patch(veicolo_a_box)
    ax.scatter([xa, xa2_c], [ya, ya2_c], color='blue', s=100, zorder=5, edgecolor='white')
    ax.text(xa, ya + 0.5, "A1", color='blue', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
    ax.text(xa2_c, ya2_c + 0.5, "A2", color='blue', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
    
    angolo_b = np.arctan2(yb3_c - yb, xb3_c - xb) * 180 / np.pi
    veicolo_b_box = patches.Rectangle((xb, yb - 0.7), 4.2, 1.8, angle=angolo_b, linewidth=1, edgecolor='black', facecolor='#780000', alpha=0.9, zorder=4)
    ax.add_patch(veicolo_b_box)
    ax.scatter([xb, xb3_c], [yb, yb3_c], color='red', s=100, zorder=5, edgecolor='white')
    ax.text(xb, yb - 0.9, "B1", color='red', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
    ax.text(xb3_c, yb3_c - 0.9, "B3", color='red', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
    
    ax.plot([0, xa], [0, ya], 'b--', linewidth=1, alpha=0.5)
    ax.plot([base_xz, xa], [0, ya], 'b--', linewidth=1, alpha=0.5)
    ax.plot([0, xb], [0, yb], 'r--', linewidth=1, alpha=0.5)
    ax.plot([base_xz, xb], [0, yb], 'r--', linewidth=1, alpha=0.5)
    
    x_blocco_destra = base_xz + 4.5
    testo_comando = f"SCHIZZO PLANIMETRICO DI RILIEVO\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}"
    ax.text(x_blocco_destra, larg_carreggiata + 1.2, testo_comando, fontsize=11, fontweight='bold', bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.9', linewidth=1.5))
    
    testo_misure_riquadro = f"MISURE {modello_a.upper()} ({targa_a}):\nXA1 = {xa1:.2f} m | ZA1 = {za1:.2f} m\nXA2 = {xa2:.2f} m | ZA2 = {za2:.2f} m\n\nMISURE {modello_b.upper()} ({targa_b}):\nXB1 = {xb1:.2f} m | ZB1 = {zb1:.2f} m\nXB3 = {xb3:.2f} m | ZB3 = {zb3:.2f} m"
    ax.text(x_blocco_destra, larg_carreggiata - 5, testo_misure_riquadro, fontsize=10.5, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
    
    testo_cartiglio = f"CARTIGLIO DI RILIEVO\n\nData: {data_ora}\nLocalità: {localita}\nGPS: {gps}\nBase X-Z = {base_xz} m"
    ax.text(-4, -5.2, testo_cartiglio, fontsize=10.5, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
    
    testo_ambientale = f"CARATTERISTICHE DEL LUOGO DEL SINISTRO\n\n{note_luogo}"
    ax.text(9, -5.2, testo_ambientale, fontsize=10, wrap=True, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
    
    ax.set_xlim(-5, base_xz + 18)
    ax.set_ylim(-6, larg_carreggiata + 5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    st.pyplot(fig)

    # Conversione corretta dell'immagine in oggetto PIL per evitare il crash [INDEX]
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    img_buf.seek(0)
    plt.close()
    
    immagine_pil = Image.open(img_buf) # Forza la lettura come immagine pulita [INDEX]

    # Creazione del pacchetto PDF finale
    pdf_buf = io.BytesIO()
    p = canvas.Canvas(pdf_buf, pagesize=landscape(letter))
    
    # Stampa l'immagine convertita nel PDF [INDEX]
    p.drawInlineImage(immagine_pil, 0.25*inch, 0.25*inch, width=10.5*inch, height=8*inch)
    p.showPage()
    
    # Pagina 2: Verbale descrittivo integrato
    p.setFont("Helvetica-Bold", 16)
    p.drawString(0.5*inch, 7.5*inch, "VERBALE DESCRITTIVO DI RILIEVO PLANIMETRICO")
    p.setFont("Helvetica", 11)
    
    testo_pdf = [
        f"Comando procedente: {stazione}",
        f"Operanti sul posto: {operanti}",
        f"Dati Sinistro: {localita} | Data e Ora: {data_ora}",
        f"Riferimenti Geografici GPS: {gps}",
        f"Larghezza sede stradale complessiva: {larg_carreggiata} m | Linea di Base X-Z: {base_xz} m",
        "",
        "POSIZIONAMENTO MEZZI RILEVATI (Coordinate calcolate tramite algoritmo):",
        f"- {modello_a} (Targa: {targa_a}) -> Punto A1: X={xa:.2f}, Y={ya:.2f} | Punto A2: X={xa2_c:.2f}, Y={ya2_c:.2f}",
        f"- {modello_b} (Targa: {targa_b}) -> Punto B1: X={xb:.2f}, Y={yb:.2f} | Punto B3: X={xb3_c:.2f}, Y={yb3_c:.2f}",
        "",
        "CARATTERISTICHE DELLO STATO DEI LUOGHI:",
        f"{note_luogo}"
    ]
    
    y_pos = 7.0*inch
    for riga in testo_pdf:
        p.drawString(0.5*inch, y_pos, riga)
        y_pos -= 0.25*inch
        
    p.save()
    pdf_buf.seek(0)

    st.divider()
    st.download_button(
        label="📥 SCARICA TAVOLA E VERBALE IN PDF (Pronto da stampare)",
        data=pdf_buf,
        file_name=f"Rilievo_Planimetrico_{localita.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
