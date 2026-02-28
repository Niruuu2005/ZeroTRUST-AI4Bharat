# ZeroTRUST: Module-Wise Documentation
## Detailed Implementation Guide for Each System Module

**Version:** 2.0  
**Last Updated:** February 26, 2026  
**Team:** ZeroTrust

---

## Table of Contents

1. [Frontend Modules](#1-frontend-modules)
2. [Backend API Modules](#2-backend-api-modules)
3. [Multi-Agent Engine Modules](#3-multi-agent-engine-modules)
4. [Media Analysis Modules](#4-media-analysis-modules)
5. [Caching & Storage Modules](#5-caching--storage-modules)
6. [External Integration Modules](#6-external-integration-modules)
7. [Infrastructure & DevOps Modules](#7-infrastructure--devops-modules)

---

## 1. Frontend Modules

### Module 1.1: Web Portal (React.js Application)

**Purpose:** Primary user interface for claim verification via web browser

**Technology Stack:**
- React 18.2 with TypeScript
- Vite 5.0 (build tool)
- TanStack Query (React Query) for data fetching
- Zustand for state management
- Tailwind CSS v3 for styling
- Framer Motion for animations

**Directory Structure:**
```
web-portal/
├── src/
│   ├── components/
│   │   ├── claim/
│   │   │   ├── ClaimInput.tsx          # Text/URL input interface
│   │   │   ├── ClaimUpload.tsx         # Image/video upload interface
│   │   │   └── ClaimHistory.tsx        # Past verifications list
│   │   ├── results/
│   │   │   ├── CredibilityScore.tsx    # Visual score display
│   │   │   ├── EvidenceSummary.tsx     # Source breakdown
│   │   │   ├── SourceList.tsx          # Detailed source citations
│   │   │   └── AgentBreakdown.tsx      # Per-agent verdict display
│   │   ├── layout/
│   │   │   ├── Header.tsx              # Navigation and user menu
│   │   │   ├── Footer.tsx              # Links and info
│   │   │   └── Sidebar.tsx             # Quick actions and filters
│   │   └── common/
│   │       ├── Button.tsx              # Reusable button component
│   │       ├── Card.tsx                # Container component
│   │       ├── Modal.tsx               # Overlay dialogs
│   │       └── Spinner.tsx             # Loading indicators
│   ├── pages/
│   │   ├── Home.tsx                    # Landing page
│   │   ├── Verify.tsx                  # Main verification interface
│   │   ├── History.tsx                 # Verification history
│   │   ├── Dashboard.tsx               # User dashboard (Pro tier)
│   │   ├── Pricing.tsx                 # Subscription plans
│   │   └── About.tsx                   # About/How it works
│   ├── hooks/
│   │   ├── useVerification.ts          # Claim verification logic
│   │   ├── useAuth.ts                  # Authentication state
│   │   └── useWebSocket.ts             # Real-time updates
│   ├── services/
│   │   ├── api.ts                      # API client configuration
│   │   └── verificationService.ts      # Verification API calls
│   ├── store/
│   │   ├── authStore.ts                # Authentication state (Zustand)
│   │   └── verificationStore.ts        # Verification state
│   ├── types/
│   │   ├── verification.types.ts       # TypeScript interfaces
│   │   └── user.types.ts               # User-related types
│   └── utils/
│       ├── formatters.ts               # Date, number formatting
│       └── validators.ts               # Input validation
├── public/
│   ├── index.html
│   └── assets/
├── .env.example
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

**Key Components Implementation:**

**ClaimInput.tsx:**
```typescript
import React, { useState } from 'react';
import { useVerification } from '@/hooks/useVerification';
import { Button } from '@/components/common/Button';

interface ClaimInputProps {
  onVerificationStart: () => void;
}

export const ClaimInput: React.FC<ClaimInputProps> = ({ onVerificationStart }) => {
  const [inputType, setInputType] = useState<'text' | 'url'>('text');
  const [claim, setClaim] = useState('');
  const { verifyClaim, isLoading } = useVerification();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim()) return;
    
    onVerificationStart();
    await verifyClaim({
      content: claim,
      type: inputType,
      source: 'web_portal'
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex gap-4 mb-4">
        <Button
          variant={inputType === 'text' ? 'primary' : 'secondary'}
          onClick={() => setInputType('text')}
        >
          Text Claim
        </Button>
        <Button
          variant={inputType === 'url' ? 'primary' : 'secondary'}
          onClick={() => setInputType('url')}
        >
          URL
        </Button>
      </div>
      
      <form onSubmit={handleSubmit}>
        <textarea
          className="w-full p-4 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none resize-none"
          rows={inputType === 'text' ? 6 : 2}
          placeholder={
            inputType === 'text'
              ? 'Enter a claim to verify...'
              : 'Enter URL to article or post...'
          }
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          disabled={isLoading}
        />
        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="mt-4 w-full"
          disabled={isLoading || !claim.trim()}
        >
          {isLoading ? 'Verifying...' : 'Verify Claim'}
        </Button>
      </form>
    </div>
  );
};
```

**CredibilityScore.tsx:**
```typescript
import React from 'react';
import { motion } from 'framer-motion';

interface CredibilityScoreProps {
  score: number;
  category: string;
  confidence: string;
}

const getScoreColor = (score: number): string => {
  if (score >= 85) return 'bg-green-600';
  if (score >= 70) return 'bg-green-400';
  if (score >= 55) return 'bg-yellow-500';
  if (score >= 40) return 'bg-orange-500';
  return 'bg-red-600';
};

const getScoreText = (score: number): string => {
  if (score >= 85) return 'Verified True';
  if (score >= 70) return 'Likely True';
  if (score >= 55) return 'Mixed Evidence';
  if (score >= 40) return 'Likely False';
  return 'Verified False';
};

export const CredibilityScore: React.FC<CredibilityScoreProps> = ({
  score,
  category,
  confidence
}) => {
  const scoreColor = getScoreColor(score);
  const scoreText = getScoreText(score);

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold mb-2">Credibility Score</h2>
        <p className="text-gray-600">{confidence} confidence</p>
      </div>

      <div className="relative w-48 h-48 mx-auto mb-6">
        <svg className="transform -rotate-90 w-48 h-48">
          {/* Background circle */}
          <circle
            cx="96"
            cy="96"
            r="88"
            stroke="#e5e7eb"
            strokeWidth="12"
            fill="none"
          />
          {/* Progress circle */}
          <motion.circle
            cx="96"
            cy="96"
            r="88"
            stroke={scoreColor.replace('bg-', '#')}
            strokeWidth="12"
            fill="none"
            strokeLinecap="round"
            initial={{ strokeDashoffset: 552 }}
            animate={{ strokeDashoffset: 552 - (552 * score) / 100 }}
            transition={{ duration: 1, ease: 'easeOut' }}
            style={{
              strokeDasharray: 552,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: 'spring' }}
            className="text-center"
          >
            <div className="text-5xl font-bold">{score}</div>
            <div className="text-sm text-gray-600">out of 100</div>
          </motion.div>
        </div>
      </div>

      <div className={`${scoreColor} text-white text-center py-3 px-6 rounded-lg font-semibold text-lg`}>
        {scoreText}
      </div>
    </div>
  );
};
```

**API Integration (verificationService.ts):**
```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface VerificationRequest {
  content: string;
  type: 'text' | 'url' | 'image' | 'video';
  source: string;
}

interface VerificationResponse {
  id: string;
  credibility_score: number;
  category: string;
  confidence: string;
  sources_consulted: number;
  agent_consensus: string;
  evidence_summary: {
    supporting: number;
    contradicting: number;
    neutral: number;
  };
  sources: Array<{
    url: string;
    title: string;
    excerpt: string;
    credibility: number;
  }>;
  agent_verdicts: Record<string, any>;
  limitations: string[];
  recommendation: string;
  created_at: string;
}

export const verificationService = {
  async verifyClaim(request: VerificationRequest): Promise<VerificationResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/verify`, request, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    return response.data;
  },

  async getVerificationHistory(page = 1, limit = 20): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/history`, {
      params: { page, limit },
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    return response.data;
  },

  async exportHistory(format: 'csv' | 'pdf'): Promise<Blob> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/export`, {
      params: { format },
      responseType: 'blob',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });
    return response.data;
  }
};
```

**Deployment:**
- Build: `npm run build` → generates optimized static files in `dist/`
- Deploy to AWS S3 + CloudFront
- Environment variables via `.env` file:
  ```
  VITE_API_BASE_URL=https://api.zerotrust.ai
  VITE_WS_URL=wss://api.zerotrust.ai
  VITE_SENTRY_DSN=https://...
  ```

**Performance Optimizations:**
- Code splitting with React.lazy()
- Image optimization with next-gen formats (WebP, AVIF)
- Lighthouse score target: 95+ (Performance, Accessibility, SEO)
- Bundle size target: <500KB (gzipped)

---

### Module 1.2: Browser Extension (Chrome/Edge/Brave)

**Purpose:** Enable right-click verification directly on web pages

**Technology Stack:**
- Manifest V3 (Chrome Extension API)
- React 18.2 + TypeScript for popup UI
- Chrome Storage API for local caching
- Chrome Context Menus API for right-click integration

**Directory Structure:**
```
browser-extension/
├── src/
│   ├── background/
│   │   └── service-worker.ts       # Background service worker
│   ├── content/
│   │   └── content-script.ts       # Injected into web pages
│   ├── popup/
│   │   ├── Popup.tsx               # Extension popup UI
│   │   ├── QuickVerify.tsx         # Quick verification interface
│   │   └── Settings.tsx            # Extension settings
│   ├── shared/
│   │   ├── api.ts                  # API client
│   │   ├── storage.ts              # Chrome storage wrapper
│   │   └── types.ts                # Shared TypeScript types
│   └── utils/
│       ├── selection.ts            # Text selection utilities
│       └── cache.ts                # Local caching logic
├── public/
│   ├── manifest.json               # Extension manifest
│   ├── icons/
│   │   ├── icon16.png
│   │   ├── icon48.png
│   │   └── icon128.png
│   └── popup.html
├── webpack.config.js
└── package.json
```

**manifest.json:**
```json
{
  "manifest_version": 3,
  "name": "ZeroTRUST - Misinformation Detector",
  "version": "1.0.0",
  "description": "Verify claims instantly with AI-powered fact-checking",
  "permissions": [
    "activeTab",
    "contextMenus",
    "storage"
  ],
  "host_permissions": [
    "https://api.zerotrust.ai/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content-script.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

**service-worker.ts:**
```typescript
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu item
  chrome.contextMenus.create({
    id: 'verifyWithZeroTrust',
    title: 'Verify with ZeroTRUST',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'verifyWithZeroTrust' && info.selectionText) {
    // Send message to content script to show inline verification
    chrome.tabs.sendMessage(tab!.id!, {
      type: 'VERIFY_SELECTION',
      text: info.selectionText
    });
  }
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'VERIFY_CLAIM') {
    verifyClaim(request.claim)
      .then(result => sendResponse({ success: true, result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
});

async function verifyClaim(claim: string) {
  // Check cache first
  const cached = await chrome.storage.local.get(claim);
  if (cached[claim]) {
    return cached[claim];
  }

  // Call API
  const response = await fetch('https://api.zerotrust.ai/api/v1/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: claim,
      type: 'text',
      source: 'extension'
    })
  });

  const result = await response.json();

  // Cache result for 24 hours
  const cacheEntry = { [claim]: result };
  await chrome.storage.local.set(cacheEntry);

  return result;
}
```

**content-script.ts:**
```typescript
// Inject verification overlay into page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'VERIFY_SELECTION') {
    showVerificationOverlay(request.text);
  }
});

function showVerificationOverlay(text: string) {
  // Remove existing overlay if present
  const existing = document.getElementById('zerotrust-overlay');
  if (existing) existing.remove();

  // Create overlay container
  const overlay = document.createElement('div');
  overlay.id = 'zerotrust-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 400px;
    background: white;
    border: 2px solid #3b82f6;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    z-index: 999999;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  `;

  // Add loading state
  overlay.innerHTML = `
    <div style="display: flex; align-items: center; gap: 12px;">
      <div style="width: 24px; height: 24px; border: 3px solid #e5e7eb; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
      <div style="font-size: 14px; color: #6b7280;">Verifying claim...</div>
    </div>
  `;

  document.body.appendChild(overlay);

  // Verify claim
  chrome.runtime.sendMessage(
    { type: 'VERIFY_CLAIM', claim: text },
    (response) => {
      if (response.success) {
        displayResult(overlay, response.result);
      } else {
        displayError(overlay, response.error);
      }
    }
  );
}

function displayResult(container: HTMLElement, result: any) {
  const scoreColor = getScoreColor(result.credibility_score);
  
  container.innerHTML = `
    <div style="position: relative;">
      <button id="close-overlay" style="position: absolute; top: -10px; right: -10px; background: #e5e7eb; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 18px; line-height: 1;">&times;</button>
      
      <div style="text-align: center; margin-bottom: 16px;">
        <div style="font-size: 48px; font-weight: bold; color: ${scoreColor};">${result.credibility_score}</div>
        <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">${result.category}</div>
      </div>

      <div style="font-size: 13px; color: #374151; line-height: 1.6; margin-bottom: 12px;">
        ${result.recommendation}
      </div>

      <div style="display: flex; justify-content: space-between; font-size: 11px; color: #6b7280; margin-bottom: 12px;">
        <span>Sources: ${result.sources_consulted}</span>
        <span>Consensus: ${result.agent_consensus}</span>
      </div>

      <a href="https://zerotrust.ai/verify/${result.id}" target="_blank" style="display: block; text-align: center; padding: 8px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 500;">
        View Full Report
      </a>
    </div>
  `;

  container.querySelector('#close-overlay')?.addEventListener('click', () => {
    container.remove();
  });
}

function getScoreColor(score: number): string {
  if (score >= 85) return '#16a34a';
  if (score >= 70) return '#22c55e';
  if (score >= 55) return '#eab308';
  if (score >= 40) return '#f97316';
  return '#dc2626';
}

// CSS for spinner animation
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);
```

**Storage Management:**
```typescript
// storage.ts
export const storage = {
  async getCachedVerification(claim: string) {
    const result = await chrome.storage.local.get(claim);
    return result[claim] || null;
  },

  async setCachedVerification(claim: string, result: any) {
    const timestamp = Date.now();
    await chrome.storage.local.set({
      [claim]: { ...result, cached_at: timestamp }
    });
  },

  async clearExpiredCache() {
    const all = await chrome.storage.local.get(null);
    const now = Date.now();
    const TTL = 24 * 60 * 60 * 1000; // 24 hours

    const toRemove: string[] = [];
    Object.keys(all).forEach(key => {
      if (all[key].cached_at && (now - all[key].cached_at) > TTL) {
        toRemove.push(key);
      }
    });

    if (toRemove.length > 0) {
      await chrome.storage.local.remove(toRemove);
    }
  },

  async getSettings() {
    const defaults = {
      autoVerify: false,
      showNotifications: true,
      apiKey: null
    };
    const result = await chrome.storage.sync.get(defaults);
    return result;
  },

  async saveSettings(settings: any) {
    await chrome.storage.sync.set(settings);
  }
};

// Clear expired cache on extension startup
chrome.runtime.onStartup.addListener(() => {
  storage.clearExpiredCache();
});
```

**Build & Distribution:**
```bash
# Development build
npm run build:dev

# Production build
npm run build:prod

# Package for Chrome Web Store
npm run package

# Generates zerotrust-extension-v1.0.0.zip
```

**Chrome Web Store Listing:**
- Privacy Policy URL: https://zerotrust.ai/privacy
- Store listing optimization (keywords, screenshots, video demo)
- Reviews and ratings management

---

### Module 1.3: Mobile App (React Native)

**Purpose:** Native iOS and Android apps for mobile claim verification

**Technology Stack:**
- React Native 0.73
- Expo 50 (managed workflow)
- React Navigation v6 for routing
- React Native Reanimated for animations
- Expo Camera for media capture
- AsyncStorage for local persistence

**Directory Structure:**
```
mobile-app/
├── src/
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── VerifyScreen.tsx
│   │   ├── ResultsScreen.tsx
│   │   ├── HistoryScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── components/
│   │   ├── CameraCapture.tsx
│   │   ├── CredibilityCard.tsx
│   │   ├── SourceCard.tsx
│   │   └── LoadingIndicator.tsx
│   ├── navigation/
│   │   └── AppNavigator.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── storage.ts
│   ├── hooks/
│   │   ├── useVerification.ts
│   │   └── useCamera.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       ├── formatters.ts
│       └── permissions.ts
├── app.json
├── package.json
└── tsconfig.json
```

**Key Screens Implementation:**

**VerifyScreen.tsx:**
```typescript
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useVerification } from '../hooks/useVerification';
import { CameraCapture } from '../components/CameraCapture';

export const VerifyScreen = () => {
  const [mode, setMode] = useState<'text' | 'camera'>('text');
  const [claim, setClaim] = useState('');
  const navigation = useNavigation();
  const { verifyClaim, isLoading } = useVerification();

  const handleVerify = async () => {
    if (!claim.trim()) return;
    
    const result = await verifyClaim({
      content: claim,
      type: 'text',
      source: 'mobile_app'
    });

    navigation.navigate('Results', { verificationId: result.id });
  };

  const handleImageCapture = async (uri: string) => {
    const result = await verifyClaim({
      content: uri,
      type: 'image',
      source: 'mobile_app'
    });

    navigation.navigate('Results', { verificationId: result.id });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.modeSelector}>
        <TouchableOpacity
          style={[styles.modeButton, mode === 'text' && styles.modeButtonActive]}
          onPress={() => setMode('text')}
        >
          <Text style={[styles.modeButtonText, mode === 'text' && styles.modeButtonTextActive]}>
            Text
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, mode === 'camera' && styles.modeButtonActive]}
          onPress={() => setMode('camera')}
        >
          <Text style={[styles.modeButtonText, mode === 'camera' && styles.modeButtonTextActive]}>
            Camera
          </Text>
        </TouchableOpacity>
      </View>

      {mode === 'text' ? (
        <>
          <TextInput
            style={styles.input}
            placeholder="Enter claim to verify..."
            placeholderTextColor="#9CA3AF"
            value={claim}
            onChangeText={setClaim}
            multiline
            numberOfLines={6}
            textAlignVertical="top"
          />
          <TouchableOpacity
            style={[styles.verifyButton, isLoading && styles.verifyButtonDisabled]}
            onPress={handleVerify}
            disabled={isLoading || !claim.trim()}
          >
            <Text style={styles.verifyButtonText}>
              {isLoading ? 'Verifying...' : 'Verify Claim'}
            </Text>
          </TouchableOpacity>
        </>
      ) : (
        <CameraCapture onCapture={handleImageCapture} />
      )}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#F9FAFB'
  },
  modeSelector: {
    flexDirection: 'row',
    marginBottom: 20,
    backgroundColor: '#E5E7EB',
    borderRadius: 12,
    padding: 4
  },
  modeButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8
  },
  modeButtonActive: {
    backgroundColor: '#3B82F6'
  },
  modeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280'
  },
  modeButtonTextActive: {
    color: '#FFFFFF'
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#111827',
    borderWidth: 2,
    borderColor: '#E5E7EB',
    height: 180,
    marginBottom: 20
  },
  verifyButton: {
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center'
  },
  verifyButtonDisabled: {
    backgroundColor: '#9CA3AF'
  },
  verifyButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600'
  }
});
```

**Share Extension (iOS & Android):**
```typescript
// Share target configuration in app.json
{
  "expo": {
    "ios": {
      "config": {
        "usesNonExemptEncryption": false
      },
      "infoPlist": {
        "NSPhotoLibraryUsageDescription": "ZeroTRUST needs access to verify images",
        "NSCameraUsageDescription": "ZeroTRUST needs camera access to capture content"
      }
    },
    "android": {
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ],
      "intentFilters": [
        {
          "action": "SEND",
          "category": ["DEFAULT"],
          "data": [
            {
              "mimeType": "text/plain"
            },
            {
              "mimeType": "image/*"
            }
          ]
        }
      ]
    }
  }
}

