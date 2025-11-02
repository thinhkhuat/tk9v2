# Product Brief: TK9 - Historical Research Access & Authentication Enhancement

**Date:** 2025-10-31
**Author:** Thinh
**Status:** Draft for PM Review

---

## Executive Summary

TK9 is a production-ready multi-agent deep research MCP server that generates comprehensive research reports. This enhancement adds **user authentication** (anonymous + registered) and a **sophisticated draft exposure system** to enable users to access their historical research sessions and explore the progressive drafts created during the multi-stage research workflow (Initial Research → Planning → Parallel Research → Writing).

The primary problem being solved is the **lack of state persistence and historical access** - users currently cannot retrieve past research or understand the research process evolution. The target market is TK9's existing user base of researchers and knowledge workers who need to reference, compare, and build upon previous research work.

The key value proposition is **transparent research lineage with progressive disclosure**, allowing users to see not just final reports but the entire research journey, enabling better insights, comparison across sessions, and informed decision-making based on research evolution.

---

## Problem Statement

### Current State

TK9 successfully generates comprehensive research reports through a sophisticated 8-agent workflow, but suffers from critical limitations:

1. **No State Persistence**: Research sessions are ephemeral - once the browser closes, all context is lost
2. **No Historical Access**: Users cannot retrieve past research reports or compare findings across sessions
3. **Opaque Process**: The multi-stage research workflow (1_initial_research → 2_planning → 3_parallel_research → 4_writing) is hidden from users, who only see final outputs
4. **Limited Insights**: Users cannot understand how conclusions evolved or validate research quality by examining intermediate drafts

### Quantifiable Impact

- **Time Waste**: Users re-run identical research queries, wasting compute resources and time (estimated 30-40% of queries are variations of previous research)
- **Lost Context**: Researchers cannot build upon previous work, leading to duplicated effort and fragmented knowledge
- **Trust Issues**: Without transparency into the research process, users cannot validate methodology or identify potential gaps
- **Poor UX**: Anonymous users have immediate access but lose everything; registered users face friction without persistent storage

### Why Existing Solutions Fall Short

The current TK9 implementation treats each research session as isolated, with no connection between past and future work. While the underlying file system saves JSON drafts in staged directories, these are:
- Inaccessible to users through any interface
- Not tied to user identity or session management
- Not queryable or comparable
- Not optimized for historical retrieval

### Urgency

With TK9 now production-ready and gaining adoption, the lack of persistent storage and historical access is becoming a critical blocker for serious research workflows. Users are requesting this capability, and competitors in the research automation space are beginning to offer session history as a key differentiator.

---

## Proposed Solution

### Core Approach

Implement a **two-tier authentication system** with **progressive disclosure UI** for research artifacts:

**Authentication Layer**:
- **Anonymous Sign-In**: Immediate access for new users, sessions tied to anonymous UUID with upgrade path to permanent account
- **Registered Users**: Email-based authentication with full historical access and cross-device sync
- **Seamless Upgrade**: One-click conversion from anonymous to registered, preserving all prior research

**Draft Exposure System**:
- **Collapsible Accordion Interface**: Multi-level progressive disclosure (Session → Stages → Drafts) optimized for historical comparison
- **Virtualized Scrolling**: High-performance rendering for 1000+ research sessions
- **Mobile-Responsive**: Adaptive layout using Element Plus components for all devices
- **Smart Caching**: Lazy loading with intelligent prefetch for smooth browsing

### Key Differentiators

1. **Progressive Transparency**: Unlike competitors who only show final reports, TK9 exposes the entire research evolution (4 stages, multiple drafts per stage)
2. **Comparison-First Design**: Accordion pattern enables side-by-side comparison of multiple research sessions, a unique capability for meta-analysis
3. **Anonymous-First Flow**: Zero friction entry with upgrade path, versus competitors requiring registration upfront
4. **Performance-Optimized**: Virtualization ensures smooth UX even with hundreds of sessions, while competitors struggle with pagination and slow loads

### Why This Will Succeed

