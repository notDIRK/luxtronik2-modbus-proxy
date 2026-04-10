# Phase 11: Publish & Archive Legacy - Context

**Gathered:** 2026-04-10 (discuss mode, `--auto` — recommended defaults)
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the v1.2 rebrand live and irreversible:
1. Publish the local `~/claude-code/luxtronik2-hass/` working copy to a new public GitHub repository `notDIRK/luxtronik2-hass`.
2. Add an "⚠️ Experimental — not actively maintained" banner + forward link to the old repo's `README.md` and `README.de.md`.
3. Archive the old repository `notDIRK/luxtronik2-modbus-proxy` via `gh repo archive`.
4. Validate the new repo as a HACS custom repository (metadata check only, not a live HA install — that is Phase 12).

Out of scope: the maintainer's live Home Assistant migration (Phase 12), any Docker or PyPI work (scoped out of v1.2), creating a GitHub release / tag strategy beyond what HACS needs.
</domain>

<decisions>
## Implementation Decisions

### Order of Operations (irreversible gate)
- **D-01:** Strict sequence, halt-on-fail at every step:
  1. Pre-flight secret scan on BOTH working copies (new repo + legacy repo) — local grep for IPs, hostnames, tokens plus the existing pre-commit hook dry-run.
  2. Create `notDIRK/luxtronik2-hass` on GitHub as a public MIT-licensed repo using `gh repo create` (no template, no auto-init — push from the existing local history so `git filter-repo`-preserved commits survive).
  3. Push `master` + all tags from the new working copy.
  4. Verify post-push: `gh repo view`, `git blame` spot-check on `coordinator.py` + `config_flow.py`, and manifest/hacs.json fetch via raw.githubusercontent.com.
  5. Commit the experimental banner to old repo `master` (EN + DE README in the same commit).
  6. Push the banner commit.
  7. Run `gh repo archive notDIRK/luxtronik2-modbus-proxy --yes`.
  8. Post-archive verification: `gh repo view --json isArchived` returns `true`; old repo README on github.com shows the banner above the fold.
- **D-02:** If any step fails, stop immediately and report. Do NOT attempt automated rollback of the new repo (deleting a freshly-created public repo is destructive and loses the filter-repo history that took Phase 8 to produce). Manual recovery only, guided by the plan's rollback notes.

### New Repository Creation
- **D-03:** Use `gh repo create notDIRK/luxtronik2-hass --public --description "Home Assistant HACS integration for Luxtronik 2.0 heat pumps (Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, Wolf)" --source ~/claude-code/luxtronik2-hass --remote origin --push` — single command creates the repo, sets remote, and pushes.
- **D-04:** License: MIT. The new working copy must contain a `LICENSE` file before push. If missing, add it as part of the plan (Apache-2.0 is explicitly NOT used — matches the luxtronik library ecosystem per PROJECT.md).
- **D-05:** Default branch: `master` (matches existing local working copy; do not rename to `main` mid-rebrand — that is an independent decision that would churn docs and CI).
- **D-06:** Topics: `home-assistant`, `hacs`, `hacs-integration`, `luxtronik`, `heat-pump`, `alpha-innotec`, `novelan`. Set via `gh repo edit --add-topic` after creation.
- **D-07:** Repo description matches D-03 above. Homepage URL left empty for now (no docs site yet in v1.2).
- **D-08:** Push scope: `git push -u origin master` + `git push origin --tags`. No other branches exist in the filter-repo extracted working copy; nothing else to push.

### Release Tagging
- **D-09:** Do NOT create a GitHub Release or cut a `v1.2.0` tag in this phase. HACS custom repository installs work off the default branch and `manifest.json` `version` field (currently `1.1.2`). A tagged release is deferred until after Phase 12 live verification confirms the rebrand actually works on the maintainer's HA instance. Release work lives in a future phase.
- **D-10:** Leave `manifest.json` `version` at `1.1.2` in this phase — bumping it implies a release candidate and muddies Phase 12 verification. The version bump to `1.2.0` is part of the eventual release phase, not the publish phase.

### Experimental Banner (Legacy Repo)
- **D-11:** Banner placement: top of `README.md` and `README.de.md`, above ALL existing content (including the project title). Reader sees the warning before anything else.
- **D-12:** Banner content (EN, verbatim template — plan may refine wording but must preserve meaning, emoji, and the forward link):
  ```markdown
  > ## ⚠️ Experimental — Not Actively Maintained
  >
  > This repository is the **legacy Modbus TCP proxy** byproduct of the Luxtronik 2.0 integration project. It is **no longer actively maintained** and is archived on GitHub (read-only).
  >
  > **→ Use [luxtronik2-hass](https://github.com/notDIRK/luxtronik2-hass) instead** — the actively maintained Home Assistant HACS integration is the supported path for Luxtronik 2.0 heat pumps.
  >
  > The proxy remains available for niche use cases (raw Modbus access from non-HA tools like evcc standalone), but receives no updates, bug fixes, or support.
  ```