// Handle incoming shared content
import * as IntentLauncher from 'expo-intent-launcher';

export const handleSharedContent = async () => {
  if (Platform.OS === 'android') {
    const intent = await IntentLauncher.getInitialURL();
    if (intent) {
      // Parse shared content
      const { data, type } = intent;
      // Trigger verification
      return { content: data, type };
    }
  }
  return null;
};
```

**Push Notifications (Expo Notifications):**
```typescript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

export const setupNotifications = async () => {
  if (!Device.isDevice) return null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  const token = (await Notifications.getExpoPushTokenAsync()).data;
  return token;
};

// Send notification when verification complete
export const sendVerificationAlert = async (result: any) => {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Verification Complete',
      body: `Credibility Score: ${result.credibility_score} - ${result.category}`,
      data: { verificationId: result.id }
    },
    trigger: null // Immediate
  });
};
```

**Build & Distribution:**
```bash
# iOS build (requires Apple Developer account)
eas build --platform ios --profile production

# Android build
eas build --platform android --profile production

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

---

## 2. Backend API Modules

### Module 2.1: API Gateway (Express.js + TypeScript)

**Purpose:** Central REST API for all client requests

**Technology Stack:**
- Node.js 20 LTS
- Express.js 4.18
- TypeScript 5.0
- JWT authentication (jsonwebtoken)
- Express-rate-limit for rate limiting
- Helmet for security headers
- Winston for logging

