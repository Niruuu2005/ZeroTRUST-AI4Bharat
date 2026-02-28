# ZeroTRUST — Frontend & Client Applications
## IMPL-04: Web Portal, Browser Extension & Mobile App (Prototype)

**Series:** IMPL-04 of 05  
**Scope:** 🚧 PROTOTYPE — fully functional, minimal polish

---

## Table of Contents

1. [Web Portal (React + Vite)](#1-web-portal)
2. [Browser Extension (Chrome MV3)](#2-browser-extension)
3. [Mobile App (React Native + Expo)](#3-mobile-app)
4. [Deployment to S3 + CloudFront](#4-deployment)

---

## 1. Web Portal

### 1.1 Project Structure

```
apps/web-portal/
├── src/
│   ├── components/
│   │   ├── claim/
│   │   │   ├── ClaimInput.tsx         # Text / URL / Image / Video tabs
│   │   │   └── ClaimHistory.tsx
│   │   ├── results/
│   │   │   ├── CredibilityScore.tsx   # Animated gauge (0–100)
│   │   │   ├── EvidenceSummary.tsx    # Supporting / contradicting bars
│   │   │   ├── SourceList.tsx         # Paginated source table
│   │   │   └── AgentBreakdown.tsx     # Per-agent accordion
│   │   └── layout/
│   │       ├── Header.tsx
│   │       └── Footer.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Verify.tsx                 # Main verification UI
│   │   └── History.tsx
│   ├── hooks/
│   │   └── useVerification.ts
│   ├── store/
│   │   ├── authStore.ts               # Zustand
│   │   └── verificationStore.ts       # Zustand
│   ├── services/
│   │   └── api.ts                     # Axios + interceptors
│   └── types/
│       └── verification.types.ts
├── public/
│   └── index.html
├── .env.example
├── vite.config.ts
└── package.json
```

### 1.2 API Service (api.ts)

```typescript
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const BASE = import.meta.env.VITE_API_BASE_URL;

export const api = axios.create({ baseURL: BASE, timeout: 35000 });

api.interceptors.request.use(config => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true;
      try {
        const refresh = localStorage.getItem('refresh_token');
        const { data } = await axios.post(`${BASE}/api/v1/auth/refresh`, { refreshToken: refresh });
        useAuthStore.getState().setToken(data.accessToken);
        err.config.headers.Authorization = `Bearer ${data.accessToken}`;
        return api(err.config);
      } catch { useAuthStore.getState().logout(); }
    }
    return Promise.reject(err);
  }
);
```

### 1.3 Verification Store (Zustand)

```typescript
// store/verificationStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { VerificationResult } from '../types/verification.types';

interface Store {
  current: VerificationResult | null;
  history: VerificationResult[];
  isLoading: boolean;
  progress: number;
  error: string | null;
  setCurrent: (r: VerificationResult | null) => void;
  setLoading: (b: boolean) => void;
  setProgress: (n: number) => void;
  setError: (e: string | null) => void;
  addToHistory: (r: VerificationResult) => void;
}

export const useVerificationStore = create<Store>()(devtools(set => ({
  current: null, history: [], isLoading: false, progress: 0, error: null,
  setCurrent: r => set({ current: r }),
  setLoading: b => set({ isLoading: b }),
  setProgress: n => set({ progress: n }),
  setError: e => set({ error: e }),
  addToHistory: r => set(s => ({ history: [r, ...s.history].slice(0, 50) }))
}), { name: 'verification' }));
```

### 1.4 useVerification Hook

```typescript
// hooks/useVerification.ts
import { useCallback } from 'react';
import { api } from '../services/api';
import { useVerificationStore } from '../store/verificationStore';
import type { VerificationResult } from '../types/verification.types';

export function useVerification() {
  const { isLoading, current, error, setLoading, setCurrent, setError, addToHistory, setProgress } =
    useVerificationStore();

  const verify = useCallback(async (
    content: string, type: 'text'|'url'|'image'|'video', source = 'web_portal'
  ): Promise<VerificationResult | null> => {
    setLoading(true); setError(null); setProgress(10);
    try {
      setProgress(30);
      const { data } = await api.post<VerificationResult>('/api/v1/verify', { content, type, source });
      setProgress(100);
      setCurrent(data);
      addToHistory(data);
      return data;
    } catch (err: any) {
      setError(err.response?.data?.error?.message ?? 'Verification failed. Try again.');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { verify, isLoading, result: current, error };
}
```

### 1.5 Animated Credibility Score Component

```typescript
// components/results/CredibilityScore.tsx
import { motion } from 'framer-motion';
import type { VerificationResult } from '../../types/verification.types';

const COLORS: Record<string, string> = {
  'Verified True': '#16a34a', 'Likely True': '#22c55e',
  'Mixed Evidence': '#eab308', 'Likely False': '#f97316',
  'Verified False': '#dc2626', 'Insufficient Evidence': '#6b7280'
};

const C = 2 * Math.PI * 88;  // circumference at r=88

export function CredibilityScore({ result }: { result: VerificationResult }) {
  const color = COLORS[result.category] ?? '#6b7280';
  const dashOffset = C - (C * result.credibility_score) / 100;

  return (
    <div className="flex flex-col items-center gap-4 bg-white rounded-2xl shadow-xl p-8">
      <h2 className="text-xl font-bold text-gray-800">Credibility Score</h2>

      {/* SVG gauge */}
      <div className="relative w-48 h-48">
        <svg className="w-48 h-48 -rotate-90" viewBox="0 0 192 192">
          <circle cx="96" cy="96" r="88" stroke="#e5e7eb" strokeWidth="12" fill="none"/>
          <motion.circle cx="96" cy="96" r="88" stroke={color} strokeWidth="12" fill="none"
            strokeLinecap="round"
            style={{ strokeDasharray: C, strokeDashoffset: C }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span className="text-5xl font-black text-gray-900"
            initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, type: 'spring' }}>
            {result.credibility_score}
          </motion.span>
          <span className="text-xs text-gray-400">out of 100</span>
        </div>
      </div>

      {/* Category badge */}
      <div className="px-6 py-2 rounded-full text-white font-semibold text-sm"
           style={{ backgroundColor: color }}>
        {result.category}
      </div>

      {/* Evidence bars */}
      {(['supporting', 'contradicting', 'neutral'] as const).map(key => {
        const val = result.evidence_summary[key];
        const total = Object.values(result.evidence_summary).reduce((a, b) => a + b, 1);
        const barColor = { supporting: '#22c55e', contradicting: '#dc2626', neutral: '#9ca3af' }[key];
        return (
          <div key={key} className="w-full flex items-center gap-2">
            <span className="text-xs w-24 capitalize text-gray-600">{key}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-2">
              <motion.div className="h-2 rounded-full" style={{ backgroundColor: barColor }}
                initial={{ width: 0 }} animate={{ width: `${(val / total) * 100}%` }}
                transition={{ duration: 0.8, delay: 0.3 }}/>
            </div>
            <span className="text-xs text-gray-500 w-4">{val}</span>
          </div>
        );
      })}

      <div className="flex gap-6 text-sm text-gray-500">
        <span>📡 {result.sources_consulted} sources</span>
        <span>🤝 {result.agent_consensus}</span>
        {result.cached && <span>⚡ Cached ({result.cache_tier})</span>}
      </div>

      <p className="text-sm text-gray-700 text-center bg-gray-50 rounded-xl p-3">
        {result.recommendation}
      </p>
    </div>
  );
}
```

### 1.6 Claim Input Component

```typescript
// components/claim/ClaimInput.tsx
import { useState, useRef } from 'react';
import { useVerification } from '../../hooks/useVerification';

type Mode = 'text'|'url'|'image'|'video';
const MODES = [
  { v: 'text' as Mode, label: 'Text', icon: '📝' },
  { v: 'url'  as Mode, label: 'URL',  icon: '🔗' },
  { v: 'image'as Mode, label: 'Image',icon: '🖼️' },
  { v: 'video'as Mode, label: 'Video',icon: '🎥' },
];

export function ClaimInput() {
  const [mode, setMode] = useState<Mode>('text');
  const [content, setContent] = useState('');
  const [file, setFile] = useState<File|null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const { verify, isLoading, error } = useVerification();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'text' || mode === 'url') {
      await verify(content, mode);
    } else if (file) {
      // Get pre-signed S3 URL and upload
      const res = await fetch('/api/v1/verify/presign', { method: 'POST' });
      const { uploadUrl, fileKey } = await res.json();
      await fetch(uploadUrl, { method: 'PUT', body: file });
      await verify(fileKey, mode);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Mode tabs */}
      <div className="flex gap-2 mb-4 bg-gray-100 rounded-xl p-1">
        {MODES.map(({ v, label, icon }) => (
          <button key={v} onClick={() => { setMode(v); setContent(''); setFile(null); }}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all
              ${mode === v ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            {icon} {label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {(mode === 'text' || mode === 'url') ? (
          <textarea
            className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500
                       focus:ring-2 focus:ring-blue-100 outline-none resize-none transition-all"
            rows={mode === 'text' ? 5 : 2}
            placeholder={mode === 'text'
              ? 'Paste a claim, statement, or news headline to verify...'
              : 'Paste a URL to an article or webpage...'}
            value={content} onChange={e => setContent(e.target.value)} disabled={isLoading}
          />
        ) : (
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center
                          cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-all"
               onClick={() => fileRef.current?.click()}
               onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }}
               onDragOver={e => e.preventDefault()}>
            <input ref={fileRef} type="file" className="hidden"
              accept={mode === 'image' ? 'image/*' : 'video/*'}
              onChange={e => setFile(e.target.files?.[0] ?? null)}/>
            {file
              ? <p className="text-blue-600 font-medium">{file.name} ({(file.size/1e6).toFixed(1)} MB)</p>
              : <p className="text-gray-500">Drop {mode} here or click to browse</p>
            }
          </div>
        )}

        {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-3 text-sm">{error}</div>}

        <button type="submit" disabled={isLoading || (!content.trim() && !file)}
          className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white
                     rounded-xl font-semibold text-lg hover:shadow-lg hover:scale-[1.01]
                     transition-all disabled:opacity-50 disabled:cursor-not-allowed">
          {isLoading ? '⏳ Verifying...' : '⚡ Verify Now'}
        </button>
      </form>
    </div>
  );
}
```

### 1.7 Shared Types

```typescript
// types/verification.types.ts
export type CredibilityCategory =
  | 'Verified True' | 'Likely True' | 'Mixed Evidence'
  | 'Likely False' | 'Verified False' | 'Insufficient Evidence';

export interface VerificationResult {
  id: string;
  credibility_score: number;
  category: CredibilityCategory;
  confidence: 'High' | 'Medium' | 'Low';
  claim_type: string;
  sources_consulted: number;
  agent_consensus: string;
  evidence_summary: { supporting: number; contradicting: number; neutral: number };
  sources: SourceReference[];
  agent_verdicts: Record<string, AgentVerdict>;
  limitations: string[];
  recommendation: string;
  processing_time: number;
  cached: boolean;
  cache_tier?: 'redis' | 'dynamodb' | 'cloudfront';
  created_at: string;
}

export interface SourceReference {
  url: string; title: string; excerpt: string;
  credibility_tier: 'tier_1'|'tier_2'|'tier_3'|'tier_4';
  credibility_score: number;
  stance: 'supporting'|'contradicting'|'neutral';
  source_type: string; published_at?: string;
}

export interface AgentVerdict {
  verdict: string; confidence: number; summary: string;
  sources_count: number; error?: string;
}
```

### 1.8 Vite Config

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          motion: ['framer-motion'],
          query: ['@tanstack/react-query']
        }
      }
    }
  },
  server: { proxy: { '/api': 'http://localhost:3000' } }
});
```

---

## 2. Browser Extension

### 2.1 manifest.json

```json
{
  "manifest_version": 3,
  "name": "ZeroTRUST — Misinformation Detector",
  "version": "1.0.0",
  "description": "AI fact-checking in one click — verify any claim in under 5 seconds.",
  "icons": {"16":"icons/icon16.png","48":"icons/icon48.png","128":"icons/icon128.png"},
  "action": {"default_popup":"popup.html","default_icon":{"48":"icons/icon48.png"}},
  "background": {"service_worker":"background.js","type":"module"},
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content-script.js"],
    "run_at": "document_idle"
  }],
  "permissions": ["activeTab","contextMenus","storage","notifications"],
  "host_permissions": ["https://api.zerotrust.ai/*","http://localhost:3000/*"]
}
```

### 2.2 Service Worker (background.ts)

```typescript
const API_BASE = 'https://api.zerotrust.ai/api/v1';  // or http://localhost:3000/api/v1 for dev
const CACHE_TTL = 24 * 60 * 60 * 1000;

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'zerotrust-verify',
    title: '⚡ Verify with ZeroTRUST',
    contexts: ['selection', 'link']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const text = info.selectionText ?? info.linkUrl ?? '';
  if (text.trim().length > 5 && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: 'ZEROTRUST_VERIFY', text });
  }
});

