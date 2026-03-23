import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import { Nav } from "@/components/nav";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Starter Template",
  description: "Next.js starter with Neon, Drizzle, Auth.js, and shadcn/ui",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans min-h-dvh flex flex-col antialiased`}>
        <Providers>
          <Nav />
          <main className="flex-1">{children}</main>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