**Directory Structure:**
```
api-gateway/
├── src/
│   ├── routes/
│   │   ├── verify.routes.ts        # Verification endpoints
│   │   ├── auth.routes.ts          # Authentication endpoints
│   │   ├── history.routes.ts       # Verification history
│   │   └── api.routes.ts           # API key management
│   ├── controllers/
│   │   ├── VerificationController.ts
│   │   ├── AuthController.ts
│   │   └── HistoryController.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts      # JWT validation
│   │   ├── rateLimit.middleware.ts # Rate limiting
│   │   ├── validation.middleware.ts # Request validation
│   │   └── error.middleware.ts     # Error handling
│   ├── services/
│   │   ├── VerificationService.ts  # Business logic
│   │   ├── CacheService.ts         # Redis caching
│   │   └── QueueService.ts         # SQS job queuing
│   ├── models/
│   │   ├── User.model.ts
│   │   ├── Verification.model.ts
│   │   └── ApiKey.model.ts
│   ├── utils/
│   │   ├── logger.ts               # Winston logger
│   │   ├── validators.ts           # Input validation
│   │   └── errors.ts               # Custom error classes
│   └── app.ts                      # Express app initialization
├── Dockerfile
├── package.json
└── tsconfig.json
```

**app.ts:**
```typescript
import express, { Application } from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import { verifyRoutes, authRoutes, historyRoutes, apiRoutes } from './routes';
import { errorMiddleware } from './middleware/error.middleware';
import { logger } from './utils/logger';

const app: Application = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['https://zerotrust.ai'],
  credentials: true
}));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Compression
app.use(compression());

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent')
  });
  next();
});

// Routes
app.use('/api/v1/verify', verifyRoutes);
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/history', historyRoutes);
app.use('/api/v1/api-keys', apiRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Error handling
app.use(errorMiddleware);

export default app;
```

