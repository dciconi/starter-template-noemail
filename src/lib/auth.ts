import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";
// ──────────────────────────────────────────────────────────────────────────────
// GOOGLE OAUTH (optional)
// ──────────────────────────────────────────────────────────────────────────────
// To enable Google OAuth:
// 1. Go to Google Cloud Console → APIs & Credentials → Create OAuth Client ID
//    https://console.cloud.google.com/apis/credentials
// 2. Set authorized redirect URI to: http://localhost:3000/api/auth/callback/google
//    (and your production URL when deploying)
// 3. In "Testing" mode, only manually-added test users can sign in (max 100)
// 4. For public access, submit for Google verification (requires privacy policy
//    page, takes days/weeks)
// 5. Uncomment the import and provider below
// 6. Set AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET in your .env
//
// import Google from "next-auth/providers/google";
// ──────────────────────────────────────────────────────────────────────────────

// ──────────────────────────────────────────────────────────────────────────────
// RESEND MAGIC LINK (optional)
// ──────────────────────────────────────────────────────────────────────────────
// To enable Resend magic link (passwordless email sign-in):
// 1. Sign up at https://resend.com (free tier: 3,000 emails/month, 1 domain)
// 2. Generate an API key and verify your sending domain
// 3. Install the resend package: npm install resend
// 4. Uncomment the import and provider below
// 5. Set AUTH_RESEND_KEY in your .env
// 6. Note: free tier shares 3,000 emails across ALL projects using the same
//    Resend account
//
// import Resend from "next-auth/providers/resend";
// ──────────────────────────────────────────────────────────────────────────────

import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db } from "@/lib/db";
import {
  accounts,
  sessions,
  users,
  verificationTokens,
} from "@/db/schema";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db, {
    usersTable: users,
    accountsTable: accounts,
    sessionsTable: sessions,
    verificationTokensTable: verificationTokens,
  }),
  providers: [
    GitHub,
    // ── Uncomment to enable Google OAuth ──
    // Google({
    //   clientId: process.env.AUTH_GOOGLE_ID,
    //   clientSecret: process.env.AUTH_GOOGLE_SECRET,
    // }),
    // ── Uncomment to enable Resend magic link ──
    // Resend({
    //   apiKey: process.env.AUTH_RESEND_KEY,
    // }),
  ],
  pages: {
    signIn: "/sign-in",
  },
  callbacks: {
    authorized({ auth: session, request: { nextUrl } }) {
      const isLoggedIn = !!session?.user;
      const isOnDashboard = nextUrl.pathname.startsWith("/dashboard");

      if (isOnDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect to sign-in
      }

      return true;
    },
    session({ session, user }) {
      session.user.id = user.id;
      return session;
    },
  },
});
