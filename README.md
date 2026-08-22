# 3cstore
Gestionale Magazzino e Ricette

Documento dei Requisiti (PRD) - Web App Gestionale Ristorante
1. Panoramica del Progetto
Sviluppo di una web app gestionale su misura per il ristorante, progettata per sostituire i fogli di calcolo Excel con un sistema centralizzato. L'applicazione permetterà di gestire il magazzino (con storico prezzi e molteplici varianti fornitore), calcolare automaticamente il costo (food cost) delle ricette in base al peso a crudo e scalare dinamicamente le porzioni.

2. Stack Tecnologico Scelto
Frontend & UI: Streamlit (Python). Scelto per garantire un'interfaccia minimalista, data-centrica e basata su griglie interattive (stile Excel).

Backend, Database & Autenticazione: Supabase (PostgreSQL). Fornisce un database relazionale robusto e gestisce nativamente i permessi degli utenti (Row Level Security).

Version Control & Code Hosting: GitHub.

3. Architettura dei Dati (Requisiti Logici)
Per superare i limiti di Excel e gestire listini complessi, il database utilizzerà una logica relazionale separando i concetti chiave:

Ingredienti (Generici): Il concetto astratto usato in cucina (es. "Riso Carnaroli", "Farina 00").

Fornitori: Anagrafica dei fornitori (abituali e occasionali).

Listino Acquisti (Specifico): Collega un ingrediente generico a un fornitore specifico, definendo la variante esatta, il formato di acquisto (peso) e il prezzo. Permette a un singolo fornitore di avere più versioni/qualità dello stesso ingrediente base.

Ricette: Dettagli del piatto, collegati dinamicamente agli ingredienti generici.

4. Funzionalità Principali (Core Features)
4.1 Modulo Magazzino e Acquisti
Inserimento e Modifica (Stile Excel): Interfaccia a tabella editabile per inserire e modificare rapidamente fornitori, ingredienti e prezzi.

Gestione Varianti Fornitore: Capacità di associare più versioni di un prodotto a un singolo fornitore (es. "Riso Arborio MARR" e "Riso Carnaroli MARR"), selezionando quale variante utilizzare attivamente per i calcoli del food cost.

Calcolo Prezzo Automatico: L'app calcola automaticamente il fornitore più conveniente e il prezzo netto al grammo in base ai formati di acquisto inseriti.

Tabella Conversioni Volumetriche: Sezione impostazioni (accessibile al responsabile) per definire i pesi specifici dei liquidi (es. Olio, Latte). Il sistema convertirà automaticamente i "ml" inseriti nelle ricette nei corrispondenti "grammi" per il calcolo dei costi.

Modulo Vini e Giacenze:

Identificazione dei vini tramite flag specifico (is_wine = true).

Aggiornamento manuale delle giacenze tramite app.

Sistema di allerta visiva quando la giacenza scende sotto una soglia minima preimpostata.

Soft Delete: Divieto assoluto di cancellazione definitiva dal database. I prodotti non più utilizzati verranno etichettati come inattivi per nasconderli dalla vista, mantenendo intatti gli storici delle vecchie ricette.

4.2 Modulo Ricettario
Creazione Ricetta: Associazione di un nome, istruzioni e una lista di ingredienti (pescati dal magazzino) con relative quantità.

Automazione Allergeni: Il sistema analizza gli ingredienti che compongono la ricetta e genera automaticamente la lista degli allergeni del piatto finito.

Scalabilità Dinamica (Calcolatore): Inserendo il numero di porzioni desiderate o il peso in Kg da raggiungere, l'app ricalcola istantaneamente:

Le quantità necessarie di ogni singolo ingrediente.

Il food cost totale aggiornato (esclusivamente basato sul peso a crudo).

Soft Delete Ricette: Le ricette fuori carta, passate o prettamente stagionali (es. piatti autunnali/invernali rimossi in estate) possono essere nascoste rendendole "inattive", senza perdere il lavoro di composizione fatto.

5. Ruoli e Accessi (RBAC)
Il sistema prevede tre livelli di autorizzazione rigorosi:

Admin (Amministratore di Sistema):

Accesso totale a ogni modulo e funzione.

Gestione della piattaforma e configurazione degli account utente.

Responsabile (Cucina/Acquisti):

Aggiunta, modifica e "soft-delete" di prodotti, varianti e fornitori.

Modifica dei prezzi di listino.

Aggiornamento manuale delle giacenze dei vini.

Creazione, modifica e disattivazione delle ricette.

Compilazione della tabella di conversione liquidi/grammi.

Visitatore (Personale di Cucina):

Lettura (sola visualizzazione) del ricettario attivo.

Utilizzo dello strumento di scalabilità (calcolo porzioni/Kg) per la preparazione delle linee.

Restrizione: I costi finanziari (food cost, prezzi di acquisto) saranno oscurati a questo ruolo.

6. Requisiti di Interfaccia (UI/UX)
Minimalismo: Assenza di grafiche superflue; focus sui dati.

Data Grid Interattive: Utilizzo estensivo di st.data_editor per simulare l'inserimento, la modifica e la navigazione in stile foglio di calcolo.
