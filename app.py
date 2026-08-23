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
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Credenziali errate.")
    st.stop()

with st.sidebar:
    st.write(f"Utente: {st.session_state.user.email}")
    if st.button("Log Out"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("🍷 Gestionale Osteria")

tab_listino, tab_fornitori, tab_ricettario = st.tabs(["🛒 Listino Acquisti", "🚚 Fornitori", "📖 Ricettario"])

# --- SCHEDA LISTINO ACQUISTI (LA GRIGLIA PRINCIPALE) ---
with tab_listino:
    st.subheader("Inserimento Prezzi e Varianti")
    st.markdown("Compila la tabella. Gli ingredienti nuovi verranno creati automaticamente.")
    
    # 1. Recuperiamo i Fornitori per il menu a tendina
    res_fornitori = supabase.table("fornitori").select("id, nome").eq("is_active", True).execute()
    fornitori_dict = {f["nome"]: f["id"] for f in res_fornitori.data} if res_fornitori.data else {}
    lista_nomi_fornitori = list(fornitori_dict.keys())
    
    # 2. Recuperiamo il Listino attuale unito agli Ingredienti
    # Nota: su Supabase usiamo la sintassi relazionale per unire le tabelle
    query = """
        id, 
        prezzo_acquisto, 
        peso_unita_acquisto_g, 
        iva, 
        is_scelto,
        nome_specifico_prodotto,
        ingredienti (id, nome_generico, dettaglio_variante, um_ricetta, categoria),
        fornitori (id, nome)
    """
    res_listino = supabase.table("listino_acquisti").select(query).eq("is_active", True).execute()
    
    # 3. Trasformiamo i dati complessi in una tabella piatta per Streamlit (stile Excel)
    dati_piatti = []
    if res_listino.data:
        for row in res_listino.data:
            ing = row.get("ingredienti", {})
            forn = row.get("fornitori", {})
            
            # Gestione sicura per evitare errori se un ingrediente o fornitore è stato eliminato
            if not ing: ing = {"nome_generico": "N/A", "dettaglio_variante": "", "um_ricetta": "g", "categoria": "N/A"}
            if not forn: forn = {"nome": "N/A"}
                
            gen = ing.get("nome_generico", "")
            dett = ing.get("dettaglio_variante", "")
            # Creiamo la stringa concatenata che i cuochi vedranno
            nome_ricetta = f"{gen} {dett}".strip()
            
            dati_piatti.append({
                "listino_id": row["id"],
                "ingrediente_id": ing.get("id"),
                "Generico": gen,
                "Dettaglio (Variante)": dett,
                "Nome in Ricetta": nome_ricetta,
                "UM Ricetta": ing.get("um_ricetta", "g"),
                "Categoria": ing.get("categoria", ""),
                "Fornitore": forn.get("nome", ""),
                "Nome Commerciale": row.get("nome_specifico_prodotto", ""),
                "Peso Acquisto (g/ml)": row.get("peso_unita_acquisto_g", 0),
                "Prezzo (€)": row.get("prezzo_acquisto", 0.0),
                "IVA (%)": row.get("iva", 0),
                "Scelto": row.get("is_scelto", False)
            })
    
    df_listino = pd.DataFrame(dati_piatti) if dati_piatti else pd.DataFrame(columns=[
        "listino_id", "ingrediente_id", "Generico", "Dettaglio (Variante)", "Nome in Ricetta", 
        "UM Ricetta", "Categoria", "Fornitore", "Nome Commerciale", "Peso Acquisto (g/ml)", 
        "Prezzo (€)", "IVA (%)", "Scelto"
    ])
    
    # 4. Renderizziamo la Griglia Dati (st.data_editor)
    edited_listino = st.data_editor(
        df_listino,
        column_config={
            "listino_id": None, # Nascosto
            "ingrediente_id": None, # Nascosto
            "Nome in Ricetta": st.column_config.TextColumn("🔗 Nome in Ricetta", disabled=True), # Sola lettura
            "UM Ricetta": st.column_config.SelectboxColumn("UM", options=["g", "Kg", "ml", "L", "pz"]),
            "Fornitore": st.column_config.SelectboxColumn("Fornitore", options=lista_nomi_fornitori),
            "Peso Acquisto (g/ml)": st.column_config.NumberColumn("Peso (g/ml)", min_value=0),
            "Prezzo (€)": st.column_config.NumberColumn("Prezzo (€)", format="%.2f"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="listino_editor"
    )
    
    # 5. Logica di Salvataggio Intelligente
    if st.button("💾 Salva Magazzino", type="primary"):
        changes = st.session_state["listino_editor"]
        
        # --- Aggiunta Nuove Righe ---
        if changes.get("added_rows"):
            for riga in changes["added_rows"]:
                # Pulisce i testi per evitare duplicati causati da spazi
                gen = str(riga.get("Generico", "")).strip().title()
                dett = str(riga.get("Dettaglio (Variante)", "")).strip().lower()
                nome_forn = riga.get("Fornitore")
                
                if not gen or not nome_forn:
                    st.warning("Per aggiungere una riga, 'Generico' e 'Fornitore' sono obbligatori.")
                    continue
                
                forn_id = fornitori_dict.get(nome_forn)
                
                # Check se l'ingrediente Base esiste già
                check_ing = supabase.table("ingredienti").select("id").eq("nome_generico", gen).eq("dettaglio_variante", dett).execute()
                
                if check_ing.data:
                    # L'ingrediente esiste, usiamo il suo ID
                    ing_id = check_ing.data[0]["id"]
                else:
                    # L'ingrediente NON esiste, lo creiamo "dietro le quinte"
                    nuovo_ing = {
                        "nome_generico": gen,
                        "dettaglio_variante": dett,
                        "um_ricetta": riga.get("UM Ricetta", "g"),
                        "categoria": riga.get("Categoria", "Altro")
                    }
                    res_ing = supabase.table("ingredienti").insert(nuovo_ing).execute()
                    ing_id = res_ing.data[0]["id"]
                
                # Ora salviamo il prezzo specifico nel Listino
                nuovo_prezzo = {
                    "ingrediente_id": ing_id,
                    "fornitore_id": forn_id,
                    "nome_specifico_prodotto": riga.get("Nome Commerciale", f"{gen} {dett} {nome_forn}"),
                    "peso_unita_acquisto_g": riga.get("Peso Acquisto (g/ml)", 1000),
                    "prezzo_acquisto": riga.get("Prezzo (€)", 0.0),
                    "iva": riga.get("IVA (%)", 0),
                    "is_scelto": riga.get("Scelto", False)
                }
                supabase.table("listino_acquisti").insert(nuovo_prezzo).execute()
        
        # (Nota per lo sviluppo: qui andrà aggiunta anche la logica per edited_rows e deleted_rows)
        
        st.success("Listino aggiornato con successo!")
        st.rerun()

# --- SCHEDA FORNITORI (Il codice che avevamo scritto nello step precedente) ---
with tab_fornitori:
    st.subheader("Gestione Fornitori")
    # (Inserisci qui il codice della griglia fornitori che abbiamo testato prima)

# --- SCHEDA RICETTARIO ---
with tab_ricettario:
    st.subheader("Modulo Ricettario")
