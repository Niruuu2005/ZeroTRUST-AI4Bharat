/**
 * api.ts — Central typed API client for ZeroTRUST backend
 *
 * All requests go through `apiFetch`, which:
 *  - Prefixes the configured API gateway base URL
 *  - Attaches Authorization header when a token is available
 *  - On 401: attempts a silent token refresh, then retries once
 *  - Throws ApiError with { status, message, details? } on non-2xx responses
 */

import { tokenStore, type TokenSet } from '@/lib/auth';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000';

// ── Error type ────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ── Shared types (mirror backend shapes) ──────────────────────────────────────

export interface VerificationSource {
  url: string;
  title: string;
  credibility_tier?: string;
  credibility_score?: number;
  stance?: string;
}

export interface EvidenceSummary {
  supporting: number;
  contradicting: number;
  neutral: number;
}

export interface AgentVerdict {
  verdict: string;
  confidence: string;
  summary: string;
  sources_count: number;
  error?: string;
}

export interface VerificationResult {
  id: string;
  credibility_score: number;
  category: 'Verified False' | 'Likely False' | 'Uncertain' | 'Likely True' | 'Verified True';
  confidence: 'Low' | 'Moderate' | 'High';
  claim_type: 'text' | 'url' | 'image' | 'video' | 'audio' | 'mixed';
  sources_consulted: number;
  agent_consensus?: string;
  evidence_summary: EvidenceSummary | Record<string, unknown>;
  sources: VerificationSource[];
  agent_verdicts: Record<string, AgentVerdict | string>;
  limitations: string[];
  recommendation?: string;
  processing_time?: number;
  created_at: string;
  cached: boolean;
  cache_tier?: 'redis' | 'dynamodb' | 'cloudfront';
}

export interface VerifyRequest {
  content: string;
  type: 'text' | 'url' | 'image' | 'video' | 'audio';
  source?: string;
}

export interface PaginatedHistory {
  items: VerificationResult[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface TrendingItem {
  claimHash: string;
  claimText: string;
  count: number;
  lastSeen: string;
  sampleVerificationId?: string;
  category?: string;
  credibilityScore?: number;
}

export interface TrendingResult {
  items: TrendingItem[];
  windowDays: number;
  limit: number;
}

export interface PresignResponse {
  uploadUrl: string;
  key: string;
  expiresIn: number;
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────────

let _refreshing: Promise<void> | null = null;

async function silentRefresh(): Promise<void> {
  // Deduplicate concurrent refresh attempts
  if (_refreshing) return _refreshing;

  _refreshing = (async () => {
    const refreshToken = tokenStore.getRefreshToken();
    if (!refreshToken) throw new ApiError(401, 'No refresh token available');

    const res = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });

    if (!res.ok) {
      tokenStore.clear();
      throw new ApiError(401, 'Session expired. Please log in again.');
    }

    const { accessToken } = await res.json() as { accessToken: string };
    tokenStore.setAccessToken(accessToken);
  })().finally(() => { _refreshing = null; });

  return _refreshing;
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string> ?? {}),
  };

  const token = tokenStore.getAccessToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (res.status === 401 && retry) {
    try {
      await silentRefresh();
      return apiFetch<T>(path, init, false); // retry once with new token
    } catch {
      throw new ApiError(401, 'Session expired. Please log in again.');
    }
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    let details: unknown;
    try {
      const body = await res.json();
      message = body?.message ?? body?.error ?? message;
      details = body;
    } catch { /* ignore parse error */ }
    throw new ApiError(res.status, message, details);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ── Auth endpoints ────────────────────────────────────────────────────────────

export const authApi = {
  async register(email: string, password: string) {
    return apiFetch<{ message: string; user: { id: string; email: string; tier: string } }>(
      '/api/v1/auth/register',
      { method: 'POST', body: JSON.stringify({ email, password }) },
    );
  },

  async login(email: string, password: string): Promise<TokenSet> {
    const res = await apiFetch<{
      accessToken: string;
      refreshToken: string;
      user: { id: string; email: string; tier: 'free' | 'pro' | 'enterprise' };
    }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const tokens: TokenSet = {
      accessToken:  res.accessToken,
      refreshToken: res.refreshToken,
      user: res.user,
    };
    tokenStore.setTokens(tokens);
    return tokens;
  },

  async logout() {
    try {
      await apiFetch<void>('/api/v1/auth/logout', { method: 'POST' });
    } finally {
      tokenStore.clear();
    }
  },
};

// ── Verify endpoints ──────────────────────────────────────────────────────────

export const verifyApi = {
  async submit(payload: VerifyRequest): Promise<VerificationResult> {
    return apiFetch<VerificationResult>('/api/v1/verify', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getById(id: string): Promise<VerificationResult> {
    return apiFetch<VerificationResult>(`/api/v1/verify/${id}`);
  },
};

// ── History endpoint (requires auth) ─────────────────────────────────────────

export const historyApi = {
  async list(page = 1, limit = 20): Promise<PaginatedHistory> {
    return apiFetch<PaginatedHistory>(
      `/api/v1/history?page=${page}&limit=${limit}`,
    );
  },
};

// ── Trending endpoint ─────────────────────────────────────────────────────────

export const trendingApi = {
  async list(limit = 20, days = 7): Promise<TrendingResult> {
    return apiFetch<TrendingResult>(
      `/api/v1/trending?limit=${limit}&days=${days}`,
    );
  },
};

// ── Media endpoints ───────────────────────────────────────────────────────────

export const mediaApi = {
  /** Get a presigned S3 PUT URL, then upload file directly to S3. */
  async uploadFile(file: File): Promise<{ s3Url: string; key: string }> {
    const { uploadUrl, key } = await apiFetch<PresignResponse>(
      '/api/v1/media/presign',
      {
        method: 'POST',
        body: JSON.stringify({
          contentType: file.type,
          extension: file.name.split('.').pop(),
        }),
      },
    );

    // PUT directly to S3 — no auth header needed here
    const s3Res = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': file.type },
    });

    if (!s3Res.ok) {
      throw new ApiError(s3Res.status, 'Failed to upload file to storage');
    }

    // Derive the S3 object URL from the presigned URL (strip query string)
    const s3Url = uploadUrl.split('?')[0];
    return { s3Url, key };
  },
};