chrome.runtime.onMessage.addListener((msg, _, respond) => {
  if (msg.type === 'VERIFY_CLAIM') {
    handleVerify(msg.claim).then(respond).catch(err => respond({ success: false, error: err.message }));
    return true;
  }
});

async function handleVerify(claim: string) {
  const key = `zt:${await sha256(claim)}`;
  const cached = await chrome.storage.local.get(key);
  if (cached[key] && Date.now() - cached[key].ts < CACHE_TTL) {
    return { success: true, result: cached[key].data, fromCache: true };
  }
  const { auth_token } = await chrome.storage.sync.get('auth_token');
  const res = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(auth_token ? { Authorization: `Bearer ${auth_token}` } : {})
    },
    body: JSON.stringify({ content: claim, type: 'text', source: 'extension' })
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const result = await res.json();
  await chrome.storage.local.set({ [key]: { data: result, ts: Date.now() } });
  return { success: true, result, fromCache: false };
}

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
}
```

### 2.3 Content Script (content-script.ts) — Overlay UI

```typescript
const COLORS: Record<string, string> = {
  'Verified True': '#16a34a', 'Likely True': '#22c55e',
  'Mixed Evidence': '#eab308', 'Likely False': '#f97316',
  'Verified False': '#dc2626'
};

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === 'ZEROTRUST_VERIFY') showOverlay(msg.text);
});

