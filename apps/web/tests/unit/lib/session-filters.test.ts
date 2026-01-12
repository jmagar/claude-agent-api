/**
 * Session filter query param tests
 */

import { buildSessionQueryParams } from "@/lib/session-filters";

describe("buildSessionQueryParams", () => {
  it("serializes all supported filters", () => {
    const params = buildSessionQueryParams({
      mode: "code",
      project_id: "project-1",
      tags: ["one", "two"],
      search: "alpha",
      page: 2,
      page_size: 25,
    });

    expect(params.toString()).toBe(
      "mode=code&project_id=project-1&tags=one&tags=two&search=alpha&page=2&page_size=25"
    );
  });

  it("skips empty filters", () => {
    const params = buildSessionQueryParams({
      mode: undefined,
      tags: [],
      search: "",
    });

    expect(params.toString()).toBe("");
  });
});
