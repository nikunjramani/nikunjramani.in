/**
 * DO NOT EDIT. Generated from architecture/api-routes.json by `make gen`.
 */
/* eslint-disable */
export const API_ROUTES = {
  content: {
    profile: "content/profile",
    projects: "content/projects",
    skills: "content/skills",
    experience: "content/experience",
    education: "content/education",
    certifications: "content/certifications",
    posts: "content/posts",
    settings: "content/settings",
  },
  identity: { admins: "identity/admins" },
  inbox: { contact: "inbox/contact", messages: "inbox/messages" },
  media: { upload: "media/upload", library: "media/library" },
  ops: { health: "ops/health", audit: "ops/audit" },
} as const;

export type ContentApiDomain =
  (typeof API_ROUTES.content)[keyof typeof API_ROUTES.content];
