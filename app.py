import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configurazione della pagina dell'applicazione web
st.set_page_config(page_title="Generatore Planimetrico Professionale", layout="wide")
st.title("🚓 Sistema di Generazione Planimetrica ed Elaborazione Rilievi")
st.info("💡 Compila i campi per generare la tavola ufficiale impaginata con cartiglio e legenda.")

col1, col2 = st.columns([1, 1.2])

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
        
        # Calcolo dei punti geometrici dei veicoli nello spazio cartesiano
        pt_a1 = calcola_punto(xa1, za1, base_xz)
        pt_a2 = calcola_punto(xa2, za2, base_xz)
        pt_b1 = calcola_punto(xb1, zb1, base_xz)
        pt_b3 = calcola_punto(xb3, zb3, base_xz)
        
        # Inizializzazione della figura con proporzioni fisse da disegno tecnico (16:10 esteso)
        fig, ax = plt.subplots(figsize=(16, 10))
        fig.patch.set_facecolor('#ffffff')
        
        # Disegno la cornice nera esterna della tavola
        cornice = patches.Rectangle((-4, -6), base_xz + 20, larg_carreggiata + 13, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        # --- CARREGGIATA STRADALE ---
        ax.axhline(y=0, color='#444444', linestyle='-', linewidth=2.5)
        ax.axhline(y=larg_carreggiata, color='#444444', linestyle='-', linewidth=2.5)
        ax.axhline(y=larg_carreggiata/2, color='#888888', linestyle='--', linewidth=1.5)
        ax.text(-3, larg_carreggiata - 0.6, f"cd = {larg_carreggiata} m", fontsize=9, style='italic')
        
        # --- CAPISALDI DI RIFERIMENTO ---
        ax.scatter(0, 0, color='#e67e22', s=150, zorder=5, edgecolor='black')
        ax.scatter(base_xz, 0, color='#e67e22', s=150, zorder=5, edgecolor='black')
        ax.text(0, -0.8, "Caposaldo X\n(Civico 57)", fontsize=9, fontweight='bold', ha='center')
        ax.text(base_xz, -0.8, "Mira Z\n(Palo TIM N°)", fontsize=9, fontweight='bold', ha='center')
        
        # --- VEICOLO A (Punti e Linee di ingombro) ---
        ax.scatter([pt_a1[0], pt_a2[0]], [pt_a1[1], pt_a2[1]], color='blue', s=80, zorder=6)
        ax.plot([pt_a1[0], pt_a2[0]], [pt_a1[1], pt_a2[1]], 'b-', linewidth=3, label=f"Veicolo A: {modello_a}")
        ax.text(pt_a1[0], pt_a1[1] + 0.3, "A1", color='blue', fontweight='bold', fontsize=10)
        ax.text(pt_a2[0], pt_a2[1] + 0.3, "A2", color='blue', fontweight='bold', fontsize=10)
        
        # --- VEICOLO B (Punti e Linee di ingombro) ---
        ax.scatter([pt_b1[0], pt_b3[0]], [pt_b1[1], pt_b3[1]], color='red', s=80, zorder=6)
        ax.plot([pt_b1[0], pt_b3[0]], [pt_b1[1], pt_b3[1]], 'r-', linewidth=3, label=f"Veicolo B: {modello_b}")
        ax.text(pt_b1[0], pt_b1[1] - 0.6, "B1", color='red', fontweight='bold', fontsize=10)
        ax.text(pt_b3[0], pt_b3[1] - 0.6, "B3", color='red', fontweight='bold', fontsize=10)
        
        # Proiezioni metriche tratteggiate verso i capisaldi
        ax.plot([0, pt_a1[0]], [0, pt_a1[1]], 'b:', alpha=0.4)
        ax.plot([base_xz, pt_a1[0]], [0, pt_a1[1]], 'b:', alpha=0.4)
        ax.plot([0, pt_b1[0]], [0, pt_b1[1]], 'r:', alpha=0.4)
        ax.plot([base_xz, pt_b1[0]], [0, pt_b1[1]], 'r:', alpha=0.4)
        
        # --- RIQUADRI IMPAGINATI (LAYOUT ESTERNO) ---
        x_colonna_destra = base_xz + 3
        
        # 1. Box Intestazione / Comando (In alto a destra)
        testo_comando = f"SCHIZZO PLANIMETRICO DI RILIEVO\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}"
        ax.text(x_colonna_destra, larg_carreggiata + 2, testo_comando, fontsize=10, fontweight='bold',
                bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.8'))
        
        # 2. Box Misure dei Veicoli (A destra al centro)
        testo_misure_riquadro = (
            f"MISURE {modello_a.upper()} ({targa_a}):\n"
            f"XA1 = {xa1:.2f} m | ZA1 = {za1:.2f} m\n"
            f"XA2 = {xa2:.2f} m | ZA2 = {za2:.2f} m\n\n"
            f"MISURE {modello_b.upper()} ({targa_b}):\n"
            f"XB1 = {xb1:.2f} m | ZB1 = {zb1:.2f} m\n"
            f"XB3 = {xb3:.2f} m | ZB3 = {zb3:.2f} m"
        )
        ax.text(x_colonna_destra, larg_carreggiata - 4, testo_misure_riquadro, fontsize=9.5,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        
        # 3. Box Cartiglio Località (In basso a sinistra)
        testo_cartiglio = f"CARTIGLIO\n\nData Rilievo: {data_ora}\nLocalità: {localita}\nGPS: {gps}\nBase X-Z = {base_xz} m"
        ax.text(-3, -5.2, testo_cartiglio, fontsize=9.5,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        
        # 4. Box Caratteristiche del Luogo (In basso al centro/destra)
        testo_ambientale = f"CARATTERISTICHE DEL LUOGO DEL SINISTRO\n\n{note_luogo}"
        ax.text(9, -5.2, testo_ambientale, fontsize=9, wrap=True,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7'))
        
        # Pulizia assi matematici per impaginazione pulita da foglio da disegno
        ax.set_xlim(-4, base_xz + 15)
        ax.set_ylim(-6, larg_carreggiata + 6)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Mostra il disegno finito a schermo sul telefono
        st.pyplot(fig)
        
        # Generazione automatica del testo della relazione per copia-incolla
        st.subheader("3. Verbale e Relazione Descrittiva")
        verbale = f"""
        RELAZIONE DESCRITTIVA DI RILIEVO PLANIMETRICO AUTOMATIZZATO
        -----------------------------------------------------------
        Ufficio/Comando: {stazione}
        Operanti: {operanti}
        Dati Sinistro: {localita} | Data-Ora: {data_ora} | GPS: {gps}
        Larghezza Sede Stradale: {larg_carreggiata} metri | Linea di Base X-Z: {base_xz} metri
        
        POSIZIONE STATICA DI BLOCCO DEI VEICOLI COINVOLTI (Coordinate Relative):
        - {modello_a} (Targa: {targa_a}): Spigolo A1 ({xa:.2f}, {ya:.2f}) | Spigolo A2 ({pt_a2[0]:.2f}, {pt_a2[1]:.2f})
        - {modello_b} (Targa: {targa_b}): Spigolo B1 ({xb:.2f}, {yb:.2f}) | Spigolo B3 ({pt_b3[0]:.2f}, {pt_b3[1]:.2f})
        """
        st.code(verbale, language="text")