- **D-13:** Banner content (DE) is a semantic mirror of D-12 — NOT a mechanical machine translation. Same structure, same forward link, German idiom. Plan must draft both versions and have them reviewed before commit.
- **D-14:** Banner commit message: `docs(legacy): add experimental banner and forward link to luxtronik2-hass`. Single commit, covers both READMEs, no other changes bundled.
- **D-15:** Banner commit is made in the CURRENT working directory (`~/claude-code/PUBLIC-luxtronik2-modbus-proxy`), pushed to `notDIRK/luxtronik2-modbus-proxy` master, THEN the repo is archived. Committing after archive is harder (archived repos are read-only on the GitHub side, though local pushes may still be rejected by the UI).

### Secret Scan (Pre-flight)
- **D-16:** Before ANY push, run `git grep -nE '192\.168\.|10\.[0-9]+\.|172\.(1[6-9]|2[0-9]|3[01])\.|\.local|\.lan|password|token|[A-Za-z0-9_-]{32,}'` across both working copies. Any hit blocks the push and requires investigation (false positives documented inline in the plan).
- **D-17:** Run the existing pre-commit hook as a dry-run on the banner commit before pushing: `pre-commit run --all-files` in the legacy repo. If the hook blocks, do not bypass with `--no-verify` (explicit CLAUDE.md rule).
- **D-18:** The new repo's history is the `git filter-repo` output from Phase 8, which has already been audited. No re-scan of every historical commit — just the HEAD tree and the Phase 8 extraction was verified by grep at the time. Re-running the secret scan on HEAD of the new repo is sufficient.

### HACS Custom Repository Validation
- **D-19:** Post-push validation is metadata-only in this phase, not a live HA install:
  - Fetch `https://raw.githubusercontent.com/notDIRK/luxtronik2-hass/master/hacs.json` via `curl` — must return valid JSON matching the local file.
  - Fetch `.../custom_components/luxtronik2_hass/manifest.json` — must return valid JSON with `domain: luxtronik2_hass`.
  - Run the HACS action validator locally if available (optional; CI action is already wired from Phase 4).
- **D-20:** Live "Add custom repository" dialog test on the maintainer's HA instance is explicitly Phase 12 work, not Phase 11. This phase's success criterion SC-4 ("HACS custom repository URL validates successfully in a trial HACS dialog") is satisfied by the metadata checks plus the Phase 4 HACS CI action passing on the new repo's first push — not by a human clicking through HA's UI. Phase 12 covers the live install.

### Old Repo Archive
- **D-21:** Archive command: `gh repo archive notDIRK/luxtronik2-modbus-proxy --yes`. No pre-archive settings change (disabling issues, wiki, etc.) — archiving makes them read-only automatically.
- **D-22:** Archive happens AFTER the banner commit is pushed and visible on github.com. Verification: `gh repo view notDIRK/luxtronik2-modbus-proxy --json isArchived,url` returns `isArchived: true`.

### Verification Gates
- **D-23:** Human gate before the irreversible step: between D-01 step 4 (new repo verified) and step 5 (banner commit) the plan MUST pause and require explicit user confirmation ("proceed with legacy archive"). This is the single human-in-the-loop checkpoint; everything before it is reversible (delete the new empty repo), everything after is not (archiving is reversible via UI but the banner commit is part of permanent history).
- **D-24:** Post-phase verification ties each of the 4 roadmap success criteria to a concrete `gh`/`curl`/`git blame` command. VERIFICATION.md must show command output, not just "looks good".

### Claude's Discretion
- Exact wording of the DE banner (as long as it preserves D-12 structure and forward link).
- Whether to bundle the `LICENSE` file addition into the new repo as its own commit or as part of the initial push tree adjustment.
- Formatting details of the metadata validation output in VERIFICATION.md.
- Whether to run the HACS CI action locally via `act` or rely on the remote CI run.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §"Phase 11: Publish & Archive Legacy" — goal, success criteria, requirement IDs (SPLIT-01, SPLIT-04, SPLIT-05, DOCS-05)
- `.planning/REQUIREMENTS.md` §"Repo Split (SPLIT)" and §"Documentation (DOCS)" — acceptance criteria for SPLIT-01/04/05 and DOCS-05
- `.planning/PROJECT.md` — MIT license decision, public-repo security rules, two-repo strategy

