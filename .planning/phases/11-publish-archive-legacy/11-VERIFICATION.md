# Phase 11: Publish & Archive Legacy — Verification

**Date:** 2026-04-10
**Phase:** 11-publish-archive-legacy
**Plan:** 11-01-PLAN.md
**Mode:** execute (manual inline, --auto --chain, with user approval at D-23 human gate)
**Status:** PASSED — all 4 roadmap success criteria satisfied

---

## Success Criterion 1 (SPLIT-01): New repo public, MIT-licensed, HA integration with preserved history

**Roadmap text:** *"`gh repo view notDIRK/luxtronik2-hass` shows a public, MIT-licensed repository containing `custom_components/luxtronik2_hass/`; clicking through to `coordinator.py` shows the preserved Phase 4-7 commit history via `git blame`."*

### Command 1: Repo metadata

```
$ gh repo view notDIRK/luxtronik2-hass --json name,visibility,licenseInfo,url,defaultBranchRef,repositoryTopics
```
```json
{
  "defaultBranchRef": {"name": "master"},
  "licenseInfo": {"key": "mit", "name": "MIT License", "nickname": ""},
  "name": "luxtronik2-hass",
  "repositoryTopics": [
    {"name": "alpha-innotec"},
    {"name": "hacs"},
    {"name": "hacs-integration"},
    {"name": "heat-pump"},
    {"name": "home-assistant"},
    {"name": "luxtronik"},
    {"name": "novelan"}
  ],
  "url": "https://github.com/notDIRK/luxtronik2-hass",
  "visibility": "PUBLIC"
}
```
**Result:** PUBLIC ✓, MIT License ✓, default branch `master` ✓, 7 topics ✓.

### Command 2: History preservation (coordinator.py)

```
$ cd ~/claude-code/luxtronik2-hass && git log --oneline --follow custom_components/luxtronik2_hass/coordinator.py
986fb9c refactor(09): rename luxtronik2_modbus_proxy to luxtronik2_hass
b0067e8 fix(coordinator): use dict.items() for luxtronik parameter/calculation extraction
7f4bc4d feat(07-01): add write methods and rate limiting to LuxtronikCoordinator
1f7b490 feat(05-01): add LuxtronikCoordinator with connect-per-call polling
```
**Result:** Phase 5 (`feat(05-01)`) and Phase 7 (`feat(07-01)`) commits preserved ✓. History visible via `--follow` through the Phase 9 rename.

### Command 3: History preservation (config_flow.py)

```
$ git log --oneline --follow custom_components/luxtronik2_hass/config_flow.py
986fb9c refactor(09): rename luxtronik2_modbus_proxy to luxtronik2_hass
6bae448 fix(config_flow): remove manual config_entry init from OptionsFlow
149b67b feat(260409-l1l): add LuxtronikOptionsFlow to config_flow.py
669e442 feat(05-02): add config flow with connection test and BenPru conflict detection
```
**Result:** Phase 5 (`feat(05-02)`) commit preserved ✓.

### Command 4: Total commit count

```
$ git log --oneline | wc -l
52
```
**Result:** 52 commits in history (matches Phase 8 filter-repo extraction + Phase 9 rename + Phase 10 docs + Phase 11 LICENSE + .gitignore) ✓.

**SC-1: PASS**

---

## Success Criterion 2 (SPLIT-04, SPLIT-05, DOCS-05): Legacy archived with banner + forward link (EN + DE)

**Roadmap text:** *"The old repo `notDIRK/luxtronik2-modbus-proxy` displays the GitHub 'Archived' label, is read-only, and both `README.md` and `README.de.md` begin with a '⚠️ Experimental — not actively maintained' banner and a '→ Use luxtronik2-hass instead' forward link to the new repo."*

### Command 1: Archive state

```
$ gh repo view notDIRK/luxtronik2-modbus-proxy --json isArchived,url,name
```
```json
{
  "isArchived": true,
  "name": "luxtronik2-modbus-proxy",
  "url": "https://github.com/notDIRK/luxtronik2-modbus-proxy"
}
```
**Result:** `isArchived: true` ✓ (SPLIT-04).

