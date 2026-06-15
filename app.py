import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configurazione della pagina dell'applicazione web
st.set_page_config(page_title="Generatore Planimetrico Professionale", layout="wide")
st.title("🚓 Sistema di Generazione Planimetrica ed Elaborazione Rilievi")
st.info("💡 Compila i campi per generare la tavola ufficiale impaginata con cartiglio e legenda.")

col1, col2 = st.columns([1, 1.4])

with col1:
    st.header("1. Inserimento Dati del Sinistro")
    
    st.subheader("Intestazione e Operanti")
    stazione = st.text_input("Stazione / Comando / Studio", value="STAZIONE CC MATINO")
    operanti = st.text_input("Operanti (es. Brig. Rima G., V.B. Rizzo V.)", value="Brig. Rima G., V.B. Rizzo V.")
    
    st.subheader("Dati di Contesto")
    data_ora = st.text_input("Data e Ora del Sinistro", value="15/06/2026 | ORE: 06:50")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    gps = st.text_input("Coordinate GPS", value="40.019572, 18.118944")
    
    st.subheader("Parametri della Strada")
    base_xz = st.number_input("Distanza Base Capisaldi X-Z (metri)", value=25.05)
    larg_carreggiata = st.number_input("Larghezza Carreggiata cd (metri)", value=6.60)
    note_luogo = st.text_area("Caratteristiche del luogo", value="Strada Provinciale SP55, carreggiata a doppio senso di circolazione. Fondo stradale: asfalto asciutto. Condizioni di luce: diurna. Presenza di intersezione con strada vicinale. Nel corso del sopralluogo non sono state rilevate tracce di frenata.")

    st.divider()
    
    st.subheader("Misure Geometriche Veicoli")
    
    st.write("**Dati Veicolo A**")
    modello_a = st.text_input("Modello Veicolo A", value="Citroën C3")
    targa_a = st.text_input("Targa Veicolo A", value="AA123BB")
    xa1 = st.number_input("Distanza XA1 (da Caposaldo X)", value=16.60)
    za1 = st.number_input("Distanza ZA1 (da Mira Z)", value=11.55)
    xa2 = st.number_input("Distanza XA2 (da Caposaldo X)", value=18.20)
    za2 = st.number_input("Distanza ZA2 (da Mira Z)", value=11.00)
    
    st.write("**Dati Veicolo B**")
    modello_b = st.text_input("Modello Veicolo B", value="Alfa Romeo 147")
    targa_b = st.text_input("Targa Veicolo B", value="CC456DD")
    xb1 = st.number_input("Distanza XB1 (da Caposaldo X)", value=16.30)
    zb1 = st.number_input("Distanza ZB1 (da Mira Z)", value=10.55)
    xb3 = st.number_input("Distanza XB3 (da Caposaldo X)", value=18.05)
    zb3 = st.number_input("Distanza ZB3 (da Mira Z)", value=8.70)

