import { env } from '@/lib/env'
import { supabase } from '@/lib/supabase'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

type RequestOptions = {
  body?: unknown
  headers?: Record<string, string>
  timeoutMs?: number
  auth?: boolean
}

export class ApiError extends Error {
  readonly status: number
  readonly isNetworkError: boolean
  readonly body: unknown

  constructor(
    message: string,
    options: { status: number; isNetworkError?: boolean; body?: unknown },
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.isNetworkError = options.isNetworkError ?? false
    this.body = options.body
  }
}

async function getAccessToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

function errorMessage(body: unknown, fallback: string): string {
  if (
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    (typeof body.detail === 'string' || typeof body.detail === 'number')
  ) {
    return String(body.detail)
  }
  return fallback
}

async function request<T>(
  method: HttpMethod,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const auth = options.auth ?? true
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...options.headers,
  }

  if (auth) {
    const token = await getAccessToken()
    if (!token) {
      throw new ApiError('Not authenticated', { status: 401 })
    }
    headers.Authorization = `Bearer ${token}`
  }

  let body: BodyInit | undefined
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }

  const url = `${env.apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
  const timeoutMs = options.timeoutMs ?? 30_000

  try {
    const response = await fetch(url, {
      method,
      headers,
      body,
      signal: AbortSignal.timeout(timeoutMs),
    })

    if (!response.ok) {
      let responseBody: unknown
      try {
        responseBody = await response.json()
      } catch {
        responseBody = undefined
      }

      throw new ApiError(
        errorMessage(
          responseBody,
          response.statusText || `Request failed with status ${response.status}`,
        ),
        { status: response.status, body: responseBody },
      )
    }

    if (response.status === 204) {
      return undefined as T
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new ApiError('Request timed out', { status: 0, isNetworkError: true })
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network request failed',
      { status: 0, isNetworkError: true },
    )
  }
}

export const http = {
  request,
  getAccessToken,
}
