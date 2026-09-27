# Review del progetto

**Revisione esaminata:** `184cb0f87cffbfc7855029f98758d37b0d103ba0` (`feat(ui): adozione header centrato standard gaskb_style e badge versione isolato`)

Questa review considera esclusivamente il contenuto di `HEAD`; le modifiche non committate del working tree non sono state lette né incluse.

## Valutazione generale

Il progetto e' una buona base per un MVP personale: l'architettura e' proporzionata al problema (FastAPI, rendering server-side, SQLite) e non introduce complessita' prematura. La separazione tra API, web, dominio, orchestrazione e integrazioni e' chiara; la scelta di rendere `user_id` obbligatorio fin dall'inizio evita una migrazione concettualmente costosa quando arriveranno altri utenti.

Ci sono segnali positivi concreti:

- i flussi principali hanno test mirati e i test isolano correttamente rete, AI e TikTok;
- l'accesso ai bookmark e alle API token e' filtrato per utente;
- password e API token sono trattati correttamente con hash, mentre le FK SQLite e il WAL sono esplicitamente abilitati e testati;
- il salvataggio rapido con arricchimento successivo e' una buona scelta UX per lo share target mobile;
- Docker, Alembic e variabili d'ambiente rendono il deploy ripetibile.

La maturita' e' quindi buona per un'app self-hosted e a utente singolo. Prima di esporla stabilmente su Internet o aumentare il numero di utenti, darei priorita' alle frontiere di sicurezza e affidabilita' descritte sotto.

## Miglioramenti prioritari

### Alta - impedire SSRF nell'estrazione metadati