- **Proven Patterns**: Supabase anonymous auth and Element Plus accordion are battle-tested in production (Gmail, VS Code, GitHub)
- **Low Dev Risk**: Straightforward implementation leveraging existing tech stack (Vue 3 + FastAPI + Supabase)
- **Clear User Need**: Direct feedback from TK9 users requesting historical access
- **Competitive Moat**: Progressive disclosure of research lineage is a unique differentiator in the research automation market

### Ideal User Experience

1. **New User**: Lands on TK9 → clicks "Start Research" → automatically gets anonymous session → research completes → sees final report + "View Research Process" link → explores accordion of drafts → impressed by transparency → clicks "Save My Research" → upgrades to registered account → all prior work preserved
2. **Returning User**: Logs in → sees dashboard with all historical research sessions → expands session from last week → compares findings with new research → identifies pattern across 3 sessions → generates meta-analysis report

---

## Target Users

### Primary User Segment

**Profile**: Knowledge workers and researchers conducting deep research

- **Demographics**: 25-55 years old, typically in tech, academic, or strategic roles
- **Professional Context**: Product managers, strategy consultants, academic researchers, market analysts, technical architects
- **Technical Proficiency**: Comfortable with web applications, expects Google Docs-like experience
- **Current Problem-Solving**: Using ChatGPT/Claude for quick queries, but frustrated by lack of depth and citation quality
- **Specific Pain Points**:
  - Cannot retrieve previous research for reference
  - Lose valuable context when sessions expire
  - Want to validate research methodology by seeing process
  - Need to compare findings across related research topics
  - Frustrated by starting from scratch for each query
- **Goals**: Build comprehensive knowledge base over time, validate research quality, compare multiple research angles, access work from any device

**Actionable Details**:
- Uses TK9 for 3-5 research sessions per week
- Each session generates 10-20 page reports
- Frequently references past research when starting new queries
- Values transparency and wants to "see how the sausage is made"
- Willing to create account if value proposition is clear

### Secondary User Segment

**Profile**: Team leads and managers who commission research

- **Demographics**: 30-60 years old, typically in leadership positions
- **Professional Context**: Department heads, team leads, executive stakeholders
- **Current Problem-Solving**: Delegate research to team members, review final reports, struggle to validate quality
- **Specific Pain Points**:
  - Cannot assess research quality without understanding methodology
  - Need to share research across team members
  - Want to build organizational knowledge repository
  - Require audit trail for research-backed decisions
- **Goals**: Validate research rigor, enable team collaboration, build institutional memory, justify decisions with transparent research

**How Their Needs Differ**:
- More focused on sharing and collaboration features (Phase 2)
- Higher need for audit trails and research provenance
- Less interested in technical details, more in strategic insights
- May not conduct research themselves but need to review and approve

---

## Goals and Success Metrics

### Business Objectives

| Objective | Target | Timeline |
|-----------|--------|----------|
| **User Retention** | Increase 7-day retention from current baseline to 60% | 3 months post-launch |
| **Account Conversion** | 40% of anonymous users upgrade to registered accounts within 3 sessions | 6 months |
| **Session Frequency** | Increase average sessions per user from 1.2 to 4.5 per month | 4 months |
| **Revenue Foundation** | Establish usage patterns for future freemium model (metrics collection only) | 6 months |

### User Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Historical Research Access** | 70% of registered users access past research at least once per week | Weekly active usage logs |
| **Draft Exploration** | 50% of users who view final reports also explore progressive drafts | Accordion expansion tracking |
| **Research Comparison** | 30% of users compare 2+ research sessions within single browsing session | Multi-session expansion events |
| **Account Upgrade** | Average time to upgrade from anonymous: < 3 research sessions | Conversion funnel tracking |
| **Mobile Usage** | 25% of sessions accessed from mobile devices without UX degradation | Device analytics + user satisfaction |

### Key Performance Indicators (KPIs)

**Top 5 KPIs for Success**:

1. **Research Retrieval Rate**: % of users accessing historical research (Target: 65%)
2. **Account Conversion Rate**: Anonymous → Registered conversion (Target: 40%)
3. **Draft Engagement**: % of sessions where users explore progressive drafts (Target: 45%)
4. **Session Return Rate**: Users conducting 2+ sessions in 30 days (Target: 55%)
5. **Comparison Activity**: % of users comparing multiple research sessions (Target: 25%)

