import { keepPreviousData, useQuery, type UseQueryOptions } from '@tanstack/react-query'
import { api, type Params } from './client'

export function useGet<T>(path: string, params?: Params, opts?: Partial<UseQueryOptions<T>> & { keep?: boolean }) {
  const { keep, ...rest } = opts ?? {}
  return useQuery<T>({
    queryKey: [path, params ?? {}],
    queryFn: () => api.get<T>(path, params),
    placeholderData: keep ? keepPreviousData : undefined,
    ...(rest as object),
  })
}
