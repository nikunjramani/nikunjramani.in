/**
 * DO NOT EDIT. Generated from architecture/schemas by `make gen`.
 * CI regenerates this and fails on any diff. See ADR 0006.
 */
/* eslint-disable */
import type { JSONSchema7 } from "json-schema";

export interface AdminSchemaEntry {
  title: string;
  collection: string;
  apiDomain: string;
  slugged: boolean;
  singleton: boolean;
  required: string[];
  properties: Record<string, JSONSchema7>;
}

export const ADMIN_SCHEMAS = {
  Certification: {
    title: "Certification",
    collection: "certifications",
    apiDomain: "certifications",
    slugged: false,
    singleton: false,
    required: ["title", "issuer", "visibility"],
    properties: {
      title: { type: "string", minLength: 1, maxLength: 150 },
      issuer: { type: "string", minLength: 1, maxLength: 100 },
      issuedOn: { type: "string", pattern: "^\\d{4}-\\d{2}$" },
      expiresOn: { type: ["string", "null"], pattern: "^\\d{4}-\\d{2}$" },
      credentialId: { type: "string", maxLength: 100 },
      credentialUrl: { type: "string", format: "uri" },
      logo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      order: { type: "integer", minimum: 0, default: 0 },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Education: {
    title: "Education",
    collection: "education",
    apiDomain: "education",
    slugged: false,
    singleton: false,
    required: ["institution", "qualification", "visibility"],
    properties: {
      institution: { type: "string", minLength: 1, maxLength: 150 },
      qualification: { type: "string", minLength: 1, maxLength: 150 },
      field: { type: "string", maxLength: 150 },
      startYear: { type: "integer", minimum: 1950, maximum: 2100 },
      endYear: { type: ["integer", "null"], minimum: 1950, maximum: 2100 },
      grade: { type: "string", maxLength: 40 },
      location: { type: "string", maxLength: 80 },
      highlights: {
        type: "array",
        maxItems: 6,
        items: { type: "string", maxLength: 300 },
      },
      logo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      order: { type: "integer", minimum: 0, default: 0 },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Experience: {
    title: "Experience",
    collection: "experience",
    apiDomain: "experience",
    slugged: false,
    singleton: false,
    required: ["company", "role", "startDate", "current", "visibility"],
    properties: {
      company: { type: "string", minLength: 1, maxLength: 100 },
      role: { type: "string", minLength: 1, maxLength: 100 },
      employmentType: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/employment-type.json",
        title: "EmploymentType",
        type: "string",
        enum: ["full-time", "part-time", "contract", "internship", "freelance"],
      },
      location: { type: "string", maxLength: 80 },
      remote: { type: "boolean", default: false },
      startDate: {
        type: "string",
        pattern: "^\\d{4}-\\d{2}$",
        description: "YYYY-MM.",
      },
      endDate: { type: ["string", "null"], pattern: "^\\d{4}-\\d{2}$" },
      current: { type: "boolean", default: false },
      summary: { type: "string", maxLength: 600 },
      highlights: {
        type: "array",
        maxItems: 8,
        items: { type: "string", minLength: 1, maxLength: 400 },
        description:
          "Achievements with numbers, not duties. 'Cut API p95 from 800ms to 120ms' beats 'worked on APIs'.",
      },
      stack: {
        type: "array",
        maxItems: 25,
        items: {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          $id: "common/tech.schema.json",
          title: "Tech",
          description:
            "A technology used on a project. `primary` marks the few worth showing on a card.",
          type: "object",
          properties: {
            name: { type: "string", minLength: 1, maxLength: 40 },
            category: {
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "enums/skill-category.json",
              title: "SkillCategory",
              type: "string",
              enum: [
                "backend",
                "frontend",
                "cloud-devops",
                "data",
                "mobile",
                "tools",
              ],
            },
            primary: { type: "boolean", default: false },
          },
          required: ["name"],
          additionalProperties: false,
        },
      },
      companyLogo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      companyUrl: { type: "string", format: "uri" },
      promotions: {
        type: "array",
        maxItems: 6,
        items: {
          type: "object",
          properties: {
            role: { type: "string", minLength: 1, maxLength: 100 },
            date: { type: "string", pattern: "^\\d{4}-\\d{2}$" },
          },
          required: ["role", "date"],
          additionalProperties: false,
        },
      },
      teamSize: { type: "integer", minimum: 1, maximum: 10000 },
      order: { type: "integer", minimum: 0, default: 0 },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Post: {
    title: "Post",
    collection: "posts",
    apiDomain: "posts",
    slugged: true,
    singleton: false,
    required: ["slug", "title", "visibility"],
    properties: {
      slug: {
        type: "string",
        pattern: "^[a-z0-9]+(?:-[a-z0-9]+)*$",
        minLength: 2,
        maxLength: 80,
      },
      title: { type: "string", minLength: 1, maxLength: 140 },
      excerpt: { type: "string", maxLength: 300 },
      contentMd: { type: "string", maxLength: 100000 },
      cover: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      tags: {
        type: "array",
        maxItems: 10,
        items: { type: "string", maxLength: 40 },
      },
      readingMinutes: { type: "integer", minimum: 1, maximum: 120 },
      featured: { type: "boolean", default: false },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      seo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/seo.schema.json",
        title: "Seo",
        description:
          "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
        type: "object",
        properties: {
          metaTitle: {
            type: "string",
            maxLength: 70,
            description: "Google truncates past ~60 characters.",
          },
          metaDescription: { type: "string", maxLength: 160 },
          ogImageUrl: { type: "string", format: "uri" },
          keywords: {
            type: "array",
            items: { type: "string", maxLength: 40 },
            maxItems: 12,
          },
          noIndex: { type: "boolean", default: false },
        },
        additionalProperties: false,
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Profile: {
    title: "Profile",
    collection: "profile",
    apiDomain: "profile",
    slugged: false,
    singleton: true,
    required: ["name", "headline", "visibility"],
    properties: {
      name: { type: "string", minLength: 1, maxLength: 80 },
      headline: {
        type: "string",
        minLength: 1,
        maxLength: 120,
        description:
          "One line, what you do. 'Backend engineer building data-heavy systems', not 'passionate developer'.",
      },
      tagline: { type: "string", maxLength: 300 },
      bio: {
        type: "string",
        maxLength: 6000,
        description:
          "Markdown. Three paragraphs: what you do, how you got here, who you are outside work.",
      },
      location: { type: "string", maxLength: 80 },
      email: { type: "string", format: "email", maxLength: 200 },
      avatar: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      ogImage: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      resumeUrl: { type: "string", format: "uri" },
      availableForWork: { type: "boolean", default: false },
      socials: {
        type: "array",
        maxItems: 12,
        items: {
          type: "object",
          properties: {
            platform: {
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "enums/social-platform.json",
              title: "SocialPlatform",
              type: "string",
              enum: [
                "github",
                "linkedin",
                "x",
                "stackoverflow",
                "medium",
                "instagram",
                "youtube",
                "email",
                "other",
              ],
            },
            label: { type: "string", maxLength: 40 },
            url: { type: "string", format: "uri" },
          },
          required: ["platform", "url"],
          additionalProperties: false,
        },
      },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      seo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/seo.schema.json",
        title: "Seo",
        description:
          "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
        type: "object",
        properties: {
          metaTitle: {
            type: "string",
            maxLength: 70,
            description: "Google truncates past ~60 characters.",
          },
          metaDescription: { type: "string", maxLength: 160 },
          ogImageUrl: { type: "string", format: "uri" },
          keywords: {
            type: "array",
            items: { type: "string", maxLength: 40 },
            maxItems: 12,
          },
          noIndex: { type: "boolean", default: false },
        },
        additionalProperties: false,
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Project: {
    title: "Project",
    collection: "projects",
    apiDomain: "projects",
    slugged: true,
    singleton: false,
    required: ["slug", "title", "summary", "kind", "status", "visibility"],
    properties: {
      slug: {
        type: "string",
        pattern: "^[a-z0-9]+(?:-[a-z0-9]+)*$",
        minLength: 2,
        maxLength: 80,
        description:
          "URL segment. Unique across the collection — enforced by the service, not the schema.",
      },
      title: { type: "string", minLength: 1, maxLength: 100 },
      subtitle: { type: "string", maxLength: 140 },
      summary: {
        type: "string",
        minLength: 1,
        maxLength: 280,
        description:
          "One or two lines. This is the card text and the fallback meta description.",
      },
      kind: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/project-kind.json",
        title: "ProjectKind",
        type: "string",
        enum: [
          "professional",
          "personal",
          "open-source",
          "academic",
          "freelance",
          "experiment",
        ],
      },
      status: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/project-status.json",
        title: "ProjectStatus",
        type: "string",
        enum: ["concept", "in-progress", "shipped", "maintained", "archived"],
      },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      timeline: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/timeline.schema.json",
        title: "Timeline",
        description:
          "Replaces start/end dates for projects, which have fuzzy edges: 'a weekend', 'on and off through 2024-25', 'still maintained'. displayLabel is what renders; year and durationMonths exist only for sorting and filtering. See ADR 0008.",
        type: "object",
        properties: {
          displayLabel: {
            type: "string",
            maxLength: 60,
            description:
              "Free text, e.g. '2025 · 4 months'. Wins over everything else for display.",
          },
          year: { type: "integer", minimum: 1990, maximum: 2100 },
          durationMonths: { type: "integer", minimum: 1, maximum: 600 },
          ongoing: { type: "boolean", default: false },
        },
        additionalProperties: false,
      },
      content: {
        type: "object",
        description:
          "The story. Every block is optional and renders only when present.",
        properties: {
          overview: { type: "string", maxLength: 4000 },
          problem: {
            type: "string",
            maxLength: 4000,
            description: "What was broken, and who it hurt.",
          },
          approach: {
            type: "string",
            maxLength: 4000,
            description: "What you built, and why that way.",
          },
          architecture: {
            type: "object",
            properties: {
              description: { type: "string", maxLength: 4000 },
              diagram: {
                $schema: "https://json-schema.org/draft/2020-12/schema",
                $id: "common/media.schema.json",
                title: "Media",
                description:
                  "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
                type: "object",
                properties: {
                  url: { type: "string", format: "uri" },
                  alt: {
                    type: "string",
                    minLength: 1,
                    maxLength: 200,
                    description:
                      "Required on every image. The admin panel will not let one be used without it.",
                  },
                  caption: { type: "string", maxLength: 300 },
                  type: {
                    default: "image",
                    $schema: "https://json-schema.org/draft/2020-12/schema",
                    $id: "enums/media-type.json",
                    title: "MediaType",
                    type: "string",
                    enum: ["image", "video", "diagram"],
                  },
                  width: { type: "integer", minimum: 1 },
                  height: { type: "integer", minimum: 1 },
                  blurhash: { type: "string", maxLength: 64 },
                },
                required: ["url", "alt"],
                additionalProperties: false,
              },
              components: {
                type: "array",
                maxItems: 20,
                items: {
                  type: "object",
                  properties: {
                    name: { type: "string", minLength: 1, maxLength: 60 },
                    role: { type: "string", maxLength: 200 },
                    tech: { type: "string", maxLength: 60 },
                  },
                  required: ["name"],
                  additionalProperties: false,
                },
              },
            },
            additionalProperties: false,
          },
          challenges: {
            type: "array",
            maxItems: 10,
            items: {
              type: "object",
              properties: {
                title: { type: "string", minLength: 1, maxLength: 120 },
                detail: { type: "string", maxLength: 2000 },
              },
              required: ["title"],
              additionalProperties: false,
            },
          },
          outcomes: {
            type: "array",
            maxItems: 10,
            items: {
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "common/metric.schema.json",
              title: "Metric",
              description:
                "A measurable outcome. 'Cut p95 from 800ms to 120ms' is what a reader remembers; 'improved performance' is not.",
              type: "object",
              properties: {
                label: { type: "string", minLength: 1, maxLength: 80 },
                value: {
                  type: "string",
                  maxLength: 40,
                  description:
                    "Standalone figure, when there is no before/after.",
                },
                before: { type: "string", maxLength: 40 },
                after: { type: "string", maxLength: 40 },
                delta: {
                  type: "string",
                  maxLength: 40,
                  description: "e.g. '-85%'.",
                },
                icon: { type: "string", maxLength: 40 },
                highlight: { type: "boolean", default: false },
              },
              required: ["label"],
              additionalProperties: false,
            },
            description:
              "Before/after figures. The part a recruiter actually reads.",
          },
          learnings: {
            type: "array",
            maxItems: 10,
            items: { type: "string", maxLength: 500 },
          },
          futureWork: {
            type: "array",
            maxItems: 10,
            items: { type: "string", maxLength: 500 },
          },
        },
        additionalProperties: false,
      },
      stack: {
        type: "array",
        maxItems: 30,
        items: {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          $id: "common/tech.schema.json",
          title: "Tech",
          description:
            "A technology used on a project. `primary` marks the few worth showing on a card.",
          type: "object",
          properties: {
            name: { type: "string", minLength: 1, maxLength: 40 },
            category: {
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "enums/skill-category.json",
              title: "SkillCategory",
              type: "string",
              enum: [
                "backend",
                "frontend",
                "cloud-devops",
                "data",
                "mobile",
                "tools",
              ],
            },
            primary: { type: "boolean", default: false },
          },
          required: ["name"],
          additionalProperties: false,
        },
      },
      tags: {
        type: "array",
        maxItems: 15,
        items: { type: "string", maxLength: 40 },
      },
      role: { type: "string", maxLength: 80 },
      team: {
        type: "object",
        properties: {
          size: { type: "integer", minimum: 1, maximum: 1000 },
          myScope: { type: "string", maxLength: 300 },
        },
        additionalProperties: false,
      },
      client: {
        type: "object",
        description:
          "When confidential is true the name is stripped server-side in lib/data/ and never reaches the browser. Filtering in a component would still ship it in the RSC payload.",
        properties: {
          name: { type: "string", maxLength: 100 },
          logoUrl: { type: "string", format: "uri" },
          confidential: { type: "boolean", default: false },
          publicLabel: {
            type: "string",
            maxLength: 100,
            description:
              "Shown instead of the name when confidential, e.g. 'a logistics client'.",
          },
        },
        additionalProperties: false,
      },
      cover: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/media.schema.json",
        title: "Media",
        description:
          "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
        type: "object",
        properties: {
          url: { type: "string", format: "uri" },
          alt: {
            type: "string",
            minLength: 1,
            maxLength: 200,
            description:
              "Required on every image. The admin panel will not let one be used without it.",
          },
          caption: { type: "string", maxLength: 300 },
          type: {
            default: "image",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            $id: "enums/media-type.json",
            title: "MediaType",
            type: "string",
            enum: ["image", "video", "diagram"],
          },
          width: { type: "integer", minimum: 1 },
          height: { type: "integer", minimum: 1 },
          blurhash: { type: "string", maxLength: 64 },
        },
        required: ["url", "alt"],
        additionalProperties: false,
      },
      gallery: {
        type: "array",
        maxItems: 20,
        items: {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          $id: "common/media.schema.json",
          title: "Media",
          description:
            "An image or video. Dimensions are stored so the frontend can reserve space and avoid layout shift; blurhash gives a placeholder while the real file loads.",
          type: "object",
          properties: {
            url: { type: "string", format: "uri" },
            alt: {
              type: "string",
              minLength: 1,
              maxLength: 200,
              description:
                "Required on every image. The admin panel will not let one be used without it.",
            },
            caption: { type: "string", maxLength: 300 },
            type: {
              default: "image",
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "enums/media-type.json",
              title: "MediaType",
              type: "string",
              enum: ["image", "video", "diagram"],
            },
            width: { type: "integer", minimum: 1 },
            height: { type: "integer", minimum: 1 },
            blurhash: { type: "string", maxLength: 64 },
          },
          required: ["url", "alt"],
          additionalProperties: false,
        },
      },
      links: {
        type: "array",
        maxItems: 12,
        items: {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          $id: "common/link.schema.json",
          title: "Link",
          description:
            "An outbound link. Links are stored as an array of these rather than a fixed object, so a new kind of link needs no schema change.",
          type: "object",
          properties: {
            type: {
              $schema: "https://json-schema.org/draft/2020-12/schema",
              $id: "enums/link-type.json",
              title: "LinkType",
              description:
                "An open-ended list on purpose — links are an array so new kinds need no schema change.",
              type: "string",
              enum: [
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
              ],
            },
            label: { type: "string", minLength: 1, maxLength: 60 },
            url: { type: "string", format: "uri", maxLength: 2048 },
            primary: {
              type: "boolean",
              default: false,
              description:
                "At most one per record. Rendered as the main call to action.",
            },
          },
          required: ["type", "url"],
          additionalProperties: false,
        },
      },
      testimonial: {
        type: "object",
        properties: {
          quote: { type: "string", minLength: 1, maxLength: 600 },
          author: { type: "string", minLength: 1, maxLength: 80 },
          role: { type: "string", maxLength: 100 },
          avatarUrl: { type: "string", format: "uri" },
        },
        required: ["quote", "author"],
        additionalProperties: false,
      },
      metrics: {
        type: "array",
        maxItems: 8,
        items: {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          $id: "common/metric.schema.json",
          title: "Metric",
          description:
            "A measurable outcome. 'Cut p95 from 800ms to 120ms' is what a reader remembers; 'improved performance' is not.",
          type: "object",
          properties: {
            label: { type: "string", minLength: 1, maxLength: 80 },
            value: {
              type: "string",
              maxLength: 40,
              description: "Standalone figure, when there is no before/after.",
            },
            before: { type: "string", maxLength: 40 },
            after: { type: "string", maxLength: 40 },
            delta: {
              type: "string",
              maxLength: 40,
              description: "e.g. '-85%'.",
            },
            icon: { type: "string", maxLength: 40 },
            highlight: { type: "boolean", default: false },
          },
          required: ["label"],
          additionalProperties: false,
        },
      },
      awards: {
        type: "array",
        maxItems: 8,
        items: {
          type: "object",
          properties: {
            title: { type: "string", minLength: 1, maxLength: 120 },
            issuer: { type: "string", maxLength: 100 },
            year: { type: "integer", minimum: 1990, maximum: 2100 },
            url: { type: "string", format: "uri" },
          },
          required: ["title"],
          additionalProperties: false,
        },
      },
      collaborators: {
        type: "array",
        maxItems: 15,
        items: {
          type: "object",
          properties: {
            name: { type: "string", minLength: 1, maxLength: 80 },
            role: { type: "string", maxLength: 80 },
            url: { type: "string", format: "uri" },
          },
          required: ["name"],
          additionalProperties: false,
        },
      },
      featured: { type: "boolean", default: false },
      pinned: { type: "boolean", default: false },
      order: { type: "integer", minimum: 0, default: 0 },
      readingMinutes: { type: "integer", minimum: 1, maximum: 60 },
      seo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/seo.schema.json",
        title: "Seo",
        description:
          "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
        type: "object",
        properties: {
          metaTitle: {
            type: "string",
            maxLength: 70,
            description: "Google truncates past ~60 characters.",
          },
          metaDescription: { type: "string", maxLength: 160 },
          ogImageUrl: { type: "string", format: "uri" },
          keywords: {
            type: "array",
            items: { type: "string", maxLength: 40 },
            maxItems: 12,
          },
          noIndex: { type: "boolean", default: false },
        },
        additionalProperties: false,
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  SiteConfig: {
    title: "SiteConfig",
    collection: "site_config",
    apiDomain: "settings",
    slugged: false,
    singleton: true,
    required: ["visibility"],
    properties: {
      showBlog: { type: "boolean", default: false },
      showTestimonials: { type: "boolean", default: false },
      maintenanceMode: { type: "boolean", default: false },
      announcement: {
        type: "object",
        properties: {
          enabled: { type: "boolean", default: false },
          message: { type: "string", maxLength: 200 },
          url: { type: "string", format: "uri" },
        },
        additionalProperties: false,
      },
      defaultSeo: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/seo.schema.json",
        title: "Seo",
        description:
          "Per-record SEO overrides. All optional — sensible values are derived from title and summary when absent.",
        type: "object",
        properties: {
          metaTitle: {
            type: "string",
            maxLength: 70,
            description: "Google truncates past ~60 characters.",
          },
          metaDescription: { type: "string", maxLength: 160 },
          ogImageUrl: { type: "string", format: "uri" },
          keywords: {
            type: "array",
            items: { type: "string", maxLength: 40 },
            maxItems: 12,
          },
          noIndex: { type: "boolean", default: false },
        },
        additionalProperties: false,
      },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
  Skill: {
    title: "Skill",
    collection: "skills",
    apiDomain: "skills",
    slugged: false,
    singleton: false,
    required: ["name", "category", "level", "visibility"],
    properties: {
      name: { type: "string", minLength: 1, maxLength: 40 },
      category: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/skill-category.json",
        title: "SkillCategory",
        type: "string",
        enum: [
          "backend",
          "frontend",
          "cloud-devops",
          "data",
          "mobile",
          "tools",
        ],
      },
      level: {
        type: "integer",
        minimum: 1,
        maximum: 5,
        description:
          "5 means you are the person others ask. Be honest with the 5s.",
      },
      yearsOfExperience: { type: "number", minimum: 0, maximum: 60 },
      icon: { type: "string", maxLength: 40 },
      blurb: { type: "string", maxLength: 300 },
      projectSlugs: {
        type: "array",
        maxItems: 10,
        items: { type: "string", maxLength: 80 },
        description: "Projects that used this skill. Rendered as links.",
      },
      certificationUrl: { type: "string", format: "uri" },
      featured: { type: "boolean", default: false },
      order: { type: "integer", minimum: 0, default: 0 },
      visibility: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "enums/visibility.json",
        title: "Visibility",
        description:
          "public renders on the site. unlisted is reachable by URL but absent from indexes and sitemaps. draft is admin-only.",
        type: "string",
        enum: ["public", "unlisted", "draft"],
      },
      audit: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        $id: "common/audit.schema.json",
        title: "Audit",
        description:
          "Timestamps every record carries. ISO 8601 strings in the schema; the repository layer converts to and from Firestore Timestamp in exactly one place.",
        type: "object",
        properties: {
          createdAt: { type: "string", format: "date-time" },
          updatedAt: { type: "string", format: "date-time" },
          publishedAt: { type: ["string", "null"], format: "date-time" },
          createdBy: {
            type: "string",
            maxLength: 128,
            description: "Firebase Auth uid.",
          },
        },
        additionalProperties: false,
      },
    },
  },
} as const satisfies Record<string, AdminSchemaEntry>;
