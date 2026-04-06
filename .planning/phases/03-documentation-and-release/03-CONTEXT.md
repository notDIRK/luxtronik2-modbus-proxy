# Phase 3: Documentation and Release - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Bilingual user and developer documentation (EN + DE), systemd service deployment, and a GitHub Pages project homepage. A non-technical user can install, configure, and validate the proxy from published documentation alone, in either English or German, without reading source code.

</domain>

<decisions>
## Implementation Decisions

### Documentation Structure
- **D-01:** One markdown file per topic in `docs/en/` and `docs/de/`, mirrored 1:1 between languages — existing `evcc-integration.md` and `ha-coexistence.md` stay in place
- **D-02:** New files: `quickstart.md` (developer track), `user-guide.md` (end-user track), `systemd.md` (systemd deployment) — each in both language directories
- **D-03:** EN is the source language; DE translations mirror structure and headings exactly

### README Design
- **D-04:** Compact `README.md` (EN) with: project badges (Python version, license, Docker), one-paragraph description, ASCII architecture diagram, 3-line Docker quick-start, and links to full guides in `docs/en/`
- **D-05:** `README.de.md` mirrors `README.md` in German with a "Read in English" link at the top; pyproject.toml `readme` field stays pointing to `README.md`
- **D-06:** Architecture diagram as ASCII art in README — shows Luxtronik controller <-> Proxy <-> Modbus clients (evcc, HA) data flow

### GitHub Pages
- **D-07:** MkDocs with Material theme — standard for Python open-source projects, built-in search, responsive design
- **D-08:** Language switching via MkDocs i18n plugin (`mkdocs-static-i18n`) — EN as default, DE as alternate
- **D-09:** Deployment via GitHub Actions workflow (`mkdocs gh-deploy`) on push to main branch
- **D-10:** Navigation: Home, Quick Start (Developer), User Guide, evcc Integration, HA Coexistence, systemd Service
- **D-11:** `mkdocs.yml` configuration file at project root

### systemd Service
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing documentation (Phase 2 output)
- `docs/en/evcc-integration.md` — evcc YAML configuration guide, must be integrated into MkDocs navigation
- `docs/en/ha-coexistence.md` — HA BenPru coexistence guide, must be integrated into MkDocs navigation

### Project configuration
- `config.example.yaml` — Documented config file that user guides reference for setup instructions
- `Dockerfile` — Docker deployment reference for user guide Docker track
- `docker-compose.yml` — Docker Compose reference for quick-start instructions
- `pyproject.toml` — Project metadata, `readme` field, entry point definition

### Requirements
- `.planning/REQUIREMENTS.md` — DOCS-01, DOCS-02, DOCS-03, DOCS-04, DEPLOY-02 define Phase 3 acceptance criteria

### Source code (for architecture diagram and feature descriptions)
- `src/luxtronik2_modbus_proxy/main.py` — CLI entry point, startup sequence
- `src/luxtronik2_modbus_proxy/config.py` — All configurable options (referenced in user guide)
- `src/luxtronik2_modbus_proxy/sg_ready.py` — SG-ready feature (referenced in evcc integration docs)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/en/evcc-integration.md`: Complete evcc integration guide — integrate into MkDocs nav, translate to DE
- `docs/en/ha-coexistence.md`: Complete HA coexistence guide — integrate into MkDocs nav, translate to DE
- `config.example.yaml`: Well-commented config — user guide can reference it directly
- `Dockerfile` + `docker-compose.yml`: Working Docker deployment — quick-start can show exact commands

### Established Patterns
- Code is US English throughout — docs follow same convention for EN track
- structlog with JSON output — journald integration works naturally, no special config
- pydantic-settings with YAML config — user guide explains config.yaml, env var overrides for Docker
- CLI entry point `luxtronik2-modbus-proxy` with `--config` flag — documented in Dockerfile CMD

### Integration Points
- `pyproject.toml` `readme` field: must point to `README.md`
- GitHub repository settings: enable GitHub Pages from `gh-pages` branch (MkDocs default)
- `mkdocs.yml` at project root: new file, configures site navigation and theme
- `contrib/` directory: new directory for systemd service file template
- `.github/workflows/`: new directory for GitHub Actions MkDocs deployment

</code_context>

<specifics>
## Specific Ideas

- User preference: autonomous development — Claude decides independently, only asks when absolutely critical
- Target audience for end-user guide: German-speaking heat pump owner with no Python background
- Target audience for developer quickstart: English-speaking developer who wants to build/contribute
- Architecture diagram should make the proxy's role immediately clear: Luxtronik (port 8889) <-> Proxy <-> Modbus clients (port 502)

</specifics>

<deferred>
## Deferred Ideas

- Community announcements (evcc forum, HA forum, haustechnikdialog.de) — tracked as COMM-10 in v2 requirements
- evcc upstream heater template PR — tracked as INTEG-10 in v2 requirements
- HA HACS custom component — tracked as INTEG-11 in v2 requirements

</deferred>

---

*Phase: 03-documentation-and-release*
*Context gathered: 2026-04-06*
