import type { UIMessage } from 'ai'

import { textFromUIMessage } from '@/lib/chat-messages'

type MessageListProps = {
  messages: UIMessage[]
}

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No messages yet. Ask a question to begin.</p>
    )
  }

  return (
    <ul className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      {messages.map((message) => (
        <li
          key={message.id}
          className={
            message.role === 'user'
              ? 'ml-8 rounded-lg bg-accent px-3 py-2 text-sm text-foreground'
              : 'mr-8 rounded-lg border px-3 py-2 text-sm text-foreground'
          }
        >
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {message.role === 'user' ? 'You' : 'Assistant'}
          </p>
          <p className="whitespace-pre-wrap">{textFromUIMessage(message)}</p>
        </li>
      ))}
    </ul>
  )
}