function showOverlay(text: string) {
  document.getElementById('zt-root')?.remove();
  const root = document.createElement('div');
  root.id = 'zt-root';
  Object.assign(root.style, {
    position: 'fixed', top: '16px', right: '16px', zIndex: '2147483647',
    width: '360px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  });
  root.innerHTML = `
    <div style="background:white;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.15);overflow:hidden;">
      <div style="background:linear-gradient(135deg,#3b82f6,#6366f1);padding:14px 16px;
                  display:flex;justify-content:space-between;align-items:center;">
        <span style="color:white;font-weight:700;">⚡ ZeroTRUST</span>
        <button id="zt-close" style="color:white;background:rgba(255,255,255,0.2);border:none;
                border-radius:50%;width:24px;height:24px;cursor:pointer;font-size:16px;">×</button>
      </div>
      <div id="zt-body" style="padding:16px;">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:18px;height:18px;border:3px solid #e2e8f0;border-top:3px solid #3b82f6;
                      border-radius:50%;animation:zt-spin 1s linear infinite;"></div>
          <span style="font-size:13px;color:#64748b;">Checking 30–60 sources...</span>
        </div>
      </div>
    </div>
    <style>@keyframes zt-spin{to{transform:rotate(360deg)}}</style>`;
  document.body.appendChild(root);
  root.querySelector('#zt-close')!.addEventListener('click', () => root.remove());

  chrome.runtime.sendMessage({ type: 'VERIFY_CLAIM', claim: text }, response => {
    const body = root.querySelector('#zt-body')!;
    if (response?.success) {
      const r = response.result;
      const color = COLORS[r.category] ?? '#6b7280';
      body.innerHTML = `
        <div style="text-align:center;margin-bottom:12px;">
          <div style="font-size:52px;font-weight:900;color:${color};">${r.credibility_score}</div>
          <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">${r.category}</div>
        </div>
        <p style="font-size:12px;color:#374151;line-height:1.6;margin-bottom:10px;">${r.recommendation}</p>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:12px;">
          <span>📡 ${r.sources_consulted} sources</span>
          <span>🤝 ${r.agent_consensus}</span>
          <span>${response.fromCache ? '⚡ Cached' : '🔍 Live'}</span>
        </div>
        <a href="https://zerotrust.ai/verify/${r.id}" target="_blank"
           style="display:block;text-align:center;padding:10px;background:#3b82f6;color:white;
                  text-decoration:none;border-radius:8px;font-size:13px;font-weight:600;">
          Full Report →
        </a>`;
    } else {
      body.innerHTML = `<p style="color:#dc2626;font-size:13px;">Failed: ${response?.error}</p>`;
    }
  });
}
```

---

## 3. Mobile App (React Native)

### 3.1 Navigation (AppNavigator.tsx)

```typescript
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function Tabs() {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ size }) => {
        const i: Record<string, string> = { Verify:'🔍', History:'📋', Settings:'⚙️' };
        return <Text style={{ fontSize: size }}>{i[route.name]}</Text>;
      },
      tabBarActiveTintColor: '#3b82f6', tabBarInactiveTintColor: '#9ca3af'
    })}>
      <Tab.Screen name="Verify"   component={VerifyScreen}   />
      <Tab.Screen name="History"  component={HistoryScreen}  />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Main"    component={Tabs}            />
        <Stack.Screen name="Results" component={ResultsScreen}   />
        <Stack.Screen name="Login"   component={LoginScreen}     />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

