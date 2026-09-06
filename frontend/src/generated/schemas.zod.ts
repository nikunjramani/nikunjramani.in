/**
 * DO NOT EDIT. Generated from architecture/schemas by `make gen`.
 * CI regenerates this and fails on any diff. See ADR 0006.
 */
/* eslint-disable */
import { z } from "zod";

export const AuditLogSchema = z
  .object({
    actor: z.string().min(1).max(128).describe("Firebase Auth uid."),
    actorEmail: z.string().email().max(200).optional(),
    action: z.enum([
      "create",
      "update",
      "delete",
      "publish",
      "unpublish",
      "reorder",
    ]),
    collection: z.string().min(1).max(60),
    docId: z.string().max(128).optional(),
    before: z.union([z.record(z.any()), z.null()]).optional(),
    after: z.union([z.record(z.any()), z.null()]).optional(),
    at: z.string().datetime({ offset: true }),
  })
  .strict()
  .describe(
    "Who changed what, when. Written by the API on every admin mutation. Never client-readable.",
  );
export type AuditLogInput = z.infer<typeof AuditLogSchema>;

export const CertificationSchema = z
  .object({
    title: z.string().min(1).max(150),
    issuer: z.string().min(1).max(100),
    issuedOn: z.string().regex(new RegExp("^\\d{4}-\\d{2}$")).optional(),
    expiresOn: z
      .union([z.string().regex(new RegExp("^\\d{4}-\\d{2}$")), z.null()])
      .optional(),
    credentialId: z.string().max(100).optional(),
    credentialUrl: z.string().url().optional(),
    logo: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    order: z.number().int().gte(0).default(0),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict();
export type CertificationInput = z.infer<typeof CertificationSchema>;

export const ContactMessageSchema = z
  .object({
    name: z.string().min(1).max(100),
    email: z.string().email().max(200),
    subject: z.string().max(200).optional(),
    message: z.string().min(1).max(5000),
    ip: z.string().max(45).describe("Server-set.").optional(),
    userAgent: z.string().max(500).describe("Server-set.").optional(),
    spamScore: z
      .number()
      .gte(0)
      .lte(1)
      .describe(
        "Server-set by the on_contact_created trigger. Flags rather than deletes.",
      )
      .optional(),
    read: z.boolean().default(false),
    replied: z.boolean().default(false),
    createdAt: z.string().datetime({ offset: true }).optional(),
    expiresAt: z
      .string()
      .datetime({ offset: true })
      .describe("TTL field. Firestore deletes the document after this.")
      .optional(),
  })
  .strict()
  .describe(
    "Never client-readable or client-writable. Created only by the API after Turnstile, honeypot and rate-limit checks pass. Server-set fields are marked below.",
  );
export type ContactMessageInput = z.infer<typeof ContactMessageSchema>;

export const EducationSchema = z
  .object({
    institution: z.string().min(1).max(150),
    qualification: z.string().min(1).max(150),
    field: z.string().max(150).optional(),
    startYear: z.number().int().gte(1950).lte(2100).optional(),
    endYear: z
      .union([z.number().int().gte(1950).lte(2100), z.null()])
      .optional(),
    grade: z.string().max(40).optional(),
    location: z.string().max(80).optional(),
    highlights: z.array(z.string().max(300)).max(6).optional(),
    logo: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    order: z.number().int().gte(0).default(0),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict();
export type EducationInput = z.infer<typeof EducationSchema>;

export const ExperienceSchema = z
  .object({
    company: z.string().min(1).max(100),
    role: z.string().min(1).max(100),
    employmentType: z
      .enum(["full-time", "part-time", "contract", "internship", "freelance"])
      .optional(),
    location: z.string().max(80).optional(),
    remote: z.boolean().default(false),
    startDate: z
      .string()
      .regex(new RegExp("^\\d{4}-\\d{2}$"))
      .describe("YYYY-MM."),
    endDate: z
      .union([z.string().regex(new RegExp("^\\d{4}-\\d{2}$")), z.null()])
      .optional(),
    current: z.boolean().default(false),
    summary: z.string().max(600).optional(),
    highlights: z
      .array(z.string().min(1).max(400))
      .max(8)
      .describe(
        "Achievements with numbers, not duties. 'Cut API p95 from 800ms to 120ms' beats 'worked on APIs'.",
      )
      .optional(),
    stack: z
      .array(
        z
          .object({
            name: z.string().min(1).max(40),
            category: z
              .enum([
                "backend",
                "frontend",
                "cloud-devops",
                "data",
                "mobile",
                "tools",
              ])
              .optional(),
            primary: z.boolean().default(false),
          })
          .strict()
          .describe(
            "A technology used on a project. `primary` marks the few worth showing on a card.",
          ),
      )
      .max(25)
      .optional(),
    companyLogo: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    companyUrl: z.string().url().optional(),
    promotions: z
      .array(
        z
          .object({
            role: z.string().min(1).max(100),
            date: z.string().regex(new RegExp("^\\d{4}-\\d{2}$")),
          })
          .strict(),
      )
      .max(6)
      .optional(),
    teamSize: z.number().int().gte(1).lte(10000).optional(),
    order: z.number().int().gte(0).default(0),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict()
  .describe(
    "A role. Unlike projects, jobs genuinely have a start and an end, so real dates are kept here — see ADR 0008.",
  );
export type ExperienceInput = z.infer<typeof ExperienceSchema>;

export const PostSchema = z
  .object({
    slug: z
      .string()
      .regex(new RegExp("^[a-z0-9]+(?:-[a-z0-9]+)*$"))
      .min(2)
      .max(80),
    title: z.string().min(1).max(140),
    excerpt: z.string().max(300).optional(),
    contentMd: z.string().max(100000).optional(),
    cover: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    tags: z.array(z.string().max(40)).max(10).optional(),
    readingMinutes: z.number().int().gte(1).lte(120).optional(),
    featured: z.boolean().default(false),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    seo: z
      .object({
        metaTitle: z
          .string()
          .max(70)
          .describe("Google truncates past ~60 characters.")
          .optional(),
        metaDescription: z.string().max(160).optional(),
        ogImageUrl: z.string().url().optional(),
        keywords: z.array(z.string().max(40)).max(12).optional(),
        noIndex: z.boolean().default(false),
      })
      .strict()
      .describe(
        "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
      )
      .optional(),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict()
  .describe(
    "Blog post. Schema exists from Phase 1 so the shape is settled; the UI ships in Phase 8 behind the showBlog flag.",
  );
export type PostInput = z.infer<typeof PostSchema>;

export const ProfileSchema = z
  .object({
    name: z.string().min(1).max(80),
    headline: z
      .string()
      .min(1)
      .max(120)
      .describe(
        "One line, what you do. 'Backend engineer building data-heavy systems', not 'passionate developer'.",
      ),
    tagline: z.string().max(300).optional(),
    bio: z
      .string()
      .max(6000)
      .describe(
        "Markdown. Three paragraphs: what you do, how you got here, who you are outside work.",
      )
      .optional(),
    location: z.string().max(80).optional(),
    email: z.string().email().max(200).optional(),
    avatar: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    ogImage: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    resumeUrl: z.string().url().optional(),
    availableForWork: z.boolean().default(false),
    socials: z
      .array(
        z
          .object({
            platform: z.enum([
              "github",
              "linkedin",
              "x",
              "stackoverflow",
              "medium",
              "instagram",
              "youtube",
              "email",
              "other",
            ]),
            label: z.string().max(40).optional(),
            url: z.string().url(),
          })
          .strict(),
      )
      .max(12)
      .optional(),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    seo: z
      .object({
        metaTitle: z
          .string()
          .max(70)
          .describe("Google truncates past ~60 characters.")
          .optional(),
        metaDescription: z.string().max(160).optional(),
        ogImageUrl: z.string().url().optional(),
        keywords: z.array(z.string().max(40)).max(12).optional(),
        noIndex: z.boolean().default(false),
      })
      .strict()
      .describe(
        "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
      )
      .optional(),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict()
  .describe(
    "Singleton at profile/main. Note `visibility` is required even though drafting a profile is not a thing you would want: the security rule reads resource.data.visibility, and on a document missing the field that evaluates to null, the read is denied, and the site renders empty with no useful error.",
  );
export type ProfileInput = z.infer<typeof ProfileSchema>;

export const ProjectSchema = z
  .object({
    slug: z
      .string()
      .regex(new RegExp("^[a-z0-9]+(?:-[a-z0-9]+)*$"))
      .min(2)
      .max(80)
      .describe(
        "URL segment. Unique across the collection — enforced by the service, not the schema.",
      ),
    title: z.string().min(1).max(100),
    subtitle: z.string().max(140).optional(),
    summary: z
      .string()
      .min(1)
      .max(280)
      .describe(
        "One or two lines. This is the card text and the fallback meta description.",
      ),
    kind: z.enum([
      "professional",
      "personal",
      "open-source",
      "academic",
      "freelance",
      "experiment",
    ]),
    status: z.enum([
      "concept",
      "in-progress",
      "shipped",
      "maintained",
      "archived",
    ]),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    timeline: z
      .object({
        displayLabel: z
          .string()
          .max(60)
          .describe(
            "Free text, e.g. '2025 · 4 months'. Wins over everything else for display.",
          )
          .optional(),
        year: z.number().int().gte(1990).lte(2100).optional(),
        durationMonths: z.number().int().gte(1).lte(600).optional(),
        ongoing: z.boolean().default(false),
      })
      .strict()
      .describe(
        "Replaces start/end dates for projects, which have fuzzy edges: 'a weekend', 'on and off through 2024-25', 'still maintained'. displayLabel is what renders; year and durationMonths exist only for sorting and filtering. See ADR 0008.",
      )
      .optional(),
    content: z
      .object({
        overview: z.string().max(4000).optional(),
        problem: z
          .string()
          .max(4000)
          .describe("What was broken, and who it hurt.")
          .optional(),
        approach: z
          .string()
          .max(4000)
          .describe("What you built, and why that way.")
          .optional(),
        architecture: z
          .object({
            description: z.string().max(4000).optional(),
            diagram: z
              .object({
                url: z.string().url(),
                alt: z
                  .string()
                  .min(1)
                  .max(200)
                  .describe(
                    "Required on every image. The admin panel will not let one be used without it.",
                  ),
                caption: z.string().max(300).optional(),
                type: z.enum(["image", "video", "diagram"]).default("image"),
                width: z.number().int().gte(1).optional(),
                height: z.number().int().gte(1).optional(),
                blurhash: z.string().max(64).optional(),
              })
              .strict()
              .describe(
                "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
              )
              .optional(),
            components: z
              .array(
                z
                  .object({
                    name: z.string().min(1).max(60),
                    role: z.string().max(200).optional(),
                    tech: z.string().max(60).optional(),
                  })
                  .strict(),
              )
              .max(20)
              .optional(),
          })
          .strict()
          .optional(),
        challenges: z
          .array(
            z
              .object({
                title: z.string().min(1).max(120),
                detail: z.string().max(2000).optional(),
              })
              .strict(),
          )
          .max(10)
          .optional(),
        outcomes: z
          .array(
            z
              .object({
                label: z.string().min(1).max(80),
                value: z
                  .string()
                  .max(40)
                  .describe("Standalone figure, when there is no before/after.")
                  .optional(),
                before: z.string().max(40).optional(),
                after: z.string().max(40).optional(),
                delta: z.string().max(40).describe("e.g. '-85%'.").optional(),
                icon: z.string().max(40).optional(),
                highlight: z.boolean().default(false),
              })
              .strict()
              .describe(
                "A measurable outcome. 'Cut p95 from 800ms to 120ms' is what a reader remembers; 'improved performance' is not.",
              ),
          )
          .max(10)
          .describe(
            "Before/after figures. The part a recruiter actually reads.",
          )
          .optional(),
        learnings: z.array(z.string().max(500)).max(10).optional(),
        futureWork: z.array(z.string().max(500)).max(10).optional(),
      })
      .strict()
      .describe(
        "The story. Every block is optional and renders only when present.",
      )
      .optional(),
    stack: z
      .array(
        z
          .object({
            name: z.string().min(1).max(40),
            category: z
              .enum([
                "backend",
                "frontend",
                "cloud-devops",
                "data",
                "mobile",
                "tools",
              ])
              .optional(),
            primary: z.boolean().default(false),
          })
          .strict()
          .describe(
            "A technology used on a project. `primary` marks the few worth showing on a card.",
          ),
      )
      .max(30)
      .optional(),
    tags: z.array(z.string().max(40)).max(15).optional(),
    role: z.string().max(80).optional(),
    team: z
      .object({
        size: z.number().int().gte(1).lte(1000).optional(),
        myScope: z.string().max(300).optional(),
      })
      .strict()
      .optional(),
    client: z
      .object({
        name: z.string().max(100).optional(),
        logoUrl: z.string().url().optional(),
        confidential: z.boolean().default(false),
        publicLabel: z
          .string()
          .max(100)
          .describe(
            "Shown instead of the name when confidential, e.g. 'a logistics client'.",
          )
          .optional(),
      })
      .strict()
      .describe(
        "When confidential is true the name is stripped server-side in lib/data/ and never reaches the browser. Filtering in a component would still ship it in the RSC payload.",
      )
      .optional(),
    cover: z
      .object({
        url: z.string().url(),
        alt: z
          .string()
          .min(1)
          .max(200)
          .describe(
            "Required on every image. The admin panel will not let one be used without it.",
          ),
        caption: z.string().max(300).optional(),
        type: z.enum(["image", "video", "diagram"]).default("image"),
        width: z.number().int().gte(1).optional(),
        height: z.number().int().gte(1).optional(),
        blurhash: z.string().max(64).optional(),
      })
      .strict()
      .describe(
        "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
      )
      .optional(),
    gallery: z
      .array(
        z
          .object({
            url: z.string().url(),
            alt: z
              .string()
              .min(1)
              .max(200)
              .describe(
                "Required on every image. The admin panel will not let one be used without it.",
              ),
            caption: z.string().max(300).optional(),
            type: z.enum(["image", "video", "diagram"]).default("image"),
            width: z.number().int().gte(1).optional(),
            height: z.number().int().gte(1).optional(),
            blurhash: z.string().max(64).optional(),
          })
          .strict()
          .describe(
            "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
          ),
      )
      .max(20)
      .optional(),
    links: z
      .array(
        z
          .object({
            type: z
              .enum([
                "live",
                "repo",
                "docs",
                "case-study",
                "demo",
                "paper",
                "store",
                "article",
                "video",
                "other",
              ])
              .describe(
                "An open-ended list on purpose — links are an array so new kinds need no schema change.",
              ),
            label: z.string().min(1).max(60).optional(),
            url: z.string().url().max(2048),
            primary: z
              .boolean()
              .describe(
                "At most one per record. Rendered as the main call to action.",
              )
              .default(false),
          })
          .strict()
          .describe(
            "An outbound link. Links are stored as an array of these rather than a fixed object, so a new kind of link needs no schema change.",
          ),
      )
      .max(12)
      .optional(),
    testimonial: z
      .object({
        quote: z.string().min(1).max(600),
        author: z.string().min(1).max(80),
        role: z.string().max(100).optional(),
        avatarUrl: z.string().url().optional(),
      })
      .strict()
      .optional(),
    metrics: z
      .array(
        z
          .object({
            label: z.string().min(1).max(80),
            value: z
              .string()
              .max(40)
              .describe("Standalone figure, when there is no before/after.")
              .optional(),
            before: z.string().max(40).optional(),
            after: z.string().max(40).optional(),
            delta: z.string().max(40).describe("e.g. '-85%'.").optional(),
            icon: z.string().max(40).optional(),
            highlight: z.boolean().default(false),
          })
          .strict()
          .describe(
            "A measurable outcome. 'Cut p95 from 800ms to 120ms' is what a reader remembers; 'improved performance' is not.",
          ),
      )
      .max(8)
      .optional(),
    awards: z
      .array(
        z
          .object({
            title: z.string().min(1).max(120),
            issuer: z.string().max(100).optional(),
            year: z.number().int().gte(1990).lte(2100).optional(),
            url: z.string().url().optional(),
          })
          .strict(),
      )
      .max(8)
      .optional(),
    collaborators: z
      .array(
        z
          .object({
            name: z.string().min(1).max(80),
            role: z.string().max(80).optional(),
            url: z.string().url().optional(),
          })
          .strict(),
      )
      .max(15)
      .optional(),
    featured: z.boolean().default(false),
    pinned: z.boolean().default(false),
    order: z.number().int().gte(0).default(0),
    readingMinutes: z.number().int().gte(1).lte(60).optional(),
    seo: z
      .object({
        metaTitle: z
          .string()
          .max(70)
          .describe("Google truncates past ~60 characters.")
          .optional(),
        metaDescription: z.string().max(160).optional(),
        ogImageUrl: z.string().url().optional(),
        keywords: z.array(z.string().max(40)).max(12).optional(),
        noIndex: z.boolean().default(false),
      })
      .strict()
      .describe(
        "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
      )
      .optional(),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict()
  .describe(
    "A portfolio project. Six required fields; everything else optional and rendered only when filled. A project with three fields must look intentional, not broken. See ADR 0008.",
  );
export type ProjectInput = z.infer<typeof ProjectSchema>;

export const SiteConfigSchema = z
  .object({
    showBlog: z.boolean().default(false),
    showTestimonials: z.boolean().default(false),
    maintenanceMode: z.boolean().default(false),
    announcement: z
      .object({
        enabled: z.boolean().default(false),
        message: z.string().max(200).optional(),
        url: z.string().url().optional(),
      })
      .strict()
      .optional(),
    defaultSeo: z
      .object({
        metaTitle: z
          .string()
          .max(70)
          .describe("Google truncates past ~60 characters.")
          .optional(),
        metaDescription: z.string().max(160).optional(),
        ogImageUrl: z.string().url().optional(),
        keywords: z.array(z.string().max(40)).max(12).optional(),
        noIndex: z.boolean().default(false),
      })
      .strict()
      .describe(
        "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
      )
      .optional(),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict()
  .describe(
    "Singleton at site_config/main. Requires `visibility` for the same reason Profile does.",
  );
export type SiteConfigInput = z.infer<typeof SiteConfigSchema>;

export const SkillSchema = z
  .object({
    name: z.string().min(1).max(40),
    category: z.enum([
      "backend",
      "frontend",
      "cloud-devops",
      "data",
      "mobile",
      "tools",
    ]),
    level: z
      .number()
      .int()
      .gte(1)
      .lte(5)
      .describe(
        "5 means you are the person others ask. Be honest with the 5s.",
      ),
    yearsOfExperience: z.number().gte(0).lte(60).optional(),
    icon: z.string().max(40).optional(),
    blurb: z.string().max(300).optional(),
    projectSlugs: z
      .array(z.string().max(80))
      .max(10)
      .describe("Projects that used this skill. Rendered as links.")
      .optional(),
    certificationUrl: z.string().url().optional(),
    featured: z.boolean().default(false),
    order: z.number().int().gte(0).default(0),
    visibility: z
      .enum(["public", "unlisted", "draft"])
      .describe(
        "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
      ),
    audit: z
      .object({
        createdAt: z.string().datetime({ offset: true }).optional(),
        updatedAt: z.string().datetime({ offset: true }).optional(),
        publishedAt: z
          .union([z.string().datetime({ offset: true }), z.null()])
          .optional(),
        createdBy: z
          .string()
          .max(128)
          .describe("Firebase Auth uid.")
          .optional(),
      })
      .strict()
      .describe(
        "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
      )
      .optional(),
  })
  .strict();
export type SkillInput = z.infer<typeof SkillSchema>;
