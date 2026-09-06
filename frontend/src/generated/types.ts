/**
 * DO NOT EDIT. Generated from architecture/schemas by `make gen`.
 * CI regenerates this and fails on any diff. See ADR 0006.
 */
/* eslint-disable */
export type MediaType = "image" | "video" | "diagram";
/**
 * public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.
 */
export type Visibility = "public" | "unlisted" | "draft";
export type EmploymentType =
  | "full-time"
  | "part-time"
  | "contract"
  | "internship"
  | "freelance";
export type SkillCategory =
  | "backend"
  | "frontend"
  | "cloud-devops"
  | "data"
  | "mobile"
  | "tools";
export type SocialPlatform =
  | "github"
  | "linkedin"
  | "x"
  | "stackoverflow"
  | "medium"
  | "instagram"
  | "youtube"
  | "email"
  | "other";
export type ProjectKind =
  | "professional"
  | "personal"
  | "open-source"
  | "academic"
  | "freelance"
  | "experiment";
export type ProjectStatus =
  | "concept"
  | "in-progress"
  | "shipped"
  | "maintained"
  | "archived";
/**
 * An open-ended list on purpose — links are an array so new kinds need no schema change.
 */
export type LinkType =
  | "live"
  | "repo"
  | "docs"
  | "case-study"
  | "demo"
  | "paper"
  | "store"
  | "article"
  | "video"
  | "other";

/**
 * Who changed what, when. Written by the API on every admin mutation. Never client-readable.
 */
export interface AuditLog {
  /**
   * Firebase Auth uid.
   */
  actor: string;
  actorEmail?: string;
  action: "create" | "update" | "delete" | "publish" | "unpublish" | "reorder";
  collection: string;
  docId?: string;
  before?: {
    [k: string]: unknown;
  } | null;
  after?: {
    [k: string]: unknown;
  } | null;
  at: string;
}
export interface Certification {
  title: string;
  issuer: string;
  issuedOn?: string;
  expiresOn?: string | null;
  credentialId?: string;
  credentialUrl?: string;
  logo?: Media;
  order?: number;
  visibility: Visibility;
  audit?: Audit;
}
/**
 * An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.
 */
export interface Media {
  url: string;
  /**
   * Required on every image. The admin panel will not let one be used without it.
   */
  alt: string;
  caption?: string;
  type?: MediaType;
  width?: number;
  height?: number;
  blurhash?: string;
}
/**
 * Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.
 */
export interface Audit {
  createdAt?: string;
  updatedAt?: string;
  publishedAt?: string | null;
  /**
   * Firebase Auth uid.
   */
  createdBy?: string;
}
/**
 * Never client-readable or client-writable. Created only by the API after Turnstile, honeypot and rate-limit checks pass. Server-set fields are marked below.
 */
export interface ContactMessage {
  name: string;
  email: string;
  subject?: string;
  message: string;
  /**
   * Server-set.
   */
  ip?: string;
  /**
   * Server-set.
   */
  userAgent?: string;
  /**
   * Server-set by the on_contact_created trigger. Flags rather than deletes.
   */
  spamScore?: number;
  read?: boolean;
  replied?: boolean;
  createdAt?: string;
  /**
   * TTL field. Firestore deletes the document after this.
   */
  expiresAt?: string;
}
export interface Education {
  institution: string;
  qualification: string;
  field?: string;
  startYear?: number;
  endYear?: number | null;
  grade?: string;
  location?: string;
  /**
   * @maxItems 6
   */
  highlights?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string];
  logo?: Media;
  order?: number;
  visibility: Visibility;
  audit?: Audit;
}
/**
 * A role. Unlike projects, jobs genuinely have a start and an end, so real dates are kept here — see ADR 0008.
 */
export interface Experience {
  company: string;
  role: string;
  employmentType?: EmploymentType;
  location?: string;
  remote?: boolean;
  /**
   * YYYY-MM.
   */
  startDate: string;
  endDate?: string | null;
  current: boolean;
  summary?: string;
  /**
   * Achievements with numbers, not duties. 'Cut API p95 from 800ms to 120ms' beats 'worked on APIs'.
   *
   * @maxItems 8
   */
  highlights?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string]
    | [string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string];
  /**
   * @maxItems 25
   */
  stack?: Tech[];
  companyLogo?: Media;
  companyUrl?: string;
  /**
   * @maxItems 6
   */
  promotions?:
    | []
    | [
        {
          role: string;
          date: string;
        },
      ]
    | [
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
      ]
    | [
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
      ]
    | [
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
      ]
    | [
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
      ]
    | [
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
        {
          role: string;
          date: string;
        },
      ];
  teamSize?: number;
  order?: number;
  visibility: Visibility;
  audit?: Audit;
}
/**
 * A technology used on a project. `primary` marks the few worth showing on a card.
 */