### 3.2 Verify Screen (VerifyScreen.tsx)

```typescript
import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert } from 'react-native';
import { api } from '../services/api';

export function VerifyScreen({ navigation }: any) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.post('/api/v1/verify', { content, type: 'text', source: 'mobile_app' });
      navigation.navigate('Results', { result: data });
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.error?.message ?? 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>⚡ ZeroTRUST</Text>
      <Text style={styles.sub}>AI Fact-Checker</Text>
      <TextInput
        style={styles.input} multiline numberOfLines={5}
        placeholder="Paste a claim or news headline to verify..."
        placeholderTextColor="#94a3b8"
        value={content} onChangeText={setContent}
      />
      <TouchableOpacity style={[styles.btn, loading && styles.btnDisabled]}
        onPress={handleVerify} disabled={loading || !content.trim()}>
        <Text style={styles.btnText}>{loading ? '⏳ Verifying...' : '🔍 Verify Now'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, backgroundColor: '#f8fafc' },
  title: { fontSize: 28, fontWeight: '800', color: '#1e293b', textAlign: 'center', marginTop: 48 },
  sub: { fontSize: 14, color: '#64748b', textAlign: 'center', marginBottom: 32 },
  input: { backgroundColor: 'white', borderWidth: 2, borderColor: '#e2e8f0', borderRadius: 16,
           padding: 16, fontSize: 15, color: '#1e293b', minHeight: 140, textAlignVertical: 'top',
           marginBottom: 16 },
  btn: { backgroundColor: '#3b82f6', borderRadius: 16, padding: 18, alignItems: 'center' },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: 'white', fontSize: 17, fontWeight: '700' }
});
```

