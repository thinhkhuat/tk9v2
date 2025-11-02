# TK9 Historical Research Access & Authentication - Epic Breakdown

**Author:** Thinh
**Date:** 2025-10-31
**Project Level:** 3
**Target Scale:** 16 stories across 4 epics

---

## Overview

This document provides the detailed epic breakdown for **TK9 Historical Research Access & Authentication**, expanding on the high-level epic list in the [PRD](./PRD.md).

Each epic includes:

- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**

- Epic 1 establishes authentication foundation and database infrastructure
- Epic 2 builds historical access on top of authentication layer
- Epic 3 adds progressive disclosure UI for draft exploration
- Epic 4 optimizes performance and mobile experience
- No forward dependencies - each story builds only on previous work

**Total Estimate**: 16 stories, 61 story points, 4-6 weeks

---

## Epic 1: Authentication Foundation & Database Setup

### Goal

Establish the authentication infrastructure and database schema required for user identity management and session tracking. This epic delivers a working authentication system with anonymous sign-in, email registration, and secure session management, enabling users to create accounts and access TK9 with proper data isolation through Row-Level Security policies.

This epic is foundational - all subsequent features (historical access, draft viewing) depend on users having identities and sessions being properly linked to user accounts.

### Story Breakdown

**Total Stories**: 4 stories
**Estimated Story Points**: 16 points
**Timeline**: 1-2 weeks

---

**Story 1.1: Supabase Anonymous Authentication Integration**

As a **new user**,
I want **to access TK9 immediately without creating an account**,
So that **I can evaluate the research capabilities with zero friction**.

**Acceptance Criteria:**
1. When user lands on TK9 web dashboard, system automatically calls `supabase.auth.signInAnonymously()`
2. Anonymous user receives a unique UUID-based user ID and session token
3. Session token is stored in HTTP-only cookie (not localStorage)
4. User can initiate research without any authentication prompts
5. System displays subtle indicator showing anonymous status (e.g., "Anonymous Session" badge)
6. Anonymous session persists across browser refresh (session cookie remains valid)

**Prerequisites:** Supabase project configured, environment variables set

---

**Story 1.2: Email Registration and Login Flows**

As an **anonymous user who has completed research**,
I want **to create a permanent account with email and password**,
So that **my research history is preserved and accessible from any device**.

**Acceptance Criteria:**
1. "Upgrade to Permanent Account" button displays on research completion for anonymous users
2. Clicking button opens registration modal with email and password fields
3. Email validation enforces standard format (RFC 5322)
4. Password validation requires minimum 8 characters, 1 uppercase, 1 lowercase, 1 number
5. Upon successful registration, system transfers all anonymous research sessions to new permanent account
6. User receives email confirmation with verification link
7. Registered users can log in via email/password on subsequent visits
8. Login form includes "Forgot Password" link for password reset flow

**Prerequisites:** Story 1.1 (anonymous auth exists)

---

**Story 1.3: User and Session Database Schema**

As a **system administrator**,
I want **database tables to store user profiles and research sessions**,
So that **user data persists reliably and supports historical research access**.

**Acceptance Criteria:**
1. Create `users` table with columns: id (UUID, PK), email (unique), is_anonymous (boolean), created_at, updated_at
2. Create `research_sessions` table with columns: id (UUID, PK), user_id (FK to users), title, status (enum: in_progress, completed, failed), created_at, updated_at
3. Create `draft_files` table with columns: id (UUID, PK), session_id (FK to research_sessions), stage (enum: 1_initial_research, 2_planning, 3_parallel_research, 4_writing), file_path, detected_at
4. Add indexes on: users.email, research_sessions.user_id, research_sessions.created_at, draft_files.session_id
5. All tables include audit columns (created_at, updated_at) with automatic timestamp updates
6. Database migration script created and tested on local Supabase instance

**Prerequisites:** Story 1.1, 1.2 (auth flows defined)

---

