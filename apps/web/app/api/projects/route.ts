import { NextRequest, NextResponse } from "next/server";
import type { Project } from "@/types";

// Mock projects store (in production, this would be from the backend API)
const mockProjects: Project[] = [
  {
    id: "proj-1",
    name: "Frontend App",
    path: "/workspace/frontend-app",
    created_at: new Date("2026-01-01"),
    session_count: 5,
    last_accessed_at: new Date("2026-01-10"),
  },
  {
    id: "proj-2",
    name: "Backend API",
    path: "/workspace/backend-api",
    created_at: new Date("2025-12-15"),
    session_count: 12,
    last_accessed_at: new Date("2026-01-09"),
  },
];

/**
 * GET /api/projects
 * Returns list of all projects
 */
export async function GET() {
  try {
    // In production, fetch from backend API
    // const response = await fetch(`${process.env.API_URL}/projects`, {
    //   headers: { Authorization: `Bearer ${apiKey}` },
    // });
    // const projects = await response.json();

    return NextResponse.json(mockProjects);
  } catch (error) {
    console.error("Failed to fetch projects:", error);
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    );
  }
}

/**
 * POST /api/projects
 * Creates a new project
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, path } = body as { name: string; path: string };

    if (!name || !path) {
      return NextResponse.json(
        { error: "Name and path are required" },
        { status: 400 }
      );
    }

    // In production, create via backend API
    const newProject: Project = {
      id: `proj-${Date.now()}`,
      name,
      path,
      created_at: new Date(),
      session_count: 0,
      last_accessed_at: new Date(),
    };

    // Mock: add to store
    mockProjects.push(newProject);

    return NextResponse.json(newProject, { status: 201 });
  } catch (error) {
    console.error("Failed to create project:", error);
    return NextResponse.json(
      { error: "Failed to create project" },
      { status: 500 }
    );
  }
}
