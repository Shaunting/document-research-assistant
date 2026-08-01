import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport, type UIMessage } from 'ai'
import { useEffect, useMemo, useState } from 'react'
import { useOutletContext, useParams } from 'react-router-dom'

import { ChatInput } from '@/components/chat/chat-input'
import { MessageList } from '@/components/chat/message-list'
import { StreamingIndicator } from '@/components/chat/streaming-indicator'
import { api } from '@/lib/api'
import { toUIMessages } from '@/lib/chat-messages'
import { env } from '@/lib/env'
import { ApiError, http } from '@/lib/http'
import type { ChatOutletContext } from '@/pages/chat-page'

export function ChatThreadPage() {
  const { threadId } = useParams()
  const { onThreadMutated } = useOutletContext<ChatOutletContext>()

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
    <ActiveThread
      key={threadId}
      threadId={threadId}
      onThreadMutated={onThreadMutated}
    />
  )
}

function ActiveThread({
  threadId,
  onThreadMutated,
}: {
  threadId: string
  onThreadMutated: () => Promise<void>
}) {
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    void (async () => {
      try {
        const rows = await api.listMessages(threadId)
        if (!cancelled) setInitialMessages(toUIMessages(rows))
      } catch (caught) {
        if (!cancelled) {
          setLoadError(
            caught instanceof ApiError ? caught.message : 'Failed to load messages',
          )
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [threadId])

  if (loadError) {
    return (
      <div className="flex h-svh items-center justify-center px-6 text-sm text-destructive">
        {loadError}
      </div>
    )
  }

  if (initialMessages === null) {
    return (
      <div className="flex h-svh items-center justify-center text-sm text-muted-foreground">
        Loading messages…
      </div>
    )
  }

  return (
    <ThreadChat
      threadId={threadId}
      initialMessages={initialMessages}
      onThreadMutated={onThreadMutated}
    />
  )
}

function ThreadChat({
  threadId,
  initialMessages,
  onThreadMutated,
}: {
  threadId: string
  initialMessages: UIMessage[]
  onThreadMutated: () => Promise<void>
}) {
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${env.apiBaseUrl}/chat/stream`,
        headers: async () => {
          const token = await http.getAccessToken()
          if (!token) throw new Error('Not authenticated')
          return { Authorization: `Bearer ${token}` }
        },
        prepareSendMessagesRequest: ({ messages }) => ({
          body: {
            threadId,
            messages,
          },
        }),
      }),
    [threadId],
  )

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
    onFinish: () => {
      void onThreadMutated()
    },
  })

  const busy = status === 'submitted' || status === 'streaming'

  return (
    <div className="flex h-svh flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
        <MessageList messages={messages} />
      </div>
      <div className="border-t px-4 py-4">
        <div className="mx-auto mb-2 flex w-full max-w-2xl flex-col gap-2">
          <StreamingIndicator status={status} />
          {error ? (
            <p className="text-sm text-destructive">{error.message}</p>
          ) : null}
        </div>
        <ChatInput
          disabled={busy}
          onSend={async (text) => {
            await sendMessage({ text })
          }}
        />
      </div>
    </div>
  )
}
