---
phase: 03-documentation-and-release
plan: "04"
subsystem: documentation
tags: [readme, docs, github, bilingual]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [project-readme-en, project-readme-de]
  affects: [github-landing-page, pypi-readme]
tech_stack:
  added: []
  patterns: [bilingual-readme, badges, ascii-diagram]
key_files:
  created:
    - README.md
    - README.de.md
  modified: []
decisions:
  - "ASCII architecture diagram used over image for VCS-friendly, renderable-everywhere approach"
  - "German prose uses 'ue/oe/ae' ASCII substitutes instead of UTF-8 umlauts to ensure broad compatibility"
metrics:
  duration_seconds: 75
  completed_date: "2026-04-06"
  tasks_completed: 2
  files_changed: 2
---

# Phase 3 Plan 4: README Files (EN + DE) Summary

English and German README files at project root with badges, ASCII architecture diagram, 3-line Docker quick-start, feature list, and links to full MkDocs documentation site.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create README.md with badges, architecture diagram, and quick-start | 6f29675 | README.md |
| 2 | Create README.de.md mirroring English README | 7465b7b | README.de.md |

## What Was Built

### README.md (English)

- Badge block: Python 3.10+, MIT license, Docker (three shields.io badges)
- Title and German language link to README.de.md
- One-paragraph description covering target heat pump brands and use cases
- ASCII architecture diagram showing port 8889 (Luxtronik) and port 502 (Modbus TCP) with evcc and Home Assistant as clients
- 3-line Docker quick-start (`cp config.example.yaml`, edit comment, `docker compose up -d`)
- Six feature bullets covering FC support, connect-and-release polling, SG-ready, 1,126 params, YAML config, Docker/systemd
- Documentation links to all five `docs/en/` guides
- MIT license section

### README.de.md (German)

- "Read in English" link to README.md as the very first line
- Same badge block (language-neutral)
- German prose translation of description, quick-start explanatory text, features list
- Same ASCII architecture diagram (code unchanged)
- Documentation links to all five `docs/de/` counterparts
- German section headings (Architektur, Schnellstart, Funktionen, Dokumentation, Lizenz)

## Verification Results

| Check | Result |
|-------|--------|
| Both README files exist | PASS |
| README.md: 3 shields.io badges | PASS (count=3) |
| README.de.md: 5 docs/de/ links | PASS (count=5) |
| README.md: 5 docs/en/ links | PASS (count=5) |
| No real IP addresses in either file | PASS |
| pyproject.toml readme field unchanged | PASS (still "README.md") |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - README files are complete and accurate for the v1 shipped feature set.

## Threat Flags

No new security-relevant surface introduced. README files are static documentation only.
T-03-08 (Information Disclosure) mitigated: all examples use placeholder values, no credentials or real network addresses.

## Self-Check: PASSED

- README.md exists: FOUND
- README.de.md exists: FOUND
- Commit 6f29675 exists: FOUND
- Commit 7465b7b exists: FOUND
