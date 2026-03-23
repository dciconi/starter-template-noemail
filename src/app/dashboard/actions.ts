"use server";

import { revalidatePath } from "next/cache";
import { eq, and } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { projects } from "@/db/schema";

export async function createProject(formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) throw new Error("Unauthorized");

  const name = formData.get("name") as string;
  const description = (formData.get("description") as string) || null;

  if (!name?.trim()) throw new Error("Name is required");

  await db.insert(projects).values({
    name: name.trim(),
    description: description?.trim() || null,
    userId: session.user.id,
  });

  revalidatePath("/dashboard");
}

export async function deleteProject(projectId: string) {
  const session = await auth();
  if (!session?.user?.id) throw new Error("Unauthorized");

  await db
    .delete(projects)
    .where(
      and(eq(projects.id, projectId), eq(projects.userId, session.user.id))
    );

  revalidatePath("/dashboard");
}
