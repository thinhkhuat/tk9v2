# Database Migrations

This directory contains SQL migration scripts for the TK9 Web Dashboard database schema.

## Migration Naming Convention

Migrations follow the naming pattern: `YYYYMMDDHHMMSS_description.sql`

Example: `20251101030227_create_users_sessions_drafts_tables.sql`

## Migration History

### 20251101030227_create_users_sessions_drafts_tables.sql
**Story**: 1.3 - User and Session Database Schema
**Created**: 2025-11-01
**Applied**: 2025-11-01
**Status**: ✅ Applied successfully
**Audit File**: `audit/20251101_story_1_3_database_schema_audit.sql`

**Purpose**: Initial database schema creation for authentication and research session management.

**Tables Created**:
- `users` - User profiles (both anonymous and registered)
- `research_sessions` - Research session tracking
- `draft_files` - Draft file detection and linking

**ENUMs Created**:
- `session_status` - Session states: in_progress, completed, failed
- `research_stage` - Research stages: 1_initial_research, 2_planning, 3_parallel_research, 4_writing

**Indexes Created**:
- `idx_users_email` - Fast email lookups
- `idx_research_sessions_user_id` - User session queries
- `idx_research_sessions_created_at` - Chronological sorting
- `idx_draft_files_session_id` - Session file lookups

**Triggers Created**:
- `update_users_updated_at` - Automatic timestamp updates
- `update_research_sessions_updated_at` - Automatic timestamp updates

**Foreign Keys**:
- `research_sessions.user_id → users.id` (CASCADE DELETE)
- `draft_files.session_id → research_sessions.id` (CASCADE DELETE)

---

### 20251101_enable_rls_policies.sql
**Story**: 1.4 - Row-Level Security (RLS) Policies Implementation
**Created**: 2025-11-01
**Applied**: Pending
**Status**: ⏳ Ready for manual application

**Purpose**: Implement Row-Level Security (RLS) policies to enforce complete data isolation between users at the PostgreSQL database level.

**RLS Enabled On**:
- `users` table
- `research_sessions` table
- `draft_files` table

**Policies Created**:
1. **Users view own profile** - SELECT restricted to auth.uid() = id
2. **Users view own sessions** - SELECT restricted to user_id = auth.uid()
3. **Users insert own sessions** - INSERT restricted to user_id = auth.uid()
4. **Users update own sessions** - UPDATE restricted to user_id = auth.uid()
5. **Users view own drafts** - SELECT restricted via subquery to owned sessions

**Security Model**:
- Uses `auth.uid()` function which extracts user ID from JWT token
- Unauthenticated requests (auth.uid() = NULL) return empty results
- Service role key bypasses RLS (admin operations only)
- Supabase client automatically enforces RLS based on auth context

**Verification Queries**:
```sql
-- Verify RLS enabled
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename IN ('users', 'research_sessions', 'draft_files');

-- View all policies
SELECT tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename IN ('users', 'research_sessions', 'draft_files');
```

## Applying Migrations

### Local Supabase Instance (Testing)

1. Open Supabase SQL Editor at your local instance
2. Copy the contents of the migration file
3. Execute the UP MIGRATION section
4. Run verification queries to confirm success

### Production Supabase Instance

⚠️ **IMPORTANT**: Always test migrations on local instance first!

1. Ensure local testing is complete
2. Create a backup of production database
3. Open Supabase SQL Editor for production project
4. Execute the migration during a maintenance window
5. Run verification queries
6. Update this README with deployment timestamp

## Rolling Back Migrations

To rollback a migration:

1. Copy the DOWN MIGRATION section from the migration file
2. Execute in Supabase SQL Editor
3. Verify rollback with database inspection queries
4. Update this README

## Verification

After applying migrations, verify:

```sql
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- List all indexes
\di

-- Test triggers
INSERT INTO users (email, is_anonymous) VALUES ('test@example.com', false);
UPDATE users SET email = 'test2@example.com' WHERE email = 'test@example.com';
SELECT email, created_at, updated_at FROM users WHERE email = 'test2@example.com';

-- Test cascade deletes
DELETE FROM users WHERE email = 'test2@example.com';
```

## Notes

- All migrations use `IF NOT EXISTS` clauses for idempotency
- Foreign keys use `ON DELETE CASCADE` for automatic cleanup
- All tables include audit timestamps (created_at, updated_at)
- UUIDs are used for all primary keys (gen_random_uuid())
- PostgreSQL ENUMs provide type safety for constrained values
