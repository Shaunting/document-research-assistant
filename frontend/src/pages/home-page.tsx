import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { api, type CurrentUser } from '@/lib/api'
import { useAuth } from '@/hooks/use-auth'

export function HomePage() {
  const { session, signOut } = useAuth()
  const [backendUser, setBackendUser] = useState<CurrentUser | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function verifyBackendAuth() {
    setLoading(true)
    setError(null)
    setBackendUser(null)

    try {
      setBackendUser(await api.me())
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-svh w-full max-w-2xl flex-col gap-6 px-4 py-10">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-medium text-foreground">Document Copilot</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Signed in as {session?.user.email}
          </p>
        </div>
        <Button variant="outline" onClick={() => void signOut()}>
          Sign out
        </Button>
      </div>

      <div className="rounded-xl border bg-card p-4">
        <p className="text-sm text-muted-foreground">
          Chat UI arrives in the next phase. Use this page to confirm backend auth.
        </p>
        <Button className="mt-4" onClick={() => void verifyBackendAuth()} disabled={loading}>
          {loading ? 'Checking…' : 'Verify backend auth'}
        </Button>
        {backendUser ? (
          <p className="mt-4 text-sm text-foreground">
            Backend sees {backendUser.email} ({backendUser.id})
          </p>
        ) : null}
        {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
      </div>
    </div>
  )
}
