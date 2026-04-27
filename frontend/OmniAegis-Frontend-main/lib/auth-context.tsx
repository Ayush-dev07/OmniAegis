'use client';



import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';


export type UserRole = 'admin' | 'reviewer';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  name: string;
}

interface AuthSession {
  user: User;
  accessToken: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signupWithGoogle: () => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

declare global {
  interface Window {
    google?: any;
  }
}

const SESSION_STORAGE_KEY = 'sentinel-user';
const SESSION_TOKEN_STORAGE_KEY = 'sentinel-access-token';

const AUTH_API_BASE_URL = '/api/auth';

const ADMIN_EMAILS = new Set(['admin@sentinelai.com']);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const persistSession = (session: AuthSession) => {
    setUser(session.user);
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session.user));
    localStorage.setItem(SESSION_TOKEN_STORAGE_KEY, session.accessToken);
  };

  const clearSession = () => {
    setUser(null);
    localStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(SESSION_TOKEN_STORAGE_KEY);
  };

  const parseAuthResponse = (payload: any): AuthSession => {
    const u = payload?.user;
    const accessToken = String(payload?.access_token || '');
    if (!u || !u.user_id || !u.email || !u.role || !u.name || !accessToken) {
      throw new Error('Authentication response is invalid.');
    }

    return {
      user: {
        id: String(u.user_id),
        email: String(u.email),
        role: (u.role === 'admin' ? 'admin' : 'reviewer') as UserRole,
        name: String(u.name),
      },
      accessToken,
    };
  };

  const postAuth = async (path: string, body: Record<string, unknown>): Promise<AuthSession> => {
    const normalizedPath = path.startsWith('/auth') ? path.slice('/auth'.length) : path;

    let response: Response;
    try {
      response = await fetch(`${AUTH_API_BASE_URL}${normalizedPath}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
    } catch {
      throw new Error('Unable to reach the authentication service. Please try again.');
    }

    if (!response.ok) {
      let message = 'Authentication failed';
      try {
        const payload = await response.json();
        message = String(payload?.detail || payload?.error || message);
      } catch {
        message = `${message} (${response.status})`;
      }
      throw new Error(message);
    }

    return parseAuthResponse(await response.json());
  };

  const authenticateWithGoogle = async (mode: 'login' | 'signup') => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) {
      throw new Error('Google auth is not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID.');
    }

    if (!window.google?.accounts?.oauth2) {
      throw new Error('Google auth script is not loaded yet. Please try again.');
    }

    const tokenResponse = await new Promise<{ access_token: string }>((resolve, reject) => {
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'openid email profile',
        prompt: 'select_account',
        callback: (response: { access_token?: string; error?: string }) => {
          if (response.error || !response.access_token) {
            reject(new Error(response.error ?? 'Google authentication failed.'));
            return;
          }
          resolve({ access_token: response.access_token });
        },
      });

      tokenClient.requestAccessToken();
    });

    const profileResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
      headers: {
        Authorization: `Bearer ${tokenResponse.access_token}`,
      },
    });

    if (!profileResponse.ok) {
      throw new Error('Unable to fetch Google profile. Please try again.');
    }

    const profile = (await profileResponse.json()) as { sub?: string; email?: string; name?: string };

    if (!profile.email) {
      throw new Error('Google account email is unavailable.');
    }

    const session = await postAuth('/auth/google', {
      mode,
      email: profile.email,
      name: profile.name ?? profile.email.split('@')[0],
      google_sub: profile.sub,
      role: ADMIN_EMAILS.has(profile.email) ? 'admin' : 'reviewer',
    });
    persistSession(session);
  };

  // Simulate checking if user is already logged in (check localStorage or session)
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        clearSession();
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const session = await postAuth('/auth/login', { email, password });
      persistSession(session);
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    setLoading(true);
    try {
      const session = await postAuth('/auth/signup', {
        name,
        email,
        password,
        role: ADMIN_EMAILS.has(email.toLowerCase()) ? 'admin' : 'reviewer',
      });
      persistSession(session);
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    setLoading(true);
    try {
      await authenticateWithGoogle('login');
    } finally {
      setLoading(false);
    }
  };

  const signupWithGoogle = async () => {
    setLoading(true);
    try {
      await authenticateWithGoogle('signup');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearSession();
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, signup, loginWithGoogle, signupWithGoogle, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};