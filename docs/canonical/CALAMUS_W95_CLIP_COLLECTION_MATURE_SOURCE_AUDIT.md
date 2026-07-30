# CALAMUS W95 — CLIP COLLECTION
## Proposte di miglioramento semplice dopo audit diretto di pet, boom e Snippet Pixie

**Data:** 2026-07-29
**Baseline vincolante:** `541804f8ff361b3afacb58f18e1e429c70b3a2f9`
**Stato:** proposta pre-implementazione; nessuna patch autorizzata
**Perimetro:** W95 — Clip Collection Completion
**Esclusioni confermate:** secondo Scratchpad, clipboard manager, cattura automatica, cloud, database, tags per le shortcut

---

# 1. Conclusione sintetica

Il miglioramento più coerente e tecnicamente semplice consiste nel distinguere nettamente:

1. **shortcut di comando di Calamus**: una sola combinazione globale, proposta `Ctrl+Alt+K`, che apre **Insert Clip…**;
2. **shortcut mnemonica della clip**: un codice testuale opzionale e univoco, per esempio `firma`, `intro-articolo`, `citazione-lunga`;
3. **lista delle shortcut**: lo stesso selettore rapido, a query vuota, mostra tutte le shortcut con titolo e anteprima; digitando una shortcut la clip viene portata immediatamente in cima;
4. **inserimento**: Enter inserisce il corpo nel vero editor attraverso il command gateway, in un solo passo Undo.

La shortcut mnemonica **non è un tag**:

- una clip ne possiede al massimo una;
- deve essere univoca;
- non esprime una categoria;
- non crea relazioni;
- non produce tassonomie o filtri multipli;
- serve soltanto come indirizzo breve e stabile della clip.

Il modello più convincente deriva dall’unione di:

- `pet`: selezione rapida, query iniziale e campi compilabili;
- `boom`: nome breve come chiave diretta verso un valore;
- Snippet Pixie: abbreviazione visibile, ricerca rapida e inserimento da tastiera;
- Heynote e Gnote: focus corretto, navigazione da tastiera e selezione stabile;
- Zim: titolo derivato dal testo e marcatore di posizione del cursore.

---

# 2. Audit diretto dei nuovi sorgenti maturi

## 2.1 pet

Archivio letto: `pet-main.zip`.

### Modello

File: `snippet/snippet.go`

- `type SnippetInfo`
  - `Description`
  - `Command`
  - `Tag`
  - `Output`
- `func (*Snippets) Load`
- `func (*Snippets) Save`
- `func (*Snippets) Order`
- `func (*Snippets) FilterByTags`

Valutazione:

- **ADAPT** `Description` + `Command` come precedente di titolo + corpo.
- **REJECT** `Tag`: la shortcut Calamus non deve diventare classificazione.
- **REJECT** `Output`: non ha un equivalente utile nella Clip Collection.
- **ADAPT** `Order`: ordinamento della vista, non riordinamento implicito dell’autorità.
- **REJECT** salvataggio TOML e multi-file: Calamus conserva un’unica autorità Markdown.

### Ricerca e selezione

File: `cmd/util.go`

- `filter(options, tag, raw)`
- costruzione della riga visuale da description, command e tags;
- query iniziale passata al selector;
- associazione fra riga scelta e `SnippetInfo`;
- restituzione del corpo selezionato.

File: `cmd/search.go`

- `search`
- opzione `--query`;
- output del comando selezionato.

Precedente operativo importante: la ricerca non è un archivio separato; è un percorso breve fra una query e il contenuto da immettere nella riga corrente.

Decisione Calamus:

- **ADAPT** in un selettore GTK interno;
- nessun `fzf`, `peco`, shell o processo esterno;
- mapping mediante stable ID, mai mediante testo visualizzato;
- query su shortcut, titolo e corpo;
- Enter inserisce nel `Gtk.TextBuffer` attraverso il command gateway.

### Lista leggibile

File: `cmd/list.go`

- `list`
- modalità one-line;
- descrizione troncata;
- corpo multilinea trasformato in anteprima;
- visualizzazione dettagliata separata.

Decisione Calamus:

- **ADOPT** riga compatta con shortcut, titolo e prima riga del corpo;
- **ADAPT** anteprima con ellissi GTK;
- nessuna esposizione di tags.

### Nuova clip e duplicati

File: `cmd/new.go`