**verify.routes.ts:**
```typescript
import { Router } from 'express';
import { VerificationController } from '../controllers/VerificationController';
import { authMiddleware } from '../middleware/auth.middleware';
import { rateLimitMiddleware } from '../middleware/rateLimit.middleware';
import { validateRequest } from '../middleware/validation.middleware';
import { verificationSchema } from '../utils/validators';

const router = Router();
const controller = new VerificationController();

// Public verification endpoint (rate limited)
router.post(
  '/',
  rateLimitMiddleware({ maxRequests: 10, windowMs: 60000 }), // 10 requests per minute
  validateRequest(verificationSchema),
  controller.verify
);

// Authenticated verification endpoint (higher limits)
router.post(
  '/authenticated',
  authMiddleware,
  rateLimitMiddleware({ maxRequests: 100, windowMs: 60000 }), // 100 requests per minute
  validateRequest(verificationSchema),
  controller.verify
);

// Bulk verification (Pro/Enterprise only)
router.post(
  '/bulk',
  authMiddleware,
  controller.checkSubscription(['pro', 'enterprise']),
  validateRequest(verificationSchema.array()),
  controller.bulkVerify
);

// Get verification by ID
router.get(
  '/:id',
  controller.getVerification
);

export default router;
```

**VerificationController.ts:**
```typescript
import { Request, Response, NextFunction } from 'express';
import { VerificationService } from '../services/VerificationService';
import { CacheService } from '../services/CacheService';
import { logger } from '../utils/logger';
import { AppError } from '../utils/errors';

export class VerificationController {
  private verificationService: VerificationService;
  private cacheService: CacheService;

  constructor() {
    this.verificationService = new VerificationService();
    this.cacheService = new CacheService();
  }

  verify = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { content, type, source } = req.body;
      const userId = req.user?.id || 'anonymous';

      // Check cache first (Tier 1: Redis)
      const cacheKey = this.generateCacheKey(content, type);
      const cached = await this.cacheService.get(cacheKey);
      
      if (cached) {
        logger.info('Cache hit', { cacheKey, tier: 'redis' });
        return res.json({
          ...cached,
          cached: true,
          cache_tier: 'redis'
        });
      }

      // Perform verification
      logger.info('Cache miss, performing verification', { content: content.substring(0, 100) });
      const result = await this.verificationService.verify({
        content,
        type,
        source,
        userId
      });

      // Cache result
      await this.cacheService.set(cacheKey, result, 3600); // 1 hour TTL

      res.json({
        ...result,
        cached: false
      });
    } catch (error) {
      next(error);
    }
  };

  bulkVerify = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const claims = req.body;
      const userId = req.user!.id;

      if (claims.length > 1000) {
        throw new AppError('Maximum 1000 claims per bulk request', 400);
      }

      // Queue bulk verification job
      const jobId = await this.verificationService.queueBulkVerification(
        claims,
        userId
      );

      res.json({
        jobId,
        status: 'queued',
        estimatedTime: claims.length * 3, // ~3 seconds per claim
        message: 'Bulk verification queued. Results will be available shortly.'
      });
    } catch (error) {
      next(error);
    }
  };

  getVerification = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { id } = req.params;
      
      const result = await this.verificationService.getById(id);
      
      if (!result) {
        throw new AppError('Verification not found', 404);
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  checkSubscription = (allowedTiers: string[]) => {
    return (req: Request, res: Response, next: NextFunction) => {
      const userTier = req.user?.subscription?.tier || 'free';
      
      if (!allowedTiers.includes(userTier)) {
        throw new AppError(
          `This feature requires ${allowedTiers.join(' or ')} subscription`,
          403
        );
      }
      
      next();
    };
  };

  private generateCacheKey(content: string, type: string): string {
    const crypto = require('crypto');
    const hash = crypto
      .createHash('sha256')
      .update(content)
      .digest('hex')
      .substring(0, 32);
    return `verification:${type}:${hash}`;
  }
}
```

