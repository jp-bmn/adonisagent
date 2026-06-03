# GitHub Setup

One-time setup for the repo. Do this after the initial push.

## Branch protection on `main`

Settings → Branches → Add rule for `main`:

- ✅ Require a pull request before merging
- ✅ Require approvals (at least 1)
- ✅ Require status checks: `check` (the CI workflow)
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings

## Repository secrets

Settings → Secrets and variables → Actions → Repository secrets

For CI:
- Nothing required initially. The CI runs lint + typecheck only.

For future deploy (when ready):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ANTHROPIC_API_KEY`
- `RESEND_API_KEY`
- `SERPER_API_KEY`

Do not commit any of these to the repo.

## Repository variables

Settings → Secrets and variables → Actions → Variables

- `NODE_VERSION` — `20`
- `PNPM_VERSION` — `9`

## Teams and collaborators

Add Joel and Michael as **Maintainers**. Greg as a **Collaborator** with **Triage** access for visibility.

## GitHub Actions

Settings → Actions → General

- Allow actions and reusable workflows: `Allow all actions and reusable workflows`
- Workflow permissions: `Read repository contents and packages permissions` (default)
- Allow GitHub Actions to create and approve pull requests: **off**

## Issue labels

Settings → Labels — add or rename to:

- `bug` (red)
- `feature` (blue)
- `docs` (purple)
- `chore` (gray)
- `blocked` (orange)
- `phase-1` (green)
- `phase-2` (green)
- `phase-3` (green) — for the co-pilot stretch
- `partner-input-needed` (yellow)

## Milestones

Create three milestones matching the roadmap:
- **Phase 1 — Digest + dashboard** (due June 2)
- **Phase 2 — Full dashboard** (due June 16)
- **Phase 3 — Co-pilot stretch** (due June 23)
- **Demo Day** (June 24)
