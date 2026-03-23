import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "@/db/schema";

// Use a placeholder during build when DATABASE_URL is not set.
// The actual connection is only used at runtime.
const connectionString =
  process.env.DATABASE_URL ?? "postgresql://placeholder:placeholder@localhost/placeholder";

const sql = neon(connectionString);

export const db = drizzle(sql, { schema });
