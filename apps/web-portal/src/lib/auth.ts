/**
 * auth.ts — Token store helpers (localStorage, client-side only)
 *
 * Usage:
 *   import { tokenStore } from '@/lib/auth';
 *   tokenStore.setTokens({ accessToken, refreshToken, user });
 *   const token = tokenStore.getAccessToken();
 *   tokenStore.clear();
 */

export interface AuthUser {
  id: string;
  email: string;
  tier: 'free' | 'pro' | 'enterprise';
}

export interface TokenSet {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
}

const KEYS = {
  access:  'zt_access_token',
  refresh: 'zt_refresh_token',
  user:    'zt_user',
} as const;

function isClient() {
  return typeof window !== 'undefined';
}

export const tokenStore = {
  setTokens({ accessToken, refreshToken, user }: TokenSet) {
    if (!isClient()) return;
    localStorage.setItem(KEYS.access,  accessToken);
    localStorage.setItem(KEYS.refresh, refreshToken);
    localStorage.setItem(KEYS.user,    JSON.stringify(user));
  },

  getAccessToken(): string | null {
    if (!isClient()) return null;
    return localStorage.getItem(KEYS.access);
  },

  getRefreshToken(): string | null {
    if (!isClient()) return null;
    return localStorage.getItem(KEYS.refresh);
  },

  getUser(): AuthUser | null {
    if (!isClient()) return null;
    const raw = localStorage.getItem(KEYS.user);
    if (!raw) return null;
    try { return JSON.parse(raw) as AuthUser; } catch { return null; }
  },

  setAccessToken(token: string) {
    if (!isClient()) return;
    localStorage.setItem(KEYS.access, token);
  },

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },

  clear() {
    if (!isClient()) return;
    localStorage.removeItem(KEYS.access);
    localStorage.removeItem(KEYS.refresh);
    localStorage.removeItem(KEYS.user);
  },
};