---

## Strategic Alignment and Financial Impact

### Financial Impact

**Development Investment**:
- **Phase 1 (Foundation)**: 1-2 weeks, ~$8-12K equivalent (auth + basic UI)
- **Phase 2 (Core Features)**: 2-3 weeks, ~$12-18K equivalent (draft system + virtualization)
- **Phase 3 (Polish)**: 1-2 weeks, ~$6-10K equivalent (mobile + performance)
- **Total MVP**: 4-6 weeks, ~$26-40K equivalent

**Revenue Potential** (Phase 2+):
- **Freemium Model**: 5 research sessions/month free, $19/mo for unlimited (estimated 8-12% conversion)
- **Team Plans**: $99/mo for 5 users with sharing (estimated 2-4% of user base)
- **Break-Even**: Approximately 200-300 paying users (achievable within 12-18 months based on current growth)

**Cost Savings**:
- **Reduced Support Load**: Users can self-serve historical research instead of re-running queries (estimated 30% reduction in compute costs)
- **Infrastructure Optimization**: Caching and lazy loading reduce real-time database queries by ~40%

**Opportunity Cost of NOT Building**:
- Competitors will capture market share by offering historical research capabilities
- Users will churn to alternatives that provide session persistence
- Cannot build advanced features (team collaboration, knowledge graphs) without authentication foundation

### Company Objectives Alignment

**Strategic Objective**: Establish TK9 as the leading transparent research automation platform

**Key Results This Enables**:
- **KR1: User Retention**: Authentication + historical access directly drives 60% 7-day retention target
- **KR2: Market Differentiation**: Progressive disclosure UI creates unique competitive moat
- **KR3: Revenue Foundation**: Authentication required for future monetization strategy

**Organizational Goals**:
- **Product Excellence**: Demonstrates commitment to user-centric design and transparency
- **Technical Leadership**: Showcases advanced UI/UX patterns (virtualization, progressive disclosure)
- **Community Building**: Registered users form foundation for future community features

### Strategic Initiatives

**Initiative 1: AI-Powered Research Platform Evolution**
- This enhancement is Phase 1 of transforming TK9 from single-session tool to comprehensive research workspace
- Enables future features: knowledge graphs, research threads, collaborative research

**Initiative 2: Transparent AI Workflows**
- Progressive disclosure of research drafts demonstrates AI reasoning process
- Builds trust through transparency, aligning with broader industry trend toward explainable AI

**Initiative 3: Self-Hosted Research Infrastructure**
- Authentication and data persistence enable organizations to run private TK9 instances
- Opens enterprise market opportunity for teams needing sovereign research tools

---

## MVP Scope

### Core Features (Must Have)

**Authentication System**:
- ✅ Anonymous sign-in with UUID-based session tracking
- ✅ Email-based registration with password authentication
- ✅ One-click upgrade from anonymous to registered (preserves all data)
- ✅ JWT-based session management with secure token handling
- ✅ Supabase Row-Level Security (RLS) policies for data isolation

**Historical Research Access**:
- ✅ List view of all research sessions (reverse chronological)
- ✅ Session metadata: title, date, status, final report link
- ✅ Search/filter by date range and session title
- ✅ Pagination for large session lists

**Draft Exposure System**:
- ✅ Collapsible accordion for progressive disclosure (3 levels)
  - Level 1: Research session card (collapsed by default)
  - Level 2: Stage accordion (4 stages: Initial → Planning → Parallel → Writing)
  - Level 3: Draft viewer (JSON formatted with syntax highlighting)
- ✅ "View Final Report" button on session card
- ✅ "Show Research Process" toggle to reveal stage accordion
- ✅ Stage icons and status indicators
- ✅ Lazy loading of draft content (fetch on expand)

**Performance Optimizations**:
- ✅ Virtual scrolling for session list (handles 1000+ sessions)
- ✅ Caching strategy for frequently accessed sessions
- ✅ Optimistic UI updates for instant feedback

