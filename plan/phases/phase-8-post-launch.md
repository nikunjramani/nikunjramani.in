# Phase 8 · Post-Launch

**Ongoing** · Status: ⬜ Not started

> **Goal:** Improve a live site. Nothing here blocks launch, and nothing here should
> ever be pulled forward into an earlier phase.

Pick what you actually want. This list is a menu, not a backlog.

---

## Near-term — high value, low effort

### Blog · ~10h
- [ ] MDX rendering with syntax highlighting
- [ ] `/blog` index with tag filters
- [ ] Reading time, table of contents
- [ ] RSS feed
- [ ] Admin editor with live preview
- [ ] `showBlog` feature flag flipped on

> Only worth it if you'll actually write. An empty blog is worse than no blog.

### Analytics · ~3h
- [ ] Privacy-friendly analytics (Umami, Plausible, or Firebase Analytics)
- [ ] Track: page views, project detail views, résumé downloads, contact submissions
- [ ] Dashboard widget in `/admin`

> Knowing which projects get read should change which ones you feature.

### Polish · ~5h
- [ ] View counts on project cards
- [ ] "Recently updated" indicators
- [ ] Better empty states
- [ ] Micro-interactions on hover and focus
- [ ] Print stylesheet for the résumé view

---

## Medium-term

### Testimonials · ~4h
Schema, admin CRUD, homepage carousel, per-project quotes.

### Search · ~5h
Client-side fuzzy search over projects and posts. Cmd-K palette.

### Dynamic OG images · ~4h
Per-project generated cards with title, stack and cover. Big difference to how links look when
shared.

### Résumé generation · ~6h
Generate the PDF from Firestore instead of maintaining a separate document — one source of truth for
your career, and it can never go stale.

---

## Longer-term — only if genuinely wanted

| Idea | Effort | Honest take |
|---|---|---|
| i18n | ~8h | Only if you have a second-language audience |
| Newsletter | ~6h | Only alongside an active blog |
| Comments | ~5h | Moderation burden; probably not worth it |
| Staging environment | ~8h | Worth it once schema migrations get scary |
| Uptime status page | ~3h | Fun; unnecessary |
| Dark/light per-section | ~4h | Rabbit hole |

---

## Maintenance — the part that actually matters

Recurring, small, and easy to skip:

- **Monthly** — merge dependency updates, check analytics, review Search Console
- **Quarterly** — update projects and experience, refresh the résumé, check for broken links
- **Yearly** — rotate secrets, review IAM bindings, prune old backups, re-read the About page

> A personal site's real failure mode isn't bugs — it's going stale. The admin panel exists so
> updating it takes ten minutes. Actually doing it quarterly is what keeps the site worth having.

---

## Ideas parking lot

Anything that comes up mid-build goes here rather than into the current phase. Revisit after launch.

- [ ] …

---

**Back to:** [Plan index](../README.md)
