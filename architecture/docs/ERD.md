# Data Model — generated

> DO NOT EDIT. Generated from `architecture/schemas` by `make gen`.
> Edit the schemas instead.

## Collections

| Collection | Model | Public read | Required fields | Indexes |
|---|---|---|---|---|
| `audit_log` | **AuditLog** | ❌ | `actor`, `action`, `collection`, `at` | 2 |
| `certifications` | **Certification** | ✅ | `title`, `issuer`, `visibility` | 1 |
| `contact_messages` | **ContactMessage** | ❌ | `name`, `email`, `message` | 1 |
| `education` | **Education** | ✅ | `institution`, `qualification`, `visibility` | 1 |
| `experience` | **Experience** | ✅ | `company`, `role`, `startDate`, `current`, `visibility` | 2 |
| `posts` | **Post** | ✅ | `slug`, `title`, `visibility` | 2 |
| `profile` | **Profile** | ✅ | `name`, `headline`, `visibility` | 0 |
| `projects` | **Project** | ✅ | `slug`, `title`, `summary`, `kind`, `status`, `visibility` | 3 |
| `site_config` | **SiteConfig** | ✅ | `visibility` | 0 |
| `skills` | **Skill** | ✅ | `name`, `category`, `level`, `visibility` | 2 |

## AuditLog

_Who changed what, when. Written by the API on every admin mutation. Never client-readable._

| Field | Type | Required |
|---|---|---|
| `actor` | string | **yes** |
| `actorEmail` | string | no |
| `action` | string | **yes** |
| `collection` | string | **yes** |
| `docId` | string | no |
| `before` | object | null | no |
| `after` | object | null | no |
| `at` | string | **yes** |

## Certification

| Field | Type | Required |
|---|---|---|
| `title` | string | **yes** |
| `issuer` | string | **yes** |
| `issuedOn` | string | no |
| `expiresOn` | string | null | no |
| `credentialId` | string | no |
| `credentialUrl` | string | no |
| `logo` | media | no |
| `order` | integer | no |
| `visibility` | visibility | **yes** |
| `audit` | audit | no |

## ContactMessage

_Never client-readable or client-writable. Created only by the API after Turnstile, honeypot and rate-limit checks pass. Server-set fields are marked below._

| Field | Type | Required |
|---|---|---|
| `name` | string | **yes** |
| `email` | string | **yes** |
| `subject` | string | no |
| `message` | string | **yes** |
| `ip` | string | no |
| `userAgent` | string | no |
| `spamScore` | number | no |
| `read` | boolean | no |
| `replied` | boolean | no |
| `createdAt` | string | no |
| `expiresAt` | string | no |

## Education

| Field | Type | Required |
|---|---|---|
| `institution` | string | **yes** |
| `qualification` | string | **yes** |
| `field` | string | no |
| `startYear` | integer | no |
| `endYear` | integer | null | no |
| `grade` | string | no |
| `location` | string | no |
| `highlights` | string[] | no |
| `logo` | media | no |
| `order` | integer | no |
| `visibility` | visibility | **yes** |
| `audit` | audit | no |

## Experience

_A role. Unlike projects, jobs genuinely have a start and an end, so real dates are kept here — see ADR 0008._

| Field | Type | Required |
|---|---|---|
| `company` | string | **yes** |
| `role` | string | **yes** |
| `employmentType` | employment-type | no |
| `location` | string | no |
| `remote` | boolean | no |
| `startDate` | string | **yes** |
| `endDate` | string | null | no |
| `current` | boolean | **yes** |
| `summary` | string | no |
| `highlights` | string[] | no |
| `stack` | tech[] | no |
| `companyLogo` | media | no |
| `companyUrl` | string | no |
| `promotions` | object[] | no |
| `teamSize` | integer | no |
| `order` | integer | no |
| `visibility` | visibility | **yes** |
| `audit` | audit | no |

## Post

_Blog post. Schema exists from Phase 1 so the shape is settled; the UI ships in Phase 8 behind the showBlog flag._

| Field | Type | Required |
|---|---|---|
| `slug` | string | **yes** |
| `title` | string | **yes** |
| `excerpt` | string | no |
| `contentMd` | string | no |
| `cover` | media | no |
| `tags` | string[] | no |
| `readingMinutes` | integer | no |
| `featured` | boolean | no |
| `visibility` | visibility | **yes** |
| `seo` | seo | no |
| `audit` | audit | no |

## Profile

_Singleton at profile/main. Note `visibility` is required even though drafting a profile is not a thing you would want: the security rule reads resource.data.visibility, and on a document missing the field that evaluates to null, the read is denied, and the site renders empty with no useful error._

| Field | Type | Required |
|---|---|---|
| `name` | string | **yes** |
| `headline` | string | **yes** |
| `tagline` | string | no |
| `bio` | string | no |
| `location` | string | no |
| `email` | string | no |
| `avatar` | media | no |
| `ogImage` | media | no |
| `resumeUrl` | string | no |
| `availableForWork` | boolean | no |
| `socials` | object[] | no |
| `visibility` | visibility | **yes** |
| `seo` | seo | no |
| `audit` | audit | no |

## Project

_A portfolio project. Six required fields; everything else optional and rendered only when filled. A project with three fields must look intentional, not broken. See ADR 0008._

| Field | Type | Required |
|---|---|---|
| `slug` | string | **yes** |
| `title` | string | **yes** |
| `subtitle` | string | no |
| `summary` | string | **yes** |
| `kind` | project-kind | **yes** |
| `status` | project-status | **yes** |
| `visibility` | visibility | **yes** |
| `timeline` | timeline | no |
| `content` | object | no |
| `stack` | tech[] | no |
| `tags` | string[] | no |
| `role` | string | no |
| `team` | object | no |
| `client` | object | no |
| `cover` | media | no |
| `gallery` | media[] | no |
| `links` | link[] | no |
| `testimonial` | object | no |
| `metrics` | metric[] | no |
| `awards` | object[] | no |
| `collaborators` | object[] | no |
| `featured` | boolean | no |
| `pinned` | boolean | no |
| `order` | integer | no |
| `readingMinutes` | integer | no |
| `seo` | seo | no |
| `audit` | audit | no |

## SiteConfig

_Singleton at site_config/main. Requires `visibility` for the same reason Profile does._

| Field | Type | Required |
|---|---|---|
| `showBlog` | boolean | no |
| `showTestimonials` | boolean | no |
| `maintenanceMode` | boolean | no |
| `announcement` | object | no |
| `defaultSeo` | seo | no |
| `visibility` | visibility | **yes** |
| `audit` | audit | no |

## Skill

| Field | Type | Required |
|---|---|---|
| `name` | string | **yes** |
| `category` | skill-category | **yes** |
| `level` | integer | **yes** |
| `yearsOfExperience` | number | no |
| `icon` | string | no |
| `blurb` | string | no |
| `projectSlugs` | string[] | no |
| `certificationUrl` | string | no |
| `featured` | boolean | no |
| `order` | integer | no |
| `visibility` | visibility | **yes** |
| `audit` | audit | no |