export interface Tech {
  name: string;
  category?: SkillCategory;
  primary?: boolean;
}
/**
 * Blog post. Schema exists from Phase 1 so the shape is settled; the UI ships in Phase 8 behind the showBlog flag.
 */
export interface Post {
  slug: string;
  title: string;
  excerpt?: string;
  contentMd?: string;
  cover?: Media;
  /**
   * @maxItems 10
   */
  tags?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string]
    | [string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string, string]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ];
  readingMinutes?: number;
  featured?: boolean;
  visibility: Visibility;
  seo?: Seo;
  audit?: Audit;
}
/**
 * Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.
 */
export interface Seo {
  /**
   * Google truncates past ~60 characters.
   */
  metaTitle?: string;
  metaDescription?: string;
  ogImageUrl?: string;
  /**
   * @maxItems 12
   */
  keywords?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string]
    | [string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string, string]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ];
  noIndex?: boolean;
}
/**
 * Singleton at profile/main. Note `visibility` is required even though drafting a profile is not a thing you would want: the security rule reads resource.data.visibility, and on a document missing the field that evaluates to null, the read is denied, and the site renders empty with no useful error.
 */
export interface Profile {
  name: string;
  /**
   * One line, what you do. 'Backend engineer building data-heavy systems', not 'passionate developer'.
   */
  headline: string;
  tagline?: string;
  /**
   * Markdown. Three paragraphs: what you do, how you got here, who you are outside work.
   */
  bio?: string;
  location?: string;
  email?: string;
  avatar?: Media;
  ogImage?: Media;
  resumeUrl?: string;
  availableForWork?: boolean;
  /**
   * @maxItems 12
   */
  socials?:
    | []
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ]
    | [
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
        {
          platform: SocialPlatform;
          label?: string;
          url: string;
        },
      ];
  visibility: Visibility;
  seo?: Seo;
  audit?: Audit;
}
/**
 * A portfolio project. Six required fields; everything else optional and rendered only when filled. A project with three fields must look intentional, not broken. See ADR 0008.
 */
