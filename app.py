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

tab_listino, tab_fornitori, tab_ricettario, tab_impostazioni = st.tabs(["🛒 Listino", "🚚 Fornitori", "📖 Ricettario", "⚙️ Impostazioni"])

# --- SCHEDA LISTINO ACQUISTI (LA GRIGLIA PRINCIPALE) ---
with tab_listino:
    st.subheader("Gestione Magazzino e Prezzi")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Aggiungi nuovi prodotti in fondo alla tabella, modifica i prezzi esistenti o disattiva le vecchie referenze.")
    with col2:
        mostra_inattivi = st.checkbox("👁️ Mostra prodotti disattivati", value=False)

    categorie_predefinite = [
        "Prodotti secchi", "Prodotti freschi", "Latticini", 
        "Confezionati", "Verdure", "Preparazioni"
    ]
    
    # Definiamo i 14 allergeni ufficiali
    ALLERGENI_LIST = [
        "Glutine", "Crostacei", "Uova", "Pesce", "Arachidi", "Soia", 
        "Latte", "Frutta a guscio", "Sedano", "Senape", "Sesamo", 
        "Anidride solforosa", "Lupini", "Molluschi"
    ]
    
    # 1. Recuperiamo i Fornitori attivi
    res_fornitori = supabase.table("fornitori").select("id, nome").eq("is_active", True).execute()
    fornitori_dict = {f["nome"]: f["id"] for f in res_fornitori.data} if res_fornitori.data else {}
    lista_nomi_fornitori = list(fornitori_dict.keys())
    
    # 2. Recuperiamo il Listino e gli Ingredienti (inclusi gli allergeni)
    query = """
        id, prezzo_acquisto, peso_unita_acquisto_g, iva, is_scelto, is_active, nome_specifico_prodotto,
        ingredienti (id, nome_generico, dettaglio_variante, um_ricetta, categoria, allergeni),
        fornitori (id, nome)
    """
    res_listino = supabase.table("listino_acquisti").select(query).execute()
    
    # 3. Costruiamo i dati per la tabella aggiungendo le 14 colonne booleane
    dati_piatti = []
    if res_listino.data:
        for row in res_listino.data:
            ing = row.get("ingredienti", {}) or {}
            forn = row.get("fornitori", {}) or {}
            
            gen = ing.get("nome_generico", "")
            dett = ing.get("dettaglio_variante", "")
            nome_ricetta = f"{gen} {dett}".strip()
            
            # Gestione sicura dell'array JSON degli allergeni dal database
            allergeni_db = ing.get("allergeni", [])
            if not isinstance(allergeni_db, list):
                allergeni_db = []
            
            riga = {
                "listino_id": row.get("id"),
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
                "Scelto": row.get("is_scelto", False),
                "Attivo": row.get("is_active", True)
            }
            # Impostiamo True/False per le 14 colonne
            for al in ALLERGENI_LIST:
                riga[al] = al in allergeni_db
                
            dati_piatti.append(riga)
    
    colonne_base = [
        "listino_id", "ingrediente_id", "Generico", "Dettaglio (Variante)", "Nome in Ricetta", 
        "UM Ricetta", "Categoria", "Fornitore", "Nome Commerciale", "Peso Acquisto (g/ml)", 
        "Prezzo (€)", "IVA (%)", "Scelto", "Attivo"
    ]
    df_listino = pd.DataFrame(dati_piatti) if dati_piatti else pd.DataFrame(columns=colonne_base + ALLERGENI_LIST)
    
    if not df_listino.empty and not mostra_inattivi:
        df_listino = df_listino[df_listino["Attivo"] == True].reset_index(drop=True)
    
    # 4. Configurazione dinamica delle colonne per l'editor
    col_config = {
        "listino_id": None, 
        "ingrediente_id": None, 
        "Nome in Ricetta": st.column_config.TextColumn("🔗 Nome in Ricetta", disabled=True), 
        "UM Ricetta": st.column_config.SelectboxColumn("UM", options=["g", "Kg", "ml", "L", "pz"]),
        "Categoria": st.column_config.SelectboxColumn("Categoria", options=categorie_predefinite, required=True),
        "Fornitore": st.column_config.SelectboxColumn("Fornitore", options=lista_nomi_fornitori),
        "Peso Acquisto (g/ml)": st.column_config.NumberColumn("Peso (g/ml)", min_value=0),
        "Prezzo (€)": st.column_config.NumberColumn("Prezzo (€)", format="%.2f"),
        "Attivo": st.column_config.CheckboxColumn("Attivo"),
    }
    # Aggiungiamo automaticamente le 14 checkbox degli allergeni alla fine
    for al in ALLERGENI_LIST:
        col_config[al] = st.column_config.CheckboxColumn(al, default=False)
        
    edited_listino = st.data_editor(
        df_listino,
        column_config=col_config,
        num_rows="dynamic",
        use_container_width=True,
        key="listino_editor"
    )
    
    # 5. Logica Completa di Salvataggio
    if st.button("💾 Salva Magazzino", type="primary"):
        changes = st.session_state["listino_editor"]
        try:
            if changes.get("added_rows"):
                for riga in changes["added_rows"]:
                    gen = str(riga.get("Generico", "")).strip().title()
                    dett = str(riga.get("Dettaglio (Variante)", "")).strip().lower()
                    nome_forn = riga.get("Fornitore")
                    
                    if not gen or not nome_forn: continue
                    forn_id = fornitori_dict.get(nome_forn)
                    
                    # Raggruppiamo le spunte in una lista per il database
                    allergeni_selezionati = [al for al in ALLERGENI_LIST if riga.get(al) == True]
                    
                    check_ing = supabase.table("ingredienti").select("id").eq("nome_generico", gen).eq("dettaglio_variante", dett).execute()
                    
                    if check_ing.data:
                        ing_id = check_ing.data[0]["id"]
                    else:
                        nuovo_ing = {
                            "nome_generico": gen,
                            "dettaglio_variante": dett,
                            "um_ricetta": riga.get("UM Ricetta", "g"),
                            "categoria": riga.get("Categoria", "Altro"),
                            "allergeni": allergeni_selezionati # Salviamo qui il JSON
                        }
                        res_ing = supabase.table("ingredienti").insert(nuovo_ing).execute()
                        ing_id = res_ing.data[0]["id"]
                    
                    nuovo_prezzo = {
                        "ingrediente_id": ing_id,
                        "fornitore_id": forn_id,
                        "nome_specifico_prodotto": riga.get("Nome Commerciale", f"{gen} {dett} {nome_forn}"),
                        "peso_unita_acquisto_g": riga.get("Peso Acquisto (g/ml)", 1000),
                        "prezzo_acquisto": riga.get("Prezzo (€)", 0.0),
                        "iva": riga.get("IVA (%)", 0),
                        "is_scelto": riga.get("Scelto", False),
                        "is_active": riga.get("Attivo", True)
                    }
                    supabase.table("listino_acquisti").insert(nuovo_prezzo).execute()

            if changes.get("edited_rows"):
                for index, updates in changes["edited_rows"].items():
                    row_id = df_listino.iloc[index]["listino_id"]
                    ing_id = df_listino.iloc[index]["ingrediente_id"]
                    
                    update_listino = {}
                    update_ingrediente = {}
                    
                    if "Fornitore" in updates: update_listino["fornitore_id"] = fornitori_dict.get(updates["Fornitore"])
                    if "Nome Commerciale" in updates: update_listino["nome_specifico_prodotto"] = updates["Nome Commerciale"]
                    if "Peso Acquisto (g/ml)" in updates: update_listino["peso_unita_acquisto_g"] = updates["Peso Acquisto (g/ml)"]
                    if "Prezzo (€)" in updates: update_listino["prezzo_acquisto"] = updates["Prezzo (€)"]
                    if "IVA (%)" in updates: update_listino["iva"] = updates["IVA (%)"]
                    if "Scelto" in updates: update_listino["is_scelto"] = updates["Scelto"]
                    if "Attivo" in updates: update_listino["is_active"] = updates["Attivo"]
                    
                    if "UM Ricetta" in updates: update_ingrediente["um_ricetta"] = updates["UM Ricetta"]
                    if "Categoria" in updates: update_ingrediente["categoria"] = updates["Categoria"]
                    
                    # Intercettiamo le modifiche agli allergeni
                    allergeni_modificati = any(al in updates for al in ALLERGENI_LIST)
                    if allergeni_modificati:
                        nuovi_allergeni = []
                        for al in ALLERGENI_LIST:
                            val_allergene = updates.get(al, df_listino.iloc[index][al])
                            if val_allergene:
                                nuovi_allergeni.append(al)
                        update_ingrediente["allergeni"] = nuovi_allergeni
                    
                    if update_listino:
                        supabase.table("listino_acquisti").update(update_listino).eq("id", row_id).execute()
                    if update_ingrediente:
                        supabase.table("ingredienti").update(update_ingrediente).eq("id", ing_id).execute()

            if changes.get("deleted_rows"):
                for index in changes["deleted_rows"]:
                    row_id = df_listino.iloc[index]["listino_id"]
                    supabase.table("listino_acquisti").update({"is_active": False}).eq("id", row_id).execute()

            st.success("Magazzino aggiornato con successo!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Si è verificato un errore durante il salvataggio: {e}")

