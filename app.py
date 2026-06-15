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

# Configurazione iniziale dell'applicazione
st.set_page_config(page_title="Rilievo Topografico GPS Pro", layout="wide")
st.title("🛰️ Software di Rilievo Planimetrico GPS Professionale")
st.info("💡 Configura lo scenario, scegli i mezzi e inserisci i dati per generare la tavola formattata.")

col1, col2 = st.columns([1, 1.3])

with col1:
    st.header("1. Configurazione Scenario e Dati")
    
    st.subheader("Intestazione Verbale")
    stazione = st.text_input("Stazione / Comando / Ufficio", value="STAZIONE CC MATINO")
    operanti = st.text_input("Operanti sul posto", value="Brig. Rima G., V.B. Rizzo V.")
    data_ora = st.text_input("Data e Ora del Rilievo", value="15/06/2026 | ORE: 22:45")
    localita = st.text_input("Località / Strada", value="SP55 Matino-Taviano")
    
    st.subheader("Morfologia della Strada")
    # 3. Scelta dello sfondo stradale
    tipo_strada = st.selectbox("Tipologia di scenario stradale", options=["Rettilineo", "Curva a Destra", "Incrocio a T", "Rotatoria"], index=0)
    larg_carreggiata = st.number_input("Larghezza Carreggiata (metri)", value=6.60)
    note_luogo = st.text_area("Annotazioni sullo stato dei luoghi", value="Fondo stradale: asfalto asciutto. Condizioni di luce: diurna.")

    st.divider()
    st.subheader("Coordinate GPS Capisaldi (WGS84)")
    
    # 1. Pulsante per simulare o acquisire la posizione attuale GPS
    if st.button("📍 Usa la mia posizione attuale per Caposaldo X"):
        st.session_state["lat_x_val"] = 40.019572
        st.session_state["lon_x_val"] = 18.118944
        st.success("Posizione Caposaldo X acquisita!")

    lat_x = st.number_input("Latitudine Caposaldo X", value=st.session_state.get("lat_x_val", 40.019572), format="%.6f")
    lon_x = st.number_input("Longitudine Caposaldo X", value=st.session_state.get("lon_x_val", 18.118944), format="%.6f")
    
    lat_z = st.number_input("Latitudine Mira Z", value=40.019590, format="%.6f")
    lon_z = st.number_input("Longitudine Mira Z", value=18.119230, format="%.6f")
    
    st.divider()
    st.subheader("Configurazione Mezzi Rilevati")
    num_veicoli = st.selectbox("Numero totale di veicoli coinvolti nel sinistro", options=[2, 3, 4, 5], index=0)
    
    # Valori standard per la simulazione iniziale
    default_modelli = ["Citroën C3", "Alfa Romeo 147", "Sconosciuto", "Sconosciuto", "Sconosciuto"]
    default_targhe = ["AA123BB", "CC456DD", "EE789FF", "GG012HH", "JJ345KK"]
    default_lats = [40.019585, 40.019565, 40.019595, 40.019555, 40.019575]
    default_lons = [18.119050, 18.119060, 18.119120, 18.119150, 18.119180]
    
    elenco_veicoli = []
    
    for i in range(num_veicoli):
        lettera = chr(65 + i)
        st.write(f"--- **VEICOLO {lettera}** ---")
        
        # 4. Scelta del tipo di veicolo (Auto, Moto, Camion) con dimensioni dinamiche
        tipo_mezzo = st.selectbox(f"Tipo Veicolo {lettera}", options=["Autovettura (Standard)", "Motoveicolo (Piccolo)", "Autocarro / Camion (Grande)"], index=0, key=f"tipo_{i}")
        
        if tipo_mezzo == "Autovettura (Standard)":
            lung, larg = 4.2, 1.8
        elif tipo_mezzo == "Motoveicolo (Piccolo)":
            lung, larg = 2.0, 0.8
        else:
            lung, larg = 10.0, 2.5
            
        modello = st.text_input(f"Marca e Modello {lettera}", value=default_modelli[i], key=f"mod_{i}")
        targa = st.text_input(f"Targa {lettera}", value=default_targhe[i], key=f"tg_{i}")
        
        # 2. Slider di rotazione manuale dell'auto (0-360 gradi)
        rotazione = st.slider(f"Angolo di inclinazione / rotazione Veicolo {lettera} (gradi)", min_value=0, max_value=360, value=0, step=5, key=f"rot_{i}")
        
        lat = st.number_input(f"Latitudine GPS {lettera}", value=default_lats[i], format="%.6f", key=f"lat_{i}")
        lon = st.number_input(f"Longitudine GPS {lettera}", value=default_lons[i], format="%.6f", key=f"lon_{i}")
        
        elenco_veicoli.append({
            "lettera": lettera, "modello": modello, "targa": targa, 
            "lat": lat, "lon": lon, "lung": lung, "larg": larg, "rot": rotazione, "tipo": tipo_mezzo
        })