**Rate Limiting (rateLimit.middleware.ts):**
```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import { redisClient } from '../config/redis';
import { AppError } from '../utils/errors';

interface RateLimitOptions {
  maxRequests: number;
  windowMs: number;
  message?: string;
}

export const rateLimitMiddleware = (options: RateLimitOptions) => {
  return rateLimit({
    store: new RedisStore({
      client: redisClient,
      prefix: 'rl:'
    }),
    windowMs: options.windowMs,
    max: options.maxRequests,
    message: options.message || 'Too many requests, please try again later.',
    standardHeaders: true, // Return rate limit info in headers
    legacyHeaders: false,
    handler: (req, res) => {
      throw new AppError('Rate limit exceeded', 429);
    }
  });
};

// Tier-based rate limits
export const getUserRateLimit = (tier: string) => {
  const limits = {
    free: { maxRequests: 100, windowMs: 24 * 60 * 60 * 1000 }, // 100/day
    pro: { maxRequests: 5000, windowMs: 24 * 60 * 60 * 1000 }, // 5000/day
    enterprise: { maxRequests: 999999, windowMs: 24 * 60 * 60 * 1000 } // Unlimited
  };
  return limits[tier as keyof typeof limits] || limits.free;
};
```

**Authentication (auth.middleware.ts):**
```typescript
import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AppError } from '../utils/errors';

const JWT_SECRET = process.env.JWT_SECRET!;

interface JWTPayload {
  id: string;
  email: string;
  tier: string;
}

declare global {
  namespace Express {
    interface Request {
      user?: JWTPayload;
    }
  }
}

export const authMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new AppError('No token provided', 401);
    }

    const token = authHeader.substring(7);
    
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
      req.user = decoded;
      next();
    } catch (error) {
      throw new AppError('Invalid token', 401);
    }
  } catch (error) {
    next(error);
  }
};

// Optional auth - don't fail if no token
export const optionalAuthMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const authHeader = req.headers.authorization;
  
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
      req.user = decoded;
    } catch (error) {
      // Silently fail, continue as anonymous
    }
  }
  
  next();
};
```

