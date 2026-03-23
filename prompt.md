# Claude Code Prompt: Next.js Starter Template (with Email)

This template is for projects that need email functionality (transactional emails, magic link auth, notifications). For quick prototypes that only need OAuth, use the base template instead.

Paste everything below the line into Claude Code.

---

Build me a Next.js starter template with full email support via Resend. This is for projects where I need to send transactional emails and use email-based authentication. I work on Windows.

## Stack

- **Framework**: Next.js 15 (App Router) with TypeScript
- **Database**: Neon Postgres via `@neondatabase/serverless`
- **ORM**: Drizzle ORM with `drizzle-kit` for migrations
- **Auth**: Auth.js v5 (next-auth@beta) with the Drizzle adapter, using Neon as the session/user store. Three providers active: GitHub OAuth, Google OAuth, and Resend magic link (email passwordless sign-in).
- **Email**: Resend (`resend` npm package) + React Email (`@react-email/components`) for building email templates as React components
- **Styling**: Tailwind CSS 4 + shadcn/ui (install these components: button, input, card, avatar, dropdown-menu, toast, separator, skeleton, dialog, badge, alert)
- **Fonts**: Use `next/font` with Inter for body and a nice display font of your choice

## Project structure

```
/src
  /app
    layout.tsx              — root layout with providers, global nav
    page.tsx                — landing/home page (public)
    /dashboard
      layout.tsx            — authenticated layout wrapper
      page.tsx              — simple dashboard home (protected)
    /api/auth/[...nextauth]
      route.ts              — Auth.js route handler
  /components
    /ui                     — shadcn components go here
    nav.tsx                 — top nav bar with auth state (sign in/out, avatar)
    providers.tsx           — SessionProvider wrapper
    theme-provider.tsx      — dark mode support via next-themes
    sign-in.tsx             — sign-in page with email input + OAuth buttons
  /lib
    db.ts                   — Drizzle client connected to Neon
    auth.ts                 — Auth.js config (all three providers, adapter, callbacks)
    auth-client.ts          — re-export of useSession / signIn / signOut for client use
    email.ts                — Resend client instance + generic send helper function
  /emails
    magic-link.tsx          — React Email template for the Auth.js magic link verification email
    welcome.tsx             — React Email template for a welcome email sent after first sign-in
    _base-layout.tsx        — shared email layout wrapper (logo, footer, unsubscribe-friendly structure)
  /db
    schema.ts               — Drizzle schema: Auth.js required tables (users, accounts, sessions, verification_tokens) + an example `projects` table with userId foreign key
    migrate.ts              — migration runner script
    seed.ts                 — optional seed script (can be empty, just wired up)
  /drizzle                  — generated migration SQL files go here
```

## Auth setup

All three providers should be active and the sign-in UI should display all of them:

1. **Email magic link (primary)**: Use the Resend provider from Auth.js. When a user enters their email, Auth.js sends a magic link using Resend. Override the default email with the custom React Email template at `src/emails/magic-link.tsx`. The magic link email should look professional — include the app name, a clear call-to-action button, and a plain-text fallback of the URL.

2. **GitHub OAuth**: Active by default, no verification needed.

3. **Google OAuth**: Active by default. Code comments should note that Google requires Cloud Console setup and verification for public access.

**Sign-in UI flow**: The sign-in page should show an email input field with a "Send magic link" button as the primary/top option, with a visual divider ("or continue with"), then GitHub and Google OAuth buttons below. After the user submits their email, show a confirmation message ("Check your email for a sign-in link") instead of the form.

**Welcome email**: In the Auth.js `events.createUser` callback, send a welcome email via Resend when a new user is created (regardless of which provider they used to sign up). This uses the `src/emails/welcome.tsx` template.

## Email setup

1. **Resend client** (`src/lib/email.ts`): Create a typed helper that wraps the Resend SDK:
   ```ts
   // Should export:
   // - `resend` — the raw Resend client instance
   // - `sendEmail({ to, subject, react })` — a convenience wrapper that sets the `from` address from env and handles errors gracefully, returning { success, error }
   ```

