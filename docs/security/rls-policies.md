# Row-Level Security (RLS) Policies

**Story**: 1.4 - Row-Level Security (RLS) Policies Implementation
**Date Created**: 2025-11-01
**Status**: ✅ Active

---

## Overview

Row-Level Security (RLS) is the **primary security mechanism** for TK9's multi-user authentication system. It enforces complete data isolation between users at the **PostgreSQL database level**, not in application code.

### Why RLS?

- **Defense in Depth**: Even if application code has bugs, database enforces security
- **Automatic Enforcement**: Supabase client applies RLS to ALL queries transparently
- **No Manual Filtering**: Eliminates risk of forgetting `WHERE user_id = ?` filters
- **Audit Trail**: pg_policies table documents all security rules
- **Zero Trust**: Database doesn't trust application layer security

---

## Architecture

### Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Request                          │
│  (Browser/API with JWT token containing user_id in 'sub')  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend + JWT Middleware               │
│         (Extracts user_id, passes JWT to Supabase)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Supabase Client                           │
│      (Automatically includes JWT in database requests)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL with RLS Policies                   │
│                                                             │
│  auth.uid() extracts user ID from JWT → Filters all rows   │
│                                                             │
│  Users table: WHERE auth.uid() = id                        │
│  Sessions table: WHERE user_id = auth.uid()                │
│  Drafts table: WHERE session_id IN (owned sessions)        │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

**auth.uid()**
- PostgreSQL function provided by Supabase
- Extracts authenticated user's UUID from JWT token (`sub` claim)
- Returns NULL for unauthenticated requests
- Used in all RLS policy conditions

**USING Clause**
- Defines row visibility filter
- Applied to SELECT, UPDATE, DELETE operations
- Rows not matching the condition are invisible to the user

**WITH CHECK Clause**
- Validates rows being inserted or updated
- Prevents users from inserting/updating data they shouldn't own
- Raises permission error if check fails

---

## Implemented Policies

### 1. Users Table

#### Policy: "Users view own profile"

```sql
CREATE POLICY "Users view own profile"
ON users
FOR SELECT
USING (auth.uid() = id);
```

**Purpose**: Users can only query their own user record
**Operation**: SELECT
**Condition**: Authenticated user's ID must match the user record's ID

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') queries users table
SELECT * FROM users WHERE id = 'aaa-111';  -- ✅ Returns 1 row (own profile)
SELECT * FROM users WHERE id = 'bbb-222';  -- ❌ Returns 0 rows (RLS filters it out)
SELECT * FROM users;                        -- ✅ Returns only 1 row (own profile)
```

---

### 2. Research Sessions Table

#### Policy: "Users view own sessions"

```sql
CREATE POLICY "Users view own sessions"
ON research_sessions
FOR SELECT
USING (user_id = auth.uid());
```

**Purpose**: Users can only view sessions they own
**Operation**: SELECT
**Condition**: Session's user_id must match authenticated user

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') queries sessions
SELECT * FROM research_sessions WHERE user_id = 'aaa-111';  -- ✅ Returns User A's sessions
SELECT * FROM research_sessions WHERE user_id = 'bbb-222';  -- ❌ Returns 0 rows (RLS blocks)
SELECT * FROM research_sessions;                             -- ✅ Returns only User A's sessions
```

#### Policy: "Users insert own sessions"

```sql
CREATE POLICY "Users insert own sessions"
ON research_sessions
FOR INSERT
WITH CHECK (user_id = auth.uid());
```

**Purpose**: Prevent users from creating sessions for other users
**Operation**: INSERT
**Condition**: user_id in new row must match authenticated user

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') attempts insertions
INSERT INTO research_sessions (user_id, title, status)
VALUES ('aaa-111', 'My Research', 'in_progress');  -- ✅ Success

INSERT INTO research_sessions (user_id, title, status)
VALUES ('bbb-222', 'Fake Session', 'in_progress');  -- ❌ Permission denied (RLS WITH CHECK fails)
```

#### Policy: "Users update own sessions"

```sql
CREATE POLICY "Users update own sessions"
ON research_sessions
FOR UPDATE
USING (user_id = auth.uid());
```

**Purpose**: Users can only update sessions they own
**Operation**: UPDATE
**Condition**: Session's user_id must match authenticated user

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') attempts updates
UPDATE research_sessions SET status = 'completed'
WHERE id = 'session-owned-by-user-a';  -- ✅ Success

UPDATE research_sessions SET status = 'completed'
WHERE id = 'session-owned-by-user-b';  -- ✅ No error, but 0 rows affected (RLS filters it out)
```