**Deployment:**
- Containerize with Docker
- Deploy to AWS ECS Fargate
- Auto-scaling based on CPU/memory
- Application Load Balancer for traffic distribution
- CloudWatch Logs for monitoring

---

### Module 2.2: Verification Orchestrator (Python + FastAPI)

**Purpose:** Core verification logic and multi-agent coordination

**Technology Stack:**
- Python 3.11
- FastAPI 0.110
- LangChain 0.1.15 / LangGraph 0.0.60
- AWS Bedrock SDK
- Celery for async task queuing
- Redis for caching

**Directory Structure:**
```
verification-engine/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── manager.py               # Manager agent orchestrator
│   │   ├── research.py              # Research agent
│   │   ├── news.py                  # News agent
│   │   ├── scientific.py            # Scientific agent
│   │   ├── social_media.py          # Social media agent
│   │   ├── sentiment.py             # Sentiment & manipulation agent
│   │   └── scraper.py               # Web scraper agent
│   ├── services/
│   │   ├── credibility.py           # Credibility scoring
│   │   ├── evidence.py              # Evidence aggregation
│   │   └── report.py                # Report generation
│   ├── integrations/
│   │   ├── bedrock.py               # AWS Bedrock client
│   │   ├── search.py                # Search APIs (Google, Bing)
│   │   ├── fact_check.py            # Fact-check APIs
│   │   └── social.py                # Social media APIs
│   ├── utils/
│   │   ├── text.py                  # Text processing utilities
│   │   ├── cache.py                 # Cache utilities
│   │   └── logging.py               # Logging configuration
│   ├── models/
│   │   ├── verification.py          # Pydantic models
│   │   └── agent.py                 # Agent models
│   ├── api/
│   │   └── main.py                  # FastAPI app
│   └── tasks/
│       └── verification.py          # Celery tasks
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

**This module is continued in the detailed modules documentation...**

_(Due to character limit, I'll create separate comprehensive documentation files for remaining modules)_

---

## Key Modules Summary

The complete system is divided into 7 major module categories:

1. **Frontend Modules** - Web portal, browser extension, mobile apps
2. **Backend API Modules** - API gateway, authentication, rate limiting
3. **Multi-Agent Engine Modules** - 6 specialized agents + orchestration
4. **Media Analysis Modules** - Image, video, audio deepfake detection
5. **Caching & Storage Modules** - 3-tier cache, databases
6. **External Integration Modules** - Search APIs, fact-checkers, social media
7. **Infrastructure & DevOps Modules** - AWS services, monitoring, CI/CD

Each module has been designed for:
- **Scalability**: Handle 1M+ users and 10M+ verifications
- **Reliability**: 99.9% uptime with auto-scaling and failover
- **Performance**: <5 second verification with 90% cache hit rate
- **Maintainability**: Clean architecture, comprehensive testing, documentation

---

**For complete module-wise implementation details, refer to:**
- Module Architecture Diagrams (separate document)
- API Documentation (OpenAPI/Swagger)
- Deployment Guides (Infrastructure as Code)

**Contact:** pratik@zerotrust.ai  
**Last Updated:** February 26, 2026