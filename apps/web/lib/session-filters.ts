import type { SessionFilters } from "@/types";

export function buildSessionQueryParams(filters: SessionFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.mode) {
    params.set("mode", filters.mode);
  }

  if (filters.project_id) {
    params.set("project_id", filters.project_id);
  }

  if (filters.tags && filters.tags.length > 0) {
    filters.tags.forEach((tag) => params.append("tags", tag));
  }

  if (filters.search) {
    params.set("search", filters.search);
  }

  if (typeof filters.page === "number") {
    params.set("page", String(filters.page));
  }

  if (typeof filters.page_size === "number") {
    params.set("page_size", String(filters.page_size));
  }

  return params;
}
