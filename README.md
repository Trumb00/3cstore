# 3cstore
Gestionale Magazzino e Ricette

della lista allergeni.
*   **Scalabilità Dinamica:** Ricalcolo istantaneo delle quantità e del food cost (esclusivamente su peso a crudo) inserendo le porzioni o i Kg desiderati.
*   **Esportazione e Stampa:** 
    *   Generazione e download automatico di un documento **PDF** formattato con i dettagli e le quantità della ricetta, pronto per la stampa in cucina.
    *   Esportazione dei calcoli dei costi in formato **Excel/CSV**.
*   **Soft Delete Ricette:** Possibilità di archiviare e nascondere piatti fuori carta o di passate stagioni.

## 5. Ruoli, Accessi e Sicurezza (RBAC)
Il sistema utilizza un'autenticazione gestita tramite inviti via email (Magic Link/Password Setup) configurata tramite Supabase Auth. Sono presenti le funzioni di reset password.

*   **Admin:** 
    *   Accesso totale.
    *   Può invitare e disattivare account di Responsabili e Visitatori.
*   **Responsabile:**
    *   Gestione completa del magazzino (aggiunta, modifica, prezzi, disattivazione).
    *   Aggiornamento giacenze vini e tabella conversioni.
    *   Creazione, modifica e disattivazione ricette.
    *   **Può inviare inviti email** per l'onboarding di nuovi Responsabili e Visitatori e disattivare i profili del proprio team.
*   **Visitatore:**
    *   Sola lettura delle ricette attive.
    *   Utilizzo del calcolatore di porzioni/Kg.
    *   I costi di acquisto e i dati finanziari sono oscurati e non accessibili.