with col2:
    st.header("2. Elaborazione e Grafica Professionale")
    
    if st.button("ELABORA COORDINATE E GENERA TAVOLA UFFICIALE"):
        st.success("✨ Elaborazione layout completata!")
        
        # Funzione di conversione GPS -> Metri
        def gps_a_metri(lat1, lon1, lat2, lon2):
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlam = math.radians(lon2 - lon1)
            x = dlam * R * math.cos((phi1 + phi2) / 2)
            y = dphi * R
            return x, y

        # Calcolo distanze Capisaldi
        x_x, y_x = 0.0, 0.0
        x_z, y_z = gps_a_metri(lat_x, lon_x, lat_z, lon_z)
        base_calcolata = math.sqrt(x_z**2 + y_z**2)
        
        fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
        fig.patch.set_facecolor('#ffffff')
        
        # Bordo tavola tecnica
        cornice = patches.Rectangle((-12, -12), base_calcolata + 30, larg_carreggiata + 24, linewidth=2, edgecolor='black', facecolor='none')
        ax.add_patch(cornice)
        
        # --- 3. DISEGNO DELLO SFONDO STRADALE DINAMICO ---
        if tipo_strada == "Rettilineo":
            strada = patches.Rectangle((-12, -larg_carreggiata/2), base_calcolata + 30, larg_carreggiata, facecolor='#444444', alpha=0.9, zorder=1)
            ax.add_patch(strada)
            ax.axhline(y=0, color='white', linestyle='--', linewidth=2, zorder=2)
        elif tipo_strada == "Curva a Destra":
            strada = patches.Wedge((base_calcolata/2, -20), 20 + larg_carreggiata, 70, 110, width=larg_carreggiata, facecolor='#444444', alpha=0.9, zorder=1)
            ax.add_patch(strada)
        elif tipo_strada == "Incrocio a T":
            strada_oriz = patches.Rectangle((-12, -larg_carreggiata/2), base_calcolata + 30, larg_carreggiata, facecolor='#444444', alpha=0.9, zorder=1)
            strada_vert = patches.Rectangle((base_calcolata/2 - larg_carreggiata/2, -12), larg_carreggiata, 12, facecolor='#444444', alpha=0.9, zorder=1)
            ax.add_patch(strada_oriz)
            ax.add_patch(strada_vert)
        else: # Rotatoria
            rotatoria = patches.Circle((base_calcolata/2, 0), 8, facecolor='#444444', alpha=0.9, zorder=1)
            isola_centrale = patches.Circle((base_calcolata/2, 0), 3, facecolor='#2ecc71', edgecolor='white', zorder=2)
            ax.add_patch(rotatoria)
            ax.add_patch(isola_centrale)

        # Disegno Capisaldi fisici
        ax.scatter(x_x, y_x, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.scatter(x_z, y_z, color='#e67e22', s=200, zorder=5, edgecolor='black', marker='X')
        ax.text(x_x, y_x - 1.8, "Caposaldo X\n(Origine Rilievo)", fontsize=10, fontweight='bold', ha='center')
        ax.text(x_z, y_z - 1.8, "Mira Z\n(Punto Riferimento)", fontsize=10, fontweight='bold', ha='center')
        
        colori = ['blue', 'red', 'green', 'purple', 'magenta']
        testo_misure_riquadro = ""
        testo_pdf_veicoli = ""
        
        # Disegno e calcolo di tutti i veicoli configurati
        for idx, v in enumerate(elenco_veicoli):
            x_v, y_v = gps_a_metri(lat_x, lon_x, v["lat"], v["lon"])
            colore_veicolo = colori[idx % len(colori)]
            
            # 2. & 4. Sagoma con Ingombro e Rotazione impostata dall'utente
            box_v = patches.Rectangle(
                (x_v - v["lung"]/2, y_v - v["larg"]/2), v["lung"], v["larg"], 
                angle=v["rot"], rotation_point='center',
                edgecolor='black', facecolor=colore_veicolo, alpha=0.85, zorder=4
            )
            ax.add_patch(box_v)
            
            # Etichettatura dinamica sul grafico
            ax.text(x_v, y_v + v["larg"] + 0.5, f"Veic. {v['lettera']}\n[{v['targa']}]", color=colore_veicolo, fontweight='bold', fontsize=9, ha='center', bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.2'))
            ax.plot([0, x_v], [0, y_v], color=colore_veicolo, linestyle=':', alpha=0.4) # Linea visiva di puntamento
            
            testo_misure_riquadro += f"VEICOLO {v['lettera']} ({v['modello']}):\nTipo: {v['tipo']}\nLat: {v['lat']:.6f} | Lon: {v['lon']:.6f}\nInclinazione: {v['rot']}°\n\n"
            testo_pdf_veicoli += f"- Veicolo {v['lettera']} ({v['modello']} - tg. {v['targa']}): Tipo {v['tipo']} | Angolo {v['rot']}° | GPS: Lat {v['lat']:.6f}, Lon {v['lon']:.6f}\n"

        # Strutturazione dei riquadri del cartiglio e delle tabelle laterali
        x_box = max(base_calcolata + 5, 20)
        ax.text(x_box, 7, f"SCHIZZO PLANIMETRICO PRO\n\nCOMANDO: {stazione.upper()}\n\nOPERANTI:\n{operanti}", fontsize=10, fontweight='bold', bbox=dict(facecolor='#f8f9fa', edgecolor='black', boxstyle='square,pad=0.8', linewidth=1.5))
        ax.text(x_box, -5, f"DATI SATELLITARI MEZZI:\n\nBase X-Z: {base_calcolata:.2f} m\n\n{testo_misure_riquadro}", fontsize=9, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7', linewidth=1.5))
        ax.text(-10, -10, f"CARTIGLIO DI RILIEVO UFFICIALE\nData: {data_ora}\nLocalità: {localita}\nScenario: {tipo_strada} (cd={larg_carreggiata}m)", fontsize=9.5, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7', linewidth=1.5))
        ax.text(8, -10, f"NOTE TECNICHE STATO DEI LUOGHI\n\n{note_luogo}", fontsize=9, wrap=True, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.7', linewidth=1.5))
        
        ax.set_xlim(-12, x_box + 14)
        ax.set_ylim(-12, larg_carreggiata + 11)
