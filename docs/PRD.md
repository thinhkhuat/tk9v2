# TK9 Historical Research Access & Authentication - Product Requirements Document (PRD)

**Author:** Thinh
**Date:** 2025-10-31
**Project Level:** 3
**Target Scale:** 15-40 stories across 2-5 epics

---

## Goals and Background Context

### Goals

1. **Enable historical research access** - Users can retrieve, browse, and reference all past research sessions from any device
2. **Provide transparent research process visibility** - Users can explore progressive drafts across 4 research stages (Initial → Planning → Parallel → Writing)
3. **Minimize authentication friction** - Anonymous users get immediate access with seamless upgrade path to permanent accounts
4. **Drive user retention and engagement** - Achieve 60% 7-day retention and 40% anonymous-to-registered conversion rate
5. **Establish monetization foundation** - Authentication layer enables future freemium model and team collaboration features

### Background Context

TK9 is a production-ready multi-agent deep research MCP server that orchestrates 8 specialized AI agents to produce comprehensive research reports. Despite its sophisticated research capabilities, the system currently lacks state persistence and historical access, making it unsuitable for serious research workflows where users need to reference, compare, and build upon previous work.

The primary problem is **ephemeral sessions** - all research context is lost when the browser closes, forcing users to re-run identical queries (estimated 30-40% of queries are duplicates). Additionally, the multi-stage research workflow (1_initial_research → 2_planning → 3_parallel_research → 4_writing) generates valuable progressive drafts that are saved to the filesystem but completely inaccessible to users, creating a "black box" experience that undermines trust and prevents users from validating research methodology.

Technical research has validated that a **collapsible accordion UI pattern with virtualized scrolling** (scored 93/100 across UX, developer experience, security, and performance criteria) combined with **Supabase anonymous authentication** provides the optimal solution. This enhancement will transform TK9 from a single-session research tool into a comprehensive research workspace, enabling users to build knowledge over time while maintaining TK9's commitment to transparency and self-hosted infrastructure.

---

## Requirements

### Functional Requirements

**Authentication & User Management**

- **FR001**: System shall provide anonymous sign-in functionality that automatically creates a session without requiring user input
- **FR002**: System shall generate unique UUID-based session identifiers for anonymous users to enable session tracking
- **FR003**: System shall provide email-based registration with password authentication for users who want permanent accounts
- **FR004**: System shall support one-click upgrade from anonymous to registered account, preserving all research history
- **FR005**: System shall implement JWT-based session management with 7-day access tokens and 30-day refresh tokens
- **FR006**: System shall apply Row-Level Security (RLS) policies to ensure users can only access their own research data

**Historical Research Access**

- **FR007**: System shall display a list of all research sessions in reverse chronological order (newest first)
- **FR008**: For each research session, system shall display: session title, creation date, status (in_progress, completed, failed), and link to final report
- **FR009**: System shall provide search functionality to filter sessions by title (case-insensitive substring matching)
- **FR010**: System shall provide date range filtering to display sessions within a specified time period
- **FR011**: System shall implement pagination for session lists exceeding 50 items
- **FR012**: System shall load session metadata on initial page load and lazy-load additional details on user interaction

**Draft Exposure System**

- **FR013**: System shall implement a 3-level collapsible accordion interface for progressive disclosure:
  - Level 1: Research session card (collapsed by default)
  - Level 2: Stage accordion showing 4 research stages with icons and status
  - Level 3: Draft viewer displaying JSON content with syntax highlighting

- **FR014**: System shall display a "View Final Report" button on each session card that opens the complete research report
- **FR015**: System shall provide a "Show Research Process" toggle that reveals the stage accordion when expanded
- **FR016**: System shall lazy-load draft content only when user expands a stage (not on initial page load)
- **FR017**: System shall display stage metadata: stage name, icon, completion status, timestamp, file count
- **FR018**: System shall format JSON draft content with syntax highlighting, line numbers, and horizontal scrolling for readability

**File Detection & Management**