### Command 2: EN banner on live master

```
$ curl -sSL https://raw.githubusercontent.com/notDIRK/luxtronik2-modbus-proxy/master/README.md | head -3
> ## ⚠️ Experimental — Not Actively Maintained
>
> This repository is the **legacy Modbus TCP proxy** byproduct of the Luxtronik 2.0 integration project. It is **no longer actively maintained** and is archived on GitHub (read-only).
```
**Result:** EN banner at line 1 ✓.

### Command 3: DE banner on live master

```
$ curl -sSL https://raw.githubusercontent.com/notDIRK/luxtronik2-modbus-proxy/master/README.de.md | head -3
> ## ⚠️ Experimentell — Nicht aktiv gepflegt
>
> Dieses Repository ist das **Legacy-Modbus-TCP-Proxy**-Nebenprodukt des Luxtronik-2.0-Integrationsprojekts. Es wird **nicht mehr aktiv gepflegt** und ist auf GitHub archiviert (schreibgeschützt).
```
**Result:** DE banner at line 1 ✓ (semantic mirror of EN, preserves emoji, header structure, forward link, niche-use caveat — hand-drafted per D-13).

### Command 4: Forward link present in both

```
$ curl -sSL https://raw.githubusercontent.com/notDIRK/luxtronik2-modbus-proxy/master/README.md | grep -c "github.com/notDIRK/luxtronik2-hass"
1
$ curl -sSL https://raw.githubusercontent.com/notDIRK/luxtronik2-modbus-proxy/master/README.de.md | grep -c "github.com/notDIRK/luxtronik2-hass"
1
```
**Result:** Forward link to `luxtronik2-hass` present in both READMEs ✓.

### Command 5: Banner commit on master

```
$ git log --oneline origin/master -1
4f0460c docs(legacy): add experimental banner and forward link to luxtronik2-hass
```
**Result:** Exact commit message per D-14 ✓.

**SC-2: PASS** (SPLIT-04 archived, SPLIT-05 banner+link, DOCS-05 EN+DE both present)

---

## Success Criterion 3: Pre-commit secret scan passed on both repos

**Roadmap text:** *"Pre-commit secret scan passes on both repos before their respective final pushes; no IP/hostname/credential leak in the new repo or in the banner commit on the old one."*

### Command 1: D-16 scan on legacy repo (file contents)

```
$ git grep -nE '192\.168\.|10\.[0-9]+\.|172\.(1[6-9]|2[0-9]|3[01])\.|\.local|\.lan|password|token|[A-Za-z0-9_-]{32,}' -- . ':!.planning/' ':!*.md'
```
**Hits:** All matches classified as documented false positives:
- `config.example.yaml:6` → `192.168.x.x` placeholder (CLAUDE.md-approved placeholder pattern)
- `.github/workflows/publish.yml:32` → `id-token: write` (GitHub Actions OIDC permission keyword, not a secret)
- `custom_components/luxtronik2_modbus_proxy/*.py` → long Python class names like `LuxtronikNumberEntityDescription` matching `{32,}` regex (identifiers, not tokens)
- `custom_components/luxtronik2_modbus_proxy/*.py` → comment separator `# ----------------------------------------------------------------------` matching `{32,}` regex

**Result:** No real IPs, hostnames, credentials, or tokens ✓.

### Command 2: D-16 scan on new repo (file contents)

```
$ cd ~/claude-code/luxtronik2-hass && git grep -nE '...' (same regex)
```
**Hits:** All matches classified as documented false positives:
- `custom_components/luxtronik2_hass/strings.json:11` → `192.168.x.x` placeholder in translation string
- `custom_components/luxtronik2_hass/translations/{en,de}.json:11` → `192.168.x.x` placeholder
- `custom_components/luxtronik2_hass/__init__.py:48,61` → `async_config_entry_first_refresh` (long Python method name)
- `tests/unit/test_*.py` → long test function names like `test_sg_ready_mode_map_writes_params_3_and_4`

**Result:** No real IPs, hostnames, credentials, or tokens ✓.

### Command 3: Staged diff scan on banner commit

