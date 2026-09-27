# cozy-bookmarks

Gestore di bookmark self-hosted: salva link disorganizzati trovati in giro, guardali e organizzali (tag, categorie) in un secondo momento. AI-assisted per il tagging automatico. Uso personale, web + Android (salvataggio dal menu "Condividi" via PWA).

## Stato

MVP in sviluppo. Backlog e progressi sono tracciati nelle [issue GitLab](http://github.com/gaskb/cozy-bookmarks/-/issues) di questo progetto (stima in "abeti", scala Fibonacci, vedi label `abeti::N`).

## Architettura (decisa per l'MVP)

- **Backend**: Python + FastAPI, monolite singolo (niente microservizi, non serve alla scala di un solo utente).
- **Frontend**: server-rendered (Jinja2 + HTMX), niente SPA/build step JS — velocità di sviluppo e nessuna curva di apprendimento su un framework frontend non necessario per un'app essenzialmente CRUD.
- **Storage**: SQLite — zero DB server da gestire, backup = copiare un file.
- **AI**: interfaccia provider astratta (chat-completion), due implementazioni:
  - `OpenAICompatibleProvider` — qualunque servizio con endpoint `/chat/completions` in stile OpenAI: il LLM locale già in homelab (Unsloth Studio, default), ma anche Qwen (DashScope compatible-mode o self-hosted), OpenAI/ChatGPT stesso, o altri — cambiare provider è pura config (`AI_OPENAI_COMPATIBLE_BASE_URL`/`_MODEL`/`_API_KEY`), zero codice nuovo.
  - `ClaudeProvider` — unico adapter dedicato, perché l'API Messages di Anthropic ha una forma diversa (system prompt separato, shape della risposta diversa). Attivabile con `AI_PROVIDER=claude`.
- **Auth**: in-app fin dall'inizio (tabella `users`, login email+password, sessione via cookie) — anche se si parte con un solo account, per non dover riscrivere il modello dati quando si aggiungerà un secondo utente. Ogni bookmark ha un `user_id` obbligatorio fin dal primo schema. Nginx Proxy Manager fa solo da reverse proxy/TLS, nessuna Access List davanti al servizio.
- **Android**: priorità alta, subito dopo le fondamenta — web app manifest + service worker, Web Share Target API per comparire nel menu "Condividi" di sistema. Motivazione: i link "al volo" (TikTok/Instagram e simili) vengono per lo più consumati e salvati da mobile, l'organizzazione avviene poi da PC.
- **iOS/app nativa**: fuori scope per ora.
- **Deploy**: Docker Compose su una VM dell'homelab (pattern: Vikunja/hyphen-check su VM 103 "web-server"), dietro Nginx Proxy Manager su un sottodominio `*.example.com`.
- **Estrazione contenuto social (sperimentale, post-MVP)**: link citati in caption di post Instagram/TikTok, ed eventualmente trascrizione audio per link menzionati a voce nei video — vedi backlog, entrambe da validare tecnicamente prima di investirci sviluppo serio.

- **Sicurezza e Affidabilità (v0.8.0 - v0.9.0)**:
  - **Protezione Anti-SSRF**: verifica rigorosa degli schemi (solo HTTP/HTTPS), risoluzione DNS preliminare e blocco tempestivo di indirizzi IP privati, loopback, intranet/LAN e link-local; validazione manuale dei redirect (max 3 hop).
  - **Session Hashing**: i token di sessione web sono memorizzati a database unicamente come digest SHA-256 (`token_hash`), garantendo che un leak o dump del database non consenta l'impersonificazione delle sessioni attive.
  - **Cookie di Sessione**: configurazione esplicita del flag `SESSION_COOKIE_SECURE` (default `true` per HTTPS in produzione).
  - **Integrità Dati Tag**: vincolo univoco di database `(user_id, name)` sui tag con gestione concorrente sicura in get-or-create per prevenire collisioni e duplicati.
  - **Validazione Input & Limiti**: validatore centralizzato degli URL HTTP(S) con vincoli stringenti di lunghezza massima su URL (2048), titoli (500), note (10.000), tag (50) e token (100) su API e form web.
  - **Ottimizzazione Import HTML**: upload controllato in streaming (max 5 MB), limite a 5.000 bookmark per file e batch commit in un'unica transazione SQLite.
  - **Affidabilità Arricchimento Asincrono**: tracciamento dello stato (`pending`, `completed`, `failed`) su ogni segnalibro e script CLI idempotente (`python -m app.scripts.retry_failed_enrichments`) per il recupero automatico di task interrotti o falliti.

Convenzioni di sviluppo (clean code, commit, backlog) seguite in questo progetto sono documentate nel workspace Notion personale, non duplicate qui.

---

Offrimi un caffè su [Ko-fi](https://ko-fi.com/gaskb)!