2. **React Email templates** (`src/emails/`): Each template should be a React component using `@react-email/components` (Html, Head, Body, Container, Text, Button, Hr, etc). They should:
   - Use the shared `_base-layout.tsx` wrapper for consistent branding
   - Accept props for dynamic content (e.g. the magic link URL, the user's name)
   - Look clean and professional — simple single-column layout, readable fonts, a clear CTA button
   - Work well in both light and dark email clients

3. **Preview**: Add a script `email:dev` in package.json that runs the React Email dev server (`email dev --dir src/emails`) so templates can be previewed in the browser during development.

## Key requirements

1. **Auth guard**: Create a reusable `auth()` server-side helper. The `/dashboard` layout should redirect to sign-in if not authenticated. Show how to get the session on both server components and client components.

2. **Database**: The example `projects` table should have: id (uuid, default random), name (text), description (text, nullable), userId (references users.id), createdAt, updatedAt. Create a simple CRUD example on the dashboard page that lists the user's projects and has a form to add one.

3. **Dark mode**: Wire up next-themes with a toggle button in the nav bar. Default to system preference.

4. **Scripts in package.json**:
   - `dev` — next dev
   - `build` — next build
   - `db:generate` — drizzle-kit generate
   - `db:migrate` — drizzle-kit migrate (or tsx src/db/migrate.ts)
   - `db:push` — drizzle-kit push (for quick prototyping without migration files)
   - `db:studio` — drizzle-kit studio
   - `email:dev` — react-email dev server for previewing templates

5. **Environment variables**: Create a `.env.example` with all required vars clearly labeled:
   ```
   # === REQUIRED ===
   DATABASE_URL=              # Neon connection string (pooled)
   AUTH_SECRET=               # Run: openssl rand -base64 32

   # === EMAIL (Resend) ===
   RESEND_API_KEY=            # resend.com → API Keys
   EMAIL_FROM=                # e.g. notifications@yourdomain.com (must be verified domain in Resend)

   # === GITHUB OAUTH ===
   AUTH_GITHUB_ID=            # GitHub → Settings → Developer Settings → OAuth Apps → New
   AUTH_GITHUB_SECRET=

   # === GOOGLE OAUTH ===
   AUTH_GOOGLE_ID=            # Google Cloud Console → APIs & Credentials → OAuth Client ID
   AUTH_GOOGLE_SECRET=        # Requires Google verification for public access (see README)
   ```

6. **drizzle.config.ts** at project root, reading DATABASE_URL from env.

7. **README.md** with:
   - One-paragraph description of the stack, noting this template includes email support
   - "Getting started" steps: clone, install, copy env, set up Resend (create account, verify domain, get API key), set up GitHub OAuth app, push schema, run dev
   - A section on "Email templates" explaining how to add new templates in `src/emails/`, preview them with `npm run email:dev`, and send them using the `sendEmail` helper
   - A section on "Google OAuth setup" explaining Cloud Console setup and the verification requirement
   - Note about Resend free tier limits (3,000 emails/month, 1 domain, shared across all projects using the same account)
   - Links to docs for each tool (Neon, Drizzle, Auth.js, shadcn, Resend, React Email)
   - A "Deploy to Vercel" note mentioning which env vars to set
   - Note that this template is meant to be used as a GitHub Template Repository

8. **Quality details**:
   - Use `"type": "module"` in package.json
   - Strict TypeScript config
   - Use server actions for the CRUD mutations (no API routes needed beyond auth)
   - Add a `.gitignore` that covers node_modules, .next, .env, drizzle meta files
   - The email templates should NOT import Tailwind — use inline styles via React Email's built-in style props (this is how email HTML works)
   - Keep it minimal — no extra pages, no bloat. This is a starting point with email wired in.

Do NOT use `prisma` anywhere. Do NOT install any CSS framework other than Tailwind (for the web app — email templates use inline styles). Do NOT use Nodemailer directly — use Resend's SDK and Auth.js Resend provider. Do NOT add any analytics or telemetry packages.

After building everything, run `npm run build` to verify it compiles cleanly (ignore type errors from missing env vars at build time if needed, but the code itself should be correct).