```
$ git diff --cached README.md README.de.md | grep -E '^\+' | grep -nE '192\.168\.|intranet|wolbeck\.net|password=|token=|[A-Za-z0-9_-]{40,}'
(no output)
$ echo "STAGED_DIFF_CLEAN"
STAGED_DIFF_CLEAN
```
**Result:** Banner text contains no secrets ✓.

### Command 4: Git author metadata scan (privacy)

**Finding (blocker caught during execution):** Initial `git log` inspection revealed all 52 commits in the new repo authored as `Ubuntu <dwolbeck@Claude-Code-1.intranet.wolbeck.net>` — an internal hostname leak forbidden by CLAUDE.md security rules. The Task 1 `git grep` scan did not catch this because it only scans file contents, not commit metadata.

**Mitigation applied (Option B chosen by user):**
```
$ git filter-repo --force --email-callback 'return b"notDIRK@users.noreply.github.com"' --name-callback 'return b"notDIRK"'
Parsed 52 commits
New history written in 0.04 seconds
```
```
$ git log --format='%ae %ce' --all | grep -c "intranet\|wolbeck.net\|Ubuntu"
0
```
**Result:** All 52 commits rewritten to clean author `notDIRK@users.noreply.github.com`. Commit messages, file contents, and tree structure preserved. Phase 8 filter-repo history continues to resolve via `git log --follow`.

**Note:** The legacy repo `notDIRK/luxtronik2-modbus-proxy` retains its original author emails (including the hostname). Since the repo is now archived and the hostname was already public pre-Phase-11, no retroactive rewrite was attempted (destructive operation vs. pre-existing public exposure).

**SC-3: PASS** (both file-content scans clean, banner diff clean, new repo author metadata cleaned via history rewrite)

---

## Success Criterion 4: HACS custom repository URL validates

**Roadmap text:** *"The HACS custom repository URL for the new repo validates successfully in a trial HACS 'Add custom repository' dialog (no manifest/hacs.json errors)."*

**D-19/D-20 interpretation:** This phase satisfies SC-4 via metadata-only validation (curl + JSON parse + domain assertion). Live HA "Add custom repository" dialog testing is Phase 12 work (maintainer migration verification).

### Command 1: Fetch hacs.json via raw content

```
$ curl -sSL -o /tmp/11-verify-hacs.json https://raw.githubusercontent.com/notDIRK/luxtronik2-hass/master/hacs.json
$ python3 -c "import json; d=json.load(open('/tmp/11-verify-hacs.json')); print('hacs.json OK:', d)"
hacs.json OK: {'name': 'Luxtronik 2.0 (Home Assistant)', 'homeassistant': '2024.1.0', 'render_readme': True}
```
**Result:** Valid JSON, required HACS fields present (`name`, `homeassistant`) ✓.

### Command 2: Fetch manifest.json and assert domain

```
$ curl -sSL -o /tmp/11-verify-manifest.json https://raw.githubusercontent.com/notDIRK/luxtronik2-hass/master/custom_components/luxtronik2_hass/manifest.json
$ python3 -c "import json; d=json.load(open('/tmp/11-verify-manifest.json')); assert d['domain']=='luxtronik2_hass'; print('manifest OK, domain=', d['domain'], 'version=', d.get('version'))"
manifest OK, domain= luxtronik2_hass version= 1.1.2
```
**Result:** Domain matches renamed identity (`luxtronik2_hass`), version preserved at 1.1.2 per D-10 ✓.

### Command 3: HACS CI action status (advisory)

```
$ gh run list --repo notDIRK/luxtronik2-hass --limit 5
(empty)
$ curl -sSL https://api.github.com/repos/notDIRK/luxtronik2-hass/actions/workflows
workflow_count: 0
```
**Finding:** `.github/workflows/validate.yml` triggers on `branches: main`, but the repo uses `master`. No CI run fired on the initial push. This is a trivial one-line configuration bug NOT introduced by Phase 11 — it was inherited from Phase 4 scaffold work that was never exercised in CI.

**Impact on SC-4:** Zero. SC-4 is satisfied by metadata validation (Commands 1 and 2 above). The CI workflow was documented in the plan as "optional per D-19, free validation per code_context" — its absence does not block Phase 11.

