import type { QueryClient, QueryKey } from "@tanstack/react-query";

interface OptimisticHandlersOptions<TData, TVariables> {
  queryClient: QueryClient;
  queryKey: QueryKey;
  updater: (current: TData | undefined, variables: TVariables) => TData;
}

interface OptimisticContext<TData> {
  previous?: TData;
}

export function createOptimisticHandlers<TData, TVariables>({
  queryClient,
  queryKey,
  updater,
}: OptimisticHandlersOptions<TData, TVariables>) {
  return {
    onMutate: async (variables: TVariables): Promise<OptimisticContext<TData>> => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<TData>(queryKey);
      const optimistic = updater(previous, variables);
      queryClient.setQueryData<TData>(queryKey, optimistic);
      return { previous };
    },
    onError: (
      _error: unknown,
      _variables: TVariables,
      context?: OptimisticContext<TData>
    ) => {
      if (context && "previous" in context) {
        queryClient.setQueryData<TData | undefined>(queryKey, context.previous);
      }
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey });
    },
  };
}