- `scan`
- `scanMultiLine`
- `_new`
- controllo di `Description` duplicata;
- inserimento multilinea;
- annullamento esplicito.

Decisione Calamus:

- **ADAPT** controllo duplicati:
  - collisione della shortcut: errore bloccante;
  - corpo identico: avviso, non sostituzione silenziosa;
- **ADAPT** annullamento senza persistenza;
- input multilinea già coperto dal dialogo GTK;
- **REJECT** creazione provvisoria di record vuoto prima dell’editor.

### Apertura dell’autorità

File: `cmd/edit.go`

- `edit`
- `fileContent`
- confronto before/after;
- apertura del file configurato.

Decisione Calamus:

- **ADOPT/già previsto** `Open Clip File`;
- apertura shell-free mediante GIO;
- Refresh reale al ritorno;
- nessun sync remoto.

### Copia

File: `cmd/clip.go`

- `clip`
- selezione;
- unione dei risultati;
- copia negli appunti.

Decisione Calamus:

- **ADOPT/già previsto** `Copy Body`;
- **REJECT** multi-selezione e concatenazione;
- nessuna cronologia clipboard.

### Parametri

File: `dialog/params.go`

- `SearchForParams`
- `insertParams`
- ordine di prima apparizione;
- campi ripetuti compilati una sola volta;
- valori predefiniti.

File: `dialog/view.go`

- `GenerateParamsLayout`
- viste editabili;
- Tab per passare al campo seguente;
- Enter per confermare;
- Ctrl+C per annullare.

Questo è il contributo più interessante di `pet` oltre alla ricerca.

Decisione proposta:

- **ADAPT opzionale**, con sintassi Calamus limitata:
  - `{{nome}}`
  - `{{nome=valore predefinito}}`
- nessuna esecuzione;
- nessuna shell;
- nessuna scelta multipla;
- nessun annidamento;
- campi ripetuti chiesti una sola volta;
- annullamento senza modifica del documento.

Difficoltà: **medio-bassa**, ma superiore alle altre proposte.

---

## 2.2 boom

Archivio letto: `boom-master.zip`.

### Chiave breve e valore

File: `lib/boom/item.rb`

- `Boom::Item`
- `name`
- `value`
- `short_name`
- `to_hash`

File: `lib/boom/list.rb`

- `find_item`
- confronto esatto sul nome;
- supporto al nome troncato;
- `add_item` sostituisce l’elemento omonimo.

Decisione Calamus:

- **ADOPT** il principio “nome breve → valore”.
- **ADAPT** come shortcut mnemonica → corpo della clip.
- **REJECT** sostituzione silenziosa su collisione.
- **REJECT** ricerca tramite nome troncato: la shortcut deve essere esatta e non ambigua.

### Lista e accesso diretto

File: `lib/boom/command.rb`

- `all`
- `echo`
- `copy`
- `search_items`
- `search_list_for_item`
- `delete_item`

Decisione Calamus:

- **ADOPT** vista completa shortcut + titolo + anteprima.
- **ADAPT** `echo` come Insert nel vero editor.
- **ADAPT** `copy` come Copy Body.
- **ADOPT** lookup esatto della shortcut.
- **ADOPT** conferma Delete.
- **REJECT** liste/categorie: diventerebbero una classificazione parallela.
- **REJECT** apertura automatica di URL contenuti nella clip.

### Completamento

File:

- `completion/boom.bash`
- `completion/boom.zsh`

Le completion espongono nomi di liste e item come vocabolario interrogabile.

Decisione Calamus:

- **ADAPT** nel selettore interno: la lista delle shortcut è il vocabolario disponibile.
- nessuna completion di shell;
- nessun comando esterno.

---

## 2.3 Snippet Pixie

Archivio letto: `snippetpixie-develop.zip`.

### Abbreviazione

File: `src/Snippet.vala`

Classe: `SnippetPixie.Snippet`

- `id`
- `abbreviation`
- `body`
- `last_used`
- `trigger()`

Decisione Calamus:

- **ADAPT** `abbreviation` come shortcut mnemonica.
- **ADOPT** stable ID distinto dalla shortcut.
- **DEFER** `last_used` persistente.
- **REJECT** trigger automatico digitato in qualunque applicazione.

### Gestione e ricerca

File: `src/SnippetsManager.vala`

Classe: `SnippetPixie.SnippetsManager`

