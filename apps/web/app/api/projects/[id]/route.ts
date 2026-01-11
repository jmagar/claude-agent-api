import { NextRequest, NextResponse } from "next/server";
import type { Project } from "@/types";

// Mock projects store (shared with parent route in production)
const mockProjects: Map<string, Project> = new Map([
  [
    "proj-1",
    {
      id: "proj-1",
      name: "Frontend App",
      path: "/workspace/frontend-app",
      created_at: new Date("2026-01-01"),
      session_count: 5,
      last_accessed_at: new Date("2026-01-10"),
    },
  ],
  [
    "proj-2",
    {
      id: "proj-2",
      name: "Backend API",
      path: "/workspace/backend-api",
      created_at: new Date("2025-12-15"),
      session_count: 12,
      last_accessed_at: new Date("2026-01-09"),
    },
  ],
]);

interface RouteParams {
  params: Promise<{ id: string }>;
}

/**
 * GET /api/projects/[id]
 * Returns a single project by ID
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const project = mockProjects.get(id);

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    return NextResponse.json(project);
  } catch (error) {
    console.error("Failed to fetch project:", error);
    return NextResponse.json(
      { error: "Failed to fetch project" },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/projects/[id]
 * Updates a project
 */
export async function PATCH(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const project = mockProjects.get(id);

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    const body = await request.json();
    const { name, path } = body as { name?: string; path?: string };

    const updatedProject: Project = {
      ...project,
      ...(name && { name }),
      ...(path && { path }),
      last_accessed_at: new Date(),
    };

    mockProjects.set(id, updatedProject);

    return NextResponse.json(updatedProject);
  } catch (error) {
    console.error("Failed to update project:", error);
    return NextResponse.json(
      { error: "Failed to update project" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/projects/[id]
 * Deletes a project
 */
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const project = mockProjects.get(id);

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    mockProjects.delete(id);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to delete project:", error);
    return NextResponse.json(
      { error: "Failed to delete project" },
      { status: 500 }
    );
  }
}
