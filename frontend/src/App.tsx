import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { GuestRoute } from '@/components/auth/guest-route'
import { ProtectedRoute } from '@/components/auth/protected-route'
import { AuthProvider } from '@/components/auth/auth-provider'
import { ChatPage } from '@/pages/chat-page'
import { ChatThreadPage } from '@/pages/chat-thread-page'
import { LoginPage } from '@/pages/login-page'
import { SignUpPage } from '@/pages/sign-up-page'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignUpPage />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route element={<ChatPage />}>
              <Route index element={<ChatThreadPage />} />
              <Route path="chat/:threadId" element={<ChatThreadPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
