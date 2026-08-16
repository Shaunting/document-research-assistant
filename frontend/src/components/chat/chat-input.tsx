import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

type ChatInputProps = {
  disabled: boolean
  onSend: (text: string) => void | Promise<void>
}

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [text, setText] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    await onSend(trimmed)
    setText('')
  }

  return (
    <form className="mx-auto flex w-full max-w-2xl gap-2" onSubmit={(e) => void handleSubmit(e)}>
      <Textarea
        aria-label="Message"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Ask about the research corpus…"
        disabled={disabled}
        rows={2}
        className="min-h-[60px] resize-none"
      />
      <Button type="submit" disabled={disabled || text.trim() === ''}>
        Send
      </Button>
    </form>
  )
}
