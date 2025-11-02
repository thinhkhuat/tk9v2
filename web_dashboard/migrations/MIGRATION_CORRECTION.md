# Migration Correction: Using auth.users Instead of Custom Users Table

**Date**: 2025-11-01
**Story**: 1.3 User and Session Database Schema
**Issue**: Original migration attempted to create custom `public.users` table
**Resolution**: Use Supabase Auth's built-in `auth.users` table

---

## Problem Summary

The original migration `20251101030227_create_users_sessions_drafts_tables.sql` attempted to create a custom `public.users` table:

```sql
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  is_anonymous BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Why This Failed

1. **Table Already Exists**: The Supabase instance is shared across multiple projects. A `public.users` table already exists with 153 rows and a different schema:
   - Old schema: `id, email, created_at, last_seen, total_jobs, active_jobs`
   - New schema: `id, email, is_anonymous, created_at, updated_at`

2. **Silent Failure**: The `CREATE TABLE IF NOT EXISTS` statement silently skipped table creation, but the existing table doesn't have the `is_anonymous` column required by tests.

3. **Schema Conflict**: Tests failed with `Could not find the 'is_anonymous' column of 'users'` because the existing table has a completely different structure.

4. **Non-Negotiable Constraint**: Cannot delete or modify the existing `public.users` table as it's used by other projects.

---

## Solution: Use auth.users

After consulting Gemini and validating with official Supabase documentation, the correct approach is:

### ✅ DO: Reference auth.users Directly

```sql
CREATE TABLE IF NOT EXISTS research_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- CORRECT: Reference Supabase Auth's user table
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### ❌ DON'T: Create Custom Users Table

```sql
-- WRONG: Do NOT create custom users table
CREATE TABLE users (...);

-- WRONG: Do NOT reference public.users
user_id UUID NOT NULL REFERENCES users(id)
```

---

## Why auth.users is the Correct Approach

### 1. **Single Source of Truth**
- Supabase's entire authentication system (JWT, RLS, Auth API) is built around `auth.users`
- No synchronization issues between custom table and auth system

### 2. **Avoids Conflicts**
- `auth` schema is managed by Supabase - stable and isolated
- No collisions with other projects on shared instances

### 3. **No Manual Syncing Required**
- Don't need to create triggers to sync custom users table with auth.users
- Changes to auth.users (signup, delete) automatically handled

### 4. **Security**
- `auth` schema is protected from direct API access
- Database can enforce foreign key constraints while keeping auth data secure

