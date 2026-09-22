import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center justify-center gap-4 px-6 py-32 text-center">
      <p className="text-sm text-muted-foreground">404</p>
      <h1 className="text-2xl font-medium tracking-tight">Page not found</h1>
      <p className="max-w-sm text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist, or has moved.
      </p>
      <Link
        href="/"
        className="mt-2 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90"
      >
        Back home
      </Link>
    </div>
  );
}
