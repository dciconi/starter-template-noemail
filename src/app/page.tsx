import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
        Next.js Starter Template
      </h1>
      <p className="text-muted-foreground max-w-md text-lg">
        A minimal, free-tier-friendly stack with Neon Postgres, Drizzle ORM,
        Auth.js, Tailwind CSS, and shadcn/ui.
      </p>
      <div className="flex gap-3">
        <Link
          href="/dashboard"
          className="inline-flex h-8 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80"
        >
          Go to Dashboard
        </Link>
        <a
          href="https://github.com/new?template_name=starter-template"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-8 items-center justify-center rounded-lg border border-border bg-background px-4 text-sm font-medium transition-colors hover:bg-muted"
        >
          Use this template
        </a>
      </div>
    </div>
  );
}