[`app/integrations/metadata_extractor.py`](app/integrations/metadata_extractor.py) scarica ogni URL inserito dall'utente, segue i redirect e non verifica schema, hostname o indirizzo IP. Un bookmark come `http://127.0.0.1:...`, un IP privato o un hostname che risolve nella LAN puo' far effettuare al container richieste verso servizi interni (inclusi eventuali endpoint dell'homelab). Anche un URL pubblico puo' poi reindirizzare a una destinazione privata.

Azioni consigliate:

1. Accettare solo `http` e `https` e rifiutare host assenti.
2. Risolvere l'hostname prima di ogni richiesta e di ogni redirect; rifiutare loopback, link-local, private, multicast, unspecified e reti riservate.
3. Disabilitare il redirect automatico e validare manualmente ogni `Location`, con un limite basso al numero di redirect.
4. Aggiungere test per IP privati, URL con schema non HTTP(S), redirect verso indirizzi privati e DNS con piu' record.

Il limite di 2 MB e il timeout sono gia' una buona difesa contro risposte troppo grandi e lente: manca il controllo sulla destinazione.

### Alta - rendere robusta la configurazione della sessione in produzione

Le sessioni web in [`app/domain/session.py`](app/domain/session.py) sono token bearer conservati in chiaro nel database per 30 giorni. Una copia del database consente quindi di impersonare gli utenti fino alla scadenza. Inoltre il flag `Secure` del cookie dipende da `ENV`: se in deploy resta il valore di default `development`, il cookie viene emesso senza `Secure`.

Azioni consigliate:

1. Conservare l'hash SHA-256 del token di sessione, come gia' avviene per le API token, e cercare la sessione tramite hash.
2. Sostituire la logica implicita basata su `ENV` con una variabile esplicita `SESSION_COOKIE_SECURE`, predefinita a `true`; impostarla a `false` solo nello sviluppo HTTP locale.
3. Aggiungere rate limiting al login, almeno nel reverse proxy, e testare scadenza e invalidazione della sessione.
4. Per le route web mutanti, aggiungere un token CSRF oppure validare `Origin`/`Referer`; `SameSite=Lax` e' utile ma non sostituisce una difesa esplicita.

### Media - imporre vincoli sui tag nel database

[`app/domain/bookmark.py`](app/domain/bookmark.py) cerca un tag e poi lo crea se non lo trova, ma lo schema non impone l'unicita' di `(user_id, name)`. Due richieste concorrenti possono creare tag uguali; una volta presenti, selezioni e statistiche possono restituire risultati incoerenti.

Azioni consigliate:

1. Aggiungere una migration con vincolo univoco su `(user_id, name)`.
2. Normalizzare il nome una sola volta e gestire l'`IntegrityError` nel percorso get-or-create, rileggendo il tag creato dall'altra transazione.
3. Aggiungere un test concorrente o almeno un test che verifichi il vincolo a livello SQLite.

### Media - validare e limitare tutti gli input

Le API dichiarano gli URL come semplici `str` in [`app/api/schemas.py`](app/api/schemas.py), mentre i form web salvano qualunque stringa non vuota. Questo e' anche il primo punto di difesa per la SSRF, ma migliora pure la qualita' dei dati. L'import HTML in [`app/web/bookmarks.py`](app/web/bookmarks.py) esegue inoltre `await file.read()` senza alcun limite e fa un commit per ogni link.

Azioni consigliate:

1. Introdurre un tipo/validatore URL condiviso per API, form, share target e import, con limiti di lunghezza per URL, titolo, nota, tag e nome token.
2. Limitare la dimensione del file importato prima di leggerlo interamente e stabilire un limite al numero di bookmark importabili per richiesta.
3. Per l'import, usare una transazione o commit a batch: migliora molto la velocita' e rende esplicita la semantica in caso di errore.
4. Aggiungere test per input malformati, file troppo grandi e import molto grandi.

### Media - rendere affidabile l'arricchimento asincrono

[`app/api/quick_save.py`](app/api/quick_save.py), [`app/web/bookmarks.py`](app/web/bookmarks.py) e [`app/web/share_target.py`](app/web/share_target.py) usano `BackgroundTasks`. E' ottimo per non bloccare la risposta, ma il lavoro vive nel processo Uvicorn: un riavvio, un crash o un deploy tra il salvataggio e l'esecuzione lascia il bookmark permanentemente senza metadati e suggerimenti AI. Le operazioni lente possono inoltre occupare worker web.

Per il MVP, una soluzione minima e' memorizzare uno stato di arricchimento (`pending`, `done`, `failed`) e aggiungere uno script idempotente che recuperi i bookmark pending. Se il carico aumenta, spostare il task su una coda persistente. Servono test sul recupero dopo un fallimento e sull'idempotenza.

### Bassa - rendere il deploy piu' difensivo e osservabile

[`Dockerfile`](Dockerfile) esegue l'app come root e installa dipendenze da intervalli di versione, non da un lock file. [`docker-entrypoint.sh`](docker-entrypoint.sh) applica inoltre automaticamente le migration ad ogni avvio: e' comodo con una sola replica, ma richiede coordinamento se il deploy diventera' multi-processo o multi-replica.

Azioni consigliate:

1. Eseguire il container con utente non privilegiato e fissare le dipendenze in un lock file riproducibile.
2. Separare il comando di migrazione dal processo web quando il deploy superera' una singola replica.
3. Aggiungere backup verificati del volume `data` e una breve procedura di restore: con SQLite il backup e' semplice, ma va anche provato.
4. Esporre metriche/log strutturati per errori di enrichment, login falliti e invio digest; oggi gli errori sono loggati, ma non facilmente misurabili.

## Copertura e verifica

La suite contiene molti test di comportamento e isolamento per utente; mancano in particolare casi per SSRF/redirect, sicurezza delle sessioni, limiti degli upload e concorrenza sui tag.

Ho tentato di eseguire i test su un archivio temporaneo di `HEAD`, quindi senza usare il working tree. L'esecuzione non e' partita per un problema dell'ambiente locale: `.venv/bin/pytest` punta a `./.venv/bin/python3.14`, che non esiste. Prima della prossima modifica al codice conviene ricreare il virtualenv e rieseguire `pytest -q`.
