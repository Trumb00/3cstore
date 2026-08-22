import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Gestionale Osteria", page_icon="🍷", layout="wide")

# 2. Connessione a Supabase
# Usiamo st.cache_resource per mantenere la connessione attiva ed evitare rallentamenti
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Errore di connessione a Supabase. Assicurati di aver inserito i Secrets nella dashboard di Streamlit.")
    st.stop()

# 3. Interfaccia Principale
st.title("🍷 Gestionale Osteria")

# Creiamo le schede di navigazione
tab_magazzino, tab_ricettario = st.tabs(["📦 Magazzino & Acquisti", "📖 Ricettario (Food Cost)"])

# --- SCHEDA MAGAZZINO ---
with tab_magazzino:
    st.subheader("Gestione Fornitori")
    st.markdown("Aggiungi o modifica i fornitori cliccando direttamente sulle celle della tabella qui sotto.")
    
    # Leggiamo i dati dal database
    response = supabase.table("fornitori").select("*").execute()
    fornitori_data = response.data
    
    # Trasformiamo i dati in un DataFrame Pandas per gestirli meglio nella griglia
    if fornitori_data:
        df_fornitori = pd.DataFrame(fornitori_data)
    else:
        # Se la tabella è vuota, creiamo un DataFrame vuoto con le colonne corrette
        df_fornitori = pd.DataFrame(columns=["id", "nome", "tipo", "is_active", "created_at"])
    
    # Mostriamo solo le colonne utili da modificare, nascondendo ID e date di sistema
    colonne_visibili = ["nome", "tipo", "is_active"]
    
    # Creiamo la griglia interattiva
    # num_rows="dynamic" permette di aggiungere nuove righe col tasto (+)
    edited_df = st.data_editor(
        df_fornitori[colonne_visibili] if not df_fornitori.empty else pd.DataFrame(columns=colonne_visibili),
        num_rows="dynamic",
        use_container_width=True,
        key="fornitori_editor"
    )
    
    # Aggiungiamo un pulsante per salvare (la logica di salvataggio la implementeremo nel prossimo step)
    if st.button("💾 Salva Modifiche Fornitori", type="primary"):
        st.info("La funzione di salvataggio sul database arriverà nel prossimo step!")

# --- SCHEDA RICETTARIO ---
with tab_ricettario:
    st.subheader("Ricettario in arrivo")
    st.write("Qui inseriremo il calcolatore dinamico delle porzioni.")