- **FR019**: System shall monitor the `./outputs/{session_id}/` directory structure for new research files
- **FR020**: System shall detect and catalog files in staged directories: `1_initial_research/`, `2_planning/`, `3_parallel_research/`, `4_writing/`
- **FR021**: System shall link detected files to the corresponding user session in the database
- **FR022**: System shall handle file detection race conditions (research completing while user views session)
- **FR023**: System shall provide WebSocket-based real-time updates when new files are detected for active user sessions

**Performance & Scalability**

- **FR024**: System shall implement virtual scrolling for session lists to efficiently render 1000+ sessions
- **FR025**: System shall cache frequently accessed session metadata in memory with LRU eviction policy
- **FR026**: System shall implement optimistic UI updates for instant feedback on user interactions (expand/collapse)
- **FR027**: System shall prefetch draft content for the next 2 stages when user expands a stage accordion

### Non-Functional Requirements

**Performance**

- **NFR001**: Session list page load time shall be < 2 seconds for lists containing up to 100 sessions (measured at 50th percentile)
- **NFR002**: Accordion expansion and draft loading shall complete in < 500ms (measured at 95th percentile)
- **NFR003**: Virtual scrolling shall maintain 60 FPS during scroll interactions with 1000+ session items
- **NFR004**: Mobile devices (mid-range Android/iOS) shall experience no performance degradation compared to desktop

**Security**

- **NFR005**: Authentication system shall implement rate limiting of 100 requests per minute per user to prevent brute force attacks
- **NFR006**: JWT tokens shall be securely stored using HTTP-only cookies (not localStorage) to mitigate XSS attacks
- **NFR007**: RLS policies shall be tested and verified to prevent unauthorized access to other users' research data

**Usability & Accessibility**

- **NFR008**: UI shall achieve WCAG 2.1 AA compliance including keyboard navigation, screen reader support, and color contrast requirements
- **NFR009**: Accordion expand/collapse interactions shall provide clear visual feedback (icons rotate, content animates smoothly)
- **NFR010**: Mobile responsive design shall adapt accordion layout for screens as small as 360px width

**Reliability**

- **NFR011**: File detection mechanism shall include retry logic (3 attempts with exponential backoff) to handle transient filesystem errors
- **NFR012**: System shall gracefully handle missing or corrupted draft files by displaying error message without breaking the UI

---

## User Journeys

### Journey 1: New Anonymous User Conducts First Research

1. **User lands on TK9 web dashboard** → automatically signed in anonymously (no action required)
2. **User initiates research query** → system creates session with UUID, research begins
3. **Research completes** → user sees notification with "View Final Report" button
4. **User clicks "View Final Report"** → opens comprehensive research document
5. **User notices "Show Research Process" toggle** → curiosity drives click
6. **Stage accordion expands** → user sees 4 stages with completion timestamps
7. **User expands "1_initial_research" stage** → JSON drafts load with syntax highlighting
8. **User explores progressive drafts** → gains trust by seeing methodology transparency
9. **User sees "Save My Research" prompt** → realizes value of persistent access
10. **User clicks "Upgrade to Permanent Account"** → email registration modal appears
11. **User enters email and password** → account created, all anonymous research transferred
12. **User receives confirmation** → "Your 1 research session has been saved to your account"

**Decision Points & Alternatives**:
- Step 5 Alternative: User closes tab → research lost (pain point that drives upgrade)
- Step 9 Alternative: User dismisses prompt → sees reminder after 3rd research session
- Step 11 Alternative: User abandons registration → remains anonymous, sees prompt on next visit

### Journey 2: Registered User Retrieves Historical Research

1. **User logs in to TK9** → dashboard displays all historical research sessions
2. **User sees 12 past research sessions** → list sorted by date (newest first)
3. **User searches for "climate change"** → list filters to 3 matching sessions
4. **User clicks on session from 2 weeks ago** → session card expands
5. **User compares findings** → opens 2 session cards side-by-side
6. **User identifies pattern** → "Both sessions mention same data source inconsistency"
7. **User expands stage accordion for both** → compares planning stage drafts
8. **User spots methodology difference** → one session had more comprehensive source coverage
9. **User initiates new research** → incorporates insights from comparison
10. **New research completes** → builds upon previous work, avoids duplicated effort