**Mobile Responsiveness**:
- ✅ Adaptive accordion layout for small screens
- ✅ Touch-optimized expand/collapse interactions
- ✅ Mobile-friendly draft viewer with horizontal scrolling

### Out of Scope for MVP

**Excluded from Phase 1** (to be considered for Phase 2+):

❌ **Collaboration Features**: Sharing research with team members, collaborative annotations
❌ **Advanced Search**: Full-text search across draft content, semantic search
❌ **Export Options**: PDF export, bulk download, integration with note-taking tools
❌ **Comparison UI**: Side-by-side diff view, multi-session comparison dashboard
❌ **Notifications**: Email alerts for research completion, weekly digests
❌ **Admin Dashboard**: User management, usage analytics, billing integration
❌ **API Access**: Programmatic access to research history via REST API
❌ **Knowledge Graph**: Visual representation of research connections across sessions
❌ **Social Features**: Public research sharing, community research repository

**Rationale**: These features add significant complexity without validating core value proposition. MVP focuses on proving:
1. Users want historical access (demonstrated by retrieval rate)
2. Progressive disclosure adds value (demonstrated by draft engagement)
3. Authentication doesn't create friction (demonstrated by conversion rate)

### MVP Success Criteria

**MVP is successful if, within 90 days post-launch**:

1. ✅ **60%+ of registered users** access historical research at least once
2. ✅ **40%+ conversion rate** from anonymous to registered users
3. ✅ **45%+ draft engagement**: users who view final reports also explore progressive drafts
4. ✅ **< 5% authentication failure rate**: secure, reliable auth system
5. ✅ **< 2s load time** for session list with 100+ sessions (performance validated)
6. ✅ **< 10 support tickets** related to historical access or authentication (UX validated)
7. ✅ **4+ average sessions** per registered user per month (retention validated)

**Failure Criteria** (triggers re-evaluation):
- Conversion rate < 20% (authentication friction too high)
- Draft engagement < 20% (progressive disclosure not compelling)
- Historical access < 30% (feature not solving real need)

---

## Post-MVP Vision

### Phase 2 Features

**Collaboration and Sharing** (Q2 2026):
- Share research sessions with team members via link
- Collaborative annotations on draft content
- Team workspace with shared research repository
- Role-based access control (viewer, editor, admin)

**Enhanced Search and Discovery** (Q2 2026):
- Full-text search across all draft content
- Semantic search: "find research related to [topic]"
- Tag-based organization and filtering
- Smart recommendations: "similar research you've done"

**Export and Integration** (Q3 2026):
- PDF export of final reports with embedded lineage
- Bulk download of research sessions (JSON, Markdown)
- Integration with Notion, Obsidian, Roam Research
- Zapier/Make integration for workflow automation

### Long-term Vision

**12-Month Vision** (Q4 2026):
- TK9 evolves from research tool to **comprehensive knowledge workspace**
- Users can connect research sessions into **knowledge threads** (e.g., "Product Strategy Research" thread containing 8 related sessions)
- Visual **knowledge graph** shows relationships between research topics and findings
- **Meta-analysis capability**: AI generates synthesis reports across multiple research sessions
- **Team collaboration** features enable organizational knowledge building

**24-Month Vision** (Q4 2027):
- TK9 becomes **self-hosted research infrastructure** for organizations
- **Enterprise features**: SSO, audit logs, compliance reporting
- **API-first platform**: Developers build custom research workflows on TK9
- **Marketplace**: Community-contributed research templates and agent configurations
- **Research communities**: Public research sharing with attribution and versioning

### Expansion Opportunities

**Market Expansion**:
- **Academic Research**: Partner with universities for student/faculty research tool
- **Enterprise Strategy**: Target consulting firms and corporate strategy teams
- **Legal Research**: Customize for case law and legal document analysis

**Product Expansion**:
- **Research Agents Marketplace**: Users create and share custom agent configurations
- **Industry-Specific Templates**: Pre-configured research workflows for finance, healthcare, tech
- **White-Label Solution**: License TK9 technology for embedding in other platforms