- `select_snippet`
- `search_snippets`
- `count_snippets_ending_with`
- `min_length_ending_with`
- `max_length_ending_with`
- `add`
- `update`
- `remove`
- `refresh_snippets`

`search_snippets` cerca abbreviazione e corpo; ordina per ultimo utilizzo, abbreviazione e ID.

Decisione Calamus:

- **ADOPT** ricerca su shortcut e corpo;
- **ADAPT** aggiungendo il titolo;
- **ADOPT** exact shortcut match prioritario;
- **DEFER** ordinamento persistente per ultimo uso;
- **REJECT** SQLite: il dato resta Markdown.

### Selettore rapido

File: `src/Windows/SearchAndPasteWindow.vala`

Classe: `SearchAndPasteWindow`

- SearchEntry con focus;
- Esc chiude;
- lista a selezione singola;
- `row_activated`;
- frecce Su/Giù;
- tasti numerici per i primi risultati;
- stati “nessun risultato” e “nessuna snippet”.

File: `src/Widgets/SearchAndPasteListRow.vala`

Classe: `SearchAndPasteListRow`

- keycap numerico;
- abbreviazione;
- anteprima del corpo in una riga;
- ellissi.

Decisione Calamus:

- **ADOPT** selettore rapido GTK.
- **ADOPT** riga shortcut + titolo + anteprima.
- **ADOPT** Esc, Su/Giù, Enter.
- **ADAPT** numeri soltanto dentro il selettore o come compatibilità delle scorciatoie 1–9 già esistenti.
- **REJECT** paste sintetico verso applicazioni esterne.

### Selezione stabile

File: `src/Widgets/SnippetsList.vala`

Classe: `SnippetsList`

Metodo: `set_snippets`

La selezione viene ricordata attraverso l’ID e ripristinata dopo il refresh.

Decisione Calamus:

- **ADOPT** integralmente: selezione sempre per stable ID.

### Modifica immediata

File: `src/Widgets/ViewStack.vala`

- `abbreviation_updated`
- `body_updated`
- persistenza a ogni variazione.

Decisione Calamus:

- **REJECT** autosave a ogni battuta;
- Calamus usa draft + conferma + stale check + atomic replace.

### Espansioni

File: `src/Application.vala`

- `expand_snippet`
- `expand_snippet_placeholder`
- `expand_date_placeholder`
- `expand_clipboard_placeholder`
- `expand_cursor_placeholder`

Decisione Calamus:

- **ADOPT** soltanto il marcatore del cursore.
- **ADAPT opzionale** campi compilabili secondo il modello più semplice di `pet`.
- **REJECT** clipboard placeholder.
- **REJECT** snippet annidate.
- **DEFER** date/time placeholder: Calamus possiede già Insert Date/Time.
- **REJECT** espansione automatica in applicazioni esterne.

### Shortcut di sistema

File:

- `src/Settings/Shortcut.vala`
- `src/Settings/CustomShortcutSettings.vala`
- `src/Widgets/ShortcutEntry.vala`

Decisione Calamus:

- **REJECT** creazione di scorciatoie GNOME globali e modifica di GSettings;
- Calamus usa esclusivamente un acceleratore app-local;
- nessun servizio residente.

---

# 3. Conferme dai sorgenti maturi già inclusi nell’handover

## Heynote

File:

- `src/components/library-search/LibrarySearch.vue`
- `src/stores/heynote-store.js`

Funzioni/metodi:

- `focusInput`
- `focusFirstResult`
- `moveSelectedRow`
- `activateSelectedRow`
- `openLibrarySearch`
- `openBuffer`
- `addRecentBuffer`

Decisioni:

- **ADOPT** focus one-shot;
- **ADOPT** Su/Giù, Enter, Esc;
- **ADOPT** conteggio risultati;
- **DEFER** MRU persistente.

## Gnote

File: `src/searchnoteswidget.cpp`

Classe: `SearchNotesWidget`

- `perform_search`
- `select_notes`
- `delete_selected_notes`
- ripristino della selezione dopo nuovo filtro.

Decisioni:

- **ADOPT** selezione per identità;
- **ADOPT** stato azioni dipendente dalla selezione;
- **ADOPT** Delete confermato.

## Zim

File: `zim/plugins/quicknote.py`

Classe: `QuickNoteDialog`

- `on_text_changed`
- `do_response`
- `do_response_ok`
- uso di `CURSOR_CHAR`;
- `create_new_page`
- `append_to_page`.

Decisioni:

