import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  checkAuth,
  isUnauthorizedError,
  login,
  type ApiError,
} from '../lib/api'

export type AuthQueryData = {
  isAuthenticated: boolean
}

export const AUTH_QUERY_KEY = ['auth', 'status'] as const

async function fetchAuthStatus(): Promise<AuthQueryData> {
  try {
    await checkAuth()
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

  const markAuthenticated = useCallback(() => {
    queryClient.setQueryData<AuthQueryData>(AUTH_QUERY_KEY, { isAuthenticated: true })
  }, [queryClient])

  const markUnauthenticated = useCallback(() => {
    queryClient.setQueryData<AuthQueryData>(AUTH_QUERY_KEY, { isAuthenticated: false })
  }, [queryClient])

  return { markAuthenticated, markUnauthenticated }
}

export function useAuth() {
  const { markAuthenticated, markUnauthenticated } = useAuthActions()

  const authQuery = useQuery<AuthQueryData, ApiError | Error>({
    queryKey: AUTH_QUERY_KEY,
    queryFn: fetchAuthStatus,
    retry: false,
    staleTime: Infinity,
    gcTime: Infinity,
  })

  const loginMutation = useMutation<void, ApiError | Error, string>({
    mutationFn: (password) => login(password),
    onSuccess: () => {
      markAuthenticated()
    },
    onError: (error) => {
      if (isUnauthorizedError(error)) {
        markUnauthenticated()
      }
    },
  })

  return {
    isChecking: authQuery.isPending,
    isAuthenticated: authQuery.data?.isAuthenticated ?? false,
    authError: authQuery.error instanceof Error ? authQuery.error : null,
    refetchAuth: authQuery.refetch,
    loginMutation,
    markAuthenticated,
    markUnauthenticated,
  }
}
