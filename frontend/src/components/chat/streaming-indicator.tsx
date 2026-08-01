type StreamingIndicatorProps = {
  status: 'submitted' | 'streaming' | 'ready' | 'error'
}

export function StreamingIndicator({ status }: StreamingIndicatorProps) {
  if (status !== 'submitted' && status !== 'streaming') return null
  return (
    <p className="text-sm text-muted-foreground" aria-live="polite">
      {status === 'submitted' ? 'Sending…' : 'Assistant is typing…'}
    </p>
  )
}
