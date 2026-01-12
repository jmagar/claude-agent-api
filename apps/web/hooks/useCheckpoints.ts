/**
 * useCheckpoints Hook
 *
 * React Query hook for listing session checkpoints.
 */

"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Checkpoint } from "@/types";
import { mapCheckpoint } from "@/lib/api-mappers";
import { queryKeys } from "@/lib/query-keys";

async function fetchCheckpoints(sessionId: string): Promise<Checkpoint[]> {
  const response = await fetch(`/api/sessions/${sessionId}/checkpoints`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Failed to fetch checkpoints" }));
    const message =
      typeof error?.message === "string" ? error.message : "Failed to fetch checkpoints";
    throw new Error(message);
  }

  const data = await response.json();
  const checkpoints = Array.isArray(data.checkpoints) ? data.checkpoints : [];

  return checkpoints.map((checkpoint) => mapCheckpoint(checkpoint));
}

export interface UseCheckpointsReturn {
  checkpoints: Checkpoint[] | undefined;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useCheckpoints(sessionId: string): UseCheckpointsReturn {
  const query = useQuery({
    queryKey: queryKeys.sessions.checkpoints(sessionId),
    queryFn: () => fetchCheckpoints(sessionId),
    enabled: Boolean(sessionId),
  });

  return useMemo(
    () => ({
      checkpoints: query.data,
      isLoading: query.isLoading,
      error: query.error instanceof Error ? query.error.message : null,
      refetch: () => {
        void query.refetch();
      },
    }),
    [query.data, query.error, query.isLoading, query]
  );
}