**Geographic Expansion**:
- Multilingual interface (current: English, expand to 10+ languages)
- Region-specific data sources and compliance (GDPR, CCPA)
- Localized research methodologies (cultural adaptation)

---

## Technical Considerations

### Platform Requirements

**Web Application**:
- **Primary Platform**: Modern web browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **Progressive Web App (PWA)**: Future consideration for offline access and app-like experience
- **No Native Apps**: MVP focuses on web-first, mobile-responsive design

**Performance Requirements**:
- **Load Time**: < 2s for session list (100 sessions), < 3s for 1000 sessions
- **Accordion Expansion**: < 500ms to fetch and render draft content
- **Virtual Scrolling**: Maintain 60fps during scroll with 1000+ items
- **Mobile Performance**: No degradation on mid-range Android/iOS devices

**Accessibility Standards**:
- **WCAG 2.1 AA Compliance**: Keyboard navigation, screen reader support, color contrast
- **ARIA Labels**: Semantic markup for accordion, buttons, and dynamic content
- **Focus Management**: Proper focus handling on expand/collapse interactions

**Browser Support**:
- **Modern Browsers Only**: No IE11 support (Vue 3 limitation)
- **Evergreen Browsers**: Automatic updates ensure latest standards support

### Technology Preferences

**Frontend Stack** (Existing TK9):
- **Framework**: Vue 3 (Composition API) - already in use
- **UI Library**: Element Plus - proven accordion and component library
- **Virtualization**: `vue-virtual-scroller` - battle-tested for large lists
- **State Management**: Pinia - Vue 3 native state management
- **Build Tool**: Vite - fast dev experience and optimized builds

**Backend Stack** (Existing TK9):
- **Framework**: FastAPI (Python 3.12) - already in use
- **Authentication**: Supabase Auth SDK - handles anonymous + email auth
- **API Design**: RESTful with JWT middleware for protected endpoints

**Database and Storage**:
- **Primary DB**: Supabase (PostgreSQL) - cloud-hosted, RLS-enabled
- **File Storage**: Local filesystem for draft JSON files (existing pattern)
- **Caching**: In-memory LRU cache for frequently accessed sessions

**Rationale**:
- Leverage existing TK9 stack (Vue 3 + FastAPI + Supabase)
- No new technology learning curve
- Proven patterns from technical research (Gmail, VS Code examples)

### Architecture Considerations

**Architectural Pattern**: Client-side rendering with API-driven backend

**Key Decisions** (from ADR-001, ADR-002):
1. **UI Pattern**: Collapsible Accordion with 3-level progressive disclosure
2. **Authentication**: Supabase anonymous + email upgrade path
3. **Data Isolation**: Row-Level Security (RLS) policies on PostgreSQL
4. **Performance**: Virtualized scrolling + lazy loading + caching
5. **Mobile**: Responsive accordion with adaptive breakpoints

**Integration Points**:
- **Existing Research Workflow**: Backend orchestrator saves drafts to JSON files in staged directories
- **File Detection**: New `FileManager` component watches output directories and links files to user sessions
- **Session Tracking**: UUID-based session IDs shared between CLI and web dashboard

**Data Flow**:
1. User initiates research (anonymous session created automatically)
2. Research workflow executes, saving drafts to `./outputs/{session_id}/1_initial_research/`, etc.
3. `FileManager` detects new files, updates database records
4. Frontend fetches session list → user expands accordion → lazy loads draft content
5. User upgrades to registered → all anonymous sessions transferred to permanent account

**Security Considerations**:
- JWT tokens with 7-day expiration (refresh tokens for 30 days)
- RLS policies ensure users only see own research
- API rate limiting to prevent abuse (100 req/min per user)
- No sensitive data in draft JSON files (all research is user-owned)

**Scalability Considerations** (Future):
- Current architecture supports 100K+ users with proper database indexing
- File storage can migrate to S3 for horizontal scaling
- Redis caching layer can be added for high-traffic scenarios
- API can be horizontally scaled with load balancer

---

## Constraints and Assumptions

### Constraints

