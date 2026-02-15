import { useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchSelf,
  isUnauthorizedError,
  type ApiError,
} from '../lib/api'

export type AuthQueryData = {
  isAuthenticated: boolean
}

export const AUTH_QUERY_KEY = ['auth', 'status'] as const

async function fetchAuthStatus(): Promise<AuthQueryData> {
  try {
    await fetchSelf()
    return { isAuthenticated: true }
  } catch (error) {
    if (isUnauthorizedError(error)) {
      return { isAuthenticated: false }
    }

    throw error
  }
}

export function useAuthActions() {
  const queryClient = useQueryClient()

  const markUnauthenticated = useCallback(() => {
    queryClient.setQueryData<AuthQueryData>(AUTH_QUERY_KEY, { isAuthenticated: false })
  }, [queryClient])

  return { markUnauthenticated }
}

export function useAuth() {
  const { markUnauthenticated } = useAuthActions()

  const authQuery = useQuery<AuthQueryData, ApiError | Error>({
    queryKey: AUTH_QUERY_KEY,
    queryFn: fetchAuthStatus,
    retry: false,
    staleTime: Infinity,
    gcTime: Infinity,
  })

  return {
    isChecking: authQuery.isPending,
    isAuthenticated: authQuery.data?.isAuthenticated ?? false,
    authError: authQuery.error instanceof Error ? authQuery.error : null,
    refetchAuth: authQuery.refetch,
    markUnauthenticated,
  }
}