**Story 1.4: Row-Level Security (RLS) Policies Implementation**

As a **security-conscious user**,
I want **my research data to be completely isolated from other users**,
So that **no unauthorized access to my research is possible**.

**Acceptance Criteria:**
1. Enable RLS on `users`, `research_sessions`, and `draft_files` tables
2. Implement policy: `users` table SELECT restricted to `auth.uid() = id`
3. Implement policy: `research_sessions` table SELECT restricted to `user_id = auth.uid()`
4. Implement policy: `research_sessions` table INSERT/UPDATE restricted to `user_id = auth.uid()`
5. Implement policy: `draft_files` table access restricted via join to `research_sessions` where user owns session
6. Test RLS policies: User A cannot query User B's sessions via SQL or API
7. Document RLS policies in `docs/security/rls-policies.md`

**Prerequisites:** Story 1.3 (database schema exists)

---

## Epic 2: Historical Research Access & Session Management

### Goal

Enable users to view, search, filter, and retrieve their historical research sessions. This epic transforms TK9 from an ephemeral single-session tool into a persistent research workspace where users can access all past work. The file detection mechanism ensures that research artifacts (JSON drafts) generated by the multi-agent system are automatically linked to user sessions and displayed in the UI.

This epic delivers immediate value to users by solving the core pain point: "I can't find my previous research."

### Story Breakdown

**Total Stories**: 5 stories
**Estimated Story Points**: 18 points
**Timeline**: 2 weeks

---

**Story 2.1: Research Session List View**

As a **registered user**,
I want **to see a list of all my historical research sessions**,
So that **I can browse and retrieve past research work**.

**Acceptance Criteria:**
1. Dashboard displays all user's research sessions in reverse chronological order (newest first)
2. Each session card shows: title, creation date (relative time format: "2 hours ago"), status badge (color-coded)
3. Sessions with status "completed" display green badge, "in_progress" blue badge, "failed" red badge
4. List view implements pagination: 50 sessions per page
5. "Load More" button fetches next page when user reaches bottom of list
6. Empty state displays friendly message: "No research sessions yet. Start your first research!" with CTA button
7. Loading state displays skeleton loaders while fetching sessions

**Prerequisites:** Epic 1 complete (auth + database)

---

**Story 2.2: Session Metadata and Final Report Access**

As a **user viewing my session list**,
I want **to see key metadata and access final reports**,
So that **I can quickly find the research I'm looking for**.

**Acceptance Criteria:**
1. Each session card displays "View Final Report" button
2. Clicking "View Final Report" opens full-screen modal with complete research report (Markdown rendered)
3. Report modal includes close button, print option, and scroll-to-top button
4. Session card shows word count of final report (e.g., "3,240 words")
5. Session card shows research duration if available (e.g., "Completed in 4m 32s")
6. For sessions with status "in_progress", display progress indicator (e.g., "Stage: Parallel Research")
7. For sessions with status "failed", display error message summary

**Prerequisites:** Story 2.1 (session list exists)

---

**Story 2.3: Search and Filter Functionality**

As a **user with many research sessions**,
I want **to search by title and filter by date range**,
So that **I can quickly find specific research without scrolling**.

**Acceptance Criteria:**
1. Search bar at top of dashboard with placeholder "Search research sessions..."
2. Search filters sessions in real-time (debounced 300ms) by case-insensitive substring match on title
3. Date range filter dropdown with presets: "Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom range"
4. Custom range opens date picker for start date and end date selection
5. Filters apply cumulatively: search + date range both active simultaneously
6. Active filters display as removable chips below search bar
7. "Clear Filters" button resets all filters and shows full session list
8. No results state displays: "No sessions found matching '[search term]'" with clear filters link

**Prerequisites:** Story 2.1, 2.2 (session list with metadata)

---

**Story 2.4: File Detection and Session Linking**

As a **user who has completed research**,
I want **the system to automatically detect generated draft files**,
So that **my research artifacts are linked to my session without manual action**.