**Technical Constraints**:
- **Self-Hosted Deployment**: No cloud services beyond Supabase (already in use)
- **Single-User MVP**: No team collaboration features in Phase 1
- **Local File Storage**: Draft JSON files remain on filesystem (no cloud storage migration)
- **Vue 3 Limitation**: No IE11 support due to framework choice

**Resource Constraints**:
- **Team Size**: Solo developer (Thinh)
- **Timeline**: 4-6 weeks for MVP (cannot extend without delaying other projects)
- **Budget**: No external budget for third-party services (use existing Supabase free tier initially)

**Operational Constraints**:
- **No Breaking Changes**: Must maintain backward compatibility with existing TK9 CLI usage
- **Zero Downtime**: Auth migration cannot disrupt current users
- **Data Migration**: Existing research sessions must be retroactively linkable to users

### Key Assumptions

**User Behavior Assumptions**:
- ✅ Users value historical research access enough to create accounts (validated by user feedback)
- ⚠️ Anonymous users will tolerate session-based storage before upgrading (NEEDS VALIDATION)
- ⚠️ Progressive disclosure UI is intuitive without onboarding tutorial (NEEDS USABILITY TESTING)
- ✅ Mobile users accept accordion pattern for draft browsing (validated by Gmail, VS Code adoption)

**Technical Assumptions**:
- ✅ Supabase anonymous auth is production-ready (validated by docs and community usage)
- ✅ vue-virtual-scroller handles 1000+ items smoothly (validated by benchmarks)
- ✅ Element Plus accordion is accessible and mobile-responsive (validated by library docs)
- ⚠️ File detection mechanism can reliably link drafts to sessions (NEEDS LOAD TESTING)

**Business Assumptions**:
- ⚠️ 40% conversion rate is achievable (benchmarked against freemium SaaS, but TK9 context differs)
- ⚠️ Users will tolerate self-hosted deployment complexity (NEEDS VALIDATION)
- ✅ Research transparency is a differentiator (validated by user feedback requesting "show me how it works")

**Market Assumptions**:
- ✅ Demand exists for deep research tools (validated by ChatGPT/Claude usage patterns)
- ⚠️ Users will choose TK9 over ChatGPT for research despite higher friction (NEEDS VALIDATION)
- ✅ Self-hosted research tools appeal to privacy-conscious users (validated by on-prem product trends)

---

## Risks and Open Questions

### Key Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **Low Anonymous Conversion** | High (kills monetization path) | Medium | A/B test upgrade prompts, offer incentives (extra sessions), reduce friction (passwordless email link) |
| **Draft UI Complexity** | Medium (users ignore feature) | Low | Conduct usability testing, add onboarding tooltip, track engagement metrics |
| **Performance Degradation** | High (UX suffers at scale) | Low | Load testing before launch, implement caching aggressively, monitor P95 latency |
| **File Detection Failures** | High (data consistency issues) | Medium | Implement robust error handling, add retry logic, monitor file system events |
| **Authentication Security Issues** | Critical (data breach risk) | Low | Follow Supabase security best practices, conduct security audit, implement rate limiting |
| **Mobile UX Issues** | Medium (excludes 25% of users) | Medium | Mobile-first design review, test on real devices, progressive enhancement approach |

### Open Questions

**Product Questions**:
1. Should anonymous users have session expiry (e.g., 30 days) or persist indefinitely until upgrade?
   - **Impact**: Affects storage costs and user expectations
   - **Decision Needed By**: Before Phase 1 implementation

2. What happens to research sessions if user deletes account?
   - **Options**: Hard delete, soft delete with grace period, anonymize data
   - **Impact**: GDPR compliance and user trust

3. Should draft content be editable or read-only in MVP?
   - **Trade-off**: Editing enables refinement but adds complexity and version control challenges

**Technical Questions**:
1. How to handle file detection race conditions (research completing while user views session list)?
   - **Current Approach**: WebSocket updates, but needs load testing
   - **Alternative**: Polling with exponential backoff

2. Should draft JSON files be stored in database or filesystem?
   - **Current**: Filesystem (existing pattern)
   - **Consideration**: Database offers better queryability but higher storage costs