**Follow-up captured (out of scope for Phase 11):** Add `master` to the `validate.yml` trigger branches. This should be a separate quick-task post-Phase-12 verification.

**SC-4: PASS** (metadata served correctly, domain matches, version preserved)

---

## Summary

| Criterion | Requirement | Status | Evidence |
|-----------|-------------|--------|----------|
| SC-1 | SPLIT-01: New repo public, MIT, history preserved | PASS | `gh repo view` + `git log --follow` |
| SC-2 | SPLIT-04, SPLIT-05, DOCS-05: Archived + banners (EN+DE) + forward link | PASS | `gh repo view --json isArchived` + `curl` raw READMEs |
| SC-3 | Pre-commit secret scan on both repos | PASS | `git grep` file-content scan + filter-repo metadata cleanup |
| SC-4 | HACS metadata validates | PASS | `curl` hacs.json + manifest.json, domain asserted |

## Deviations from Plan

1. **LICENSE file did not pre-exist in the new repo working copy.** Task 2 action included a fallback "create if missing" path, which was executed. Commit: initially `8238b21` (later rewritten to `151e984` as part of the filter-repo privacy sweep). MIT License text, copyright `(c) 2026 notDIRK`.

2. **`.gitignore` added.** Not in plan; created during Task 3 pre-checks when `git status` showed untracked `__pycache__` directories that would otherwise have been pushed. Standard Python `.gitignore` added in its own commit (`afebdc7`, later rewritten).

3. **History rewrite (filter-repo second pass).** Not in plan. Triggered by discovery that all 52 commits carried `dwolbeck@Claude-Code-1.intranet.wolbeck.net` in author metadata — a CLAUDE.md-forbidden hostname leak that Task 1's `git grep` could not detect. User was presented with Options A (accept), B (rewrite), C (halt) and chose **Option B**. Filter-repo rewrote all 52 commits to `notDIRK <notDIRK@users.noreply.github.com>` before the new repo was pushed to GitHub. Commit messages and tree contents preserved; SHAs all changed (expected).

4. **No pre-commit hook installed in the legacy repo working copy.** CLAUDE.md claims a pre-commit hook exists; reality in this working copy was `.git/hooks/pre-commit` absent and no `.pre-commit-config.yaml`. Task 8's D-17 dry-run was replaced with a targeted `git diff --cached` secret scan (documented in SC-3 Command 3). This is a gap in the project's security tooling that should be closed in a follow-up (install `pre-commit` and wire the hook), not in Phase 11.

5. **Push race condition on `gh repo create --push`.** The combined create+push command returned "Repository not found" because the push fired before GitHub had finished provisioning the new repo. Remote was correctly set; retrying `git push -u origin master` and `git push origin --tags` succeeded without further intervention.

6. **CI workflow trigger misconfiguration (not caused by Phase 11).** `.github/workflows/validate.yml` uses `branches: main` but the repo uses `master`. No CI runs fired. Documented in SC-4 Command 3 as advisory finding; does not block the phase.

## Irreversibility Gate (D-23)

The human checkpoint between Task 5 and Task 7 was honored. User was presented with a full checkpoint summary including:
- The 4 deviations known at that point (LICENSE, .gitignore, filter-repo rewrite, CI misconfig)
- Verification evidence for SC-1 and SC-4 (already reversible up to this point)
- Explicit enumeration of what would happen after approval (banner commit, push, archive)

User approved via "wir machen weiter von dir empfohlen" after a brief logo inspection question.

## Requirement IDs Closed by this Phase

- [x] **SPLIT-01** — new repo public, MIT
- [x] **SPLIT-04** — legacy archived
- [x] **SPLIT-05** — legacy banner + forward link
- [x] **DOCS-05** — EN + DE banner

## Next Phase

**Phase 12: Maintainer Migration Verification** — Live migration of the maintainer's Home Assistant instance from `luxtronik2_modbus_proxy` to `luxtronik2_hass` via HACS custom repository install. This is where the live HACS "Add custom repository" dialog gets exercised on real hardware (D-20).

---

*Phase 11 verified: 2026-04-10*
