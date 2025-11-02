# Security Architecture: Backend vs Frontend

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser (Client)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Vue.js Frontend                                       │ │
│  │                                                        │ │
│  │  Uses: frontend_poc/.env                              │ │
│  │  ✅ VITE_SUPABASE_URL (public)                        │ │
│  │  ✅ VITE_SUPABASE_ANON_KEY (public, RLS-enforced)     │ │
│  │  ❌ NO service_role key                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ▼                               │
│                    HTTP/WebSocket Requests                   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Server (Backend)                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Backend (main.py)                            │ │
│  │                                                        │ │
│  │  Uses: web_dashboard/.env                             │ │
│  │  ✅ SUPABASE_URL                                      │ │
│  │  ✅ SUPABASE_SERVICE_KEY (ADMIN - bypasses RLS) 🔒    │ │
│  │  ✅ JWT_SECRET 🔒                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                              ▼                               │
│                    Database Operations                       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Supabase Database  │
                    │  (PostgreSQL + RLS) │
                    └─────────────────────┘
```

## 🔑 Key Types and Access Levels

### 1. `anon` Key (Public) 🌐
- **Location**: Frontend `.env` (VITE_SUPABASE_ANON_KEY)
- **Access Level**: User-level (respects RLS policies)
- **Use Case**: Browser/client operations
- **Safe to expose**: ✅ Yes (designed for public use)
- **Example operations**:
  - User login/registration
  - Fetching user's own sessions
  - Creating sessions for current user

### 2. `service_role` Key (Secret) 🔒
- **Location**: Backend `.env` only (SUPABASE_SERVICE_KEY)
- **Access Level**: Admin (bypasses ALL RLS policies)
- **Use Case**: Server-side admin operations
- **Safe to expose**: ❌ NO! (complete database access)
- **Example operations**:
  - Creating sessions for any user
  - Transferring sessions between users
  - Admin queries across all data
  - Integration testing

## 🛡️ Row-Level Security (RLS) Flow

### With `anon` Key (Frontend):
```
User Request → anon key → Supabase
                            ↓
                     RLS Policy Check
                            ↓
              ┌─────────────┴─────────────┐
              ▼                           ▼
         ✅ ALLOWED                  ❌ DENIED
    (user's own data)          (other users' data)
```

### With `service_role` Key (Backend):
```
Backend Request → service_role key → Supabase
                                        ↓
                                 RLS BYPASSED
                                        ↓
                                 ✅ FULL ACCESS
                              (all data, all users)
```

## 🚨 Security Threats if `service_role` Exposed

### Scenario: service_role key leaked to frontend

```
❌ BAD: Frontend has service_role key
    ↓
User opens browser DevTools
    ↓
Inspects network requests or JS bundle
    ↓
Extracts service_role key
    ↓
Uses key to make direct API calls
    ↓
🔓 COMPLETE DATABASE COMPROMISE
```

**Attacker can**:
- Access all users' personal data
- Read all research sessions
- Modify or delete any data
- Bypass all authentication
- Impersonate any user
- Export entire database

## ✅ Correct Implementation

### Backend Operations (with service_role)

```python
# web_dashboard/database.py
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")  # Backend .env

SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Admin operation - bypasses RLS
async def transfer_sessions(old_user_id, new_user_id):
    # Only backend can do this!
    return client.table("research_sessions")
        .update({"user_id": new_user_id})
        .eq("user_id", old_user_id)
        .execute()
```

### Frontend Operations (with anon key)

```typescript
// frontend_poc/src/utils/supabase.ts
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// User operation - RLS enforced
async function fetchMySessions() {
  // Can only see current user's sessions (RLS enforced)
  return supabase
    .from('research_sessions')
    .select('*')
    // RLS automatically filters to current user
}
```

## 📋 Checklist: Is Your Setup Secure?

- [ ] `service_role` key ONLY in `web_dashboard/.env`
- [ ] `web_dashboard/.env` is in `.gitignore`
- [ ] Frontend uses `VITE_` prefixed variables
- [ ] Frontend NEVER imports from `web_dashboard/.env`
- [ ] `service_role` key NEVER logged or printed
- [ ] Backend `.env` has proper file permissions (600)
- [ ] Frontend `.env` only contains public keys

## 🔄 Migration Path (Current to Story 1.4)

### Current State (Story 1.3)
```
✅ Database tables created
❌ RLS policies NOT implemented yet
→ anon key can access all data (no RLS to enforce)
→ service_role key = overkill but future-proof
```

### After Story 1.4 (RLS Implementation)
```
✅ Database tables created
✅ RLS policies implemented
→ anon key = restricted to user's own data
→ service_role key = REQUIRED for backend operations
```

## 🎯 Summary

| Aspect | Frontend | Backend |
|--------|----------|---------|
| **Key Type** | `anon` (public) | `service_role` (secret) |
| **RLS** | ✅ Enforced | ❌ Bypassed |
| **Expose to Browser** | ✅ Yes | ❌ NEVER |
| **Access Level** | User data only | All data (admin) |
| **File** | `frontend_poc/.env` | `web_dashboard/.env` |
| **Commit to Git** | ✅ Can (if needed) | ❌ NEVER |

**Golden Rule**: If it's a secret, it stays on the server! 🔒