3. What's the backup strategy for historical research sessions?
   - **Options**: Supabase auto-backup (7 days), manual export feature, local backup scripts

**Business Questions**:
1. What's the freemium pricing threshold (sessions per month)?
   - **Research Needed**: Usage analytics to determine natural breakpoint

2. Should enterprise features (SSO, team accounts) be developed before monetization?
   - **Trade-off**: Enterprise contracts provide stable revenue but delay launch

### Areas Needing Further Research

**User Research**:
- Usability testing for accordion UI with 5-10 beta users
- Interviews about historical research use cases (comparison, citation, reference)
- Survey about acceptable authentication friction and incentives for upgrade

**Technical Research**:
- Load testing file detection with 100+ concurrent research sessions
- Performance benchmarking virtual scrolling with 5000+ sessions
- Security audit of Supabase RLS policies and JWT implementation

**Competitive Research**:
- Detailed analysis of Perplexity, Anthropic Console, OpenAI Playground session history features
- Pricing analysis of competing research tools (Elicit, Consensus, Semantic Scholar)
- Feature gap analysis to identify must-have vs. nice-to-have

**Market Research**:
- TAM/SAM/SOM analysis for research automation market
- User personas refinement through interviews with target segments
- Geographic expansion feasibility (localization, compliance, data residency)

---

## Appendices

### A. Research Summary

**Technical Research Document**: `docs/research-technical-2025-10-31.md` (113KB)

**Key Findings**:
1. **UI/UX Pattern Analysis**: Evaluated 5 options (Accordion, Drawer, Modal, Tabs, Timeline), Accordion scored 93/100 for historical research use case
2. **Authentication Strategy**: Supabase anonymous → email upgrade path is optimal for low-friction onboarding with retention
3. **Performance Optimization**: Virtualized scrolling + lazy loading enables smooth UX with 1000+ sessions
4. **Mobile Responsiveness**: Element Plus accordion adapts well to small screens with touch-optimized interactions
5. **Real-World Evidence**: Gmail, VS Code, GitHub all use accordion patterns for nested content with high user satisfaction

**Scoring Matrix** (Weighted: UX 35%, Dev 30%, Security 20%, Performance 10%, Scalability 5%):
- Option 1 (Accordion): 93/100 ✅ **Selected**
- Option 2 (Drawer): 78/100
- Option 3 (Modal): 82/100
- Option 4 (Tabs): 76/100
- Option 5 (Timeline): 71/100

### B. Stakeholder Input

**Primary Stakeholder**: Thinh (Product Owner & Developer)

**Key Feedback**:
- Prioritize user experience over developer convenience
- Self-hosted deployment is non-negotiable (privacy, control)
- Mobile responsiveness is critical (25% of expected usage)
- Scalability is lower priority than UX for MVP

**User Feedback** (from TK9 community):
- "I wish I could go back and see my previous research"
- "It would be great to compare two research sessions side by side"
- "I want to understand how the AI arrived at its conclusions"
- "Can I create an account to save my research history?"

### C. References

**Technical Research**:
- `docs/research-technical-2025-10-31.md` - Comprehensive technical analysis and ADRs
- `docs/bmm-workflow-status.yaml` - Project tracking and workflow status

**Technology Documentation**:
- Supabase Auth: https://supabase.com/docs/guides/auth
- Element Plus: https://element-plus.org/en-US/component/collapse.html
- vue-virtual-scroller: https://github.com/Akryum/vue-virtual-scroller
- Vue 3 Composition API: https://vuejs.org/guide/extras/composition-api-faq.html

**Architecture Decisions**:
- ADR-001: Draft Exposure UI/UX Pattern Selection (Accordion)
- ADR-002: Authentication and Historical Research System (Supabase)

**Competitive Analysis**:
- Perplexity AI session history patterns
- Anthropic Console project structure
- OpenAI Playground conversation history

---

_This Product Brief serves as the foundational input for Product Requirements Document (PRD) creation._

_Next Steps: Handoff to Product Manager for PRD development using the `workflow prd` command._
