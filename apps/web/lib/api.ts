/**
 * API client for Claude Agent API
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:54000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public correlationId?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const apiKey = typeof window !== "undefined"
    ? localStorage.getItem("auth.apiKey")
    : process.env.NEXT_PUBLIC_API_KEY;

  const headers = new Headers(options.headers);
  if (apiKey) {
    headers.set("X-API-Key", apiKey);
  }
  headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const correlationId = response.headers.get("X-Correlation-ID") || undefined;

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: response.statusText,
    }));
    throw new ApiError(
      response.status,
      error.error || error.detail || "Request failed",
      correlationId
    );
  }

  return response.json();
}

// Session API
export const sessionsApi = {
  list: () => fetchApi<{ sessions: unknown[] }>("/sessions"),
  get: (id: string) => fetchApi<unknown>(`/sessions/${id}`),
  create: (mode: "brainstorm" | "code", projectId?: string) =>
    fetchApi<unknown>("/sessions", {
      method: "POST",
      body: JSON.stringify({ mode, project_id: projectId }),
    }),
  delete: (id: string) =>
    fetchApi<void>(`/sessions/${id}`, { method: "DELETE" }),
  updateTitle: (id: string, title: string) =>
    fetchApi<unknown>(`/sessions/${id}/title`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
};

// Projects API
export const projectsApi = {
  list: () => fetchApi<{ projects: unknown[] }>("/projects"),
  get: (id: string) => fetchApi<unknown>(`/projects/${id}`),
  create: (name: string, path: string) =>
    fetchApi<unknown>("/projects", {
      method: "POST",
      body: JSON.stringify({ name, path }),
    }),
  delete: (id: string) =>
    fetchApi<void>(`/projects/${id}`, { method: "DELETE" }),
};

// MCP Servers API
export const mcpServersApi = {
  list: () => fetchApi<{ servers: unknown[] }>("/mcp/servers"),
  get: (id: string) => fetchApi<unknown>(`/mcp/servers/${id}`),
  create: (config: unknown) =>
    fetchApi<unknown>("/mcp/servers", {
      method: "POST",
      body: JSON.stringify(config),
    }),
  update: (id: string, config: unknown) =>
    fetchApi<unknown>(`/mcp/servers/${id}`, {
      method: "PUT",
      body: JSON.stringify(config),
    }),
  delete: (id: string) =>
    fetchApi<void>(`/mcp/servers/${id}`, { method: "DELETE" }),
  toggle: (id: string, enabled: boolean) =>
    fetchApi<unknown>(`/mcp/servers/${id}/toggle`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
    }),
};

// Agents API
export const agentsApi = {
  list: () => fetchApi<{ agents: unknown[] }>("/agents"),
  get: (id: string) => fetchApi<unknown>(`/agents/${id}`),
  create: (agent: unknown) =>
    fetchApi<unknown>("/agents", {
      method: "POST",
      body: JSON.stringify(agent),
    }),
  update: (id: string, agent: unknown) =>
    fetchApi<unknown>(`/agents/${id}`, {
      method: "PUT",
      body: JSON.stringify(agent),
    }),
  delete: (id: string) => fetchApi<void>(`/agents/${id}`, { method: "DELETE" }),
};

// Skills API
export const skillsApi = {
  list: () => fetchApi<{ skills: unknown[] }>("/skills"),
  get: (id: string) => fetchApi<unknown>(`/skills/${id}`),
  create: (skill: unknown) =>
    fetchApi<unknown>("/skills", {
      method: "POST",
      body: JSON.stringify(skill),
    }),
  update: (id: string, skill: unknown) =>
    fetchApi<unknown>(`/skills/${id}`, {
      method: "PUT",
      body: JSON.stringify(skill),
    }),
  delete: (id: string) => fetchApi<void>(`/skills/${id}`, { method: "DELETE" }),
};

export { API_URL };
