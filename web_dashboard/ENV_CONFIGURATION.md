# Environment Configuration

## 🔐 CRITICAL: Backend vs Frontend Separation

### Two Separate `.env` Files

**1. Backend (Server-Side) - PRIVATE** 🔒
- **Location**: `web_dashboard/.env`
- **Contains**: SECRETS (service_role key, JWT secret)
- **Used by**: Python backend (FastAPI, database.py, tests)
- **Security**: NEVER commit to Git, NEVER expose to frontend

**2. Frontend (Client-Side) - PUBLIC** 🌐
- **Location**: `web_dashboard/frontend_poc/.env`
- **Contains**: Public keys (URL, anon key with `VITE_` prefix)
- **Used by**: Vue.js frontend (browser)
- **Security**: Safe to expose (designed for browsers)

## Current Configuration

### Backend `.env` (web_dashboard/.env) - PRIVATE 🔒

```bash
# ⚠️ NEVER COMMIT THIS FILE - Contains admin secrets!

# Supabase Configuration (Backend)
SUPABASE_URL=https://yurbnrqgsipdlijeyyuw.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ⚠️ CRITICAL: service_role key = ADMIN ACCESS
SUPABASE_SERVICE_KEY=PASTE_YOUR_SERVICE_ROLE_KEY_HERE  # ← ADD THIS!

# JWT Secret for token verification
JWT_SECRET=y50Mph1j3TzKH5d7OxymJvzPCdYAyDU79Onoq/SbvzFZBgBZ82T2ZQo4oIP1v4uJz8Y7hIPetQGB2HHC3B9ySg==
```

### Frontend `.env` (web_dashboard/frontend_poc/.env) - PUBLIC 🌐

```bash
# ✅ Safe to commit (public keys designed for browsers)

# Supabase Configuration (Frontend)
VITE_SUPABASE_URL=https://yurbnrqgsipdlijeyyuw.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ❌ NEVER add service_role key here!
```

## Missing Credential

❌ **`SUPABASE_SERVICE_KEY` is missing!**

To get it:
1. Go to: https://supabase.com/dashboard
2. Select project: "Supabase github-auth" (yurbnrqgsipdlijeyyuw)
3. Navigate to: Settings → API
4. Copy the **`service_role` (secret)** key
5. Paste it in `web_dashboard/.env`:
   ```bash
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...
   ```

## Why Backend/Frontend Separation Matters

### Security Risk Without Separation

❌ **BAD**: Putting `service_role` key in frontend `.env`:
```
Frontend .env → Built into JavaScript bundle → Sent to browser → Anyone can extract it!
```

If exposed:
- 🔓 Anyone can bypass ALL Row-Level Security
- 🔓 Anyone can access ALL users' data
- 🔓 Anyone can delete/modify ANY data
- 🔓 Complete database compromise

### Correct Architecture

✅ **GOOD**: Keep `service_role` key in backend only:
```
Backend .env → Stays on server → Never sent to browser → Only backend code can use it
Frontend .env → Built into JS bundle → Safe (only contains public anon key)
```

## Why `service_role` Key is Required

The `service_role` key is needed for backend:
- **Server-side operations**: Creating sessions, updating status
- **Bypassing RLS**: Admin operations (Story 1.4 will need this)
- **Integration tests**: Database validation tests
- **Session transfer**: Moving sessions between users

⚠️ **CRITICAL**: `service_role` key = **complete database admin access**
- NEVER commit to Git
- NEVER expose to frontend
- NEVER log it
- ONLY use on secure backend server

## Path Logic

```python
# database.py (web_dashboard/database.py)
env_path = Path(__file__).parent / ".env"
# → web_dashboard/.env

# tests (web_dashboard/tests/integration/test_*.py)
env_path = Path(__file__).parent.parent.parent / ".env"
# → web_dashboard/.env (3 levels up)
```

## Verification

After adding `SUPABASE_SERVICE_KEY`, verify it loads:

```bash
cd web_dashboard
python3 -c "from database import SUPABASE_SERVICE_KEY; print('✅ Service key loaded' if SUPABASE_SERVICE_KEY else '❌ Key missing')"
```

## Running Tests

With correct `.env`:

```bash
pytest tests/integration/test_database_operations.py -v
```

Expected: **10 tests pass, 1 skips** (index verification requires RPC)

Without `SUPABASE_SERVICE_KEY`: **11 tests skip** (all skip - current state)

## Summary: Which `.env` for What?

| File | Purpose | Contains | Commit to Git? |
|------|---------|----------|----------------|
| `web_dashboard/.env` | **Backend secrets** | service_role, JWT secret | ❌ NEVER |
| `web_dashboard/frontend_poc/.env` | **Frontend config** | anon key (public) | ✅ Yes (if needed) |
| `tk9_source_deploy/.env` | **Multi-agent system** | LLM/search API keys | ❌ NEVER |

### Key Takeaways

✅ **DO**:
- Keep `service_role` key ONLY in backend `.env`
- Use `VITE_` prefix for frontend variables
- Add backend `.env` to `.gitignore`
- Use separate keys for backend (service_role) and frontend (anon)

❌ **DON'T**:
- Put `service_role` key in frontend `.env`
- Commit backend `.env` to Git
- Log or expose `service_role` key
- Mix backend and frontend environment variables

## Troubleshooting

### Tests Still Skip

1. Check `SUPABASE_SERVICE_KEY` is in `web_dashboard/.env`
2. Verify no typos in key
3. Key should start with `eyJhbGc...`
4. Run verification script above

### "Supabase not configured" Warning

Check database.py logs:
```bash
cd web_dashboard
python3 -c "from database import get_supabase_client; client = get_supabase_client(); print('✅ Connected' if client else '❌ Not configured')"
```

If "Not configured":
- `SUPABASE_URL` or `SUPABASE_SERVICE_KEY` is empty
- Check `.env` file exists at `web_dashboard/.env`
- Verify `python-dotenv` is installed

## Summary

✅ **DO**: Use `web_dashboard/.env` for all Supabase credentials
❌ **DON'T**: Add Supabase config to project root `.env`
❌ **DON'T**: Commit `SUPABASE_SERVICE_KEY` to Git
✅ **DO**: Add `SUPABASE_SERVICE_KEY` to run tests