#### Policy: "Users can delete their own research sessions"

```sql
CREATE POLICY "Users can delete their own research sessions"
ON research_sessions
FOR DELETE
USING (auth.uid() = user_id);
```

**Purpose**: Allow users to delete sessions they own
**Operation**: DELETE
**Condition**: Session's user_id must match authenticated user

**Note**: This policy was **manually added** outside the official Story 1.4 migration workflow. It was discovered during the database audit and **intentionally kept** during cleanup as it provides useful functionality for users to manage their own data.

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') attempts deletions
DELETE FROM research_sessions WHERE id = 'session-owned-by-user-a';  -- ✅ Success (1 row deleted)

DELETE FROM research_sessions WHERE id = 'session-owned-by-user-b';  -- ✅ No error, 0 rows deleted (RLS filters it out)

-- Attempting to delete all sessions (without WHERE clause)
DELETE FROM research_sessions;  -- ✅ Deletes ONLY User A's sessions (RLS filters automatically)
```

**CASCADE Behavior**:
When a session is deleted, the `ON DELETE CASCADE` foreign key constraint automatically deletes all associated draft files:

```sql
-- User A deletes a session with 5 draft files
DELETE FROM research_sessions WHERE id = 'session-123';
-- Result: 1 session deleted + 5 draft files automatically deleted (CASCADE)
```

**Security Implications**:
- ✅ Users can only delete their own sessions (RLS enforces ownership)
- ✅ Cascading deletes respect RLS on draft_files table
- ✅ No user can accidentally or maliciously delete other users' data
- ⚠️ Deletion is permanent - consider implementing soft deletes if undo functionality is needed

**Migration Status**: Added manually (not in `20251101_enable_rls_policies.sql`), documented in `AUDIT_TRAIL_STORY_1.4.md`

---

### 3. Draft Files Table

#### Policy: "Users view own drafts"

```sql
CREATE POLICY "Users view own drafts"
ON draft_files
FOR SELECT
USING (
  session_id IN (
    SELECT id FROM research_sessions WHERE user_id = auth.uid()
  )
);
```

**Purpose**: Users can only view draft files from sessions they own
**Operation**: SELECT
**Condition**: Draft's session_id must be in the list of sessions owned by authenticated user

**Examples**:
```sql
-- User A (auth.uid() = 'aaa-111') queries draft files
SELECT * FROM draft_files WHERE session_id = 'session-owned-by-user-a';  -- ✅ Returns drafts
SELECT * FROM draft_files WHERE session_id = 'session-owned-by-user-b';  -- ❌ Returns 0 rows (RLS blocks)
SELECT * FROM draft_files;                                                 -- ✅ Returns only drafts from User A's sessions
```

**Note**: This policy uses a subquery to check session ownership, which adds a small performance overhead but ensures complete isolation.

---

## Testing & Verification

### Verification Queries

**Check RLS is enabled**:
```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('users', 'research_sessions', 'draft_files')
AND schemaname = 'public';
```

Expected output:
```
 schemaname |     tablename      | rowsecurity
------------+--------------------+-------------
 public     | users              | t
 public     | research_sessions  | t
 public     | draft_files        | t
```

**View all policies**:
```sql
SELECT tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename IN ('users', 'research_sessions', 'draft_files')
ORDER BY tablename, policyname;
```

### Testing Methodology

**Positive Tests** (Authorized Access):
1. Create test user A
2. User A creates session → Verify visible via SELECT
3. User A updates session status → Verify UPDATE succeeds
4. User A queries own drafts → Verify visible

**Negative Tests** (Unauthorized Access):
1. Create test users A and B
2. User A creates session
3. User B queries User A's session ID → Verify returns 0 rows (not permission error)
4. User B attempts UPDATE on User A's session → Verify 0 rows affected
5. User B attempts INSERT session with user_id = User A's ID → Verify permission denied

**Edge Cases**:
1. Unauthenticated request (no JWT) → Verify returns empty results
2. JWT with non-existent user_id → Verify returns empty results
3. Anonymous user upgrades to registered → Verify session transfer maintains RLS

**Test Location**: `tests/integration/test_rls_policies.py`

---

## Security Considerations

### Service Role Key

⚠️ **CRITICAL**: The service role key **bypasses all RLS policies**.

**Never**:
- Expose service role key to frontend
- Use service role key in client-side code
- Share service role key in public repositories

**Only Use For**:
- Admin operations (user management, bulk operations)
- Backend system tasks (file detection service writing drafts)
- Database migrations and maintenance

**Safe Pattern**:
```python
# Backend only - never send to frontend
service_client = create_client(supabase_url, service_role_key)

