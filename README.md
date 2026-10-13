# Cozy-Bookmarks

*[Italiano sotto / Italian below](#cozy-bookmarks-italiano)*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-336699.svg)](https://htmx.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

A lightweight, self-hosted, AI-assisted bookmark manager. Save disorganized links on the fly, review and organize them with tags and categories later. Supports automated AI tagging, a responsive Material Design 3 interface, and seamless mobile saving via Android PWA Web Share Target.

---

## 💡 Architecture & Philosophy

- **Backend**: Python + FastAPI, engineered as a clean and fast monolith.
- **Frontend**: Pure server-rendered templates (Jinja2 + HTMX) styled with modern CSS ([`gaskb_style`](https://github.com/gaskb)) — **zero JavaScript build steps, zero bundle compilation**, ensuring maximum performance and rapid maintenance.
- **Storage**: SQLite with WAL mode — single file storage, simple zero-downtime backups, and zero external database services to manage.
- **Pluggable AI Tagging**: Clean provider abstraction supporting any OpenAI-compatible API (`/chat/completions`) — including local self-hosted models (vLLM, Ollama, Qwen) and OpenAI — as well as a native Anthropic Claude Messages adapter (`AI_PROVIDER=claude`).
- **Session Authentication**: Native in-app cookie-based authentication with SHA-256 session token hashing, bcrypt password storage, and multi-user data isolation.
- **Mobile First (PWA)**: Web App Manifest, Service Worker, and Web Share Target API enabling system-level "Share to Cozy Bookmarks" directly from mobile browsers, TikTok, Instagram, and Reddit.

---

## 🛡️ Security & Reliability Hardening

* **Strict Anti-SSRF Defense**: Deep URL validation blocking loopback, RFC1918 private subnets, intranet addresses, link-local, and non-HTTP protocols prior to network resolution, with manual redirect hopping (max 3 hops).
* **Session Token Hashing**: Session identifiers are stored exclusively as SHA-256 digests (`token_hash`) in SQLite; a database snapshot leak will not expose valid user sessions.
* **Tag Data Integrity**: Unique database constraint on `(user_id, name)` with concurrent-safe get-or-create logic preventing tag duplicate collisions.
* **Streaming HTML Import**: Streaming Netscape bookmark format parser handling files up to 5 MB (up to 5,000 bookmarks) in a single transactional SQLite batch.
* **Resilient Background Enrichment**: State machine tracking (`pending`, `completed`, `failed`) on metadata extraction with an idempotent CLI retry tool (`python -m app.scripts.retry_failed_enrichments`).

---

## ⚙️ Quick Start (.env)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment options:

```env
ENV=development
DATABASE_URL=sqlite:///./data/cozy_bookmarks.db
SESSION_COOKIE_SECURE=true

# AI Auto-tagging configuration
AI_TAGGING_ENABLED=true
AI_PROVIDER=openai_compatible
AI_OPENAI_COMPATIBLE_BASE_URL=http://localhost:8000/v1
AI_OPENAI_COMPATIBLE_MODEL=default
AI_OPENAI_COMPATIBLE_API_KEY=

# Optional: Daily Digest via SMTP
SMTP_ENABLED=false
BASE_URL=http://localhost:8000
```

### Running with Docker

```bash
docker compose up -d
```

Access the web interface at `http://localhost:8000`.

### Running Locally

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Automated Tests

The extensive test suite includes **213 automated tests** covering anti-SSRF protections, auth security, concurrent tag creation, import/export, and AI provider mocking:

```bash
pytest -v
```

---

## 📜 License

Released under the [MIT](LICENSE) License.

Cozy-Bookmarks is free and open-source. If you find it helpful for organizing your links, feel free to [buy me a coffee on Ko-fi](https://ko-fi.com/gaskb) ☕!

---

<br>

<a name="cozy-bookmarks-italiano"></a>
# Cozy-Bookmarks (Italiano)

Gestore di bookmark self-hosted leggero, assistito da AI (tagging automatico), per web e Android (PWA share target). Salva link al volo da mobile e organizzali con calma in un secondo momento.

---

## 💡 Architettura & Filosofia

- **Backend**: Python + FastAPI, monolite pulito e reattivo.
- **Frontend**: Pagine renderizzate lato server (Jinja2 + HTMX) con CSS moderno — **zero build step JS, zero framework pesanti**, massima velocità di navigazione.
- **Storage**: SQLite con WAL mode — zero server database esterni da manutenere, backup istantaneo copiando un file.
- **AI Modulare**: Interfaccia provider astratta che supporta endpoint compatibili OpenAI (`/chat/completions`) per LLM locali self-hosted (Ollama, vLLM, Qwen) oppure adapter dedicato per Anthropic Claude.
- **Autenticazione**: Gestione sessioni via cookie protetti, password con bcrypt e hashing SHA-256 dei token di sessione.
- **Android / Mobile (PWA)**: Web App Manifest, Service Worker e Web Share Target API per comparire direttamente nel menu "Condividi" di Android.

---

## 🛡️ Sicurezza & Resilienza

- **Protezione Anti-SSRF**: Verifica preventiva dei domini con blocco di indirizzi IP privati, intranet, loopback e controllo rigoroso dei redirect (max 3 hop).
- **Session Hashing**: I token di sessione web sono memorizzati nel database solo come digest SHA-256 (`token_hash`).
- **Integrità dei Tag**: Vincolo univoco `(user_id, name)` con gestione concorrente sicura in get-or-create per prevenire duplicazioni.
- **Import HTML Ottimizzato**: Upload streaming fino a 5 MB e fino a 5.000 segnalibri in un'unica transazione SQLite.
- **Arricchimento Asincrono**: Tracciamento dello stato (`pending`, `completed`, `failed`) e script CLI (`python -m app.scripts.retry_failed_enrichments`) per il recupero dei task interrotti.

---

## ⚙️ Configurazione & Avvio

```bash
cp .env.example .env
docker compose up -d
```

L'applicazione sarà raggiungibile su `http://localhost:8000`.

---

## 🧪 Test Automatici

La suite include **213 test automatici** che convalidano sicurezza, import/export, protezione SSRF, autenticazione e provider AI:

```bash
pytest -v
```

---

## 📜 Licenza

Rilasciato sotto licenza [MIT](LICENSE).

Cozy-Bookmarks è gratuito e open-source. Se ti torna utile per gestire i tuoi link, sentiti libero di [offrirmi un caffè su Ko-fi](https://ko-fi.com/gaskb) ☕!
