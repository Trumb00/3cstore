# --- SCHEDA LISTINO ACQUISTI (LA GRIGLIA PRINCIPALE) ---
with tab_listino:
    st.subheader("Gestione Magazzino e Prezzi")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Aggiungi nuovi prodotti in fondo alla tabella, modifica i prezzi esistenti o disattiva le vecchie referenze.")
    with col2:
        # Interruttore per visualizzare la roba archiviata
        mostra_inattivi = st.checkbox("👁️ Mostra prodotti disattivati", value=False)
    
    # 1. Recuperiamo i Fornitori attivi per il menu a tendina
    res_fornitori = supabase.table("fornitori").select("id, nome").eq("is_active", True).execute()
    fornitori_dict = {f["nome"]: f["id"] for f in res_fornitori.data} if res_fornitori.data else {}
    lista_nomi_fornitori = list(fornitori_dict.keys())
    
    # 2. Recuperiamo TUTTO il Listino unito agli Ingredienti
    query = """
        id, 
        prezzo_acquisto, 
        peso_unita_acquisto_g, 
        iva, 
        is_scelto,
        is_active,
        nome_specifico_prodotto,
        ingredienti (id, nome_generico, dettaglio_variante, um_ricetta, categoria),
        fornitori (id, nome)
    """
    res_listino = supabase.table("listino_acquisti").select(query).execute()
    
    # 3. Costruiamo i dati per la tabella
    dati_piatti = []
    if res_listino.data:
        for row in res_listino.data:
            ing = row.get("ingredienti", {})
            forn = row.get("fornitori", {})
            
            if not ing: ing = {"nome_generico": "N/A", "dettaglio_variante": "", "um_ricetta": "g", "categoria": "N/A"}
            if not forn: forn = {"nome": "N/A"}
                
            gen = ing.get("nome_generico", "")
            dett = ing.get("dettaglio_variante", "")
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
                "Scelto": row.get("is_scelto", False),
                "Attivo": row.get("is_active", True) # Il nostro campo per disattivare
            })
    
    df_listino = pd.DataFrame(dati_piatti) if dati_piatti else pd.DataFrame(columns=[
        "listino_id", "ingrediente_id", "Generico", "Dettaglio (Variante)", "Nome in Ricetta", 
        "UM Ricetta", "Categoria", "Fornitore", "Nome Commerciale", "Peso Acquisto (g/ml)", 
        "Prezzo (€)", "IVA (%)", "Scelto", "Attivo"
    ])
    
    # Filtriamo i dati in base all'interruttore
    if not df_listino.empty and not mostra_inattivi:
        # Teniamo solo quelli attivi e resettiamo l'indice (fondamentale per evitare errori nell'editor)
        df_listino = df_listino[df_listino["Attivo"] == True].reset_index(drop=True)
    
    # 4. Renderizziamo la Griglia Dati
    edited_listino = st.data_editor(
        df_listino,
        column_config={
            "listino_id": None, 
            "ingrediente_id": None, 
            "Nome in Ricetta": st.column_config.TextColumn("🔗 Nome in Ricetta", disabled=True), 
            "UM Ricetta": st.column_config.SelectboxColumn("UM", options=["g", "Kg", "ml", "L", "pz"]),
            "Fornitore": st.column_config.SelectboxColumn("Fornitore", options=lista_nomi_fornitori),
            "Peso Acquisto (g/ml)": st.column_config.NumberColumn("Peso (g/ml)", min_value=0),
            "Prezzo (€)": st.column_config.NumberColumn("Prezzo (€)", format="%.2f"),
            "Attivo": st.column_config.CheckboxColumn("Attivo"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="listino_editor"
    )
    
    # 5. Logica Completa di Salvataggio (Creazione, Modifica, Eliminazione)
    if st.button("💾 Salva Magazzino", type="primary"):
        changes = st.session_state["listino_editor"]
        
        try:
            # --- A. INSERIMENTO NUOVE RIGHE ---
            if changes.get("added_rows"):
                for riga in changes["added_rows"]:
                    gen = str(riga.get("Generico", "")).strip().title()
                    dett = str(riga.get("Dettaglio (Variante)", "")).strip().lower()
                    nome_forn = riga.get("Fornitore")
                    
                    if not gen or not nome_forn:
                        continue # Salta righe incomplete
                    
                    forn_id = fornitori_dict.get(nome_forn)
                    
                    check_ing = supabase.table("ingredienti").select("id").eq("nome_generico", gen).eq("dettaglio_variante", dett).execute()
                    
                    if check_ing.data:
                        ing_id = check_ing.data[0]["id"]
                    else:
                        nuovo_ing = {
                            "nome_generico": gen,
                            "dettaglio_variante": dett,
                            "um_ricetta": riga.get("UM Ricetta", "g"),
                            "categoria": riga.get("Categoria", "Altro")
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

            # --- B. MODIFICA RIGHE ESISTENTI (INCLUSA LA DISATTIVAZIONE CON SPUNTA) ---
            if changes.get("edited_rows"):
                for index, updates in changes["edited_rows"].items():
                    # Recuperiamo gli ID corretti grazie all'indice del dataframe
                    row_id = df_listino.iloc[index]["listino_id"]
                    ing_id = df_listino.iloc[index]["ingrediente_id"]
                    
                    update_listino = {}
                    update_ingrediente = {}
                    
                    # Suddividiamo gli aggiornamenti a seconda di quale tabella impattano
                    if "Fornitore" in updates: update_listino["fornitore_id"] = fornitori_dict.get(updates["Fornitore"])
                    if "Nome Commerciale" in updates: update_listino["nome_specifico_prodotto"] = updates["Nome Commerciale"]
                    if "Peso Acquisto (g/ml)" in updates: update_listino["peso_unita_acquisto_g"] = updates["Peso Acquisto (g/ml)"]
                    if "Prezzo (€)" in updates: update_listino["prezzo_acquisto"] = updates["Prezzo (€)"]
                    if "IVA (%)" in updates: update_listino["iva"] = updates["IVA (%)"]
                    if "Scelto" in updates: update_listino["is_scelto"] = updates["Scelto"]
                    if "Attivo" in updates: update_listino["is_active"] = updates["Attivo"]
                    
                    if "UM Ricetta" in updates: update_ingrediente["um_ricetta"] = updates["UM Ricetta"]
                    if "Categoria" in updates: update_ingrediente["categoria"] = updates["Categoria"]
                    
                    # Eseguiamo le query di aggiornamento separate
                    if update_listino:
                        supabase.table("listino_acquisti").update(update_listino).eq("id", row_id).execute()
                    if update_ingrediente:
                        supabase.table("ingredienti").update(update_ingrediente).eq("id", ing_id).execute()

            # --- C. ELIMINAZIONE DAL CESTINO (TRADOTTA IN SOFT DELETE) ---
            if changes.get("deleted_rows"):
                for index in changes["deleted_rows"]:
                    row_id = df_listino.iloc[index]["listino_id"]
                    # Intercettiamo l'eliminazione visiva e la traduciamo in un is_active = False sul database
                    supabase.table("listino_acquisti").update({"is_active": False}).eq("id", row_id).execute()

            st.success("Magazzino aggiornato con successo!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Si è verificato un errore durante il salvataggio: {e}")
