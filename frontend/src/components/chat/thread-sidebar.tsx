import { NavLink } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import type { ChatThread } from '@/lib/api'

type ThreadSidebarProps = {
  threads: ChatThread[]
  activeThreadId: string | undefined
  loading: boolean
  error: string | null
  onNewChat: () => void
  onSignOut: () => void
  creating: boolean
}

export function ThreadSidebar({
  threads,
  activeThreadId,
  loading,
  error,
  onNewChat,
  onSignOut,
  creating,
}: ThreadSidebarProps) {
  return (
    <aside className="flex h-svh w-64 shrink-0 flex-col border-r bg-background">
      <div className="flex items-center justify-between gap-2 border-b p-3">
        <p className="text-sm font-medium text-foreground">Document Copilot</p>
        <Button variant="outline" size="sm" onClick={onNewChat} disabled={creating}>
          {creating ? 'Creating…' : 'New chat'}
        </Button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="px-2 py-1 text-sm text-muted-foreground">Loading…</p>
        ) : null}
        {error ? <p className="px-2 py-1 text-sm text-destructive">{error}</p> : null}
        {!loading && threads.length === 0 ? (
          <p className="px-2 py-1 text-sm text-muted-foreground">No conversations yet</p>
        ) : null}
        <ul className="grid gap-1">
          {threads.map((thread) => (
            <li key={thread.id}>
              <NavLink
                to={`/chat/${thread.id}`}
                className={({ isActive }) =>
                  [
                    'block rounded-md px-2 py-1.5 text-sm',
                    isActive || activeThreadId === thread.id
                      ? 'bg-accent text-foreground'
                      : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
                  ].join(' ')
                }
              >
                {thread.title?.trim() || 'Untitled chat'}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      <div className="border-t p-3">
        <Button variant="outline" className="w-full" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    </aside>
  )
}
