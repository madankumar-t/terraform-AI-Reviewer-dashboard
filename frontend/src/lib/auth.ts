/**
 * Authentication and Authorization Utilities
 * 
 * Handles Cognito authentication and JWT token management
 */

import { CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserSession } from 'amazon-cognito-identity-js'

// Cognito configuration
const USER_POOL_ID = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || ''
const CLIENT_ID = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || ''
const REGION = process.env.NEXT_PUBLIC_AWS_REGION || 'us-east-1'

const userPool = new CognitoUserPool({
  UserPoolId: USER_POOL_ID,
  ClientId: CLIENT_ID,
})

export interface AuthUser {
  id: string
  email: string
  groups: string[]
  token: string
}

export class AuthService {
  /**
   * Sign in with username and password
   */
  static async signIn(username: string, password: string): Promise<AuthUser> {
    return new Promise((resolve, reject) => {
      const authenticationDetails = new AuthenticationDetails({
        Username: username,
        Password: password,
      })

      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: userPool,
      })

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session: CognitoUserSession) => {
          const idToken = session.getIdToken()
          const payload = idToken.getPayload()
          
          resolve({
            id: payload.sub,
            email: payload.email || '',
            groups: payload['cognito:groups'] || [],
            token: idToken.getJwtToken(),
          })
        },
        onFailure: (err) => {
          reject(err)
        },
        mfaRequired: () => {
          reject(new Error('MFA required'))
        },
      })
    })
  }

  /**
   * Sign in with Azure Entra ID (SAML)
   */
  static async signInWithAzure(): Promise<void> {
    const domain = process.env.NEXT_PUBLIC_COGNITO_DOMAIN || ''
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`)
    const clientId = CLIENT_ID
    
    // Redirect to Cognito hosted UI with Azure AD as identity provider
    const authUrl = `https://${domain}.auth.${REGION}.amazoncognito.com/oauth2/authorize?client_id=${clientId}&response_type=code&scope=email+openid+profile&redirect_uri=${redirectUri}&identity_provider=AzureAD`
    
    window.location.href = authUrl
  }

  /**
   * Get current user session
   */
  static async getCurrentUser(): Promise<AuthUser | null> {
    return new Promise((resolve) => {
      const cognitoUser = userPool.getCurrentUser()
      
      if (!cognitoUser) {
        resolve(null)
        return
      }

      cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session) {
          resolve(null)
          return
        }

        if (session.isValid()) {
          const idToken = session.getIdToken()
          const payload = idToken.getPayload()
          
          resolve({
            id: payload.sub,
            email: payload.email || '',
            groups: payload['cognito:groups'] || [],
            token: idToken.getJwtToken(),
          })
        } else {
          resolve(null)
        }
      })
    })
  }

  /**
   * Sign out
   */
  static async signOut(): Promise<void> {
    const cognitoUser = userPool.getCurrentUser()
    if (cognitoUser) {
      cognitoUser.signOut()
    }
    
    // Clear local storage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
  }

  /**
   * Get authorization header
   */
  static async getAuthHeader(): Promise<string | null> {
    const user = await this.getCurrentUser()
    return user ? `Bearer ${user.token}` : null
  }

  /**
   * Check if user has required role
   */
  static hasRole(user: AuthUser | null, requiredRole: 'admin' | 'reviewer' | 'readonly'): boolean {
    if (!user) return false
    
    const userGroups = user.groups.map(g => g.toLowerCase())
    
    // Admin has all permissions
    if (userGroups.includes('admin')) {
      return true
    }
    
    // Check specific role
    if (requiredRole === 'readonly') {
      return true  // All authenticated users can read
    }
    
    if (requiredRole === 'reviewer') {
      return userGroups.includes('reviewer') || userGroups.includes('admin')
    }
    
    return false
  }

  /**
   * Handle OAuth callback
   */
  static async handleCallback(code: string): Promise<AuthUser> {
    // Exchange authorization code for tokens
    const domain = process.env.NEXT_PUBLIC_COGNITO_DOMAIN || ''
    const redirectUri = `${window.location.origin}/auth/callback`
    const tokenUrl = `https://${domain}.auth.${REGION}.amazoncognito.com/oauth2/token`
    
    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: CLIENT_ID,
      code: code,
      redirect_uri: redirectUri,
    })
    
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    })
    
    if (!response.ok) {
      throw new Error('Failed to exchange authorization code')
    }
    
    const data = await response.json()
    
    // Decode ID token to get user info
    const idToken = data.id_token
    const payload = JSON.parse(atob(idToken.split('.')[1]))
    
    // Store token
    localStorage.setItem('auth_token', idToken)
    localStorage.setItem('user_info', JSON.stringify({
      id: payload.sub,
      email: payload.email,
      groups: payload['cognito:groups'] || [],
    }))
    
    return {
      id: payload.sub,
      email: payload.email || '',
      groups: payload['cognito:groups'] || [],
      token: idToken,
    }
  }
}

