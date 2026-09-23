# Phase 5 · Admin Panel

**~14 hours** · Status: ⬜ Not started

> **Goal:** Go to `nikunjramani.in/admin`, sign in with Google, and edit every piece of
> content on the site. No Firebase console, no redeploy.

This is the phase that determines whether the site still gets updated in six months.

---

## Prerequisites

- [x] [Phase 3](./phase-3-backend.md) done — the admin API exists and is tested
- [x] [Phase 4](./phase-4-public-site.md) done — components exist to reuse for preview
- [x] Your account holds the `admin: true` claim — granted via `infra/scripts/set_admin_claim.py`
      against the Auth emulator for local dev; production grant happens post-deploy (Phase 6)

---

## Tasks

### 5.1 · Auth

- [x] `/admin/login` — Google sign-in
- [x] Session cookie set from the ID token
- [x] Middleware guarding `/admin/*` — `proxy.ts`, Next 16's middleware successor
- [x] `(admin)/layout.tsx` — verify the claim, redirect if absent
- [x] Token refresh + graceful expiry
- [x] Sign out
- [x] Signed-in-but-not-admin shows a clear message, not a blank page

> Reminder from [03 · Security](../03-security.md): this is convenience, not the gate. Every write is
> re-authorised server-side.

### 5.2 · `<SchemaForm>` — the centrepiece

A renderer that reads a JSON Schema and produces the form. Build this properly and the remaining
screens are almost free.

- [x] Field resolver: schema type → control
- [x] Controls: text, textarea, markdown, number, boolean, enum select, date, URL, tags
- [x] Array-of-objects — add, remove, reorder (up/down, not drag — see 5.4 note)
- [x] Nested objects → collapsible sections
- [x] Media picker integration
- [x] Validation from the generated Zod schemas, inline errors
- [x] **Optional sections collapsed by default** with an "add a section" affordance
- [x] Dirty tracking + an unsaved-changes guard

### 5.3 · Shell

- [x] Admin layout — sidebar, breadcrumbs, user menu
- [x] `/admin` dashboard — content counts, unread messages, recent edits, quick actions
- [x] Toasts, confirm dialogs, optimistic updates

### 5.4 · Content screens

- [ ] `/admin/projects` — table, search, filter by visibility/kind, **drag to reorder**, duplicate, delete
- [ ] `/admin/projects/[id]` — the full editor, live preview, draft/publish
- [x] `/admin/skills` — inline-editable grid grouped by category, reorder (up/down buttons,
      not drag-and-drop — functionally equivalent, no new dependency; revisit if this
      becomes a real friction point)
- [x] `/admin/experience` · `/education` · `/certifications`
- [x] `/admin/profile` — bio, socials, availability toggle via `<SchemaForm>`. Résumé is a
      URL field, not a direct upload widget: the media pipeline's signed-upload endpoint is
      image-only (`ALLOWED_CONTENT_TYPES`, `on_media_uploaded`'s trigger unconditionally
      runs image processing on anything matching its path pattern — a PDF would crash it),
      and signed URLs can't be exercised live before a real deployment exists to sign them
      with anyway (same limitation the media upload flow already has, documented in
      `shared/services/storage.py`). Pasting a hosted PDF URL is a real, working path in
      the meantime; a dedicated document-upload endpoint is a small, isolated addition for
      whenever it's worth the round trip to verify against a deployed environment.
- [x] `/admin/posts` — stub, wired in Phase 8

### 5.5 · Media library

- [ ] `/admin/media` — grid, upload via signed URL, progress
- [ ] Drag-and-drop, multi-file
- [ ] Alt text editing *(required before an image can be used)*
- [ ] Copy URL, delete with usage check
- [ ] Automatic WebP + thumbnails from the Phase 3 trigger

### 5.6 · Messages

- [ ] `/admin/messages` — inbox, read/unread
- [ ] Detail view, mark replied, spam flag
- [ ] `mailto:` reply with the subject pre-filled
- [ ] Export to CSV

### 5.7 · Settings & publishing

- [ ] `/admin/settings` — feature flags, announcement banner, maintenance mode
- [ ] **Preview before publish** — renders the real public component with draft data
- [ ] Publish triggers revalidation; the change is live within seconds
- [ ] Autosave drafts to localStorage
- [ ] Audit trail visible per document

---

## Definition of done

1. You can create a complete project — every field, images uploaded — without touching the console
2. Reordering by drag persists and reorders the public site
3. Preview shows exactly what publishing will produce
4. Publishing revalidates; the public page updates within seconds
5. A non-admin Google account gets a clear refusal on every route and every API call
6. Adding a field to a schema, then `make gen`, makes it appear in the form with no form code changed

**Test 6 is the one that matters** — it's the payoff for the whole schema-first approach.

---

## Gotchas

**`<SchemaForm>` is where the time goes.** Budget half the phase for it. Build it against
`skill.schema.json` (small) before pointing it at `project.schema.json` (large and deeply nested).

**Arrays of objects are the hard part.** Add, remove and reorder with stable keys — index-based keys
will scramble your form state the moment something moves.

**Don't let the editor become a CMS.** No rich-text WYSIWYG, no revision history, no collaborative
editing. Markdown in a textarea with a preview toggle. Scope creep here is the top risk in
[08 · Costs & Risks](../08-costs-and-risks.md).

**Session cookies and App Hosting.** Set `httpOnly`, `secure`, `sameSite=lax`, and check the flow
works on the deployed environment, not just localhost.

**Optimistic updates need rollback.** If the API rejects a write, restore the previous state and say
so — silently reverting looks like a bug.

**Preview must use the real components.** A separate preview renderer will drift from the public
page, and then preview stops meaning anything.

---

**Next:** [Phase 6 · Deploy & DNS](./phase-6-deploy.md)
