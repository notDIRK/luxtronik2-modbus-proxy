# Phase 3: Documentation and Release - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-06
**Phase:** 03-documentation-and-release
**Areas discussed:** Docs-Struktur, README-Umfang, GitHub Pages, systemd Service

---

## Docs-Struktur

| Option | Description | Selected |
|--------|-------------|----------|
| Ein File pro Thema | docs/en/ und docs/de/ spiegeln sich 1:1. Einzelne Dateien pro Thema. Vorhandene Docs bleiben. | ✓ |
| Ein grosses Guide-Dokument | Alles in einer grossen Datei pro Sprache. Einfacher zu pflegen, schwerer zu navigieren. | |
| MkDocs-Kapitelstruktur | Kapitel in Unterordnern. Mehr Struktur, aber erst bei GitHub Pages sinnvoll. | |

**User's choice:** Claude's discretion — user delegated all decisions
**Notes:** One-file-per-topic chosen for maintainability and natural MkDocs integration. Existing Phase 2 docs stay in place.

---

## README-Umfang

| Option | Description | Selected |
|--------|-------------|----------|
| Kompaktes README mit Badges + Quick-Start | Badges, 1-Absatz Beschreibung, ASCII-Diagramm, Docker 3-Zeiler, Links zu Guides | ✓ |
| Ausführliches README als Hauptdokumentation | README als primäre Doku, Guides nur als Ergänzung | |
| Minimales README nur mit Links | Nur Projektname + Links zu docs/ und GitHub Pages | |

**User's choice:** Claude's discretion — user delegated all decisions
**Notes:** Compact README with architecture diagram balances immediate usefulness with pointing to detailed guides.

---

## GitHub Pages

| Option | Description | Selected |
|--------|-------------|----------|
| MkDocs + Material Theme | Standard für Python-Projekte, eingebaute Suche, i18n Plugin für DE/EN | ✓ |
| Jekyll (GitHub default) | Kein Build-Step nötig, aber weniger Features für technische Docs | |
| Einfaches Markdown ohne Generator | Kein Tooling-Overhead, aber keine Suche, kein Theme, keine Navigation | |

**User's choice:** Claude's discretion — user delegated all decisions
**Notes:** MkDocs Material is the ecosystem standard for Python projects. i18n plugin handles language switching cleanly.

---

## systemd Service

| Option | Description | Selected |
|--------|-------------|----------|
| Template Service-File in contrib/ | EnvironmentFile für Config, dedicated User, After=network-online.target | ✓ |
| Installationsscript mit auto-Setup | Script erstellt User, kopiert Service-File, enabled Service | |
| Nur Dokumentation, kein Service-File | Anleitung zum Erstellen des Service-Files selbst | |

**User's choice:** Claude's discretion — user delegated all decisions
**Notes:** Template file in contrib/ is the standard approach — users copy and adapt. Auto-install scripts are fragile across distributions.

---

## Claude's Discretion

- All four areas decided by Claude at user's explicit request
- MkDocs plugin versions, badge selection, GitHub Actions workflow details
- Exact ASCII diagram layout, documentation tone and depth
- User preference: autonomous development, only ask when critical

## Deferred Ideas

- Community announcements (evcc, HA, haustechnikdialog.de) — v2
- evcc upstream heater template PR — v2
- HA HACS custom component — v2