### 5. **Official Best Practice**
From official Supabase docs ([User Management](https://supabase.com/docs/guides/auth/managing-user-data)):

> For security, the Auth schema is not exposed in the auto-generated API. If you want to access users data via the API, you can create your own user tables in the public schema.
>
> Make sure to protect the table by enabling Row Level Security. **Reference the auth.users table to ensure data integrity**. Specify on delete cascade in the reference.

Example from official docs:
```sql
create table public.profiles (
  id uuid not null references auth.users on delete cascade,
  first_name text,
  last_name text,
  primary key (id)
);
```

---

## Corrected Migration

**File**: `20251101040000_create_sessions_drafts_tables_with_auth.sql`

Key changes:
1. **Removed** `CREATE TABLE users` statement entirely
2. **Changed** foreign key reference:
   - Old: `REFERENCES users(id)`
   - New: `REFERENCES auth.users(id)`
3. **Kept** all other table structures (research_sessions, draft_files)
4. **Preserved** all indexes, triggers, and CASCADE behavior

---

## Code Changes Required

### 1. ✅ database.py
**No changes needed** - already works correctly:
- Functions only interact with `research_sessions` and `draft_files`
- Accepts `user_id` as parameter (works with any valid UUID from auth.users)

### 2. ✅ models.py
**Minor documentation updates**:
```python
class User(BaseModel):
    """
    Database model for auth.users table (managed by Supabase Auth).

    NOTE: This model is for TYPE REFERENCE ONLY. Do NOT create a custom
    public.users table. Always reference auth.users directly in foreign keys.
    """

class ResearchSessionDB(BaseModel):
    """Database model for research_sessions table"""
    # Changed comment:
    user_id: UUID = Field(..., description="Foreign key to auth.users(id)")
```

### 3. ✅ tests/integration/test_database_operations_auth_users.py
**New test file** that:
- Uses existing users from `auth.users` (doesn't create test users)
- Skips tests that would delete users (too risky for shared instance)
- Uses fixtures to get test user IDs safely
- Documents why cascade delete tests are skipped

---

## Migration Execution Plan

### Step 1: Rollback Old Migration (If Applied)

If the old migration was applied, check what needs cleanup:

```sql
-- Check what was created:
SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  AND tablename IN ('users', 'research_sessions', 'draft_files');

-- Check ENUMs:
SELECT typname FROM pg_type WHERE typname IN ('session_status', 'research_stage');

-- Cleanup OLD migration artifacts ONLY (keep research_sessions & draft_files if correct):
DROP TABLE IF EXISTS research_sessions CASCADE;  -- Only if referencing wrong users table
DROP TABLE IF EXISTS draft_files CASCADE;
-- DO NOT drop 'users' table - used by other projects!
DROP TYPE IF EXISTS session_status;
DROP TYPE IF EXISTS research_stage;
```

### Step 2: Apply Corrected Migration

```bash
# Apply new migration via Supabase Dashboard SQL Editor
# OR via psql:
psql "postgresql://..." -f migrations/20251101040000_create_sessions_drafts_tables_with_auth.sql
```

### Step 3: Verify Correct Foreign Keys

```sql
-- Verify foreign key points to auth.users:
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'research_sessions';

-- Expected result:
-- research_sessions | user_id | auth | users | id
```

### Step 4: Test with Existing Users

```sql
-- Get an existing user from auth.users:
SELECT id, email FROM auth.users LIMIT 1;

-- Create a test session (replace USER_ID):
INSERT INTO research_sessions (user_id, title, status)
VALUES ('USER_ID_HERE', 'Test Session', 'in_progress')
RETURNING *;

-- Verify it worked:
SELECT * FROM research_sessions WHERE title = 'Test Session';

-- Cleanup:
DELETE FROM research_sessions WHERE title = 'Test Session';
```

### Step 5: Run Tests

```bash
cd web_dashboard
pytest tests/integration/test_database_operations_auth_users.py -v
```

Expected results:
- Most tests should pass
- Some tests may skip if insufficient users in auth.users
- No errors about missing `is_anonymous` column

---

## Additional Considerations

### Anonymous Users

Supabase Auth supports anonymous users automatically:
- Anonymous users exist in `auth.users` with `is_anonymous = true`
- No need for custom logic - just use `auth.users.is_anonymous` column

### User Profile Data

If you need to store additional user-specific data (beyond what's in auth.users), create a separate profile table:

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  avatar_url TEXT,
  -- other custom fields
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Trigger to auto-create profile on signup:
CREATE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### Session Transfer

The `transfer_sessions()` function works correctly:
- Transfers sessions from anonymous user to registered user
- Both users must exist in `auth.users`
- No changes needed to existing code

---

## References

### Gemini Consultation
- **Session ID**: `3b07ef5d-3e39-40be-b542-a0639c0bad3f`
- **Recommendation**: Always reference `auth.users` directly, never create custom users table
- **Rationale**: Single source of truth, no sync issues, security, official best practice

### Official Supabase Documentation
1. [User Management](https://supabase.com/docs/guides/auth/managing-user-data) - "Reference the auth.users table to ensure data integrity"
2. [RAG with Permissions](https://supabase.com/docs/guides/ai/rag-with-permissions) - Examples showing `owner_id uuid not null references auth.users (id)`
3. [Database Advisor: Foreign Keys](https://supabase.com/docs/guides/database/database-advisors?lint=0021_fkey_to_auth_unique) - Warns against referencing non-PK unique constraints
4. [Migrate from Auth0](https://supabase.com/docs/guides/platform/migrating-to-supabase/auth0) - Migration patterns showing auth.users usage

---

## Summary

**Problem**: Tried to create custom `public.users` table, conflicted with existing table
**Root Cause**: Shared Supabase instance, existing table with different schema
**Solution**: Reference `auth.users(id)` directly in foreign keys
**Validation**: Confirmed by Gemini consultation + official Supabase docs
**Impact**: Code changes minimal, tests updated, migration corrected
**Status**: ✅ Ready to apply corrected migration

**Key Takeaway**: When using Supabase Auth, **always** reference `auth.users` directly. Never create a custom users table to mirror authentication data.
