"use client";

import {
  Award,
  Briefcase,
  FileText,
  FolderKanban,
  GraduationCap,
  Image as ImageIcon,
  LayoutDashboard,
  Mail,
  Settings,
  Sparkles,
  User,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const SECTIONS = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/admin/projects", label: "Projects", icon: FolderKanban, exact: false },
  { href: "/admin/skills", label: "Skills", icon: Sparkles, exact: false },
  { href: "/admin/experience", label: "Experience", icon: Briefcase, exact: false },
  { href: "/admin/education", label: "Education", icon: GraduationCap, exact: false },
  { href: "/admin/certifications", label: "Certifications", icon: Award, exact: false },
  { href: "/admin/profile", label: "Profile", icon: User, exact: false },
  { href: "/admin/posts", label: "Posts", icon: FileText, exact: false },
  { href: "/admin/media", label: "Media", icon: ImageIcon, exact: false },
  { href: "/admin/messages", label: "Messages", icon: Mail, exact: false },
  { href: "/admin/settings", label: "Settings", icon: Settings, exact: false },
] as const;

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-0.5 p-3" aria-label="Admin">
      {SECTIONS.map((section) => {
        const active = section.exact ? pathname === section.href : pathname.startsWith(section.href);
        const Icon = section.icon;
        return (
          <Link
            key={section.href}
            href={section.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-accent/10 text-accent"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {section.label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Used by the breadcrumb trail too, so both stay in sync from one source of truth. */
export const ADMIN_SECTIONS = SECTIONS;