**Acceptance Criteria:**
1. `FileManager` background service monitors `./outputs/{session_id}/` directories
2. When new file detected in `1_initial_research/`, `2_planning/`, `3_parallel_research/`, or `4_writing/`, create record in `draft_files` table
3. Record includes: session_id (from directory name), stage (from subdirectory), file_path (absolute), detected_at (timestamp)
4. File detection handles race conditions: retries 3 times with exponential backoff (1s, 2s, 4s) if file read fails
5. Corrupted or invalid JSON files are logged as errors but don't break detection process
6. File detection runs every 5 seconds for active sessions (status = in_progress)
7. Admin endpoint `/api/admin/reindex-files` triggers manual re-scan of all output directories

**Prerequisites:** Story 2.1 (sessions exist), Epic 1 (database schema with draft_files table)

---

**Story 2.5: WebSocket Real-Time Updates**

As a **user viewing my session list while research is running**,
I want **to see live updates when new files are detected**,
So that **I don't need to refresh the page to see completed research**.

**Acceptance Criteria:**
1. Dashboard establishes WebSocket connection on mount: `ws://localhost:12656/ws/sessions`
2. Server broadcasts message when file detected: `{"type": "file_detected", "session_id": "...", "stage": "...", "file_count": 3}`
3. Client updates UI in real-time: session card updates file count badge
4. When research completes (status changes to "completed"), client displays toast notification: "Research '[title]' completed!"
5. Toast notification includes "View Report" button that opens report modal
6. WebSocket reconnects automatically if connection drops (exponential backoff: 1s, 2s, 4s, 8s, 16s max)
7. Heartbeat ping/pong every 30 seconds to detect dead connections

**Prerequisites:** Story 2.4 (file detection working), Story 2.2 (final report access exists)

---

## Epic 3: Draft Exposure System & Progressive Disclosure UI

### Goal

Implement the collapsible accordion interface that enables progressive disclosure of research artifacts across 4 stages. This epic delivers the core differentiator of TK9: transparency into the research process. Users can expand research sessions to explore how conclusions evolved through Initial Research → Planning → Parallel Research → Writing stages, viewing the actual JSON drafts generated by each agent.

This epic transforms TK9 from a "black box" to a "glass box" research tool, building trust and enabling users to validate methodology.

### Story Breakdown

**Total Stories**: 5 stories
**Estimated Story Points**: 19 points
**Timeline**: 2-3 weeks

---

**Story 3.1: Session Card Accordion Component**

As a **user viewing my session list**,
I want **to expand session cards to see more details**,
So that **I can access research process information without leaving the list view**.

**Acceptance Criteria:**
1. Session card header is clickable to toggle expand/collapse
2. Collapsed state shows: title, date, status badge, "View Report" button (card height ~80px)
3. Expanded state adds: session summary (2-3 sentences), "Show Research Process" toggle, stage accordion (card height expands to fit content)
4. Expand/collapse animates smoothly (300ms ease-in-out transition)
5. Chevron icon rotates 180° on expand (pointing down → pointing up)
6. Only one session expanded at a time (accordion behavior: expanding new card collapses previous)
7. Session expansion state persists in URL hash: `#session-{id}` for deep linking

**Prerequisites:** Story 2.1, 2.2 (session list and metadata)

---

**Story 3.2: Stage Accordion with Icons and Status**

As a **user who expanded a research session**,
I want **to see the 4 research stages with completion status**,
So that **I can understand the research workflow and explore stages of interest**.

**Acceptance Criteria:**
1. "Show Research Process" toggle appears in expanded session card
2. Toggling reveals stage accordion with 4 stages: "1 - Initial Research", "2 - Planning", "3 - Parallel Research", "4 - Writing"
3. Each stage displays: icon (🔍, 📋, 🔬, ✍️), stage name, completion status (checkmark/spinner/X), file count badge
4. Stages collapse accordion behavior: expanding one stage auto-collapses others
5. Completed stages show green checkmark icon, in-progress stages show blue spinner, failed stages show red X
6. Stage timestamp displays in relative format: "Completed 3 hours ago"
7. Empty stages (no files detected) display: "No drafts generated for this stage yet"