- **ADOPT** titolo suggerito dal primo testo;
- **ADOPT** annullamento protetto;
- **ADOPT** singolo marcatore del cursore;
- **REJECT** append verso pagine o struttura notebook: appartiene allo Scratchpad/Document model, non alle clip.

## QOwnNotes

File:

- `src/managers/searchfiltermanager.cpp`
- `src/managers/noteoperationsmanager.cpp`
- `src/mainwindow.cpp`

Funzioni:

- `filterNotes`
- `filterNotesBySearchLineEditText`
- `removeCurrentNote`
- `removeSelectedNotes`
- `on_searchLineEdit_returnPressed`

Decisioni:

- **ADOPT** filtro immediato;
- **ADOPT** Enter come attivazione;
- **ADOPT** conferma operazioni distruttive;
- **REJECT** saved searches: troppo per una libreria di massimo 200 clip.

## FromScratch

File:

- `app/containers/FromScratch.jsx`
- `app/components/Shortcuts.jsx`

Metodi:

- `componentDidUpdate`
- `toggleShortcutsVisible`

Decisioni:

- **ADAPT** pannello/lista leggibile delle scorciatoie;
- **REJECT** salvataggio a ogni aggiornamento;
- la lista delle shortcut Clip viene realizzata dal quick selector stesso, non da un overlay separato.

---

# 4. Proposte funzionali

## P1 — Shortcut mnemonica univoca

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** molto alto

Ogni clip può avere una sola shortcut mnemonica opzionale.

Esempi:

- `firma`
- `intro-articolo`
- `risposta-ringraziamento`
- `citazione-lunga`

Regole:

- 1–32 caratteri;
- ASCII minuscolo;
- primo carattere alfanumerico;
- caratteri ammessi: `a-z`, `0-9`, `-`, `_`;
- confronto case-insensitive;
- univocità globale;
- nessuna lista di valori;
- nessun `#`;
- nessuna semantica di categoria;
- nessuna autorità Tags coinvolta.

La shortcut è un indirizzo, non un’etichetta.

### Modello Markdown

Aggiunta al record v2:

```text
Shortcut: firma
```

Se assente o vuota, la clip resta valida e viene trovata tramite titolo/corpo.

Migrazione:

- le clip v1 ricevono shortcut vuota;
- nessuna generazione automatica durante la migrazione;
- Duplicate azzera la shortcut;
- Edit blocca le collisioni;
- la shortcut non sostituisce lo stable ID.

---

## P2 — Insert Clip… con `Ctrl+Alt+K`

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** molto alto

Nuovo comando visibile:

`Research → Insert Clip…    Ctrl+Alt+K`

`Ctrl+Alt+K` non compare nelle binding correnti di `calamus_ui.shortcut_bindings`, quindi è libero nella baseline W94. Resta obbligatoria la validazione desktop contro eventuali shortcut del sistema.

### Comportamento

1. apre un dialogo compatto;
2. Search riceve il focus;
3. query vuota: mostra la lista completa delle shortcut;
4. digitazione: filtra e ordina;
5. Su/Giù: cambia selezione;
6. Enter o doppio clic: inserisce;
7. Esc: annulla;
8. il dialogo si chiude dopo l’inserimento;
9. il focus torna all’editor;
10. l’operazione è un solo Undo.

Nessuna clip viene inserita automaticamente soltanto perché la query coincide esattamente: serve sempre Enter o attivazione esplicita.

---

## P3 — Lista delle shortcut incorporata nel selettore

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** alto

Non serve un secondo pannello.

A query vuota, `Insert Clip…` è anche la lista delle shortcut.

Riga proposta:

```text
[firma]  Firma e recapiti
         Cordiali saluti, …
```

Per una clip senza shortcut:

```text
[—]      Paragrafo introduttivo
         Questo contributo intende…
```

Ordine a query vuota:

1. clip con shortcut, shortcut A–Z;
2. clip senza shortcut, titolo A–Z.

Il pannello Clip Collection può mantenere l’ordine canonico del file; il quick selector usa un ordinamento di sola vista.

---

## P4 — Ricerca ponderata

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** alto

Ordine dei risultati:

1. shortcut esatta;
2. shortcut che inizia con la query;
3. titolo che inizia con la query;
4. shortcut contenente la query;
5. titolo contenente la query;
6. corpo contenente la query;
7. ordine alfabetico stabile come spareggio.

