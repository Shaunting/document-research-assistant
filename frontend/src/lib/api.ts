import type { ChatMessageDto } from '@/lib/chat-messages'
import { http } from '@/lib/http'

export type CurrentUser = {
  id: string
  email: string
}

export type ChatThread = {
  id: string
  title: string | null
  createdAt: string
  updatedAt: string
}

export const api = {
  get<T>(path: string) {
    return http.request<T>('GET', path)
  },

  post<T>(path: string, body?: unknown) {
    return http.request<T>('POST', path, { body })
  },

  put<T>(path: string, body?: unknown) {
    return http.request<T>('PUT', path, { body })
  },

  patch<T>(path: string, body?: unknown) {
    return http.request<T>('PATCH', path, { body })
  },

  delete<T>(path: string) {
    return http.request<T>('DELETE', path)
  },

  me() {
    return http.request<CurrentUser>('GET', '/me')
  },

  listThreads() {
    return http.request<ChatThread[]>('GET', '/chat/threads')
  },

  createThread(body?: { title?: string | null }) {
    return http.request<ChatThread>('POST', '/chat/threads', { body: body ?? {} })
  },

  listMessages(threadId: string) {
    return http.request<ChatMessageDto[]>(
      'GET',
      `/chat/threads/${threadId}/messages`,
    )
  },
}
