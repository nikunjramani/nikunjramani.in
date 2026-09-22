import { BookOpen, ExternalLink, FileText, Globe, Newspaper, Play, ShoppingBag } from "lucide-react";
import type { ComponentType, SVGProps } from "react";

import type { LinkType } from "@/generated/types";
import { GithubIcon } from "@/components/site/brand-icons";

const ICONS: Record<LinkType, ComponentType<SVGProps<SVGSVGElement>>> = {
  live: Globe,
  repo: GithubIcon,
  docs: BookOpen,
  "case-study": FileText,
  demo: Play,
  paper: FileText,
  store: ShoppingBag,
  article: Newspaper,
  video: Play,
  other: ExternalLink,
};

export function LinkIcon({ type, className }: { type: LinkType; className?: string }) {
  const Icon = ICONS[type] ?? ExternalLink;
  return <Icon className={className} aria-hidden="true" />;
}

export function linkTypeLabel(type: LinkType): string {
  switch (type) {
    case "live":
      return "Live";
    case "repo":
      return "Source";
    case "docs":
      return "Docs";
    case "case-study":
      return "Case study";
    case "demo":
      return "Demo";
    case "paper":
      return "Paper";
    case "store":
      return "Store";
    case "article":
      return "Article";
    case "video":
      return "Video";
    default:
      return "Link";
  }
}
