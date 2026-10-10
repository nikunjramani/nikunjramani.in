# Phase 5 · Admin Panel

**~14 hours** · Status: 🟡 Built and verified against the real emulators (Auth, Firestore,
Functions, Storage) through actual signed-in browser sessions — every screen, both
real-bug fixes it surfaced along the way, and the two things that genuinely can't run
locally: the signed-upload PUT itself (needs a deployed service account — Phase 6) and a
production admin claim grant (same).

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

- [x] `/admin/projects` — table, search, filter by visibility/kind, reorder (up/down
      buttons, same scope decision as `/admin/skills` below — no drag-and-drop
      dependency), duplicate, delete
- [x] `/admin/projects/[id]` — the full editor, live preview (via the same
      `ProjectDetailView` the public page renders), draft/publish, autosave, audit trail
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

- [x] `/admin/media` — grid, upload via signed URL, progress. The signed-URL round trip
      itself can't run end-to-end locally (IAM signBlob needs a real deployed service
      account — `shared/services/storage.py`'s own docstring says so); verified up to that
      exact boundary instead: POST /media/upload-url passes validation against the live
      Functions emulator with a real admin token and fails only on the outbound signing
      call. One real check for Phase 6.
- [x] Drag-and-drop, multi-file
- [x] Alt text editing *(required before an image can be used)*
- [x] Copy URL, delete with usage check
- [x] Automatic WebP + thumbnails from the Phase 3 trigger — unchanged since Phase 3,
      exercised by this screen's list/grid rendering the trigger's output shape

### 5.6 · Messages

- [x] `/admin/messages` — inbox, read/unread
- [x] Detail view, mark replied, spam flag
- [x] `mailto:` reply with the subject pre-filled
- [x] Export to CSV — via a Blob download (apiFetchBlob), not a plain `<a href>`: the
      export endpoint needs the same Bearer auth as everything else, which a real
      navigation can't carry

### 5.7 · Settings & publishing

- [x] `/admin/settings` — feature flags, announcement banner, maintenance mode (5.4's commit)
- [x] **Preview before publish** — renders the real public component with draft data.
      Built for Projects specifically, which is also the only content type that has one: it's
      the only public model with its own standalone detail page to preview against (skills/
      experience/etc. only ever render embedded in other pages, not as their own route)
- [x] Publish triggers revalidation; the change is live within seconds — unchanged backend
      behavior from Phase 3 (visibility → public in a PATCH auto-triggers it in
      shared/crud.py), reverified live in the 5.4 commit: GET /projects/test-project-editor
      on the public site returned 200 with the right content immediately after save
- [x] Autosave drafts to localStorage — built into `<SchemaForm>` itself via an
      `autosaveKey` prop, so every screen gets it for free rather than each one wiring its
      own. Restore-on-reload shows a dismissible banner; discard resets to the last saved
      version. Finding and fixing this took two real bugs: a hydration mismatch from
      reading `localStorage` inside a `useState` initializer (SSR has no `localStorage`;
      moved the read into a `useEffect` so server and first client render agree), and a
      stale uncontrolled `<input>` after `form.reset()` that react-hook-form's own internal
      state didn't reflect — worked around by remounting the field tree on discard rather
      than fighting the sync, plus an `isDirty` guard so the autosave timer scheduled by
      reset's own change-event doesn't resurrect the draft it was just asked to clear.
- [x] Audit trail visible per document — one `<AuditTrail>` component, used by the
      Projects editor, every `ContentCollectionScreen` edit dialog, and `SingletonScreen`

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
