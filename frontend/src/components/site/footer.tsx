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
} from "@/components/site/brand-icons";
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
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-4 px-6 py-10 text-sm text-muted-foreground sm:flex-row sm:justify-between">
        <p>
          © {year} {profile?.name ?? SITE_NAME}
        </p>

        {profile?.socials?.length ? (
          <div className="flex items-center gap-3">
            {profile.socials.map((social) => {
              // "other" (or anything unmapped) gets a neutral link icon, not a brand.
              const Icon = ICONS[social.platform] ?? Link2;
              return (
                <Link
                  key={social.url}
                  href={social.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  aria-label={social.label ?? social.platform}
                  className="rounded-full p-2 transition-colors hover:text-foreground"
                >
                  <Icon className="h-4 w-4" />
                </Link>
              );
            })}
          </div>
        ) : null}

        <Link href="#top" className="hover:text-foreground">
          Back to top
        </Link>
      </div>
    </footer>
  );
}