**Decision Points & Alternatives**:
- Step 3 Alternative: User filters by date range → "Show sessions from last 30 days"
- Step 5 Alternative: User only needs final report → clicks "View Final Report" without expanding
- Step 9 Alternative: User exports sessions → downloads JSON for external analysis (Phase 2 feature)

### Journey 3: Mobile User Accesses Research on the Go

1. **User opens TK9 on mobile device** (360px screen width)
2. **Accordion layout adapts** → touch-optimized expand/collapse interactions
3. **User taps session card** → expands smoothly with animation
4. **Stage accordion displays** → 4 stages vertically stacked
5. **User taps "2_planning" stage** → draft content loads
6. **JSON content displays** → horizontal scroll enabled for long lines
7. **User pinch-zooms** → syntax highlighting remains readable
8. **User navigates back** → session collapses smoothly
9. **User scrolls session list** → virtual scrolling maintains smooth 60 FPS

**Decision Points & Alternatives**:
- Step 5 Alternative: Draft takes >2s to load on slow network → loading spinner displays with "Loading draft..." message
- Step 6 Alternative: JSON too complex for mobile → user opens desktop version via "View on Desktop" link

---

## UX Design Principles

### Core UX Principles

1. **Progressive Disclosure** - Reveal information gradually as users demonstrate interest, preventing cognitive overload while enabling deep exploration for motivated users
2. **Transparency by Default** - Research methodology and process are always accessible, building trust through visibility into how conclusions were reached
3. **Zero-Friction Entry** - Anonymous access eliminates barriers to first-time use, with upgrade path appearing only after value is demonstrated
4. **Comparison-Optimized** - UI layout enables side-by-side comparison of multiple research sessions, supporting meta-analysis workflows

### Platform & Screens

**Target Platforms**:
- **Primary**: Modern web browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+ (responsive web, no native app)

**Core Screens**:
- **Research Dashboard** - List view of all historical research sessions (primary screen)
- **Session Detail View** - Expanded accordion showing session metadata, stages, and drafts
- **Final Report Viewer** - Full-screen view of completed research report
- **Authentication Modals** - Anonymous upgrade prompt, email registration, login

**Key Interaction Patterns**:
- **Accordion Expand/Collapse** - Click/tap session card or stage to toggle visibility
- **Lazy Loading** - Content loads on-demand when user expands sections
- **Virtual Scrolling** - Smooth infinite scroll for long session lists
- **Touch Gestures** (mobile) - Tap to expand, horizontal swipe on draft content

### Design Constraints

**Existing Design System**:
- **Element Plus** - Vue 3 UI component library used for accordion, buttons, icons
- **Color Scheme** - Inherit from existing TK9 web dashboard (dark/light mode support)
- **Typography** - Monospace font for JSON content, system fonts for UI text

**Technical UI Constraints**:
- **Browser Support** - No IE11 support (Vue 3 limitation)
- **Performance Budget** - 60 FPS during scroll, <500ms draft load time
- **Accessibility** - WCAG 2.1 AA compliance (keyboard nav, screen readers, contrast)

---

## User Interface Design Goals

### UI Goals by Priority

1. **Clarity Over Complexity** - Avoid overwhelming users with too much information at once; default to collapsed state and expand on user action
2. **Performance Perception** - Use skeleton loaders, optimistic updates, and smooth animations to make UI feel fast even when fetching data
3. **Scannable Session List** - Session cards display essential metadata (title, date, status) at a glance without requiring expansion
4. **Mobile-First Responsive** - Accordion adapts gracefully to small screens with touch-optimized interactions, no horizontal scrolling on session list
5. **Visual Hierarchy** - Clear distinction between session-level, stage-level, and draft-level information using typography, spacing, and icons

### High-Level UI Specifications

**Session Card Design**:
- **Collapsed State**: Title (h3), date (muted text), status badge (color-coded: blue=in_progress, green=completed, red=failed), "View Report" button
- **Expanded State**: Adds session summary, "Show Research Process" toggle, stage accordion
- **Visual Treatment**: Card with border, subtle shadow on hover, expand icon rotates 180° when opened