**Prerequisites:** Story 3.1 (session card accordion), Story 2.4 (file detection)

---

**Story 3.3: Lazy Loading of Draft Content**

As a **user expanding a research stage**,
I want **draft content to load only when I request it**,
So that **the page loads quickly and doesn't fetch unnecessary data**.

**Acceptance Criteria:**
1. Stage expansion triggers API call: `GET /api/sessions/{session_id}/stages/{stage}/drafts`
2. API returns array of draft files with: file_name, file_path, size (KB), created_at
3. While loading, display skeleton loader: animated shimmer effect on 3 placeholder draft items
4. Once loaded, display list of draft files with clickable file names
5. Draft content itself loads on click (nested lazy loading): `GET /api/sessions/{session_id}/files/{file_id}`
6. Cache loaded draft content for 5 minutes to avoid re-fetching on collapse/expand
7. Error handling: if API fails, display "Failed to load drafts. Retry" button

**Prerequisites:** Story 3.2 (stage accordion exists)

---

**Story 3.4: JSON Draft Viewer with Syntax Highlighting**

As a **user viewing a draft file**,
I want **JSON content to be formatted and syntax-highlighted**,
So that **I can easily read and understand the structured data**.

**Acceptance Criteria:**
1. Clicking draft file name expands inline viewer below the file item
2. JSON content formatted with 2-space indentation for readability
3. Syntax highlighting: keys (blue), strings (green), numbers (orange), booleans (purple), null (gray)
4. Line numbers displayed in left gutter (gray, monospace font)
5. Horizontal scrolling enabled for long lines (important for mobile)
6. "Copy JSON" button copies raw content to clipboard with toast confirmation
7. "Collapse" button closes the draft viewer
8. Large files (>100KB) display warning: "Large file - may impact performance" with "Load Anyway" button

**Prerequisites:** Story 3.3 (draft content loading works)

---

**Story 3.5: Expand/Collapse Animations and Polish**

As a **user interacting with the accordion UI**,
I want **smooth animations and clear visual feedback**,
So that **the interface feels responsive and professional**.

**Acceptance Criteria:**
1. Session card expansion: height animates smoothly with ease-in-out curve (300ms)
2. Stage accordion expansion: content fades in while height expands (200ms)
3. Chevron/arrow icons rotate with CSS transform transition (150ms)
4. Hover states: session cards and stage headers show subtle background color change
5. Active state: expanded session card has blue left border (4px)
6. Focus states: keyboard navigation highlights focused element with blue outline
7. Loading states: skeleton loaders pulse with shimmer animation
8. Empty state illustrations: friendly iconography for "No drafts yet" states

**Prerequisites:** Story 3.1, 3.2, 3.3, 3.4 (all accordion functionality implemented)

---

## Epic 4: Performance Optimization & Mobile Polish

### Goal

Ensure the draft exposure system performs smoothly with large datasets (1000+ research sessions) and delivers excellent mobile experience on small screens and touch devices. This epic focuses on production readiness: implementing virtualized scrolling to handle scale, optimizing caching strategies, and adapting the accordion UI for mobile constraints.

This epic ensures TK9 remains fast and usable as users accumulate extensive research history over months/years of usage.

### Story Breakdown

**Total Stories**: 3 stories
**Estimated Story Points**: 8 points
**Timeline**: 1 week

---

**Story 4.1: Virtual Scrolling for Session List**

As a **power user with 500+ research sessions**,
I want **the session list to scroll smoothly without lag**,
So that **I can browse my extensive research history efficiently**.

