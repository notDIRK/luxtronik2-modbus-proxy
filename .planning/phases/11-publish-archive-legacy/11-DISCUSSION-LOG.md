# Phase 11: Publish & Archive Legacy - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in 11-CONTEXT.md — this log preserves the reasoning.

**Date:** 2026-04-10
**Phase:** 11-publish-archive-legacy
**Mode:** discuss (--auto, --chain)
**Invoked by:** user ("machen weiter und beantworte du alle fragen go phase 11")

## Gray Areas Auto-Resolved

All gray areas resolved with recommended defaults per `--auto` contract. User memory `feedback_autonomous.md` grants Claude authority to decide autonomously on non-critical items; the one critical decision (irreversible archive) is surfaced as a human gate (D-23) instead of being auto-decided.

| # | Area | Options Considered | Chosen (Recommended) | Rationale |
|---|------|---|---|---|
| 1 | Order of operations | (a) Create repo → push → banner → archive / (b) Banner first → archive → create new repo / (c) Parallel | (a) Strict sequential, halt-on-fail | Reversible steps first, irreversible last; minimizes blast radius if anything fails mid-flow |
| 2 | Repo creation tool | (a) `gh repo create --source --push` / (b) Manual web UI + `git push` / (c) Terraform / API | (a) gh single command | Already authenticated; single atomic operation; scriptable; matches user memory `reference_github.md` |
| 3 | New repo visibility | Public / Private | Public | SPLIT-01 requires public; project is open source MIT |
| 4 | License | MIT / Apache-2.0 / GPL | MIT | Matches `luxtronik` library ecosystem per PROJECT.md |
| 5 | Default branch | `master` / `main` | `master` | Matches existing filter-repo extracted working copy; renaming mid-rebrand adds churn |
| 6 | Repo topics | Minimal / Rich | Rich (7 topics) | Discoverability for HA users searching HACS + heat pump brands |
| 7 | Push scope | `master` only / `--all --tags` / `master + --tags` | `master + --tags` | Only branch in working copy; tags preserved from Phase 8 filter-repo |
| 8 | Release tagging | Cut `v1.2.0` release now / Defer to post-Phase-12 | Defer | HACS custom repo installs work without releases; cutting a release pre-verification risks a yank |
| 9 | Manifest version bump | Bump to 1.2.0 / Leave at 1.1.2 | Leave at 1.1.2 | Version bump belongs to the release phase, not publish phase; keeps Phase 12 verification clean |
| 10 | Banner placement | Top of README / Dedicated section / Separate file | Top of README, above title | Maximum visibility — users see warning before anything else |
| 11 | Banner content EN | Terse one-liner / Structured warning block | Structured block with header, forward link, niche-use caveat | Terse loses context; niche-use caveat preserves evcc-standalone users |
| 12 | Banner content DE | Machine translation / Hand-written semantic mirror | Semantic mirror | User memory: German speaker, quality matters; machine translation produces awkward German |
| 13 | Banner commit | Single commit both READMEs / Separate commits / Bundle with other changes | Single commit both READMEs | Atomic doc change; matches project's EN+DE lockstep pattern |
| 14 | Secret scan | Pre-commit hook only / Manual grep / Both | Both | Defense in depth; SPLIT-01 and CLAUDE.md mandate scan-before-push |
| 15 | Hook bypass policy | Allow `--no-verify` for known false positives / Never bypass | Never bypass | CLAUDE.md explicit rule |
| 16 | HACS validation | Metadata only / Live HA install / Both | Metadata only (live install is Phase 12) | Keeps Phase 11 scope clean; Phase 12 covers live migration |
| 17 | Archive command | `gh repo archive` / Web UI / Delete repo | `gh repo archive --yes` | Scriptable, reversible via UI, SPLIT-04 says archive not delete |
| 18 | Human gate | No gate (full auto) / Gate before archive / Gate at every step | Single gate before archive (between verify-new-repo and commit-banner) | Only truly irreversible step needs human confirmation; everything before is reversible |
| 19 | Rollback strategy | Automated rollback / Manual only | Manual only | Automated rollback of a freshly-created repo risks deleting preserved filter-repo history; manual intervention safer |
| 20 | Verification output format | Prose / Command output transcripts | Command output transcripts | Matches project pattern: VERIFICATION.md shows `gh`/`curl`/`git blame` output, not opinions |

## Corrections Made

None — this was a fully auto-resolved session per user instruction ("beantworte du alle fragen").

## External Research

None performed. Codebase + prior phase artifacts + user memory provided sufficient evidence for all decisions. `gh` CLI commands are standard; no library version research needed for a phase that is purely git/GitHub operations.

## Confidence Assessment

- **Confident:** D-01 through D-10 (operations sequence, repo creation mechanics, tagging deferral) — directly supported by roadmap/requirements and Phase 8 output shape.
- **Confident:** D-11 through D-15 (banner placement and format) — standard pattern for deprecation notices.
- **Confident:** D-16 through D-18 (secret scan) — mandated by CLAUDE.md.
- **Confident:** D-19 through D-22 (HACS validation + archive) — routine operations.
- **High-stakes but Confident:** D-23 (human gate) — the one place Claude explicitly hands control back to the user, per `feedback_autonomous.md` ("only ask when critical"). Archiving a public repo qualifies as critical.

## Next Step

Auto-advancing to `/gsd-plan-phase 11 --auto` (chain flag set).