export interface Project {
  /**
   * URL segment. Unique across the collection — enforced by the service, not the schema.
   */
  slug: string;
  title: string;
  subtitle?: string;
  /**
   * One or two lines. This is the card text and the fallback meta description.
   */
  summary: string;
  kind: ProjectKind;
  status: ProjectStatus;
  visibility: Visibility;
  timeline?: Timeline;
  /**
   * The story. Every block is optional and renders only when present.
   */
  content?: {
    overview?: string;
    /**
     * What was broken, and who it hurt.
     */
    problem?: string;
    /**
     * What you built, and why that way.
     */
    approach?: string;
    architecture?: {
      description?: string;
      diagram?: Media;
      /**
       * @maxItems 20
       */
      components?:
        | []
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ]
        | [
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
            {
              name: string;
              role?: string;
              tech?: string;
            },
          ];
    };
    /**
     * @maxItems 10
     */
    challenges?:
      | []
      | [
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ]
      | [
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
          {
            title: string;
            detail?: string;
          },
        ];
    /**
     * Before/after figures. The part a recruiter actually reads.
     *
     * @maxItems 10
     */
    outcomes?:
      | []
      | [Metric]
      | [Metric, Metric]
      | [Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric, Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric, Metric, Metric, Metric, Metric]
      | [Metric, Metric, Metric, Metric, Metric, Metric, Metric, Metric, Metric]
      | [
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
          Metric,
        ];
    /**
     * @maxItems 10
     */
    learnings?:
      | []
      | [string]
      | [string, string]
      | [string, string, string]
      | [string, string, string, string]
      | [string, string, string, string, string]
      | [string, string, string, string, string, string]
      | [string, string, string, string, string, string, string]
      | [string, string, string, string, string, string, string, string]
      | [string, string, string, string, string, string, string, string, string]
      | [
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
        ];
    /**
     * @maxItems 10
     */
    futureWork?:
      | []
      | [string]
      | [string, string]
      | [string, string, string]
      | [string, string, string, string]
      | [string, string, string, string, string]
      | [string, string, string, string, string, string]
      | [string, string, string, string, string, string, string]
      | [string, string, string, string, string, string, string, string]
      | [string, string, string, string, string, string, string, string, string]
      | [
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
          string,
        ];
  };
  /**
   * @maxItems 30
   */
  stack?: Tech[];
  /**
   * @maxItems 15
   */
  tags?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string]
    | [string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string, string]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ];
  role?: string;
  team?: {
    size?: number;
    myScope?: string;
  };
  /**
   * When confidential is true the name is stripped server-side in lib/data/ and never reaches the browser. Filtering in a component would still ship it in the RSC payload.
   */
  client?: {
    name?: string;
    logoUrl?: string;
    confidential?: boolean;
    /**
     * Shown instead of the name when confidential, e.g. 'a logistics client'.
     */
    publicLabel?: string;
  };
  cover?: Media;
  /**
   * @maxItems 20
   */
  gallery?:
    | []
    | [Media]
    | [Media, Media]
    | [Media, Media, Media]
    | [Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media, Media, Media, Media, Media]
    | [Media, Media, Media, Media, Media, Media, Media, Media, Media, Media]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ]
    | [
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
        Media,
      ];
  /**
   * @maxItems 12
   */
  links?:
    | []
    | [Link]
    | [Link, Link]
    | [Link, Link, Link]
    | [Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link, Link, Link, Link, Link]
    | [Link, Link, Link, Link, Link, Link, Link, Link, Link, Link, Link, Link];
  testimonial?: {
    quote: string;
    author: string;
    role?: string;
    avatarUrl?: string;
  };
  /**
   * @maxItems 8
   */
  metrics?:
    | []
    | [Metric]
    | [Metric, Metric]
    | [Metric, Metric, Metric]
    | [Metric, Metric, Metric, Metric]
    | [Metric, Metric, Metric, Metric, Metric]
    | [Metric, Metric, Metric, Metric, Metric, Metric]
    | [Metric, Metric, Metric, Metric, Metric, Metric, Metric]
    | [Metric, Metric, Metric, Metric, Metric, Metric, Metric, Metric];
  /**
   * @maxItems 8
   */
  awards?:
    | []
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ]
    | [
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
        {
          title: string;
          issuer?: string;
          year?: number;
          url?: string;
        },
      ];
  /**
   * @maxItems 15
   */
  collaborators?:
    | []
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ]
    | [
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
        {
          name: string;
          role?: string;
          url?: string;
        },
      ];
  featured?: boolean;
  pinned?: boolean;
  order?: number;
  readingMinutes?: number;
  seo?: Seo;
  audit?: Audit;
}
/**
 * Replaces start/end dates for projects, which have fuzzy edges: 'a weekend', 'on and off through 2024-25', 'still maintained'. displayLabel is what renders; year and durationMonths exist only for sorting and filtering. See ADR 0008.
 */
export interface Timeline {
  /**
   * Free text, e.g. '2025 · 4 months'. Wins over everything else for display.
   */
  displayLabel?: string;
  year?: number;
  durationMonths?: number;
  ongoing?: boolean;
}
/**
 * A measurable outcome. 'Cut p95 from 800ms to 120ms' is what a reader remembers; 'improved performance' is not.
 */
export interface Metric {
  label: string;
  /**
   * Standalone figure, when there is no before/after.
   */
  value?: string;
  before?: string;
  after?: string;
  /**
   * e.g. '-85%'.
   */
  delta?: string;
  icon?: string;
  highlight?: boolean;
}
/**
 * An outbound link. Links are stored as an array of these rather than a fixed object, so a new kind of link needs no schema change.
 */
export interface Link {
  type: LinkType;
  label?: string;
  url: string;
  /**
   * At most one per record. Rendered as the main call to action.
   */
  primary?: boolean;
}
/**
 * Singleton at site_config/main. Requires `visibility` for the same reason Profile does.
 */
export interface SiteConfig {
  showBlog?: boolean;
  showTestimonials?: boolean;
  maintenanceMode?: boolean;
  announcement?: {
    enabled?: boolean;
    message?: string;
    url?: string;
  };
  defaultSeo?: Seo;
  visibility: Visibility;
  audit?: Audit;
}
export interface Skill {
  name: string;
  category: SkillCategory;
  /**
   * 5 means you are the person others ask. Be honest with the 5s.
   */
  level: number;
  yearsOfExperience?: number;
  icon?: string;
  blurb?: string;
  /**
   * Projects that used this skill. Rendered as links.
   *
   * @maxItems 10
   */
  projectSlugs?:
    | []
    | [string]
    | [string, string]
    | [string, string, string]
    | [string, string, string, string]
    | [string, string, string, string, string]
    | [string, string, string, string, string, string]
    | [string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string]
    | [string, string, string, string, string, string, string, string, string]
    | [
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
        string,
      ];
  certificationUrl?: string;
  featured?: boolean;
  order?: number;
  visibility: Visibility;
  audit?: Audit;
}
