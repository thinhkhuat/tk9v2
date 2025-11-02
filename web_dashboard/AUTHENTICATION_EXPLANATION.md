# Authentication Flow Explanation

## You're Seeing NORMAL Behavior - Nothing is Hardcoded! ✅

### What You're Seeing in Console

```
[API] Added JWT to request from – "sb-yurbnrqgsipdlijeyyuw-auth-token"
```

This is showing the **localStorage key name**, NOT the actual JWT token.

### How It Works (Step by Step)

#### 1. Environment Variable (from .env)
```env
VITE_SUPABASE_URL=https://yurbnrqgsipdlijeyyuw.supabase.co
```

#### 2. Dynamic Key Construction (api.ts:88-95)
```typescript
// Read from .env - NO HARDCODING
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''

// Extract project reference dynamically
const projectRef = supabaseUrl.match(/https:\/\/([^.]+)\.supabase\.co/)?.[1]
// Result: "yurbnrqgsipdlijeyyuw"

// Build localStorage key (Supabase's standard format)
const supabaseSessionKey = `sb-${projectRef}-auth-token`
// Result: "sb-yurbnrqgsipdlijeyyuw-auth-token"
```

#### 3. Read JWT from LocalStorage (api.ts:96-104)
```typescript
// Supabase automatically stores session here
const supabaseSession = localStorage.getItem(supabaseSessionKey)

// Parse and extract the REAL JWT token
const session = JSON.parse(supabaseSession)
const accessToken = session?.access_token  // <-- This is the actual JWT

// Add to request header
config.headers.Authorization = `Bearer ${accessToken}`
```

### What Supabase Does Automatically

When you sign in (anonymously or with email), Supabase automatically:
1. Creates a JWT access token
2. Stores it in localStorage with key: `sb-{project-ref}-auth-token`
3. Auto-refreshes the token when it expires

### Why This is CORRECT

✅ **NO hardcoded tokens** - Everything comes from .env
✅ **NO hardcoded keys** - Key is built from your Supabase URL
✅ **Standard Supabase behavior** - This is how Supabase works
✅ **Automatic token refresh** - Supabase handles expiration
✅ **Secure** - Token is stored in browser's localStorage

### Where Values Come From

| Value | Source | Location |
|-------|--------|----------|
| `VITE_SUPABASE_URL` | Environment variable | `.env` file |
| `VITE_SUPABASE_ANON_KEY` | Environment variable | `.env` file |
| Project reference | Extracted from VITE_SUPABASE_URL | Dynamic |
| localStorage key | Constructed from project ref | Dynamic |
| JWT token | Supabase auth response | localStorage |

### Current Configuration

From your `.env` file:
```env
VITE_SUPABASE_URL=https://yurbnrqgsipdlijeyyuw.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- ✅ Project reference: `yurbnrqgsipdlijeyyuw` (extracted from URL)
- ✅ localStorage key: `sb-yurbnrqgsipdlijeyyuw-auth-token` (constructed)
- ✅ JWT token: Stored by Supabase after anonymous sign-in

### What the Log Actually Means

```
[API] Added JWT to request from – "sb-yurbnrqgsipdlijeyyuw-auth-token"
```

Translation:
- "I found a JWT token"
- "It was stored in localStorage"
- "Under this key: sb-yurbnrqgsipdlijeyyuw-auth-token"
- "I added it to the Authorization header"

### How to Verify in Browser DevTools

1. Open DevTools (F12)
2. Go to Application tab
3. Click "Local Storage"
4. Look for key: `sb-yurbnrqgsipdlijeyyuw-auth-token`
5. See the actual JWT value (long encoded string)

### Why Anonymous Auth Works

When you load the dashboard:
1. `authStore.initializeAuth()` runs (in App.vue)
2. Checks for existing session in localStorage
3. If none exists, calls `signInAnonymously()`
4. Supabase creates anonymous user and JWT
5. JWT is automatically stored in localStorage
6. API client reads JWT from localStorage on every request
7. Backend validates JWT and identifies user

### Security Notes

✅ **Anon key is PUBLIC** - Safe to expose in frontend code
✅ **JWT is USER-SPECIFIC** - Each user gets their own
✅ **RLS policies protect data** - JWT contains user_id claim
✅ **Token auto-refreshes** - Supabase handles expiration

## Summary

**Nothing is broken!** Your authentication is working exactly as designed:
- All config comes from `.env`
- No hardcoded values anywhere
- Standard Supabase authentication flow
- JWT is properly extracted and sent to backend

The log message is just showing you which localStorage key was used to retrieve the JWT. This is **debugging information**, not a security issue.
