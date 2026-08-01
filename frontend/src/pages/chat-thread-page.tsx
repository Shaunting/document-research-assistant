import { useParams } from 'react-router-dom'

export function ChatThreadPage() {
  const { threadId } = useParams()

  if (!threadId) {
    return (
      <div className="flex h-svh flex-col items-center justify-center gap-2 px-6 text-center">
        <h1 className="text-xl font-medium text-foreground">Start a conversation</h1>
        <p className="text-sm text-muted-foreground">
          Create a new chat or pick one from the sidebar.
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-svh items-center justify-center text-sm text-muted-foreground">
      Thread {threadId}
    </div>
  )
}
