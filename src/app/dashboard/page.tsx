import { eq } from "drizzle-orm";
import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { projects } from "@/db/schema";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { createProject, deleteProject } from "./actions";

export default async function DashboardPage() {
  const session = await auth();

  const userProjects = await db
    .select()
    .from(projects)
    .where(eq(projects.userId, session!.user!.id!))
    .orderBy(projects.createdAt);

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome, {session!.user!.name ?? "there"}. Manage your projects below.
        </p>
      </div>

      <Separator />

      {/* Add project form */}
      <Card>
        <CardHeader>
          <CardTitle>New Project</CardTitle>
          <CardDescription>Add a new project to your list.</CardDescription>
        </CardHeader>
        <CardContent>
          <form action={createProject} className="flex flex-col gap-3 sm:flex-row">
            <Input
              name="name"
              placeholder="Project name"
              required
              className="flex-1"
            />
            <Input
              name="description"
              placeholder="Description (optional)"
              className="flex-1"
            />
            <Button type="submit">Add</Button>
          </form>
        </CardContent>
      </Card>

      {/* Project list */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Projects</h2>
        {userProjects.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No projects yet. Create one above.
          </p>
        ) : (
          <div className="grid gap-3">
            {userProjects.map((project) => (
              <Card key={project.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium">{project.name}</p>
                    {project.description && (
                      <p className="text-muted-foreground text-sm">
                        {project.description}
                      </p>
                    )}
                  </div>
                  <form action={deleteProject.bind(null, project.id)}>
                    <Button variant="ghost" size="sm" type="submit">
                      Delete
                    </Button>
                  </form>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
