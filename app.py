import streamlit as st
from supabase import create_client, Client
import pandas as pd

st.set_page_config(page_title="Gestionale Osteria", page_icon="🍷", layout="wide")

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- SISTEMA DI LOGIN ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔒 Accesso Richiesto")
    st.info("Per visualizzare e modificare il magazzino, devi effettuare l'accesso.")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        
        if submitted:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Credenziali errate. Riprova.")
    st.stop() # Ferma l'esecuzione del resto della pagina se non sei loggato

# Tasto di uscita
with st.sidebar:
    if st.button("Log Out"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("🍷 Gestionale Osteria")

tab_magazzino, tab_ricettario = st.tabs(["📦 Magazzino & Acquisti", "📖 Ricettario (Food Cost)"])

with tab_magazzino:
    st.subheader("Gestione Fornitori")
    
    # Lettura dati dal database
    response = supabase.table("fornitori").select("*").order("created_at").execute()
    
    # Creazione del dataframe
    if response.data:
        df_fornitori = pd.DataFrame(response.data)
        # Filtriamo per mostrare solo i fornitori attivi (nascondiamo quelli eliminati)
        df_fornitori = df_fornitori[df_fornitori["is_active"] == True] 
    else:
        df_fornitori = pd.DataFrame(columns=["id", "nome", "tipo", "is_active", "created_at"])
    
    # Creiamo la griglia interattiva
    # La funzione column_config ci permette di nascondere colonne tecniche (come l'ID) senza perderle
    edited_df = st.data_editor(
        df_fornitori,
        column_config={
            "id": None, 
            "created_at": None,
            "is_active": None, # Lo nascondiamo perché usiamo il cestino per il soft delete
            "nome": st.column_config.TextColumn("Nome Fornitore", required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["Abituale", "Occasionale"], required=True),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="fornitori_editor" # Fondamentale per tracciare le modifiche
    )
    
    # Logica di salvataggio
    if st.button("💾 Salva Modifiche Fornitori", type="primary"):
        changes = st.session_state["fornitori_editor"]
        
        try:
            # 1. Inserimento nuove righe (Added Rows)
            if changes.get("added_rows"):
                nuovi = [{"nome": r.get("nome"), "tipo": r.get("tipo", "Abituale"), "is_active": True} for r in changes["added_rows"]]
                supabase.table("fornitori").insert(nuovi).execute()
            
            # 2. Modifica righe esistenti (Edited Rows)
            if changes.get("edited_rows"):
                for index, updates in changes["edited_rows"].items():
                    row_id = df_fornitori.iloc[index]["id"]
                    supabase.table("fornitori").update(updates).eq("id", row_id).execute()
            
            # 3. Eliminazione (Deleted Rows) -> Facciamo il Soft Delete
            if changes.get("deleted_rows"):
                for index in changes["deleted_rows"]:
                    row_id = df_fornitori.iloc[index]["id"]
                    supabase.table("fornitori").update({"is_active": False}).eq("id", row_id).execute()

            st.success("Modifiche salvate con successo!")
            st.rerun() # Ricarica per aggiornare i dati
        except Exception as e:
            st.error(f"Errore di autorizzazione: il tuo utente non ha i permessi da Admin/Responsabile.")

with tab_ricettario:
    st.subheader("Modulo Ricettario")
    st.write("Questa sezione verrà costruita a breve.")