# Frontend gets anon key (respects RLS)
anon_client = create_client(supabase_url, anon_key)
```

### JWT Token Security

**Best Practices**:
- Store JWT in HTTP-only cookies (prevents XSS attacks)
- Use Secure flag in production (HTTPS only)
- Set SameSite=Lax (prevents CSRF)
- Never store in localStorage (vulnerable to XSS)
- Token expiration: 7 days (access) + 30 days (refresh)

### RLS Bypass Risks

**Scenarios where RLS doesn't protect**:
1. SQL injection in application code (use parameterized queries)
2. Compromised service role key (rotate immediately if exposed)
3. Database admin accounts (limit access strictly)

### Defense-in-Depth Strategy

TK9 implements **layered security** by combining RLS policies with application-level user_id filters, creating multiple independent security barriers.

#### Why Keep Application Filters with RLS?

**RLS is Primary, Application Filters are Secondary**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: Application                     │
│  Backend code explicitly filters: .eq("user_id", user_id)  │
│         (Catches: Logic bugs, API misuse)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ If Layer 1 fails ↓
┌─────────────────────────────────────────────────────────────┐
│                   Layer 2: Database (RLS)                   │
│  PostgreSQL policies: WHERE user_id = auth.uid()            │
│      (Catches: All unauthorized access, even if app fails)  │
└─────────────────────────────────────────────────────────────┘
```

**Real-World Protection Scenarios**:

1. **Application Bug**: Developer forgets to add `.eq("user_id", user_id)` to a query
   - ❌ Layer 1 (Application) fails to filter
   - ✅ Layer 2 (RLS) automatically filters → Security maintained

2. **API Misuse**: Frontend sends request with wrong user_id in query params
   - ❌ Layer 1 (Application) uses provided user_id
   - ✅ Layer 2 (RLS) filters using JWT's auth.uid() → Security maintained

3. **Direct Database Access**: Someone bypasses API and queries database directly
   - ❌ Layer 1 (Application) not invoked
   - ✅ Layer 2 (RLS) enforces policy → Security maintained

4. **Both Layers Working**: Normal operation with correct code
   - ✅ Layer 1 (Application) filters correctly
   - ✅ Layer 2 (RLS) validates → Double protection

#### Implementation Example

**Backend code in `web_dashboard/database.py`**:
```python
def get_user_sessions(user_id: str) -> List[Dict]:
    """
    Fetch research sessions for a specific user.

    Defense-in-Depth:
    - Application Layer: .eq("user_id", user_id) explicit filter
    - Database Layer: RLS policy automatically enforces user_id = auth.uid()

    Even if application filter is removed by mistake, RLS prevents data leaks.
    """
    response = supabase.table("research_sessions") \
        .select("*") \
        .eq("user_id", user_id) \  # Application-level filter (Layer 1)
        .order("created_at", desc=True) \
        .execute()
    # RLS policy enforces user_id = auth.uid() automatically (Layer 2)
    return response.data
```

**What happens if application filter is removed**:
```python
# BROKEN CODE (application filter missing):
response = supabase.table("research_sessions") \
    .select("*") \
    .execute()
# Expected: Returns ALL sessions (security breach)
# Actual: RLS filters to only auth.uid()'s sessions (security maintained)
```

#### Why Not Rely on RLS Alone?

**Application filters provide benefits beyond security**:

1. **Performance**: Explicit filters help query planner use indexes more efficiently
2. **Clarity**: Code explicitly shows security intent (self-documenting)
3. **Early Validation**: Catches logic errors before database query
4. **API Semantics**: RESTful APIs naturally include user_id in queries

**Example - Performance Benefit**:
```sql
-- With application filter (better query plan):
SELECT * FROM research_sessions WHERE user_id = 'abc-123';
-- Uses idx_research_sessions_user_id directly

-- Without application filter (relies on RLS only):
SELECT * FROM research_sessions;
-- RLS adds WHERE user_id = auth.uid() after initial scan
```

#### Decision: Keep Both Layers

**TK9's Security Policy** (Story 1.4, Task 10):
- ✅ **KEEP** application-level `.eq("user_id", user_id)` filters
- ✅ **KEEP** RLS policies as primary security mechanism
- ❌ **NEVER** remove either layer

