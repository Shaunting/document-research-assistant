function required(name: keyof ImportMetaEnv): string {
  const value = import.meta.env[name]
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value.trim()
}

function requiredUrl(name: keyof ImportMetaEnv, value: string): string {
  try {
    new URL(value)
  } catch {
    throw new Error(`Invalid URL in environment variable: ${name}`)
  }
  return value
}

export const env = {
  apiBaseUrl: requiredUrl(
    'VITE_API_BASE_URL',
    required('VITE_API_BASE_URL'),
  ).replace(/\/$/, ''),
  supabaseUrl: requiredUrl('VITE_SUPABASE_URL', required('VITE_SUPABASE_URL')),
  supabaseAnonKey: required('VITE_SUPABASE_ANON_KEY'),
} as const
