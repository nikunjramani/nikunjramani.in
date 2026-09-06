# 03 · Security

Three independent layers. Any one of them failing shouldn't be enough to let a write through.

---

## The layers

| # | Layer | Protects against | If it fails alone |
|---|---|---|---|
| 1 | **Firestore rules** | Direct SDK writes from any browser | Layers 2–3 still hold |
| 2 | **API auth** — Firebase ID token + `admin` claim | Anyone hitting the API directly | Layer 1 still denies client writes |
| 3 | **Next.js middleware** on `/admin/*` | Casual snooping at the UI | Convenience only, never the real gate |

The important asymmetry: **layer 3 is not security.** It stops the admin UI rendering for a logged-out
visitor, nothing more. Every actual mutation is authorised server-side in layer 2.

---

## 1 · Firestore rules

Public gets read on published documents. **Client writes are denied entirely — including yours.**
Everything mutating goes through the Python API.

```js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    function isPublicCollection(col) {
      return col in ['profile', 'projects', 'skills', 'experience', 'education',
                     'certifications', 'posts', 'site_config'];
    }

    function isPublished() {
      return resource.data.visibility == 'public';
    }

    // Content: world-readable when published, never client-writable
    match /{col}/{id} {
      allow read:  if isPublicCollection(col) && isPublished();
      allow write: if false;          // ← Python API only, no exceptions
    }

    // contact_messages and audit_log fall through to the default: no access.
    // They are never readable or writable by any client.
  }
}
```

> ⚠️ Two things that are easy to get wrong here.
>
> **Match statements have no `where` clause.** The collection wildcard is bound as a variable
> (`col`) and filtered *inside the condition* — there's no way to restrict the match path itself to
> a list. Writing `match /{col}/{id} where col in [...]` doesn't compile.
>
> **A default-deny fallthrough is safer than an explicit deny.** Any collection not named in
> `isPublicCollection` is inaccessible because nothing grants access to it, not because a rule
> denies it. That means a new collection is private by default — you have to consciously add it to
> the list to expose it, rather than remembering to write a deny rule for it.

**Every publicly-readable document must carry `visibility`** — including the singletons
`profile/main` and `site_config/main`. `resource.data.visibility` on a document that lacks the field
evaluates to `null`, the read is denied, and the site renders empty with no error anywhere useful.
The schemas make the field required for exactly this reason.

**Why deny writes even for the admin?** Because a client-side write path means the browser holds
credentials capable of mutating the database, and every XSS bug then becomes a data-integrity bug.
Routing writes through the API means validation, rate limits, audit logging and business rules run
on *every* mutation with no way around them. The cost is one extra hop on a form submit — invisible
behind a spinner.

## Storage rules

```js
match /public/{allPaths=**} {
  allow read:  if true;
  allow write: if false;      // uploads happen via signed URLs the API issues
}
match /{allPaths=**} {
  allow read, write: if false;
}
```

Uploads: the admin panel asks the API for a signed URL, the API checks the admin claim and the
content type, then the browser PUTs directly to Storage. Large files never pass through the function.

---

## 2 · API auth

```
Browser ──[Firebase ID token]──▶ FastAPI dependency
                                   │
                                   ├─ verify_id_token()      ← Admin SDK, checks signature + expiry
                                   ├─ claims["admin"] == True ← the actual gate
                                   └─ else 403
```

Signing in with Google is **not** enough — anyone can do that. Authorisation is the custom
`admin: true` claim, set once on your UID by `infra/scripts/set_admin_claim.py` and verifiable only
server-side.

- Public routes: `/health`, `/contact`, `/resume`, `/sitemap.xml`
- Everything under `/api/v1/admin/*` requires the claim
- Tokens are verified on every request — no session cache, no "trust the cookie"
- Every admin mutation writes `{ actor, action, collection, docId, before, after, at }` to `audit_log`

---

## 3 · Secrets

| Secret | Where it lives |
|---|---|
| Resend API key | Secret Manager → injected into the function by Terraform |
| Turnstile secret | Secret Manager |
| Firebase Admin credentials | Ambient — the runtime service account, no key file |
| Public Firebase config | `NEXT_PUBLIC_*`, in the client bundle by design (it's not a secret) |

**No `.env` file is ever committed** — `.gitignore` blocks `.env*`, `service-account*.json` and
`*.tfvars` up front.

The Firebase web config being public is fine and intended; it identifies the project, it doesn't
authorise anything. The security is in the rules, not in hiding that config.

### Service accounts — least privilege

| Identity | Gets | Doesn't get |
|---|---|---|
| Functions runtime SA | Firestore user, Storage object admin, Secret accessor | Project editor, IAM admin |
| App Hosting SA | Firestore **read**, Secret accessor | Any write role |
| GitHub Actions (WIF) | Deploy functions, apply Terraform | Long-lived key — there isn't one |

---

## 4 · Contact form defence

A public form that writes to your database is the one genuinely exposed surface on the site.
Five stacked defences:

1. **Honeypot field** — hidden input; if filled, accept the request and silently discard it
2. **Cloudflare Turnstile** — verified server-side, not just rendered
3. **Rate limit** — 3/hour per IP, 20/hour globally, in Firestore
4. **Body size cap** — 5 KB, rejected before parsing
5. **Spam scoring** — the Firestore trigger scores links, keywords and entropy, flags rather than deletes

Failures return a generic success message. Telling a bot *why* it was rejected just helps it tune.

---

## 5 · Headers & transport

Set in `next.config.ts`:

```
Content-Security-Policy       # scripts limited to self + Firebase + Turnstile
Strict-Transport-Security     # max-age 63072000, includeSubDomains, preload
X-Content-Type-Options        # nosniff
Referrer-Policy               # strict-origin-when-cross-origin
Permissions-Policy            # camera, mic, geolocation all denied
X-Frame-Options               # DENY
```

CORS on the API: `nikunjramani.in`, `www.nikunjramani.in` and `localhost:3000` only — not `*`.

---

## 6 · Backups

Nightly scheduled function exports every Firestore collection to Storage as JSON, retained 30 days
with a lifecycle rule. Verified weekly by a CI job that checks the export actually landed — an
unverified backup isn't a backup.

---

**Next:** [04 · Infrastructure](./04-infrastructure.md)