Normalizzazione:

- `casefold`;
- trim;
- spazi consecutivi normalizzati per titolo e query;
- nessuna fuzzy search complessa;
- nessuna regex;
- nessun indice background.

Questo è sufficiente per un massimo di 200 record.

---

## P5 — Riga con shortcut, titolo e anteprima

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** alto

Il source corrente `calamus_clip_panel.ClipCollectionViewAdapter.render` mostra soltanto il titolo.

La nuova riga deve mostrare:

- shortcut;
- titolo;
- prima riga non vuota del corpo;
- ellissi;
- stable ID conservato come dato della riga, non mostrato.

Precedenti:

- `pet/cmd/list.go:list`;
- `SnippetPixie.SearchAndPasteListRow`;
- `Boom::Command.all`.

---

## P6 — Marcatore `{{cursor}}`

**Decisione raccomandata:** ADOPT
**Difficoltà:** bassa
**Valore:** alto

Una clip può contenere al massimo un marcatore:

```text
Gentile {{cursor}},

la ringrazio per…
```

All’inserimento:

- il marcatore viene rimosso;
- il testo viene inserito;
- il cursore viene collocato nel punto del marcatore;
- l’intera operazione resta un solo comando Undo.

Regole:

- zero o un marcatore;
- più marcatori: clip non inseribile finché non viene corretta;
- nessun marcatore: cursore alla fine del testo inserito;
- nessuna modifica dell’autorità durante l’inserimento.

Precedenti:

- `SnippetPixie.Application.expand_cursor_placeholder`;
- `Zim QuickNoteDialog` con `CURSOR_CHAR`.

---

## P7 — Avviso per corpo identico

**Decisione raccomandata:** ADAPT
**Difficoltà:** bassa
**Valore:** medio

Durante New, Capture e Duplicate:

- shortcut duplicata: errore bloccante;
- corpo identico a una clip esistente:
  - `Select Existing`;
  - `Create Anyway`;
  - `Cancel`.

Nessuna sostituzione automatica.

Precedenti:

- `pet/cmd/new.go:_new` blocca descrizioni duplicate;
- `Boom::List.add_item` sostituisce gli omonimi, comportamento che Calamus deve evitare.

---

## P8 — Scorciatoie numeriche esistenti

**Decisione raccomandata:** ADAPT, non ampliare
**Difficoltà:** bassa
**Valore:** compatibilità

La baseline possiede:

`Ctrl+Alt+1…9 → insert_clip_number`

Proposta:

- mantenerle per compatibilità durante W95;
- definirle come primi nove record dell’ordine canonico del file;
- mostrare il numero nella Clip Collection;
- non chiamarle “shortcut della clip” nella UI;
- chiamarle **numeric quick slots** nella documentazione;
- non usarle quando la query del pannello produce un ordine filtrato;
- la nuova via primaria diventa `Ctrl+Alt+K` + shortcut mnemonica.

Non creare un acceleratore GTK arbitrario per ciascuna clip.

---

## P9 — Campi compilabili prima dell’inserimento

**Decisione raccomandata:** ADAPT opzionale
**Difficoltà:** medio-bassa
**Valore:** alto per testi ricorrenti

Questa è l’unica proposta che si trova al limite superiore del criterio “semplice”.

Sintassi:

```text
Gentile {{nome}},

la ringrazio per l’incontro del {{data=giorno mese anno}}.
```

Comportamento:

1. il parser GTK-free trova i campi in ordine di prima apparizione;
2. lo stesso nome compare una sola volta nel dialogo;
3. il valore predefinito precompila l’entry;
4. Enter conferma;
5. Esc/Cancel non modifica il documento;
6. dopo la compilazione, il testo viene inserito in un solo comando;
7. `{{cursor}}` viene risolto dopo i campi.

Vincoli:

- nome: stessa grammatica della shortcut;
- nessun annidamento;
- nessun campo multilinea nella prima versione;
- nessuna scelta multipla;
- nessuna valutazione di espressioni;
- nessuna data automatica;
- nessuna clipboard;
- nessun richiamo ad altre clip;
- default divergenti per lo stesso nome: errore di validazione.

Precedenti diretti:

- `pet/dialog/params.go:SearchForParams`;
- `pet/dialog/params.go:insertParams`;
- `pet/dialog/view.go:GenerateParamsLayout`.

Questa funzione può essere:

