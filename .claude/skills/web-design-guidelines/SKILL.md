---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance — accessibility, focus states, forms, animation, typography, images, touch, dark mode, hydration. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or after building or redesigning a page or component.
argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review the given files (or ask which) against [guidelines.md](guidelines.md) and report findings
in its `file:line` format.

Adapted from vercel-labs/agent-skills `web-design-guidelines` (MIT). The original fetches the
rules from GitHub on every run; this copy reads a reviewed snapshot instead, so the instructions
can't change without a commit. Source and licence: `.claude/skills/THIRD_PARTY.md`.

## Steps

1. Read [guidelines.md](guidelines.md).
2. Read the target files.
3. Check every rule; output findings grouped by file, terse, `file:line - issue`.

## This project overrides

- **Copy casing**: sentence case for headings and buttons, not the snapshot's Title Case — the
  `frontend-design` skill's writing guidance and the existing site use sentence case.
- **Dates/numbers**: formatting helpers belong in `admin/lib/format.ts`, built on `Intl.*`; flag
  hand-rolled formats in components.
- **Virtualisation**: no list on this site approaches 50 items; don't add a virtualisation
  dependency for one.
- **URL state**: the project filters already live in query params — keep new filters there too.

## Refreshing the snapshot

Fetch `vercel-labs/web-interface-guidelines` `command.md` at a specific commit, read the whole
diff against `guidelines.md`, then update the commit SHA in `THIRD_PARTY.md`.