**Acceptance Criteria:**
1. Integrate `vue-virtual-scroller` library for session list rendering
2. Only visible session cards (viewport + buffer) are rendered to DOM (typically 10-15 cards)
3. Scrolling maintains 60 FPS performance with 1000+ sessions (measured via Chrome DevTools)
4. Session card height estimated at 80px collapsed, dynamic height when expanded
5. Virtual scroller recalculates item heights when session cards expand/collapse
6. Scroll position persists on browser back/forward navigation
7. Performance monitoring: log warning if scroll FPS drops below 50 for >1 second

**Prerequisites:** Story 2.1 (session list exists), Story 3.1 (expandable cards)

---

**Story 4.2: Caching Strategy and Prefetching**

As a **user frequently accessing the same research sessions**,
I want **subsequent views to load instantly**,
So that **I don't waste time waiting for data I've already fetched**.

**Acceptance Criteria:**
1. Implement in-memory LRU cache (Least Recently Used eviction) for session metadata (max 200 sessions cached)
2. API responses include `Cache-Control: max-age=300` header (5 minute cache)
3. Draft content cached in IndexedDB for offline access (expires after 24 hours)
4. When user expands stage 1, prefetch stage 2 and 3 drafts in background
5. Stale-while-revalidate pattern: serve cached data immediately, fetch fresh data in background
6. Cache invalidation: clear cache when user initiates new research (session list refetch)
7. Cache stats displayed in developer console: hit rate, size, eviction count

**Prerequisites:** Story 2.1 (API endpoints exist), Story 3.3 (draft loading)

---

**Story 4.3: Mobile Responsive Accordion and Touch Optimization**

As a **mobile user on a 360px screen**,
I want **the accordion UI to adapt to small screens with touch-friendly interactions**,
So that **I can access my research history on the go without frustration**.

**Acceptance Criteria:**
1. Session cards stack vertically with 16px padding on mobile (vs 24px desktop)
2. Session card text wraps properly: title truncates to 2 lines with ellipsis, date displays below title
3. Stage accordion adjusts for mobile: stage name truncates if needed, icons remain visible
4. Touch targets meet minimum size: 44x44px for all tappable elements (WCAG guideline)
5. JSON viewer enables horizontal scroll for long lines (no word wrap)
6. Pinch-to-zoom enabled on JSON content for readability
7. Mobile navigation: "Back to Top" floating button appears after scrolling 2 screens
8. Responsive breakpoints: 360px (small mobile), 768px (tablet), 1024px (desktop)
9. Test on real devices: iPhone 12 (iOS Safari), Samsung Galaxy S21 (Chrome Mobile)

**Prerequisites:** Story 3.1-3.5 (full accordion UI implemented)

---

## Story Guidelines Reference

**Story Format:**

```
**Story [EPIC.N]: [Story Title]**

As a [user type],
I want [goal/desire],
So that [benefit/value].

**Acceptance Criteria:**
1. [Specific testable criterion]
2. [Another specific criterion]
3. [etc.]

**Prerequisites:** [Dependencies on previous stories, if any]
```

**Story Requirements:**

- **Vertical slices** - Complete, testable functionality delivery
- **Sequential ordering** - Logical progression within epic
- **No forward dependencies** - Only depend on previous work
- **AI-agent sized** - Completable in 2-4 hour focused session
- **Value-focused** - Integrate technical enablers into value-delivering stories

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.

## Summary Statistics

**Total Stories**: 16 stories across 4 epics
**Total Story Points**: 61 points (estimated)
**Estimated Timeline**: 4-6 weeks

**Epic Breakdown**:
- Epic 1 (Foundation): 4 stories, 16 points, 1-2 weeks
- Epic 2 (Historical Access): 5 stories, 18 points, 2 weeks
- Epic 3 (Draft UI): 5 stories, 19 points, 2-3 weeks
- Epic 4 (Performance): 3 stories, 8 points, 1 week

**Key Milestones**:
- Week 2: Authentication and database operational
- Week 4: Historical research access working
- Week 6: Progressive disclosure UI complete
- Week 6-7: Performance optimized, mobile polish, production-ready