- inclusa in W95, se si vuole portare Clip al massimo livello ancora ragionevolmente semplice;
- oppure DEFER, senza indebolire il nucleo P1–P8.

---

# 5. Funzioni analizzate ma da non introdurre

## REJECT

- tag delle clip;
- più shortcut per una clip;
- liste o cartelle di clip;
- clipboard history;
- clipboard watcher;
- shortcut di sistema per ogni clip;
- servizio residente;
- espansione automatica mentre si digita;
- inserimento in applicazioni esterne;
- sync;
- database;
- esecuzione del contenuto;
- concatenazione di più clip;
- nested clips;
- clipboard placeholder;
- URL opener;
- sostituzione silenziosa su collisione;
- salvataggio a ogni battuta.

## DEFER

- ordinamento persistente per ultimo uso;
- usage count;
- pinning;
- recent clips persistenti;
- date/time placeholder;
- import/export dedicato;
- batch operations;
- shortcut multiple/alias secondari;
- collegamenti alle sezioni;
- Tags integration;
- watcher filesystem.

W93 Scratchpad Full resta congelato e non viene coinvolto.

---

# 6. Revisione proposta del modello Markdown v2

```text
# Calamus Clip Collection v2

## Firma e recapiti

ID: clip-0123456789abcdef0123456789abcdef
Shortcut: firma
Created: 2026-07-29T20:00:00+02:00
Updated: 2026-07-29T20:00:00+02:00

```text
Cordiali saluti,

{{cursor}}
```
```

Regole aggiuntive:

- `Shortcut` può essere vuoto;
- stable ID obbligatorio;
- i campi sconosciuti vengono conservati;
- la shortcut è un singolo valore;
- `{{cursor}}` e gli eventuali campi sono contenuto del body, non metadati;
- Duplicate genera nuovo ID, timestamp nuovi e shortcut vuota.

---

# 7. Transazioni

## Quick Insert senza campi

1. aprire il selettore con snapshot dell’autorità;
2. scegliere la clip per ID;
3. verificare revision token;
4. se stale: annullare e offrire Refresh;
5. espandere `{{cursor}}`;
6. eseguire un solo comando sul documento;
7. tornare al focus editor.

Il file `clips.md` non viene riscritto.

## Quick Insert con campi

1. scelta per ID;
2. stale check;
3. parsing campi;
4. dialogo valori;
5. Cancel: nessuna modifica;
6. nuova verifica che la clip selezionata sia ancora la stessa;
7. espansione;
8. un solo comando documento.

## New/Edit

- draft non persistito;
- validazione shortcut;
- validazione marker/campi;
- revisione token;
- atomic replace;
- runtime aggiornato solo dopo successo.

---

# 8. Test headless ostili aggiuntivi

## Shortcut

- shortcut vuota valida;
- caratteri non ammessi;
- lunghezza 0/1/32/33;
- collisione case-insensitive;
- collisione durante migrazione;
- Duplicate azzera shortcut;
- shortcut sconosciuta preservata dopo round trip;
- exact match prioritario;
- prefix e substring ordering;
- query Unicode nel titolo/corpo;
- ricerca nel corpo multilinea;
- due clip con titolo e corpo uguali ma ID diversi.

## Quick Insert

- nessuna selezione;
- clip rimossa dopo apertura dialogo;
- file modificato esternamente;
- query senza risultati;
- Enter con risultato;
- Esc;
- focus restituito;
- un solo Undo;
- documento invariato su errore;
- selezione editor non sostituita implicitamente.

## Cursor marker

- zero marker;
- un marker;
- marker a inizio/fine;
- marker in testo multilinea;
- due marker;
- marker dentro code fence;
- offset corretto con Unicode.

## Campi opzionali

- nessun campo;
- campo senza default;
- campo con default;
- campo ripetuto;
- ordine prima apparizione;
- default divergenti;
- annullamento;
- testo contenente brace non valide;
- campo più `{{cursor}}`;
- nessun residuo di placeholder dopo conferma;
- documento invariato su dialog failure.

---

# 9. True App / True GTK

Corsie necessarie:

1. `Research → Insert Clip…`;
2. `Ctrl+Alt+K`;
3. Search focus reale;
4. lista completa a query vuota;
5. exact shortcut;
6. ricerca per titolo e corpo;
7. Su/Giù;
8. Enter;
9. doppio clic;
10. Esc;
11. inserimento nel vero `Gtk.TextBuffer`;
12. Undo;
13. caret su `{{cursor}}`;
14. dialogo campi, se adottato;
15. stale conflict;
16. hide/show Research Panel;
17. switch fra client;
18. resize narrow/medium/wide;
19. normal close;
20. nessun processo residuo.

