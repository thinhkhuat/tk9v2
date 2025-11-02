# Migration Application Instructions

## Migration: 20251101030227_create_users_sessions_drafts_tables.sql

**Status**: ⏳ Ready for manual execution
**MCP Status**: Query timeout - requires manual application

### Steps to Apply:

1. **Open Supabase Dashboard**
   - Navigate to https://supabase.com/dashboard
   - Select project: "Supabase github-auth" (yurbnrqgsipdlijeyyuw)

2. **Open SQL Editor**
   - Click "SQL Editor" in left sidebar
   - Click "New Query"

3. **Execute Migration**
   - Copy contents of `20251101030227_create_users_sessions_drafts_tables.sql`
   - Paste into SQL Editor
   - Execute only the UP MIGRATION section (lines 10-78)
   - Verify no errors

4. **Verify Tables Created**
   ```sql
   -- List all tables
   SELECT tablename FROM pg_tables WHERE schemaname = 'public';

   -- Should see: users, research_sessions, draft_files
   ```

5. **Verify Indexes**
   ```sql
   SELECT indexname FROM pg_indexes WHERE schemaname = 'public';

   -- Should see:
   -- idx_users_email
   -- idx_research_sessions_user_id
   -- idx_research_sessions_created_at
   -- idx_draft_files_session_id
   ```

6. **Test Trigger Function**
   ```sql
   -- Insert test user
   INSERT INTO users (email, is_anonymous)
   VALUES ('test@example.com', false)
   RETURNING id, email, created_at, updated_at;

   -- Wait 1 second, then update
   UPDATE users
   SET email = 'test2@example.com'
   WHERE email = 'test@example.com';

   -- Verify updated_at changed
   SELECT email, created_at, updated_at
   FROM users
   WHERE email = 'test2@example.com';
   -- updated_at should be later than created_at

   -- Cleanup
   DELETE FROM users WHERE email = 'test2@example.com';
   ```

7. **Update Migration README**
   - Mark migration as "✅ Applied" in `migrations/README.md`
   - Add application timestamp

### Rollback (if needed):
Execute the DOWN MIGRATION section (lines 86-97) from the migration file.

### After Successful Application:
Notify the development team that database schema is ready for backend integration.