---

## 4. Deployment

### 4.1 Build & Deploy Web Portal to S3

```bash
#!/bin/bash
# deploy-web.sh

set -e
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="zerotrust-static-$ACCOUNT"
CF_DIST_ID="YOUR_CLOUDFRONT_DISTRIBUTION_ID"  # from §7.3 in IMPL-02

cd apps/web-portal

# Build
VITE_API_BASE_URL="https://api.zerotrust.ai" npm run build

# Upload assets (immutable, 1-year cache)
aws s3 sync dist/assets s3://$S3_BUCKET/assets \
  --cache-control "max-age=31536000,immutable" --delete

# Upload index.html (no-cache for SPA routing)
aws s3 cp dist/index.html s3://$S3_BUCKET/index.html \
  --cache-control "no-cache,no-store,must-revalidate"

# Invalidate CloudFront cache for HTML
aws cloudfront create-invalidation \
  --distribution-id $CF_DIST_ID \
  --paths "/index.html"

echo "✅ Web portal deployed"
```

### 4.2 Build Browser Extension

```bash
cd apps/browser-extension

# Install deps
npm install

# Build (Webpack)
npm run build

# Output: dist/
# Zip for Chrome Web Store submission (or load unpacked in dev)
cd dist && zip -r ../zerotrust-extension.zip . && cd ..

echo "Extension built: zerotrust-extension.zip"

# Load unpacked in Chrome:
# 1. chrome://extensions
# 2. Enable "Developer mode"
# 3. "Load unpacked" → select dist/
```

### 4.3 Build Mobile App (Expo EAS)

```bash
cd apps/mobile-app

# Local dev (simulator)
npx expo start

# Build for prototype demo (APK for Android sharing)
eas build --platform android --profile preview

# Build for iOS TestFlight
eas build --platform ios --profile preview
```
