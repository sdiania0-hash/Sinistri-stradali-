import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configurazione della pagina dell'app
st.set_page_config(page_title="Rilievo Sinistri Smart", layout="wide")
st.title("🚓 Sistema Automatizzato Rilievi ed Elaborazione Planimetrica")
st.info("💡 Inserisci i dati letti dallo schizzo per generare la planimetria vettoriale.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Acquisizione Dati")
    
    st.subheader("Dati di Contesto")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    gps = st.text_input("Coordinate GPS", value="40.019572, 18.118944")
    base_xz = st.number_input("Distanza Base Capisaldi X-Z (metri)", value=25.05)
    larg_carreggiata = st.number_input("Larghezza Carreggiata (metri)", value=6.60)
    
    st.subheader("Misure di Trilaterazione")
    st.write("**Veicolo A (Citroën C3)**")
    xa1 = st.number_input("Distanza XA1", value=16.60)
    za1 = st.number_input("Distanza ZA1", value=11.55)
    
    st.write("**Veicolo B (Alfa Romeo 147)**")
    xb1 = st.number_input("Distanza XB1", value=16.30)
    zb1 = st.number_input("Distanza ZB1", value=10.55)

with col2:
    st.header("2. Elaborazione e Output Grafico")
    
    if st.button("ELABORA I DATI E GENERA PLANIMETRIA"):
        st.success("✨ Calcolo geometrico completato!")
        
        # Algoritmo matematico di trilaterazione
        def calcola_punto(rx, rz, d):
            a = (rx**2 - rz**2 + d**2) / (2 * d)
            h = np.sqrt(max(0, rx**2 - a**2))
            return a, h
        
        # Calcolo delle posizioni cartesiane dei veicoli
        xa, ya = calcola_punto(xa1, za1, base_xz)
        xb, yb = calcola_punto(xb1, zb1, base_xz)
        
        # Generazione della planimetria grafica
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.axhline(y=0, color='black', linestyle='-', linewidth=2)
        ax.axhline(y=larg_carreggiata, color='black', linestyle='-', linewidth=2)
        ax.axhline(y=larg_carreggiata/2, color='gray', linestyle='--', linewidth=1)
        
        # Capisaldi fisici
        ax.scatter(0, 0, color='orange', s=120, zorder=5)
        ax.scatter(base_xz, 0, color='orange', s=120, zorder=5)
        
        # Posizione dei veicoli rilevati
        ax.scatter(xa, ya, color='blue', s=100, zorder=5, label='Veicolo A (Citroën C3)')
        ax.scatter(xb, yb, color='red', s=100, zorder=5, label='Veicolo B (Alfa Romeo 147)')
        
        ax.text(-1, -0.6, 'X (Civ. 57)', fontsize=9, fontweight='bold', color='orange')
        ax.text(base_xz-2, -0.6, 'Z (Palo TIM)', fontsize=9, fontweight='bold', color='orange')
        ax.text(xa+0.3, ya, 'A1', fontsize=10, color='blue', fontweight='bold')
        ax.text(xb+0.3, yb, 'B1', fontsize=10, color='red', fontweight='bold')
        
        ax.set_xlim(-3, base_xz + 3)
        ax.set_ylim(-1.5, larg_carreggiata + 2)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend()
        
        st.pyplot(fig)
        
        # Compilazione automatica del testo della relazione
        st.subheader("3. Relazione Tecnica Descrittiva")
        verbale = f"""
        RELAZIONE DESCRITTIVA DI RILIEVO PLANIMETRICO AUTOMATIZZATO
        -----------------------------------------------------------
        Località: {localita} | Coordinate GPS: {gps}
        Base di misurazione X-Z: {base_xz} m | Larghezza strada: {larg_carreggiata} m
        
        Punti geometrici calcolati rispetto ai Capisaldi fisici:
        - Spigolo Anteriore Veicolo A (A1): X={xa:.2f}, Y={ya:.2f}
        - Spigolo Anteriore Veicolo B (B1): X={xb:.2f}, Y={yb:.2f}
        """
        st.code(verbale, language="text")
