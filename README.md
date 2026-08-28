# cozy-bookmarks

Gestore di bookmark self-hosted: salva link disorganizzati trovati in giro, guardali e organizzali (tag, categorie) in un secondo momento. AI-assisted per il tagging automatico. Uso personale, web + Android (salvataggio dal menu "Condividi" via PWA).

## Stato

MVP in sviluppo. Backlog e progressi sono tracciati nelle [issue GitLab](http://github.com/gaskb/cozy-bookmarks/-/issues) di questo progetto (stima in "abeti", scala Fibonacci, vedi label `abeti::N`).

## Architettura (decisa per l'MVP)

- **Backend**: Python + FastAPI, monolite singolo (niente microservizi, non serve alla scala di un solo utente).
- **Frontend**: server-rendered (Jinja2 + HTMX), niente SPA/build step JS — velocità di sviluppo e nessuna curva di apprendimento su un framework frontend non necessario per un'app essenzialmente CRUD.
- **Storage**: SQLite — zero DB server da gestire, backup = copiare un file.
- **AI**: interfaccia provider astratta (chat-completion), due implementazioni intercambiabili via config:
  - LLM locale già in homelab (`ai.home.example.com`, Unsloth Studio, endpoint OpenAI-compatible) — default, nessun costo extra.
  - API Claude — opzionale, per qualità/affidabilità migliori quando serve.
- **Auth**: nessuna in-app per l'MVP (single user). Protezione via Nginx Proxy Manager (Basic Auth, Access List "gas"), come altri servizi privati dell'homelab.
- **Android**: web app manifest + service worker, Web Share Target API per comparire nel menu "Condividi" di sistema.
- **iOS/app nativa**: fuori scope per ora.
- **Deploy**: Docker Compose su una VM dell'homelab (pattern: Vikunja/hyphen-check su VM 103 "web-server"), dietro Nginx Proxy Manager su un sottodominio `*.example.com`.

Convenzioni di sviluppo (clean code, commit, backlog) seguite in questo progetto sono documentate nel workspace Notion personale, non duplicate qui.
