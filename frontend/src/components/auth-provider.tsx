"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { AuthService, AuthUser } from '@/lib/auth'

interface AuthContextType {
  user: AuthUser | null
  loading: boolean
  signIn: (username: string, password: string) => Promise<void>
  signInWithAzure: () => void
  signOut: () => Promise<void>
  hasRole: (role: 'admin' | 'reviewer' | 'readonly') => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    AuthService.getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const signIn = async (username: string, password: string) => {
    const authUser = await AuthService.signIn(username, password)
    setUser(authUser)
    localStorage.setItem('auth_token', authUser.token)
    localStorage.setItem('user_info', JSON.stringify(authUser))
  }

  const signInWithAzure = () => {
    AuthService.signInWithAzure()
  }

  const signOut = async () => {
    await AuthService.signOut()
    setUser(null)
  }

  const hasRole = (role: 'admin' | 'reviewer' | 'readonly'): boolean => {
    return AuthService.hasRole(user, role)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signInWithAzure, signOut, hasRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