Desktop acceptance:

- nessuna collisione reale di `Ctrl+Alt+K`;
- nessun cambiamento della larghezza del Research Panel;
- nessun focus rubato dopo la chiusura;
- nessuna modifica di `clips.md` durante il semplice inserimento;
- documento modificato soltanto dopo conferma esplicita.

---

# 10. User Guide

Aggiunte obbligatorie:

- differenza fra shortcut globale e shortcut mnemonica;
- grammatica della shortcut;
- esempi;
- `Ctrl+Alt+K`;
- lista a query vuota;
- ranking della ricerca;
- Enter, Esc, frecce;
- numeric quick slots 1–9;
- `{{cursor}}`;
- eventuali campi;
- collisioni;
- stale conflict;
- distinzione netta da Tags;
- distinzione netta da Scratchpad;
- nessun clipboard monitoring.

La finestra generale Keyboard Shortcuts deve includere:

- `Insert Clip… — Ctrl+Alt+K`;
- `Insert Clip 1–9 — Ctrl+Alt+1…9`, se mantenute.

---

# 11. Path presumibilmente coinvolti

## Modifica probabile

- `calamus/calamus_clips.py`
- `calamus/calamus_clip_collection.py`
- `calamus/calamus_clip_panel.py`
- `calamus/calamus_ui.py`
- `calamus/calamus_shortcuts.py`
- `calamus/calamus_commands.py`
- `bin/calamus`
- `docs/CALAMUS_USER_GUIDE.md`

## Nuovi moduli plausibili

- `calamus/calamus_clip_search.py`
- `calamus/calamus_clip_dialogs.py`
- eventuale `calamus/calamus_clip_expansion.py`

## Test

- `tests/test_clip_markdown_store.py`
- `tests/test_clip_collection_controller.py`
- `tests/test_clip_panel_adapter.py`
- nuovi test shortcut/search;
- nuovi test quick insert wiring;
- nuovi test cursor marker;
- nuovi test parametri, soltanto se adottati;
- True GTK dialogs;
- True App insert.

I path definitivi dovranno essere congelati prima del candidato.

---

# 12. Pacchetto raccomandato

## Nucleo raccomandato W95-R2

Adottare:

- P1 Shortcut mnemonica univoca;
- P2 `Ctrl+Alt+K` Insert Clip;
- P3 Lista shortcut incorporata;
- P4 Ricerca ponderata;
- P5 Riga shortcut/titolo/anteprima;
- P6 `{{cursor}}`;
- P7 Avviso corpo identico;
- P8 Compatibilità numeric quick slots.

Questo pacchetto resta tecnicamente semplice e migliora molto l’uso keyboard-first.

## Estensione facoltativa

Decidere separatamente P9:

- campi compilabili `{{nome}}` / `{{nome=default}}`.

È il miglior contributo specifico di `pet`, ma richiede un dialogo e una grammatica da testare. Non va incluso tacitamente.

---

# 13. Stato finale

- audit diretto eseguito;
- proposte prodotte;
- nessuna implementazione;
- nessuna patch;
- nessuna modifica al repository;
- nessun commit o push;
- W93 non riaperto;
- funzioni REJECT/DEFER non introdotte;
- freeze W95 da revisionare soltanto dopo decisione esplicita dell’utente.


## R4 targeted re-audit after desktop validation

- **Snippet Pixie** — `src/Application.vala::expand_cursor_placeholder`: ADAPT the explicit post-expansion caret operation, but keep it inside Calamus and never synthesize input into other applications.
- **Zim 0.76.3** — `zim/plugins/quicknote.py::QuickNoteDialog` and `CURSOR_CHAR`: ADAPT one deterministic cursor marker and reject multiple markers.
- **Snippet Pixie** — `src/Widgets/MainWindowHeader.vala`: ADAPT the `Gtk.MenuButton` + `Gtk.PopoverMenu` boundary for a bounded selector that opens from its anchor, while retaining Calamus' single-client Research stack.
- **Calamus SearchViewAdapter** — `select_span` and the existing `queue_insert_scroll` boundary: ADAPT explicit cursor placement plus deferred scrolling after a GTK buffer relayout.
