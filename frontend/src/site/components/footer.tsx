import { Link2, Mail } from "lucide-react";
import Link from "next/link";
import type { ComponentType, SVGProps } from "react";

import {
  GithubIcon,
  InstagramIcon,
  LinkedinIcon,
  MediumIcon,
  StackOverflowIcon,
  XIcon,
  YoutubeIcon,
} from "@/site/components/brand-icons";
import { Container } from "@/site/components/spec";
import type { SocialPlatform } from "@/generated/types";
import { getProfile } from "@/lib/data/profile";
import { SITE_NAME } from "@/lib/site";

const ICONS: Partial<Record<SocialPlatform, ComponentType<SVGProps<SVGSVGElement>>>> = {
  github: GithubIcon,
  linkedin: LinkedinIcon,
  instagram: InstagramIcon,
  youtube: YoutubeIcon,
  x: XIcon,
  medium: MediumIcon,
  stackoverflow: StackOverflowIcon,
  email: Mail,
};

export async function Footer() {
  const profile = await getProfile();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-24 border-t border-border">
      <Container className="flex flex-col gap-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-mono text-xs text-muted-foreground">
          © {year} {profile?.name ?? SITE_NAME}
        </p>

        {profile?.socials?.length ? (
          <ul className="flex flex-wrap items-center gap-1">
            {profile.socials.map((social) => {
              // "other" (or anything unmapped) gets a neutral link icon, not a brand.
              const Icon = ICONS[social.platform] ?? Link2;
              return (
                <li key={social.url}>
                  <Link
                    href={social.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    aria-label={social.label ?? social.platform}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-(--radius) text-muted-foreground transition-colors hover:text-foreground"
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </Link>
                </li>
              );
            })}
          </ul>
        ) : null}

        <Link href="#top" className="font-mono text-xs text-muted-foreground hover:text-foreground">
          Back to top
        </Link>
      </Container>
    </footer>
  );
}