**Stage Accordion Design**:
- **Stage Icons**: 🔍 (Initial Research), 📋 (Planning), 🔬 (Parallel Research), ✍️ (Writing)
- **Status Indicators**: Checkmark for completed stages, spinner for in_progress, X for failed
- **Timestamp Display**: Relative time ("2 hours ago") with full timestamp on hover

**Draft Viewer Design**:
- **Syntax Highlighting**: JSON keys in blue, strings in green, numbers in orange, syntax in gray
- **Line Numbers**: Left gutter with gray line numbers for reference
- **Scrolling**: Vertical scroll for long content, horizontal scroll for wide lines (mobile)

---

## Epic List

This project will be delivered through **4 major epics** with an estimated **16-20 stories** total:

### Epic 1: Authentication Foundation & Database Setup
**Goal**: Establish authentication infrastructure and database schema for user and session management

**Estimated Stories**: 4-5 stories

**Key Deliverables**:
- Supabase anonymous sign-in integration
- Email registration and login flows
- JWT token management
- RLS policies for data isolation
- User and session database tables

---

### Epic 2: Historical Research Access & Session Management
**Goal**: Enable users to view, search, and filter their historical research sessions

**Estimated Stories**: 4-5 stories

**Key Deliverables**:
- Session list view with pagination
- Search and date filtering
- Session metadata display
- File detection and database linking
- WebSocket real-time updates

---

### Epic 3: Draft Exposure System & Progressive Disclosure UI
**Goal**: Implement collapsible accordion interface for exploring progressive research drafts

**Estimated Stories**: 5-6 stories

**Key Deliverables**:
- 3-level accordion component (session → stage → draft)
- Lazy loading of draft content
- JSON syntax highlighting and viewer
- Stage icons and status indicators
- Expand/collapse animations

---

### Epic 4: Performance Optimization & Mobile Polish
**Goal**: Ensure smooth performance with large datasets and excellent mobile experience

**Estimated Stories**: 3-4 stories

**Key Deliverables**:
- Virtual scrolling for session list
- Caching strategy for session metadata
- Mobile-responsive accordion layout
- Touch-optimized interactions
- Performance monitoring and optimization

---

> **Note:** Detailed epic breakdown with full story specifications is available in [epics.md](./epics.md)

---

## Out of Scope

**Excluded from MVP** (deferred to future phases):

### Collaboration Features
- Sharing research sessions with team members via links or invitations
- Collaborative annotations or comments on draft content
- Team workspaces with shared research repositories
- Role-based access control (viewer, editor, admin)

### Advanced Search & Discovery
- Full-text search across all draft content (currently only title search)
- Semantic search: "find research related to [topic]"
- Tag-based organization and filtering
- Smart recommendations: "similar research you've done"

### Export & Integration
- PDF export of final reports with embedded research lineage
- Bulk download of research sessions in various formats (JSON, Markdown, CSV)
- Integration with third-party tools (Notion, Obsidian, Roam Research)
- Zapier/Make workflow automation integration

### Comparison & Meta-Analysis
- Side-by-side diff view for comparing multiple research sessions
- Multi-session comparison dashboard with highlighting of differences
- AI-generated meta-analysis reports synthesizing findings across sessions

### Admin & Analytics
- Admin dashboard for user management and usage monitoring
- Detailed analytics on research patterns, engagement, and performance
- Billing integration for future freemium model
- A/B testing framework for feature experiments

### API & Extensibility
- REST API for programmatic access to research history
- Webhooks for research completion notifications
- Custom research agents marketplace
- Plugin system for third-party integrations

### Knowledge Management
- Visual knowledge graph showing relationships between research topics
- Research threads: connecting related sessions into storylines
- Cross-session citation and reference tracking
- Automated knowledge base generation from research history

**Rationale**: MVP focuses on proving core value proposition (historical access + transparent process) before investing in advanced features. Success criteria (60% retention, 40% conversion, 45% draft engagement) will validate whether to build Phase 2 features.
