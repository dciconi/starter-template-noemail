# Next.js Starter Template

A minimal, free-tier-friendly starter template built with Next.js 15 (App Router), TypeScript, Neon Postgres, Drizzle ORM, Auth.js v5 (GitHub OAuth), Tailwind CSS 4, and shadcn/ui. Designed to be used as a GitHub Template Repository for rapid prototyping with zero per-project costs.

## Getting Started

1. **Clone or use as template**

   Click "Use this template" on GitHub, or clone directly:

   ```bash
   git clone <your-repo-url>
   cd starter-template
   npm install
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Fill in the required values (see `.env.example` for details).

3. **Create a GitHub OAuth App**

   Go to [GitHub Developer Settings](https://github.com/settings/developers) and create a new OAuth App:

   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`

   Copy the Client ID and Client Secret into your `.env` file.

4. **Set up the database**

   Create a free Neon database at [neon.tech](https://neon.tech) and copy the pooled connection string into `DATABASE_URL`.

   Push the schema to your database:

   ```bash
   npm run db:push
   ```

5. **Run the dev server**

   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000).

## Scripts

| Script           | Description                                      |
| ---------------- | ------------------------------------------------ |
| `npm run dev`    | Start development server with Turbopack          |
| `npm run build`  | Production build                                 |
| `npm run db:generate` | Generate Drizzle migration files            |
| `npm run db:migrate`  | Run migrations                              |
| `npm run db:push`     | Push schema directly (quick prototyping)    |
| `npm run db:studio`   | Open Drizzle Studio                         |

## Adding More Auth Providers

The template ships with **GitHub OAuth** as the only active provider. Two additional providers are included in the code but commented out with setup instructions:

### Google OAuth

See the comments in `src/lib/auth.ts` for step-by-step instructions. You will need a Google Cloud project with OAuth credentials. Note that in "Testing" mode only manually-added test users (max 100) can sign in. Public access requires Google verification.

### Resend Magic Link (Passwordless Email)

See the comments in `src/lib/auth.ts`. You will need a [Resend](https://resend.com) account (free tier: 3,000 emails/month shared across all projects). Install the `resend` package and set `AUTH_RESEND_KEY` in your `.env`.

After enabling a provider in `auth.ts`, also uncomment the corresponding UI button/form in `src/components/sign-in.tsx`.

## Deploy to Vercel

1. Push your repo to GitHub
2. Import it into [Vercel](https://vercel.com)
3. Set these environment variables in the Vercel dashboard:
   - `DATABASE_URL`
   - `AUTH_SECRET`
   - `AUTH_GITHUB_ID`
   - `AUTH_GITHUB_SECRET`
   - (Plus any optional provider keys you have enabled)
4. Update the GitHub OAuth App callback URL to your production domain

## Documentation Links

- [Next.js](https://nextjs.org/docs)
- [Neon](https://neon.tech/docs)
- [Drizzle ORM](https://orm.drizzle.team/docs/overview)
- [Auth.js](https://authjs.dev)
- [shadcn/ui](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Resend](https://resend.com/docs)

---

This template is meant to be used as a **GitHub Template Repository**. Click "Use this template" to create a new repository with this starter as the base.
