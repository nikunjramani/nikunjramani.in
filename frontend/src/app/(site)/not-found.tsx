import { NotFoundMessage } from "@/site/components/not-found-message";

/** `notFound()` inside the site (an unknown or draft project slug) — keeps the nav and footer. */
export default function NotFound() {
  return <NotFoundMessage />;
}