### Upstream phase outputs (the thing being published)
- `~/claude-code/luxtronik2-hass/` — local working copy produced by Phases 8-10; contains filter-repo preserved history, renamed `luxtronik2_hass` domain/package, and HA-first README (EN+DE) + MIGRATION.md
- `~/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/manifest.json` — current `domain: luxtronik2_hass`, `version: 1.1.2`
- `~/claude-code/luxtronik2-hass/hacs.json` — HACS metadata to validate after push
- `.planning/phases/08-new-repo-extraction-setup/08-VERIFICATION.md` — proves the filter-repo history is intact (do not re-verify in Phase 11, trust Phase 8)
- `.planning/phases/09-rename-in-new-repo/09-VERIFICATION.md` — proves the rename is complete (no `luxtronik2_modbus_proxy` leftovers)
- `.planning/phases/10-documentation-rewrite/10-VERIFICATION.md` — proves the HA-first README + MIGRATION.md exist

### Legacy repo (the thing being archived)
- `./README.md` — current EN README of `luxtronik2-modbus-proxy`, where the EN banner gets prepended
- `./README.de.md` — current DE README, where the DE banner gets prepended
- `./CLAUDE.md` §"SECURITY — READ FIRST" — public repo security rules, pre-commit hook policy, never-bypass rule

### Tools and commands
- `gh repo create` — https://cli.github.com/manual/gh_repo_create (public, --source, --push, --remote)
- `gh repo archive` — https://cli.github.com/manual/gh_repo_archive
- Pre-commit hook at `.git/hooks/pre-commit` (legacy repo) — must not bypass

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 8 extraction**: `~/claude-code/luxtronik2-hass/` is a self-contained git working copy with no remote set. `gh repo create --source=. --push --remote=origin` is the exact match for this shape.
- **Pre-commit hook**: Legacy repo has a working secret-scan pre-commit hook from Phase 3 / earlier work. Re-use it; do not re-implement.
- **HACS CI action**: Phase 4 wired `.github/workflows/` validation. It will run automatically on the first push to the new repo and becomes the first real test of the HACS metadata. This is free validation — plan should explicitly wait for the Actions run to complete before declaring the phase done.

### Established Patterns
- **Every phase has VERIFICATION.md with concrete command output** — Phase 11 must follow this pattern. `gh repo view` JSON, `curl` output, `git blame` snippets.
- **Never bypass security hooks** — CLAUDE.md rule, enforced across all phases. Phase 11 must handle hook failures by fixing, not skipping.
- **Bilingual docs in lockstep** — EN + DE changes happen in the same commit, same section structure, semantic mirror. Phase 11 banner follows this.

### Integration Points
- GitHub API via `gh` CLI (already authenticated as `notDIRK` per user memory `reference_github.md`).
- Git push to origin (new repo: https push via gh-managed credentials; legacy repo: existing remote).
- HACS validation: GitHub raw content fetch + optional HACS CI action.
- No code integration — this phase is purely publication/archival operations on git + GitHub state.

</code_context>

<specifics>
## Specific Ideas

- The irreversible nature of `gh repo archive` is the defining characteristic of this phase. Plan must treat the archive step as a one-way gate with a human checkpoint immediately before it.
- User memory `feedback_autonomous.md` indicates Claude decides independently but asks on critical decisions. Archiving a public repo IS a critical decision — the D-23 human checkpoint is therefore mandatory even in `--auto` chain mode. The auto-advance should plan and prepare everything up to the gate, then pause.
- User memory `reference_github.md`: "scan before push" — reinforces D-16 secret scan as non-optional.

</specifics>

<deferred>
## Deferred Ideas

- **v1.2.0 GitHub Release / tag cut** — deferred to a post-Phase-12 release phase once the live migration is verified. Creating a release before the rebrand works on real hardware would force a yank if anything breaks.
- **Rename `master` → `main`** — out of scope. Independent decision that affects docs, CI, and muscle memory. If done, do it in its own phase, not bundled with the rebrand.
- **GitHub repository homepage URL, social preview image, funding.yml, SECURITY.md, CODE_OF_CONDUCT.md** — community polish for a future phase, not required for the publish gate.
- **Auto-redirect or GitHub "transfer"** from old repo to new repo — GitHub's transfer mechanism doesn't fit here because the new repo has filter-repo-rewritten history. Forward link in the banner is the right mechanism.
- **Deleting the old repo** — explicitly rejected. SPLIT-04 says archive. Archived repos keep backlinks, issues, and history reachable; deletion would break evcc users and search engine links.

### Reviewed Todos (not folded)
- No matching todos surfaced for Phase 11.

</deferred>

---

*Phase: 11-publish-archive-legacy*
*Context gathered: 2026-04-10 (discuss mode, --auto)*
