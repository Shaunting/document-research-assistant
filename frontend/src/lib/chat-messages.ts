import type { UIMessage } from 'ai'

export type ChatMessageDto = {
  id: string
  role: string
  content: string
  createdAt: string
  messageJson: Record<string, unknown> | null
}

function isUIMessage(value: unknown): value is UIMessage {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return (
    typeof record.role === 'string' &&
    Array.isArray(record.parts) &&
    (typeof record.id === 'string' || record.id === undefined)
  )
}

export function toUIMessages(messages: ChatMessageDto[]): UIMessage[] {
  return messages.map((message) => {
    if (isUIMessage(message.messageJson)) {
      return {
        ...message.messageJson,
        id: message.messageJson.id ?? message.id,
      }
    }
    return {
      id: message.id,
      role: message.role as UIMessage['role'],
      parts: [{ type: 'text', text: message.content }],
    }
  })
}

export function textFromUIMessage(message: UIMessage): string {
  return message.parts
    .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
    .map((part) => part.text)
    .join('')
}
