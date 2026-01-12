/**
 * Optimistic update helper tests
 */

import { QueryClient } from "@tanstack/react-query";
import { createOptimisticHandlers } from "@/lib/react-query/optimistic";

type Item = { id: string; name: string };

describe("createOptimisticHandlers", () => {
  it("applies optimistic update and rolls back on error", async () => {
    const queryClient = new QueryClient();
    const queryKey = ["items"] as const;
    const initialItems: Item[] = [{ id: "1", name: "Alpha" }];

    queryClient.setQueryData(queryKey, initialItems);

    const handlers = createOptimisticHandlers<Item, { item: Item }>({
      queryClient,
      queryKey,
      updater: (current, variables) => [...(current ?? []), variables.item],
    });

    const context = await handlers.onMutate({ item: { id: "2", name: "Beta" } });

    expect(queryClient.getQueryData(queryKey)).toEqual([
      { id: "1", name: "Alpha" },
      { id: "2", name: "Beta" },
    ]);

    handlers.onError(new Error("fail"), { item: { id: "2", name: "Beta" } }, context);

    expect(queryClient.getQueryData(queryKey)).toEqual(initialItems);
  });

  it("invalidates queries on settle", async () => {
    const queryClient = new QueryClient();
    const queryKey = ["items"] as const;
    const invalidateSpy = jest.spyOn(queryClient, "invalidateQueries");

    const handlers = createOptimisticHandlers<Item, { item: Item }>({
      queryClient,
      queryKey,
      updater: (current) => current ?? [],
    });

    await handlers.onMutate({ item: { id: "1", name: "Alpha" } });
    await handlers.onSettled();

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey });
  });
});
