import { useEffect, useState } from 'react'
import { Outlet, useMatch, useNavigate } from 'react-router-dom'

import { ThreadSidebar } from '@/components/chat/thread-sidebar'
import { useAuth } from '@/hooks/use-auth'
import { api, type ChatThread } from '@/lib/api'
import { ApiError } from '@/lib/http'

export type ChatOutletContext = {
  onThreadMutated: () => Promise<void>
}

export function ChatPage() {
  const navigate = useNavigate()
  const threadMatch = useMatch('/chat/:threadId')
  const { signOut } = useAuth()
  const [threads, setThreads] = useState<ChatThread[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function refreshThreads() {
    setError(null)
    try {
      setThreads(await api.listThreads())
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Failed to load threads')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Initial thread loading intentionally synchronizes this shell with the API.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshThreads()
  }, [])

  async function handleNewChat() {
    setCreating(true)
    setError(null)
    try {
      const thread = await api.createThread()
      await refreshThreads()
      navigate(`/chat/${thread.id}`)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Failed to create thread')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex min-h-svh w-full">
      <ThreadSidebar
        threads={threads}
        activeThreadId={threadMatch?.params.threadId}
        loading={loading}
        error={error}
        creating={creating}
        onNewChat={() => void handleNewChat()}
        onSignOut={() => void signOut()}
      />
      <main className="min-w-0 flex-1">
        <Outlet context={{ onThreadMutated: refreshThreads } satisfies ChatOutletContext} />
      </main>
    </div>
  )
}