**Rationale**:
- RLS protects against application bugs (primary security)
- Application filters provide performance + clarity (secondary benefits)
- Cost: Minimal (one extra method call)
- Benefit: Defense-in-depth protects against single points of failure

**Anti-Pattern to Avoid**:
```python
# ❌ WRONG: Relying solely on RLS without explicit filters
def get_user_sessions_unsafe():
    # "RLS will handle it" - true but not best practice
    return supabase.table("research_sessions").select("*").execute().data

# ✅ RIGHT: Defense-in-depth with both layers
def get_user_sessions_safe(user_id: str):
    # Explicit filter + RLS both enforce security
    return supabase.table("research_sessions") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute().data
```

#### Testing Defense-in-Depth

**Verify both layers work independently**:

1. **Test RLS alone**: Use service_role client (bypasses app code) with user JWT
   - Confirms database-level security works

2. **Test application logic**: Mock database, verify filters applied
   - Confirms application-level filtering works

3. **Test combined**: Normal API requests with user authentication
   - Confirms both layers work together

See `tests/integration/test_rls_policies_real_auth.py` for RLS-specific tests.

---

## Performance Considerations

### Query Performance

**Indexes Support RLS**:
- `idx_research_sessions_user_id` - Speeds up user_id filters
- `idx_users_email` - Speeds up email lookups
- `idx_draft_files_session_id` - Speeds up session file queries

**Subquery Performance**:
The draft_files policy uses a subquery which adds overhead:
```sql
EXPLAIN ANALYZE
SELECT * FROM draft_files WHERE session_id IN (
  SELECT id FROM research_sessions WHERE user_id = auth.uid()
);
```

For optimal performance:
- Index on `research_sessions(user_id)` is critical
- PostgreSQL query planner optimizes subquery to semi-join
- Typical overhead: <5ms for queries with proper indexes

### Monitoring

**Track RLS overhead**:
```sql
-- Enable query logging in Supabase
-- Monitor slow queries in Supabase dashboard
-- Look for queries with high planning time
```

**Expected Performance**:
- Simple SELECT with RLS: +1-2ms overhead
- Complex subquery RLS (draft_files): +3-5ms overhead
- INSERT with RLS check: +1ms overhead

---

## Troubleshooting

### Common Issues

**Issue: "Permission denied for table users"**

**Cause**: Service role key not set, or RLS policy too restrictive

**Solution**:
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'users';

-- Verify policy exists
SELECT * FROM pg_policies WHERE tablename = 'users';

-- Ensure JWT token is valid and contains user_id
```

**Issue: "Query returns empty result set"**

**Cause**: RLS filtering out all rows (expected behavior for unauthorized access)

**Solution**:
- This is correct RLS behavior, not a bug
- User is not authorized to see those rows
- Check JWT token's user_id matches expected ownership

**Issue: "Cannot insert row violating policy"**

**Cause**: WITH CHECK constraint failed (trying to insert data for wrong user)

**Solution**:
- Verify user_id in INSERT matches auth.uid()
- Check JWT token is correctly set
- Ensure application passes correct user_id

### Debugging RLS

**Test RLS with specific user context**:
```sql
-- Set session user context (for testing in SQL editor)
SET request.jwt.claims TO '{"sub": "user-id-here"}';

-- Run queries as that user
SELECT * FROM research_sessions;

-- Reset context
RESET request.jwt.claims;
```

**Bypass RLS for admin debugging** (use carefully):
```sql
-- Temporarily disable RLS (requires superuser)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Re-enable after debugging
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

---

## Migration History

### Migration: 20251101_enable_rls_policies.sql

**Applied**: 2025-11-01
**Status**: ✅ Active

**Changes**:
1. Enabled RLS on users, research_sessions, draft_files tables
2. Created 5 RLS policies (1 users, 3 research_sessions, 1 draft_files)
3. Verified all policies active via pg_policies

**Rollback**:
See `web_dashboard/migrations/20251101_enable_rls_policies.sql` for rollback SQL

---

## References

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Official Docs](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Story 1.4 Implementation: `docs/stories/1-4-row-level-security-rls-policies-implementation.md`
- Architecture Doc: `docs/architecture.md#Security Architecture`
- Migration Script: `web_dashboard/migrations/20251101_enable_rls_policies.sql`
- Integration Tests: `tests/integration/test_rls_policies.py`

---

**Last Updated**: 2025-11-01
**Maintained By**: TK9 Development Team
