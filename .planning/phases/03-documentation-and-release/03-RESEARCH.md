# Phase 3: Documentation and Release - Research

**Researched:** 2026-04-06
**Domain:** MkDocs documentation site, bilingual Markdown docs, systemd service, GitHub Actions CI/CD
**Confidence:** HIGH (core stack verified against PyPI and official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** One markdown file per topic in `docs/en/` and `docs/de/`, mirrored 1:1 between languages — existing `evcc-integration.md` and `ha-coexistence.md` stay in place
- **D-02:** New files: `quickstart.md` (developer track), `user-guide.md` (end-user track), `systemd.md` (systemd deployment) — each in both language directories
- **D-03:** EN is the source language; DE translations mirror structure and headings exactly
- **D-04:** Compact `README.md` (EN) with: project badges (Python version, license, Docker), one-paragraph description, ASCII architecture diagram, 3-line Docker quick-start, and links to full guides in `docs/en/`
- **D-05:** `README.de.md` mirrors `README.md` in German with a "Read in English" link at the top; pyproject.toml `readme` field stays pointing to `README.md`
- **D-06:** Architecture diagram as ASCII art in README — shows Luxtronik controller <-> Proxy <-> Modbus clients (evcc, HA) data flow
- **D-07:** MkDocs with Material theme — standard for Python open-source projects, built-in search, responsive design
- **D-08:** Language switching via MkDocs i18n plugin (`mkdocs-static-i18n`) — EN as default, DE as alternate
- **D-09:** Deployment via GitHub Actions workflow (`mkdocs gh-deploy`) on push to main branch
- **D-10:** Navigation: Home, Quick Start (Developer), User Guide, evcc Integration, HA Coexistence, systemd Service
- **D-11:** `mkdocs.yml` configuration file at project root
- **D-12:** Template service file `contrib/luxtronik2-modbus-proxy.service` using `EnvironmentFile` for config path override
- **D-13:** Service runs as dedicated system user (matching Docker's non-root pattern), `Type=simple`, `Restart=on-failure`
- **D-14:** structlog JSON output goes naturally to journald — no separate log file configuration needed
- **D-15:** Installation instructions in `docs/en/systemd.md` and `docs/de/systemd.md` — positioned as alternative to Docker deployment
- **D-16:** Service file includes `After=network-online.target` since proxy needs network connectivity to reach Luxtronik controller

### Claude's Discretion
- MkDocs plugin versions and exact `mkdocs.yml` configuration details
- Badge selection and ordering in README
- GitHub Actions workflow details (trigger events, caching)
- Exact ASCII diagram layout
- Documentation tone and depth of explanations

### Deferred Ideas (OUT OF SCOPE)
- Community announcements (evcc forum, HA forum, haustechnikdialog.de) — tracked as COMM-10
- evcc upstream heater template PR — tracked as INTEG-10
- HA HACS custom component — tracked as INTEG-11
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | README in English and German with project overview, quick start, and architecture description | D-04, D-05, D-06 cover structure; see Badge Patterns and ASCII Diagram sections below |
| DOCS-02 | Developer quickstart guide (EN + DE) for building and running from source | D-02; existing pyproject.toml, Dockerfile, docker-compose.yml provide reference content |
| DOCS-03 | End-user guide (EN + DE) for installing and configuring the proxy | D-02; config.example.yaml documents all configurable fields; Docker + systemd tracks |
| DOCS-04 | GitHub Pages project homepage | D-07 through D-11; MkDocs Material 9.7.6 + mkdocs-static-i18n 1.3.1; GH Actions workflow |
| DEPLOY-02 | Proxy runs as a systemd service on Linux | D-12 through D-16; service file template pattern documented below |
</phase_requirements>

---

## Summary

Phase 3 delivers documentation and release artifacts: bilingual Markdown guides, a GitHub Pages site via MkDocs Material, a systemd service template, and polished README files. The technical work is primarily writing and configuration — no new Python code.

The MkDocs stack is well-established: Material for MkDocs 9.7.6 (released March 2026) paired with mkdocs-static-i18n 1.3.1 (released February 2026). Both are current and actively maintained. The `docs/en` + `docs/de` folder structure the project already uses maps cleanly onto mkdocs-static-i18n's `docs_structure: folder` mode — no file reorganization needed.

The systemd service file is straightforward: `Type=simple`, non-root user, `EnvironmentFile` for the config path, `After=network-online.target`. The proxy's journald integration (structlog JSON) works without any extra configuration.

**Primary recommendation:** Build the MkDocs site first (mkdocs.yml + GitHub Actions workflow + index.md), then write docs in order: quickstart (EN), user-guide (EN), systemd (EN), then translate all three to DE. README files last since they summarize the completed feature set.

---

## Project Constraints (from CLAUDE.md)

These directives apply to all documentation content:

- **Language:** US English for all code, comments, CLI examples in docs
- **Two tracks:** Quickstart (developers) + Guide (end users / non-technical)
- **Two languages:** US English + German (`docs/en/` and `docs/de/`)
- **Private data prohibition:** No real IP addresses, hostnames, or credentials in any file — use `192.168.x.x`, `your-heatpump-ip`, `heatpump.example.local`
- **Pre-commit hook:** Blocks commits containing real IP patterns — docs must use placeholder values
- **Docstrings:** Google style (applies to any inline code examples with docstrings)
- **Related private project:** Never reference `~/claude-code/wp-alpha-innotec/` in any file

---

## Standard Stack

### Core Documentation Tools
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mkdocs` | 1.6.1 | Static site generator | Core MkDocs engine; stable since Aug 2024 |
| `mkdocs-material` | 9.7.6 | Documentation theme | Standard for Python open-source; built-in search, mobile-responsive, GitHub integration; 9.7.6 released Mar 19 2026 |
| `mkdocs-static-i18n` | 1.3.1 | Bilingual docs via folder structure | Supports `docs_structure: folder` matching the existing `docs/en/` + `docs/de/` layout; auto-configures Material language switcher; 1.3.1 released Feb 20 2026 |

**Version verification:** [VERIFIED: pypi.org/project/mkdocs-material] 9.7.6, Mar 19 2026 | [VERIFIED: pypi.org/project/mkdocs-static-i18n] 1.3.1, Feb 20 2026 | [VERIFIED: pypi.org/project/mkdocs] 1.6.1, Aug 30 2024

### Supporting Libraries (docs build only, not in project dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `mkdocs-material[imaging]` | 9.7.6 | Social cards (OG images) | Optional; requires Cairo — skip for v1 |

### Installation (docs build environment only)
```bash
pip install mkdocs-material mkdocs-static-i18n
```

These are build-time tools, not runtime dependencies. They do NOT belong in `pyproject.toml` — only in the GitHub Actions workflow and developer setup instructions.

### Alternatives Considered
| Recommended | Alternative | Tradeoff |
|-------------|-------------|----------|
| `mkdocs-static-i18n` (folder mode) | Manual dual-nav without plugin | Plugin provides language switcher in header; without it, no automatic EN/DE toggle |
| `mkdocs-static-i18n` | `mkdocs-i18n` (GitLab project) | mkdocs-static-i18n has broader adoption and Material theme integration |
| GitHub Actions `mkdocs gh-deploy` | Third-party deploy action | Official Material docs pattern; no extra dependency |

---

## Architecture Patterns

### Existing Directory Structure (Phase 2 output)
```
docs/
├── en/
│   ├── evcc-integration.md    # EXISTS — integrate into nav
│   └── ha-coexistence.md      # EXISTS — integrate into nav
└── de/
    (empty — DE directory exists per CONTEXT.md D-01)
```

### Target Structure After Phase 3
```
docs/
├── en/
│   ├── index.md               # NEW — GitHub Pages homepage (EN)
│   ├── quickstart.md          # NEW — developer quickstart
│   ├── user-guide.md          # NEW — end-user installation guide
│   ├── systemd.md             # NEW — systemd deployment
│   ├── evcc-integration.md    # EXISTS — carry through
│   └── ha-coexistence.md      # EXISTS — carry through
└── de/
    ├── index.md               # NEW — homepage (DE)
    ├── quickstart.md          # NEW — Schnellstart
    ├── user-guide.md          # NEW — Benutzerhandbuch
    ├── systemd.md             # NEW — systemd (DE)
    ├── evcc-integration.md    # NEW — DE translation
    └── ha-coexistence.md      # NEW — DE translation

contrib/
└── luxtronik2-modbus-proxy.service  # NEW — systemd unit template

.github/
└── workflows/
    └── docs.yml               # NEW — GH Actions MkDocs deploy

mkdocs.yml                     # NEW — at project root
README.md                      # NEW (replaces placeholder)
README.de.md                   # NEW
```

### Pattern 1: MkDocs with folder-based i18n

**What:** `docs_structure: folder` maps `docs/en/` as the EN root and `docs/de/` as the DE alternate. EN content is served at `/`, DE at `/de/`.

**When to use:** When language files already live in separate subdirectories (which they do in this project).

**Example mkdocs.yml:**
```yaml
# Source: https://squidfunk.github.io/mkdocs-material/
# Source: https://ultrabug.github.io/mkdocs-static-i18n/setup/setting-up-material/
site_name: luxtronik2-modbus-proxy
site_url: https://{github-username}.github.io/PUBLIC-luxtronik2-modbus-proxy/
site_description: Modbus TCP proxy for Luxtronik 2.0 heat pump controllers
repo_url: https://github.com/{github-username}/PUBLIC-luxtronik2-modbus-proxy
repo_name: PUBLIC-luxtronik2-modbus-proxy
docs_dir: docs

theme:
  name: material
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - content.code.copy

plugins:
  - search
  - i18n:
      docs_structure: folder
      reconfigure_material: true
      languages:
        - locale: en
          default: true
          name: English
          build: true
        - locale: de
          name: Deutsch
          build: true

nav:
  - Home: index.md
  - Quick Start: quickstart.md
  - User Guide: user-guide.md
  - evcc Integration: evcc-integration.md
  - HA Coexistence: ha-coexistence.md
  - systemd Service: systemd.md
```

**Key configuration notes:**
- `reconfigure_material: true` — lets the plugin automatically inject the language switcher into the Material header [CITED: ultrabug.github.io/mkdocs-static-i18n/setup/setting-up-material/]
- `navigation.instant` must NOT be enabled — incompatible with multi-language switcher [CITED: ultrabug.github.io/mkdocs-static-i18n/setup/setting-up-material/]
- `site_url` must be set for language alternates to generate correctly [ASSUMED]
- `{github-username}` is a placeholder — the planner must substitute the actual GitHub username from the repo remote URL

### Pattern 2: GitHub Actions Deployment Workflow

**What:** Push to `main` triggers MkDocs build and deploy to `gh-pages` branch. Official Material docs pattern.

**Example `.github/workflows/docs.yml`:**
```yaml
# Source: https://squidfunk.github.io/mkdocs-material/publishing-your-site/
name: docs
on:
  push:
    branches:
      - main
permissions:
  contents: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure Git Credentials
        run: |
          git config user.name github-actions[bot]
          git config user.email 41898282+github-actions[bot]@users.noreply.github.com
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: echo "cache_id=$(date --utc '+%V')" >> $GITHUB_ENV
      - uses: actions/cache@v4
        with:
          key: mkdocs-material-${{ env.cache_id }}
          path: ~/.cache
          restore-keys: |
            mkdocs-material-
      - run: pip install mkdocs-material mkdocs-static-i18n
      - run: mkdocs gh-deploy --force
```

**Notes:**
- `permissions: contents: write` is required — GitHub Pages deploy pushes to `gh-pages` branch
- Weekly cache key (`%V` = ISO week number) balances freshness vs. speed [CITED: squidfunk.github.io/mkdocs-material/publishing-your-site/]
- GitHub repository Settings > Pages must be configured to serve from `gh-pages` branch (one-time manual step)

### Pattern 3: systemd Service File Template

**What:** `contrib/luxtronik2-modbus-proxy.service` — a template users copy to `/etc/systemd/system/` and customize.

**Example:**
```ini
# contrib/luxtronik2-modbus-proxy.service
# Copy to /etc/systemd/system/ and adjust ExecStart path and EnvironmentFile.
# Run: sudo systemctl daemon-reload && sudo systemctl enable --now luxtronik2-modbus-proxy

[Unit]
Description=Luxtronik 2.0 to Modbus TCP Proxy
Documentation=https://{github-username}.github.io/PUBLIC-luxtronik2-modbus-proxy/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
# Run as dedicated non-root user (create with: sudo useradd -r -s /bin/false luxtronik-proxy)
User=luxtronik-proxy
Group=luxtronik-proxy
# Optional: override config path via environment file
# EnvironmentFile=-/etc/luxtronik2-modbus-proxy/env
ExecStart=/usr/local/bin/luxtronik2-modbus-proxy --config /etc/luxtronik2-modbus-proxy/config.yaml
Restart=on-failure
RestartSec=10
# structlog JSON output goes to journald automatically — no LogFile needed

[Install]
WantedBy=multi-user.target
```

**Key design choices:**
- `After=network-online.target` + `Wants=network-online.target` — proxy cannot function without network; `Wants` (not `Requires`) avoids boot failure if network-online is not enabled [CITED: systemd.io/NETWORK_ONLINE/]
- `EnvironmentFile=-/etc/...` — the `-` prefix makes the file optional; if absent, service still starts [ASSUMED based on systemd documentation convention]
- `Type=simple` — proxy does not fork; asyncio event loop blocks in ExecStart [ASSUMED]
- `Restart=on-failure` — recovers from transient Luxtronik connection failures without restart loops [ASSUMED]
- Dedicated system user (`-r` for system account, `-s /bin/false` no login shell) mirrors Docker's `appuser` UID 1000 pattern
- Config path convention: `/etc/luxtronik2-modbus-proxy/config.yaml` — standard Linux system config location [ASSUMED]

### Pattern 4: README Badge Block

**Standard shields.io badges for this project:**
```markdown
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-supported-blue)
```

**Or using dynamic badges from PyPI/GitHub once published:**
```markdown
[![PyPI](https://img.shields.io/pypi/v/luxtronik2-modbus-proxy)](https://pypi.org/project/luxtronik2-modbus-proxy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
```

For v1 (not yet on PyPI), use static badges. [ASSUMED — PyPI publication is out of scope for Phase 3]

### Pattern 5: ASCII Architecture Diagram for README

**What the proxy does (from existing ha-coexistence.md diagram as reference):**
```
Luxtronik 2.0        luxtronik2-modbus-proxy        Modbus clients
Controller     <-->  (connects briefly, disconnects)  <-->  evcc
port 8889            port 502 (Modbus TCP server)          Home Assistant
```

**Expanded ASCII for README:**
```
  ┌─────────────────────┐         ┌──────────────────────┐
  │  Luxtronik 2.0      │ <─────> │  luxtronik2-         │ <── evcc
  │  Heat Pump          │         │  modbus-proxy         │
  │  port 8889          │         │  port 502 (Modbus TCP)│ <── Home Assistant
  └─────────────────────┘         └──────────────────────┘
  proprietary binary protocol          standard Modbus TCP
  (connect → read/write → disconnect)
```

The exact layout is Claude's Discretion — the content above captures the required information elements.

### Anti-Patterns to Avoid

- **Putting MkDocs tools in pyproject.toml dependencies:** They are build-time docs tools, not runtime requirements. Keep them only in the GitHub Actions workflow and developer setup notes.
- **Using `navigation.instant` with `mkdocs-static-i18n`:** Explicitly incompatible — causes language switcher to fail [CITED: mkdocs-static-i18n docs].
- **Real IP addresses or hostnames in docs:** The pre-commit hook blocks these. All examples must use `192.168.x.x` or `heatpump.example.local`.
- **Separate `mkdocs.yml` per language:** The `mkdocs-static-i18n` folder mode handles both languages from a single config — do not create per-language config files.
- **Forgetting `site_url` in mkdocs.yml:** Without it, language alternate links in the switcher are broken.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Language switcher in header | Custom HTML/JS toggle | `mkdocs-static-i18n` with `reconfigure_material: true` | Plugin injects Material-native language selector automatically |
| Multi-language URL routing | Custom nginx rules or redirects | Plugin's `docs_structure: folder` + `site_url` | Plugin generates `/` for EN and `/de/` for DE with correct `<link rel="alternate">` tags |
| Search in both languages | Custom search index | Material built-in search plugin | Material's search works across all built pages including DE |
| CI/CD doc deploy pipeline | Custom deploy script | `mkdocs gh-deploy --force` via GitHub Actions | One command handles build + commit + push to gh-pages |

**Key insight:** The entire MkDocs + i18n + GitHub Pages pipeline is solved by three tools and one YAML file. The only custom work in this phase is writing content.

---

## Common Pitfalls

### Pitfall 1: `docs_dir` and folder structure mismatch
**What goes wrong:** `mkdocs.yml` `docs_dir: docs` with `docs_structure: folder` expects language folders directly inside `docs/`. If `docs_dir` is set to `docs/en`, the plugin only sees EN content.
**Why it happens:** The plugin walks `docs_dir` looking for locale-named subdirectories (`en/`, `de/`). If `docs_dir` already points inside a language folder, the plugin finds nothing.
**How to avoid:** Set `docs_dir: docs` (the parent of `en/` and `de/`). The plugin then treats `docs/en/` and `docs/de/` as language roots.
**Warning signs:** Language switcher appears but DE pages return 404; plugin logs show "no alternate found".

### Pitfall 2: Missing `index.md` in both language folders
**What goes wrong:** MkDocs build fails or the home page 404s for DE.
**Why it happens:** MkDocs requires an `index.md` (or `README.md`) as the root document. The plugin needs one per language folder.
**How to avoid:** Create `docs/en/index.md` and `docs/de/index.md` as the first files. Both must exist before `mkdocs build` runs.
**Warning signs:** `ERROR - Config value 'docs_dir': The 'index.md' file must exist.`

### Pitfall 3: `navigation.instant` breaks language switcher
**What goes wrong:** Language switcher links in the header do not update correctly during page navigation — language switch goes to wrong page or drops query params.
**Why it happens:** Material's instant navigation intercepts link clicks at the JS level before the plugin's per-page alternate URLs are resolved.
**How to avoid:** Do not add `navigation.instant` to `theme.features` in `mkdocs.yml`.
**Warning signs:** Clicking DE in the language switcher always goes to `/de/` root rather than the current page's DE equivalent.

### Pitfall 4: GitHub Pages not configured to serve `gh-pages` branch
**What goes wrong:** GitHub Actions workflow succeeds (commits to `gh-pages` branch) but the site is never served at `{user}.github.io/{repo}`.
**Why it happens:** GitHub Pages requires a one-time manual configuration in repository Settings > Pages > Source > Branch: `gh-pages`.
**How to avoid:** Document this as a manual step in the developer quickstart. It cannot be automated by `mkdocs gh-deploy`.
**Warning signs:** Workflow green, but site returns 404.

### Pitfall 5: systemd `EnvironmentFile` vs. `Environment`
**What goes wrong:** Environment variables set in `config.yaml` (for pydantic-settings `LUXTRONIK_HOST` override) are not picked up by the service.
**Why it happens:** `Environment=` in the unit file sets a single variable directly. `EnvironmentFile=` reads from a file of `KEY=VALUE` pairs. pydantic-settings uses `LUXTRONIK_` prefix env vars — users who want Docker-style env var overrides need `EnvironmentFile`.
**How to avoid:** Use `EnvironmentFile=-/etc/luxtronik2-modbus-proxy/env` (the `-` makes it optional). Document the format in `systemd.md`.
**Warning signs:** Service starts but proxy ignores env var config overrides.

### Pitfall 6: Docs example code with real IPs
**What goes wrong:** Pre-commit hook blocks the commit.
**Why it happens:** Any IPv4 pattern matching `\d+\.\d+\.\d+\.\d+` (other than placeholder patterns) triggers the hook.
**How to avoid:** Use `192.168.x.x` everywhere in docs examples. Never use a real IP even as an illustration.
**Warning signs:** `git commit` exits non-zero with "sensitive pattern detected".

### Pitfall 7: mkdocs-static-i18n nav with folder structure
**What goes wrong:** Navigation entries referencing `en/quickstart.md` cause build errors.
**Why it happens:** When `docs_structure: folder`, nav paths are relative to the language folder root, not `docs_dir`. `quickstart.md` (not `en/quickstart.md`) is correct.
**How to avoid:** In `mkdocs.yml` nav section, reference files without the language prefix: `- Quick Start: quickstart.md`.
**Warning signs:** `WARNING - A relative path to 'en/quickstart.md' is included in the 'nav' configuration.`

---

## Code Examples

Verified patterns from official sources:

### Minimal working mkdocs.yml (verified structure)
```yaml
# Source: https://squidfunk.github.io/mkdocs-material/creating-your-site/
#         https://ultrabug.github.io/mkdocs-static-i18n/getting-started/quick-start/
site_name: luxtronik2-modbus-proxy
site_url: https://OWNER.github.io/PUBLIC-luxtronik2-modbus-proxy/
docs_dir: docs
theme:
  name: material
plugins:
  - search
  - i18n:
      docs_structure: folder
      reconfigure_material: true
      languages:
        - locale: en
          default: true
          name: English
          build: true
        - locale: de
          name: Deutsch
          build: true
nav:
  - Home: index.md
  - Quick Start: quickstart.md
  - User Guide: user-guide.md
  - evcc Integration: evcc-integration.md
  - HA Coexistence: ha-coexistence.md
  - systemd Service: systemd.md
```

### Docker quick-start block for README (3 lines)
```bash
cp config.example.yaml config.yaml
# Edit config.yaml: set luxtronik_host to your heat pump's IP
docker compose up -d
```

### systemd install sequence for user-guide
```bash
# Create dedicated system user
sudo useradd -r -s /bin/false luxtronik-proxy

# Install config
sudo mkdir -p /etc/luxtronik2-modbus-proxy
sudo cp config.example.yaml /etc/luxtronik2-modbus-proxy/config.yaml
sudo nano /etc/luxtronik2-modbus-proxy/config.yaml  # set luxtronik_host

# Install service file
sudo cp contrib/luxtronik2-modbus-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now luxtronik2-modbus-proxy
sudo systemctl status luxtronik2-modbus-proxy
```

### Developer quickstart commands
```bash
git clone https://github.com/OWNER/PUBLIC-luxtronik2-modbus-proxy.git
cd PUBLIC-luxtronik2-modbus-proxy
pip install -e ".[dev]"
cp config.example.yaml config.yaml
# Edit config.yaml: set luxtronik_host
luxtronik2-modbus-proxy --config config.yaml
```

### Journald log viewing for systemd section
```bash
# Follow live logs
journalctl -u luxtronik2-modbus-proxy -f

# Show last 50 lines
journalctl -u luxtronik2-modbus-proxy -n 50

# JSON output (structlog format)
journalctl -u luxtronik2-modbus-proxy -o json-pretty | head -40
```

---

## Content Inventory: What Exists vs. What Needs Writing

### Existing content to integrate (carry through, no rewrite needed)
| File | Status | Action |
|------|--------|--------|
| `docs/en/evcc-integration.md` | Complete and current | Add to mkdocs.yml nav; translate to DE |
| `docs/en/ha-coexistence.md` | Complete and current | Add to mkdocs.yml nav; translate to DE |
| `config.example.yaml` | Well-commented | Reference in user-guide (do not duplicate) |
| `Dockerfile` | Working | Reference Docker commands in quickstart |
| `docker-compose.yml` | Working (`docker compose up -d`) | Show in README quick-start block |

### Content that must be written from scratch
| File | Audience | Language | Key Content |
|------|----------|----------|-------------|
| `docs/en/index.md` | All users | EN | What is the proxy, who is it for, quick navigation to guides |
| `docs/de/index.md` | All users | DE | Mirror of EN index in German |
| `docs/en/quickstart.md` | Developer | EN | Clone, install, run against test controller in <15 min |
| `docs/de/quickstart.md` | Developer | DE | Mirror of EN quickstart |
| `docs/en/user-guide.md` | End user (non-technical) | EN | Prerequisites, Docker install, config.yaml walkthrough, validation |
| `docs/de/user-guide.md` | End user (non-technical, German-speaking) | DE | Mirror of EN user-guide |
| `docs/en/systemd.md` | End user (Linux) | EN | Alternative to Docker: user creation, service install, log viewing |
| `docs/de/systemd.md` | End user (Linux, German) | DE | Mirror of EN systemd |
| `docs/de/evcc-integration.md` | evcc users | DE | Translation of existing EN file |
| `docs/de/ha-coexistence.md` | HA users | DE | Translation of existing EN file |
| `README.md` | All | EN | Badge block, 1-para description, ASCII diagram, 3-line quick-start, links |
| `README.de.md` | German speakers | DE | Mirror of README.md in German, with EN link at top |
| `mkdocs.yml` | Build system | — | MkDocs configuration (see Pattern 1) |
| `contrib/luxtronik2-modbus-proxy.service` | Linux users | — | systemd unit template |
| `.github/workflows/docs.yml` | CI/CD | — | GitHub Actions deploy workflow |

---

## Documentation Content Guide

### quickstart.md scope (developer audience, <15 min goal)
Must cover:
1. Prerequisites: Python 3.10+, pip, Docker (optional for Docker track)
2. Clone and install: `pip install -e ".[dev]"` — the dev extra installs all tools
3. Copy and edit config: `cp config.example.yaml config.yaml`, set `luxtronik_host`
4. Run: `luxtronik2-modbus-proxy --config config.yaml`
5. Verify: connect a Modbus client to port 502, read a holding register
6. Optional: run tests with `pytest`

Reference: `pyproject.toml` for exact dev dependency list and entry point name (`luxtronik2-modbus-proxy`).

### user-guide.md scope (non-technical end-user, Docker + systemd tracks)
Must cover:
1. What does the proxy do (one paragraph, no jargon)
2. Prerequisites: Docker OR a Linux machine with systemd
3. Docker track: copy config.example.yaml, edit `luxtronik_host`, `docker compose up -d`
4. Config reference: explain every field in `config.example.yaml` (all 7 fields) in plain language
5. Validating it works: `docker logs`, check a Modbus client connects
6. Pointing evcc or HA at the proxy (brief — "see evcc Integration guide for full details")

The `config.example.yaml` is the authoritative reference — user-guide explains it, does not duplicate it.

### systemd.md scope (Linux end-user, systemd deployment)
Must cover:
1. When to use systemd vs. Docker (decision guide)
2. Install prerequisites: `pip install luxtronik2-modbus-proxy` (or from git)
3. Create system user
4. Install config to `/etc/luxtronik2-modbus-proxy/config.yaml`
5. Install `contrib/luxtronik2-modbus-proxy.service` to `/etc/systemd/system/`
6. Enable and start: `systemctl enable --now`
7. View logs: `journalctl -u luxtronik2-modbus-proxy -f`
8. Troubleshooting: service won't start, connection refused, log reading

Reference: `Dockerfile` for the expected user setup pattern (non-root, UID 1000).

### Proxy startup sequence (for documentation reference)
From `src/luxtronik2_modbus_proxy/main.py`:
1. Load + validate config (pydantic validation — fails fast on bad config)
2. Configure structlog logging
3. Create register map, write queue, register cache, Luxtronik client
4. Create polling engine + Modbus TCP server
5. Register SIGTERM handler
6. Run Modbus server + polling engine concurrently (asyncio)

Log events visible in journald: `proxy_starting`, `proxy_running`, `poll_interval_low` (warning), `proxy_shutting_down`, `proxy_stopped`.

### Config fields to document in user-guide
From `src/luxtronik2_modbus_proxy/config.py` (authoritative):
| Field | Default | Description |
|-------|---------|-------------|
| `luxtronik_host` | required | IP address or hostname of Luxtronik controller |
| `luxtronik_port` | 8889 | Luxtronik binary protocol port (do not change) |
| `modbus_port` | 502 | Modbus TCP server port |
| `bind_address` | 0.0.0.0 | Network interface to listen on |
| `poll_interval` | 30 | Polling interval in seconds (min 10) |
| `log_level` | INFO | DEBUG/INFO/WARNING/ERROR |
| `enable_writes` | false | Allow Modbus write commands (SG-ready) |
| `write_rate_limit` | 60 | Min seconds between writes (protects controller NAND) |
| `registers.parameters` | [] | Extra Luxtronik parameter names to expose |
| `sg_ready_mode_map` | null | Custom SG-ready mode mapping (override default) |

Environment variable overrides use `LUXTRONIK_` prefix: `LUXTRONIK_HOST`, `LUXTRONIK_POLL_INTERVAL`, etc.

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `mkdocs-material` 8.x | 9.7.6 | 9.x is current stable; 9.7.0 is last feature release (team moving to Zensical); security patches until Nov 2026 |
| `mkdocs-static-i18n` 0.x | 1.3.1 | 1.0.0 introduced breaking config changes (list syntax for languages, not dict); use current syntax |
| Per-language `mkdocs.yml` | Single `mkdocs.yml` + plugin | Plugin handles all language routing from one config |

**Deprecated/outdated:**
- `mkdocs-static-i18n` < 1.0: Configuration syntax changed in 1.0 — old dict-style `languages:` is invalid; use list syntax with `locale:`, `name:`, `build:` keys [CITED: pypi.org/project/mkdocs-static-i18n]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `site_url` must be set for language alternate links to work correctly | Architecture Patterns P1 | Build succeeds but language switcher links may be wrong; low risk — easy fix |
| A2 | `EnvironmentFile=-/path` (dash prefix) makes the file optional | Pattern 3 systemd | Service fails to start if env file is absent but required; low risk — file is documented as optional |
| A3 | `Type=simple` is correct for asyncio event loop blocking ExecStart | Pattern 3 systemd | Service might be misclassified by systemd; low risk — simple works for non-forking processes |
| A4 | `Restart=on-failure` does not cause restart loops on config errors | Pattern 3 systemd | Service could loop if config is invalid; mitigated by adding `StartLimitIntervalSec` |
| A5 | Config path convention `/etc/luxtronik2-modbus-proxy/config.yaml` | Pattern 3 systemd | User could place config elsewhere; this is a recommendation, not a constraint |
| A6 | PyPI publication is out of scope for Phase 3 | Badge Patterns | If PyPI publish is in scope, dynamic badges should replace static ones |
| A7 | `docs/de/` directory already exists (per CONTEXT.md D-01) | Directory Structure | If it doesn't exist, Wave 0 must create it |
| A8 | `OWNER` placeholder in mkdocs.yml site_url must be replaced with actual GitHub username | Architecture Patterns | Site deploys to wrong URL; planner must note this as a required substitution |

---

## Open Questions

1. **GitHub repository owner/username**
   - What we know: The repo is `PUBLIC-luxtronik2-modbus-proxy` on GitHub
   - What's unclear: The GitHub username/org is not in any project file (CLAUDE.md prohibits real names)
   - Recommendation: Planner should add a task step: "substitute `OWNER` placeholder in mkdocs.yml `site_url` with actual GitHub username before first deploy"

2. **Does `docs/de/` directory already exist?**
   - What we know: CONTEXT.md D-01 states DE directory exists; the `ls` of `docs/de/` returned empty (no files) but no error
   - What's unclear: Whether the empty directory is tracked in git (empty dirs are not tracked without a `.gitkeep`)
   - Recommendation: Wave 0 task should `mkdir -p docs/de/` to ensure it exists; idempotent

3. **PyPI publication scope**
   - What we know: `pyproject.toml` defines `name = "luxtronik2-modbus-proxy"` and `version = "0.1.0"`
   - What's unclear: Whether Phase 3 includes publishing to PyPI, or just GitHub Pages
   - Recommendation: Based on requirements (DOCS-01 through DOCS-04, DEPLOY-02), PyPI is NOT required. README can reference GitHub install (`pip install git+https://...`) rather than PyPI badges for v1.

4. **`StartLimitIntervalSec` for systemd service**
   - What we know: `Restart=on-failure` with invalid config could cause restart loops
   - What's unclear: Whether to add `StartLimitIntervalSec=60` and `StartLimitBurst=3` as safety defaults
   - Recommendation: Include these in the service template as a best practice — they cap restart attempts

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.10+ | Docs build, developer setup | Available | 3.10.12 | — |
| pip | Installing mkdocs tools | Available | 22.0.2 | — |
| `mkdocs-material` | GitHub Pages build | Not installed locally | 9.7.6 on PyPI | Install via `pip install` |
| `mkdocs-static-i18n` | Language switching | Not installed locally | 1.3.1 on PyPI | Install via `pip install` |
| Git | GitHub Actions deploy | Available (git repo) | — | — |
| GitHub Actions | Automated docs deploy | Not configured | — | Manual `mkdocs gh-deploy` from dev machine |
| `.github/workflows/` dir | CI/CD | Does not exist | — | Create directory in Wave 0 |

**Missing with no fallback:** None — all missing items can be installed or created.

**Missing with fallback:**
- GitHub Actions workflow: Can run `mkdocs gh-deploy --force` manually from dev machine as a fallback if GitHub Actions setup is deferred.

---

## Validation Architecture

> `nyquist_validation` is set to `false` in `.planning/config.json`. This section is skipped.

---

## Security Domain

Documentation phase. No new network-exposed code, authentication, or data processing surfaces introduced.

**ASVS categories applicable:** None — this phase produces only static files and a systemd template. The proxy's security posture (no auth, local network only, rate-limited writes) is documented in user-guide, not changed.

**Documentation security checklist:**
- [ ] All IP addresses in examples use placeholder form (`192.168.x.x`)
- [ ] No real hostnames, credentials, or tokens in any documentation file
- [ ] Pre-commit hook will block non-compliant commits — no special handling needed

---

## Sources

### Primary (HIGH confidence)
- [mkdocs-material PyPI](https://pypi.org/project/mkdocs-material/) — version 9.7.6, released Mar 19 2026; Python >=3.8
- [mkdocs-static-i18n PyPI](https://pypi.org/project/mkdocs-static-i18n/) — version 1.3.1, released Feb 20 2026
- [MkDocs PyPI](https://pypi.org/project/mkdocs/) — version 1.6.1, released Aug 30 2024
- [Material for MkDocs: Publishing your site](https://squidfunk.github.io/mkdocs-material/publishing-your-site/) — GitHub Actions workflow YAML
- [mkdocs-static-i18n: Setting up with Material](https://ultrabug.github.io/mkdocs-static-i18n/setup/setting-up-material/) — `reconfigure_material` option and language switcher
- [mkdocs-static-i18n: Quick Start](https://ultrabug.github.io/mkdocs-static-i18n/getting-started/quick-start/) — folder structure configuration

### Secondary (MEDIUM confidence)
- [systemd NETWORK_ONLINE](https://systemd.io/NETWORK_ONLINE/) — `After=network-online.target` semantics; `Wants` vs. `Requires`
- [mkdocs-material 2026 changelog](https://squidfunk.github.io/mkdocs-material/blog/archive/2026/) — 9.7.x is last feature release; security patches until Nov 2026

### Tertiary (LOW confidence)
- WebSearch results on systemd EnvironmentFile patterns — cross-referenced with systemd man page patterns

---

## Metadata

**Confidence breakdown:**
- Standard stack (MkDocs, Material, i18n): HIGH — verified against PyPI release dates and official docs
- Architecture patterns (mkdocs.yml, GitHub Actions): HIGH — pulled from official Material docs
- systemd service file: MEDIUM — pattern is standard but specific flag combinations (A2, A3, A4) are ASSUMED
- Documentation content scope: HIGH — derived directly from existing source code and config files in repo
- Pitfalls: HIGH for MkDocs (verified against plugin docs); MEDIUM for systemd (assumed from general knowledge)

**Research date:** 2026-04-06
**Valid until:** 2026-10-06 (MkDocs Material entering maintenance mode Nov 2026; i18n plugin stable)