with col2:
    st.header("2. Tavola Grafica di Rilievo Finita")
    
    if st.button("ELABORA E GENERA TAVOLA UFFICIALE"):
        st.success("✨ Elaborazione layout completata!")
        
        # Algoritmo matematico di trilaterazione (da raggi a coordinate cartesiane)
        def calcola_punto(rx, rz, d):
            a = (rx**2 - rz**2 + d**2) / (2 * d)
            h = np.sqrt(max(0, rx**2 - a**2))
            return a, h
        
        # Calcolo delle coordinate cartesiane reali
        xa, ya = calcola_punto(xa1, za1, base_xz)
        xa2_c, ya2_c = calcola_punto(xa2, za2, base_xz)
        xb, yb = calcola_punto(xb1, zb1, base_xz)
        xb3_c, yb3_c = calcola_punto(xb3, zb3, base_xz)
        
        # Impostazione figura espansa e ad alta definizione (DPI alti per evitare sgranature)
        fig, ax = plt.subplots(figsize=(16, 11), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        # Cornice perimetrale esterna rigida
        cornice = patches.Rectangle((-5, -6), base_xz + 24, larg_carreggiata + 13, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        # --- CARREGGIATA STRADALE STRUTTURATA ---
        ax.axhline(y=0, color='black', linestyle='-', linewidth=3)
        ax.axhline(y=larg_carreggiata, color='black', linestyle='-', linewidth=3)
        ax.axhline(y=larg_carreggiata/2, color='#7f8c8d', linestyle='--', linewidth=2)
        ax.text(-4, larg_carreggiata - 0.7, f"cd = {larg_carreggiata} m", fontsize=11, style='italic', fontweight='bold')
        
        # --- CAPISALDI DI RIFERIMENTO ---
        ax.scatter(0, 0, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.scatter(base_xz, 0, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.text(0, -1.2, "Caposaldo X\n(Civico 57)", fontsize=11, fontweight='bold', ha='center', color='#d35400')
        ax.text(base_xz, -1.2, "Mira Z\n(Palo TIM N°)", fontsize=11, fontweight='bold', ha='center', color='#d35400')
        
        # --- DISEGNO VEICOLI CON FINITURE SPESSE ---
        # Veicolo A (Blu)
        ax.plot([xa, xa2_c], [ya, ya2_c], color='#1b3a4b', linestyle='-', linewidth=8, solid_capstyle='round', zorder=6)
        ax.scatter([xa, xa2_c], [ya, ya2_c], color='blue', s=120, zorder=7, edgecolor='black')
        ax.text(xa, ya + 0.4, "A1", color='blue', fontweight='bold', fontsize=12, ha='center')
        ax.text(xa2_c, ya2_c + 0.4, "A2", color='blue', fontweight='bold', fontsize=12, ha='center')
        
        # Veicolo B (Rosso)
        ax.plot([xb, xb3_c], [yb, yb3_c], color='#780000', linestyle='-', linewidth=8, solid_capstyle='round', zorder=6)
        ax.scatter([xb, xb3_c], [yb, yb3_c], color='red', s=120, zorder=7, edgecolor='black')
        ax.text(xb, yb - 0.8, "B1", color='red', fontweight='bold', fontsize=12, ha='center')
        ax.text(xb3_c, yb3_c - 0.8, "B3", color='red', fontweight='bold', fontsize=12, ha='center')
        
        # Linee tratteggiate di proiezione ad alta visibilità
        ax.plot([0, xa], [0, ya], 'b--', linewidth=1, alpha=0.6)
        ax.plot([base_xz, xa], [0, ya], 'b--', linewidth=1, alpha=0.6)
        ax.plot([0, xb], [0, yb], 'r--', linewidth=1, alpha=0.6)
        ax.plot([base_xz, xb], [0, yb], 'r--', linewidth=1, alpha=0.6)
        
        # --- BLOCCHI DI IMPAGINAZIONE PERIMETRALI SQUADRATI ---
        x_blocco_destra = base_xz + 3.5
        
        # 1. Box Intestazione Superiore Destra
        testo_comando = f"SCHIZZO PLANIMETRICO DI RILIEVO\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}"
        ax.text(x_blocco_destra, larg_carreggiata + 1.2, testo_comando, fontsize=11, fontweight='bold',
                bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.9', linewidth=1.5))
        
        # 2. Box Elenco Misure Centrale Destra
        testo_misure_riquadro = (
            f"MISURE {modello_a.upper()} ({targa_a}):\n"
            f"XA1 = {xa1:.2f} m | ZA1 = {za1:.2f} m\n"
            f"XA2 = {xa2:.2f} m | ZA2 = {za2:.2f} m\n\n"
            f"MISURE {modello_b.upper()} ({targa_b}):\n"
            f"XB1 = {xb1:.2f} m | ZB1 = {zb1:.2f} m\n"
            f"XB3 = {xb3:.2f} m | ZB3 = {zb3:.2f} m"
        )
        ax.text(x_blocco_destra, larg_carreggiata - 5, testo_misure_riquadro, fontsize=10.5,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
        
        # 3. Box Cartiglio Inferiore Sinistra
        testo_cartiglio = f"CARTIGLIO DI RILIEVO\n\nData: {data_ora}\nLocalità: {localita}\nGPS: {gps}\nBase X-Z = {base_xz} m"
        ax.text(-4, -5.2, testo_cartiglio, fontsize=10.5,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
        
        # 4. Box Caratteristiche del Luogo Inferiore Destra
        testo_ambientale = f"CARATTERISTICHE DEL LUOGO DEL SINISTRO\n\n{note_luogo}"
        ax.text(8.5, -5.2, testo_ambientale, fontsize=10, wrap=True,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
        
        # Bilanciamento degli spazi interni ed eliminazione dei margini superflui
        ax.set_xlim(-5, base_xz + 17)
        ax.set_ylim(-6, larg_carreggiata + 5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        st.pyplot(fig)
        
        # Sezione Verbale Corretta (Risolto l'errore NameError)
        st.subheader("3. Verbale e Relazione Descrittiva")
        verbale = f"""
        RELAZIONE DESCRITTIVA DI RILIEVO PLANIMETRICO AUTOMATIZZATO
        -----------------------------------------------------------
        Ufficio/Comando: {stazione}
        Operanti: {operanti}
        Dati Sinistro: {localita} | Data-Ora: {data_ora} | GPS: {gps}
        Larghezza Sede Stradale: {larg_carreggiata} metri | Linea di Base X-Z: {base_xz} metri
        
        POSIZIONE STATICA DI BLOCCO DEI VEICOLI COINVOLTI (Coordinate Relative):
        - {modello_a} (Targa: {targa_a}): Spigolo A1 ({xa:.2f}, {ya:.2f}) | Spigolo A2 ({xa2_c:.2f}, {ya2_c:.2f})
        - {modello_b} (Targa: {targa_b}): Spigolo B1 ({xb:.2f}, {yb:.2f}) | Spigolo B3 ({xb3_c:.2f}, {yb3_c:.2f})
        """
        st.code(verbale, language="text")
