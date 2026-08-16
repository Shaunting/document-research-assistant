import { createContext } from 'react'
import type { AuthError, Session } from '@supabase/supabase-js'

export type AuthContextValue = {
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<'session' | 'confirmation'>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function authErrorMessage(error: AuthError): string {
  return error.message
}
