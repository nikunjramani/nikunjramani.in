import Link from "next/link";

import { Container } from "@/site/components/spec";
import { buttonPrimary } from "@/site/components/styles";

/** The 404 body — inside the site layout for `notFound()`, and in the global 404 page. */
export function NotFoundMessage() {
  return (
    <Container className="py-24 sm:py-32">
      <p className="font-mono text-xs text-muted-foreground">404</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight font-stretch-125% text-balance">
        There&apos;s nothing at this address
      </h1>
      <p className="mt-4 max-w-md text-muted-foreground text-pretty">
        The link may be mistyped, or the page has moved. The project list has everything that&apos;s
        published.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/projects" className={buttonPrimary}>
          See all projects
        </Link>
        <Link href="/" className="inline-flex items-center px-2 py-2.5 text-sm underline decoration-border underline-offset-4 hover:decoration-accent">
          Go to the home page
        </Link>
      </div>
    </Container>
  );
}