# --- SCHEDA FORNITORI (Il codice che avevamo scritto nello step precedente) ---
with tab_fornitori:
    st.subheader("Gestione Fornitori")
    # (Inserisci qui il codice della griglia fornitori che abbiamo testato prima)

# --- SCHEDA RICETTARIO ---
# --- SCHEDA RICETTARIO (FOOD COST & SCALABILITÀ) ---
with tab_ricettario:
    st.subheader("📖 Ricettario e Food Cost")
    
    # 1. CARICAMENTO DI TUTTI I DATI NECESSARI
    # Ricette
    ricette_res = supabase.table("ricette").select("*").eq("is_active", True).order("nome_ricetta").execute()
    lista_ricette = {r["nome_ricetta"]: r["id"] for r in ricette_res.data} if ricette_res.data else {}
    
    # Ingredienti (con i loro allergeni e UM)
    ing_res = supabase.table("ingredienti").select("id, nome_generico, dettaglio_variante, um_ricetta, allergeni").eq("is_wine", False).execute()
    ing_dict = {i["id"]: i for i in ing_res.data} if ing_res.data else {}
    
    # Dizionari per l'editor
    nomi_ing_completi = [f"{i['nome_generico']} {i['dettaglio_variante']}".strip() for i in ing_res.data] if ing_res.data else []
    nome_to_id_ing = {f"{i['nome_generico']} {i['dettaglio_variante']}".strip(): i["id"] for i in ing_res.data} if ing_res.data else {}
    
    # Prezzi 'Scelti' (Solo i fornitori attivati per il calcolo costi)
    prezzi_res = supabase.table("listino_acquisti").select("ingrediente_id, prezzo_acquisto, peso_unita_acquisto_g").eq("is_scelto", True).execute()
    prezzi_dict = {p["ingrediente_id"]: p for p in prezzi_res.data} if prezzi_res.data else {}
    
    # Moltiplicatori di conversione (es. da ml a g)
    conv_res = supabase.table("conversioni_misura").select("*").execute()
    conv_dict = {(c["ingrediente_generico"], c["da_um"]): c["moltiplicatore"] for c in conv_res.data} if conv_res.data else {}

    # 2. MENU DI NAVIGAZIONE RICETTE
    opzioni_ricetta = ["-- ✨ Crea Nuova Ricetta --"] + list(lista_ricette.keys())
    ricetta_selezionata = st.selectbox("Seleziona un piatto o creane uno nuovo:", options=opzioni_ricetta)
    st.divider()
        
    if ricetta_selezionata == "-- ✨ Crea Nuova Ricetta --":
        st.markdown("### Nuova Ricetta")
        with st.form("form_nuova_ricetta"):
            # Piccola personalizzazione per rendere l'inserimento più familiare
            nome_r = st.text_input("Nome del Piatto (es. Frico croccante, Cjarsons della Carnia)")
            tipo_r = st.selectbox("Portata", ["Antipasto", "Primo", "Secondo", "Contorno", "Dessert", "Base (es. Impasto)"])
            istruzioni = st.text_area("Procedimento in cucina (opzionale)")
            
            if st.form_submit_button("Salva Intestazione", type="primary"):
                if nome_r:
                    supabase.table("ricette").insert({"nome_ricetta": nome_r, "tipo_piatto": tipo_r, "istruzioni": istruzioni}).execute()
                    st.success("Ricetta creata! Ora puoi selezionarla dal menu in alto per aggiungere gli ingredienti.")
                    st.rerun()
                else:
                    st.error("Inserisci un nome per la ricetta.")
    else:
        # 3. VISUALIZZAZIONE E CALCOLO DELLA RICETTA SELEZIONATA
        ric_id = lista_ricette[ricetta_selezionata]
        dettagli_ricetta = next(r for r in ricette_res.data if r["id"] == ric_id)
        
        st.markdown(f"## 🍽️ {dettagli_ricetta['nome_ricetta']}")
        st.caption(f"Categoria: {dettagli_ricetta['tipo_piatto']}")
        
        # IL MOTORE DI SCALABILITÀ
        porzioni = st.number_input("🔢 Inserisci il numero di porzioni (o moltiplicatore) da preparare:", min_value=0.1, value=1.0, step=1.0)
        
        # Carichiamo gli ingredienti associati a questa specifica ricetta
        ing_ric_res = supabase.table("ingredienti_ricetta").select("*").eq("ricetta_id", ric_id).execute()
        
        dati_tabella = []
        costo_totale_ricetta = 0.0
        allergeni_totali = set()
        
        if ing_ric_res.data:
            for riga in ing_ric_res.data:
                i_id = riga["ingrediente_id"]
                qta_base = float(riga["quantita"]) # La quantità per 1 singola porzione inserita a sistema
                
                ing_info = ing_dict.get(i_id, {})
                nome_generico = ing_info.get('nome_generico', '')
                nome_completo = f"{nome_generico} {ing_info.get('dettaglio_variante', '')}".strip()
                um_ufficiale = ing_info.get("um_ricetta", "g")
                
                # Unione automatica degli allergeni
                for al in ing_info.get("allergeni", []):
                    allergeni_totali.add(al)
                    
                # 1. Moltiplichiamo per le porzioni desiderate
                qta_scalata = qta_base * porzioni
                
                # 2. Convertiamo in Grammi per il listino prezzi
                qta_in_grammi = qta_scalata
                if um_ufficiale == "Kg":
                    qta_in_grammi = qta_scalata * 1000
                elif um_ufficiale in ["ml", "L", "pz"]:
                    moltiplicatore = float(conv_dict.get((nome_generico, um_ufficiale), 1.0))
                    # Se l'UM in magazzino è Litri, forziamo prima il passaggio in ml
                    if um_ufficiale == "L":
                         qta_in_grammi = (qta_scalata * 1000) * moltiplicatore
                    else:
                         qta_in_grammi = qta_scalata * moltiplicatore
                    
                # 3. Calcoliamo il Food Cost (leggendo il prezzo "Scelto")
                prezzo_info = prezzi_dict.get(i_id)
                costo_ing = 0.0
                if prezzo_info and prezzo_info["peso_unita_acquisto_g"] > 0:
                    costo_al_grammo = float(prezzo_info["prezzo_acquisto"]) / float(prezzo_info["peso_unita_acquisto_g"])
                    costo_ing = costo_al_grammo * qta_in_grammi
                    
                costo_totale_ricetta += costo_ing
                
                dati_tabella.append({
                    "id_riga": riga["id"],
                    "Ingrediente": nome_completo,
                    "Q.tà (Base 1 porz.)": qta_base,
                    "UM": um_ufficiale,
                    "Q.tà da Preparare": qta_scalata,
                    "Costo (€)": costo_ing
                })
                
        # 4. METRICHE FINANZIARIE IN EVIDENZA
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Food Cost Totale (per queste porzioni)", f"€ {costo_totale_ricetta:.2f}")
        col_m2.metric("Food Cost per Singola Porzione", f"€ {(costo_totale_ricetta/porzioni if porzioni>0 else 0):.2f}")
        
        # ALLERGENI IN EVIDENZA
        if allergeni_totali:
            st.error(f"⚠️ **Allergeni generati automaticamente:** {', '.join(sorted(list(allergeni_totali)))}")
        else:
            st.success("✅ Nessun allergene rilevato (in base alle spunte in magazzino).")
            
        st.markdown("#### Composizione Ingredienti")
        df_ing_ric = pd.DataFrame(dati_tabella) if dati_tabella else pd.DataFrame(columns=["id_riga", "Ingrediente", "Q.tà (Base 1 porz.)", "UM", "Q.tà da Preparare", "Costo (€)"])
        
        # 5. EDITOR INGREDIENTI
        edited_ricetta = st.data_editor(
            df_ing_ric,
            column_config={
                "id_riga": None,
                "Ingrediente": st.column_config.SelectboxColumn("Ingrediente", options=nomi_ing_completi, required=True),
                "Q.tà (Base 1 porz.)": st.column_config.NumberColumn("Quantità a crudo", min_value=0.01, format="%.2f", required=True),
                "UM": st.column_config.TextColumn("UM", disabled=True),
                "Q.tà da Preparare": st.column_config.NumberColumn("Totale Scalato", disabled=True, format="%.2f"),
                "Costo (€)": st.column_config.NumberColumn("Costo Calcolato", disabled=True, format="%.3f"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_ric_{ric_id}"
        )
        
        if st.button("💾 Salva Ingredienti", type="primary"):
            changes = st.session_state[f"editor_ric_{ric_id}"]
            try:
                # Nuovi inserimenti
                if changes.get("added_rows"):
                    nuove_righe = []
                    for riga in changes["added_rows"]:
                        if riga.get("Ingrediente") and riga.get("Q.tà (Base 1 porz.)"):
                            nuove_righe.append({
                                "ricetta_id": ric_id,
                                "ingrediente_id": nome_to_id_ing.get(riga["Ingrediente"]),
                                "quantita": riga["Q.tà (Base 1 porz.)"]
                            })
                    if nuove_righe:
                        supabase.table("ingredienti_ricetta").insert(nuove_righe).execute()
                        
                # Modifiche
                if changes.get("edited_rows"):
                    for index, updates in changes["edited_rows"].items():
                        row_id = df_ing_ric.iloc[index]["id_riga"]
                        upd = {}
                        if "Ingrediente" in updates:
                            upd["ingrediente_id"] = nome_to_id_ing.get(updates["Ingrediente"])
                        if "Q.tà (Base 1 porz.)" in updates:
                            upd["quantita"] = updates["Q.tà (Base 1 porz.)"]
                        if upd:
                            supabase.table("ingredienti_ricetta").update(upd).eq("id", row_id).execute()
                            
                # Eliminazioni
                if changes.get("deleted_rows"):
                    for index in changes["deleted_rows"]:
                        row_id = df_ing_ric.iloc[index]["id_riga"]
                        supabase.table("ingredienti_ricetta").delete().eq("id", row_id).execute()
                        
                st.success("Ingredienti aggiornati con successo!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore di salvataggio: {e}")
                
        # Mostriamo le istruzioni testuali alla fine
        if dettagli_ricetta.get("istruzioni"):
            st.divider()
            st.markdown("#### 👨‍🍳 Procedimento")
            st.write(dettagli_ricetta["istruzioni"])
            
        st.divider()
        if st.button("🗑️ Archivia Ricetta (Soft Delete)", type="secondary"):
            supabase.table("ricette").update({"is_active": False}).eq("id", ric_id).execute()
            st.rerun()

# --- SCHEDA IMPOSTAZIONI (CONVERSIONI) ---
with tab_impostazioni:
    st.subheader("Conversione Unità di Misura")
    st.markdown("Imposta i moltiplicatori per convertire liquidi (ml/L) o pezzi (pz) in grammi per il calcolo preciso del food cost.")
    st.info("💡 **Esempi pratici:**\n- L'Olio EVO ha un peso specifico di circa 0.916. Quindi: da `ml` a `g` -> **0.916**\n- Il Latte ha un peso specifico di 1.03. Quindi: da `ml` a `g` -> **1.03**\n- Un Uovo intero pesa circa 50 grammi. Quindi: da `pz` a `g` -> **50.0**")
    
    # 1. Recupero dati (Conversioni e Lista Ingredienti)
    res_conv = supabase.table("conversioni_misura").select("*").execute()
    
    # NOVITÀ: Peschiamo gli ingredienti generici esistenti (escludiamo i vini per pulizia)
    res_ing = supabase.table("ingredienti").select("nome_generico").eq("is_wine", False).execute()
    
    # Creiamo una lista unica di nomi generici (usiamo un set per eliminare i duplicati)
    lista_ingredienti_generici = []
    if res_ing.data:
        lista_ingredienti_generici = sorted(list(set([ing["nome_generico"] for ing in res_ing.data])))
    
    if res_conv.data:
        df_conv = pd.DataFrame(res_conv.data)
    else:
        df_conv = pd.DataFrame(columns=["id", "ingrediente_generico", "da_um", "a_um", "moltiplicatore"])
        
    # 2. Griglia interattiva AGGIORNATA
    edited_conv = st.data_editor(
        df_conv,
        column_config={
            "id": None, 
            "created_at": None,
            # NOVITÀ: Ora è una Selectbox popolata con i dati del database
            "ingrediente_generico": st.column_config.SelectboxColumn(
                "Ingrediente (Generico)", 
                options=lista_ingredienti_generici, 
                required=True, 
                help="Seleziona l'ingrediente dal magazzino"
            ),
            "da_um": st.column_config.SelectboxColumn("Da (UM Ricetta)", options=["ml", "L", "pz"], required=True),
            "a_um": st.column_config.TextColumn("A (UM Magazzino)", disabled=True, default="g"),
            "moltiplicatore": st.column_config.NumberColumn("Moltiplicatore", min_value=0.0001, format="%.4f", required=True)
        },
        num_rows="dynamic",
        use_container_width=True,
        key="conv_editor"
    )
    
    # 3. Logica di salvataggio
    if st.button("💾 Salva Conversioni", type="primary"):
        changes = st.session_state["conv_editor"]
        
        try:
            # --- A. Nuove righe ---
            if changes.get("added_rows"):
                nuove_conv = []
                for riga in changes["added_rows"]:
                    ing = str(riga.get("ingrediente_generico", "")).strip().title()
                    da = riga.get("da_um")
                    molt = riga.get("moltiplicatore")
                    
                    if ing and da and molt:
                        nuove_conv.append({
                            "ingrediente_generico": ing,
                            "da_um": da,
                            "a_um": "g",
                            "moltiplicatore": molt
                        })
                if nuove_conv:
                    supabase.table("conversioni_misura").insert(nuove_conv).execute()
            
            # --- B. Modifiche ---
            if changes.get("edited_rows"):
                for index, updates in changes["edited_rows"].items():
                    row_id = df_conv.iloc[index]["id"]
                    update_data = {}
                    
                    if "ingrediente_generico" in updates: 
                        update_data["ingrediente_generico"] = str(updates["ingrediente_generico"]).strip().title()
                    if "da_um" in updates: 
                        update_data["da_um"] = updates["da_um"]
                    if "moltiplicatore" in updates: 
                        update_data["moltiplicatore"] = updates["moltiplicatore"]
                        
                    if update_data:
                        supabase.table("conversioni_misura").update(update_data).eq("id", row_id).execute()
                        
            # --- C. Eliminazioni definitive ---
            if changes.get("deleted_rows"):
                for index in changes["deleted_rows"]:
                    row_id = df_conv.iloc[index]["id"]
                    supabase.table("conversioni_misura").delete().eq("id", row_id).execute()

            st.success("Impostazioni di conversione aggiornate!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Errore durante il salvataggio delle conversioni: {e}")
