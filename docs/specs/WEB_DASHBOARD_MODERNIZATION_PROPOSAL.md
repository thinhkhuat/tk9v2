# Web Dashboard Modernization Proposal

**Project:** TK9 Deep Research MCP Web Dashboard
**Date:** October 31, 2025
**Status:** Proposal - Awaiting Approval
**Author:** Claude Code + Gemini Consultation

---

## Executive Summary

This proposal outlines a comprehensive modernization strategy for the TK9 Deep Research MCP web dashboard. After extensive analysis and consultation with Gemini AI, we recommend a **Full Next.js Migration** to maximize developer productivity, UI/UX quality, and long-term maintainability while leveraging existing team expertise.

### Key Decision: Full Next.js Migration

**Chosen Approach:** Migrate from vanilla JS/Jinja2 templates to a standalone Next.js 14+ application with TypeScript, shadcn/ui, and modern best practices.

**Why Not Progressive Enhancement?** While a Lit/Vite progressive approach would minimize disruption, the team's existing Next.js expertise and the availability of resources make a full migration the most pragmatic choice for long-term success.

---

## Current Architecture Analysis

### Frontend Stack (Current State)

**Technology:**
- Vanilla JavaScript (ES6+) with class-based architecture
- Jinja2 templates for server-side rendering
- Custom CSS with gradients and responsive design
- Manual DOM manipulation
- WebSocket client with auto-reconnect logic
- No build step, no bundling

**File Structure:**
```
web_dashboard/
├── main.py (FastAPI server)
├── models.py (Pydantic models)
├── cli_executor.py
├── file_manager.py
├── websocket_handler.py
├── templates/
│   └── index.html (Jinja2 template)
└── static/
    ├── css/
    │   └── dashboard.css (~865 lines)
    └── js/
        ├── dashboard.js (~800 lines)
        ├── websocket-client.js (~220 lines)
        └── enhanced-downloads.js
```

### Current Architecture Strengths

1. **Simplicity:** No build step, minimal dependencies
2. **Lightweight:** Fast initial load times
3. **Monolithic Deployment:** Single FastAPI service serves everything
4. **No CORS Issues:** Same-origin requests
5. **Production Ready:** Currently working in production

### Current Architecture Weaknesses

1. **No Type Safety:** JavaScript lacks compile-time type checking
2. **Manual DOM Manipulation:** Error-prone, difficult to maintain
3. **Scattered State Management:** State spread across class properties
4. **Limited Component Reusability:** Difficult to extract reusable UI patterns
5. **Testing Challenges:** Hard to unit test without framework support
6. **Code Organization:** Single 800-line `dashboard.js` file (God object)
7. **UI/UX Limitations:** Building rich components is time-consuming
8. **Scalability Concerns:** Adding complex features becomes increasingly difficult

---

## Detailed Comparison: Progressive vs. Full Migration

| Criterion | Lit/Preact (Progressive) | Next.js (Full Migration) | Winner |
|-----------|-------------------------|--------------------------|--------|
| **SSR/SSG Needs** | Minimal - Jinja2 provides HTML shell | World-class SSR/SSG | Tie (overkill but doesn't hurt) |
| **API Integration** | Simple - Same origin, no CORS | Complex - Separate service, CORS required | Lit/Preact |
| **WebSocket Handling** | Straightforward - Refactor existing logic | Straightforward - React hooks | Tie |
| **Deployment Complexity** | Low - Single service | High - Two services, reverse proxy | Lit/Preact |
| **Development Experience** | Good - Vite is fast | Exceptional - Team knows it | **Next.js** |
| **Component Ecosystem** | Limited - Build from scratch | Massive - React + shadcn/ui | **Next.js** |
| **Type Safety** | TypeScript supported | TypeScript first-class | Tie |
| **Testing** | Vitest unit tests | Vitest + React Testing Library | Tie |
| **Team Expertise** | Learning curve required | Already proficient | **Next.js** |
| **UI/UX Quality** | Custom CSS, manual components | shadcn/ui out of the box | **Next.js** |
| **Long-term Scalability** | Good for simple apps | Excellent for complex apps | **Next.js** |
| **Time to Market** | Moderate - Gradual refactor | Fast - Leverages existing skills | **Next.js** |

### Verdict: Full Next.js Migration

**Rationale:** The team's existing Next.js expertise, combined with access to shadcn/ui's component library, dramatically accelerates development velocity and ensures a higher-quality UI with less effort. The operational overhead of running two services is justified by these gains.

---

## Proposed Architecture: Next.js + FastAPI

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Browser                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Next.js Application                       │  │
│  │  (React Components + shadcn/ui + TypeScript)        │  │
│  │                                                      │  │
│  │  - Research Form                                    │  │
│  │  - Session Browser                                  │  │
│  │  - Real-time Log Viewer (WebSocket)                │  │
│  │  - File Manager with Preview                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│              HTTP Requests / WebSocket                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Reverse Proxy (Nginx/Caddy)                    │
│                                                             │
│  Routes:                                                    │
│  - /api/*     → FastAPI Backend (port 12656)              │
│  - /ws/*      → FastAPI WebSocket (port 12656)            │
│  - /*         → Next.js Frontend (port 3000)              │
└─────────────────────────────────────────────────────────────┘
                    ↓                    ↓
       ┌─────────────────────┐  ┌─────────────────────┐
       │  FastAPI Backend    │  │  Next.js Server     │
       │  (Python 3.12)      │  │  (Node.js 18+)      │
       │                     │  │                     │
       │  - Research API     │  │  - SSR/SSG          │
       │  - WebSocket        │  │  - Static Assets    │
       │  - File Serving     │  │  - API Routes       │
       │  - CLI Executor     │  │                     │
       └─────────────────────┘  └─────────────────────┘
```

### Technology Stack

**Frontend (Next.js Application):**
- Next.js 14+ (App Router)
- React 18+ with Server Components
- TypeScript 5+
- Tailwind CSS 3+
- shadcn/ui components
- React Hook Form + Zod for form validation
- SWR or TanStack Query for data fetching
- Custom WebSocket hook for real-time updates

**Backend (FastAPI - Unchanged):**
- FastAPI (Python 3.12)
- Pydantic v2 for data validation
- WebSocket support
- File serving capabilities

**Build & Development:**
- Vite/Turbopack (via Next.js)
- ESLint + Prettier
- Vitest for unit tests
- Playwright for E2E tests

**Deployment:**
- Docker containers (FastAPI + Next.js)
- Nginx/Caddy reverse proxy
- Environment-based configuration

---

## Proposed File Structure

```
tk9_source_deploy/
├── backend/                          # FastAPI backend (existing)
│   ├── main.py
│   ├── models.py
│   ├── cli_executor.py
│   └── ...
│
├── frontend/                         # NEW: Next.js application
│   ├── app/
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Home page (dashboard)
│   │   ├── api/                     # Next.js API routes (if needed)
│   │   └── research/
│   │       └── [sessionId]/
│   │           └── page.tsx         # Session detail page
│   │
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── form.tsx
│   │   │   └── ...
│   │   │
│   │   ├── research/
│   │   │   ├── research-form.tsx
│   │   │   ├── progress-tracker.tsx
│   │   │   └── log-viewer.tsx
│   │   │
│   │   ├── sessions/
│   │   │   ├── session-browser.tsx
│   │   │   ├── session-card.tsx
│   │   │   └── session-files.tsx
│   │   │
│   │   └── files/
│   │       ├── file-list.tsx
│   │       ├── file-preview.tsx
│   │       └── file-downloader.tsx
│   │
│   ├── lib/
│   │   ├── api-client.ts            # Typed FastAPI client
│   │   ├── websocket.ts             # WebSocket hook
│   │   ├── types.ts                 # TypeScript types
│   │   └── utils.ts                 # Utility functions
│   │
│   ├── hooks/
│   │   ├── use-websocket.ts         # WebSocket React hook
│   │   ├── use-research.ts          # Research state hook
│   │   └── use-sessions.ts          # Sessions data hook
│   │
│   ├── public/                      # Static assets
│   ├── styles/                      # Global styles
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── package.json
│
├── deploy/
│   ├── docker-compose.yml           # Multi-service orchestration
│   ├── nginx.conf                   # Reverse proxy config
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
└── docs/
    └── specs/
        └── WEB_DASHBOARD_MODERNIZATION_PROPOSAL.md  # This file
```

---

## Migration Plan: Strangler Fig Pattern

We'll use the "strangler fig" migration pattern, where the new Next.js application gradually replaces the old dashboard while both remain operational.

### Phase 1: Foundation & Setup (1-2 days)

**Goals:**
- Initialize Next.js project
- Configure FastAPI CORS
- Establish API communication
- Set up development environment

**Tasks:**

1. **Initialize Next.js Application**
   ```bash
   cd frontend
   npx create-next-app@latest . --typescript --tailwind --app --use-npm
   ```

2. **Install shadcn/ui**
   ```bash
   npx shadcn-ui@latest init
   ```

3. **Configure CORS on FastAPI Backend**
   ```python
   # backend/main.py
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # Next.js dev server
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **Create API Client**
   ```typescript
   // frontend/lib/api-client.ts
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:12656';

   export const apiClient = {
     async submitResearch(data: ResearchRequest): Promise<ResearchResponse> {
       const response = await fetch(`${API_BASE_URL}/api/research`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(data),
       });
       return response.json();
     },
     // ... more methods
   };
   ```

5. **Environment Variables**
   ```bash
   # frontend/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:12656
   ```

**Deliverables:**
- Working Next.js dev server on port 3000
- Successful API calls to FastAPI backend
- Basic layout with shadcn/ui components
- TypeScript configuration
- Git branch: `feature/nextjs-migration-phase1`

---

### Phase 2: Core UI Components (3-5 days)

**Goals:**
- Build main dashboard layout
- Implement research form
- Create session browser
- Add file management UI

**Tasks:**

1. **Setup shadcn/ui Components**
   ```bash
   npx shadcn-ui@latest add button card input form select
   npx shadcn-ui@latest add table badge progress
   ```

2. **Create Layout Components**
   ```typescript
   // app/layout.tsx
   export default function RootLayout({ children }: { children: React.ReactNode }) {
     return (
       <html lang="en">
         <body>
           <Header />
           <main className="container mx-auto px-4 py-8">
             {children}
           </main>
           <Footer />
         </body>
       </html>
     );
   }
   ```

3. **Build Research Form Component**
   ```typescript
   // components/research/research-form.tsx
   import { useForm } from 'react-hook-form';
   import { zodResolver } from '@hookform/resolvers/zod';
   import * as z from 'zod';

   const formSchema = z.object({
     subject: z.string().min(3).max(1000),
     language: z.string(),
   });

   export function ResearchForm() {
     const form = useForm<z.infer<typeof formSchema>>({
       resolver: zodResolver(formSchema),
     });

     // Form implementation with shadcn/ui components
   }
   ```

4. **Create Session Browser**
   ```typescript
   // components/sessions/session-browser.tsx
   import { useQuery } from '@tanstack/react-query';

   export function SessionBrowser() {
     const { data: sessions } = useQuery({
       queryKey: ['sessions'],
       queryFn: () => apiClient.getSessions(),
     });

     // Session list with shadcn/ui Table or Cards
   }
   ```

5. **Implement File Management UI**
   ```typescript
   // components/files/file-list.tsx
   export function FileList({ files }: { files: FileInfo[] }) {
     // File list with download buttons, previews, etc.
   }
   ```

**Deliverables:**
- Functional research submission form
- Session browsing interface
- File download/preview UI
- Responsive design with Tailwind CSS
- Git branch: `feature/nextjs-migration-phase2`

---

### Phase 3: Real-Time WebSocket Integration (2-3 days)

**Goals:**
- Port WebSocket client to React hook
- Implement real-time log viewer
- Add progress tracking
- Handle connection states

**Tasks:**

1. **Create WebSocket Hook**
   ```typescript
   // hooks/use-websocket.ts
   import { useEffect, useRef, useState } from 'react';

   export function useWebSocket(sessionId: string) {
     const [messages, setMessages] = useState<LogMessage[]>([]);
     const [isConnected, setIsConnected] = useState(false);
     const wsRef = useRef<WebSocket | null>(null);

     useEffect(() => {
       const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
       const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;

       const ws = new WebSocket(wsUrl);
       wsRef.current = ws;

       ws.onopen = () => setIsConnected(true);
       ws.onmessage = (event) => {
         const data = JSON.parse(event.data);
         if (data.type === 'log') {
           setMessages(prev => [...prev, data]);
         }
       };
       ws.onerror = (error) => console.error('WebSocket error:', error);
       ws.onclose = () => setIsConnected(false);

       return () => ws.close();
     }, [sessionId]);

     return { messages, isConnected };
   }
   ```

2. **Build Log Viewer Component**
   ```typescript
   // components/research/log-viewer.tsx
   import { useWebSocket } from '@/hooks/use-websocket';

   export function LogViewer({ sessionId }: { sessionId: string }) {
     const { messages, isConnected } = useWebSocket(sessionId);

     return (
       <Card>
         <CardHeader>
           <CardTitle>Live Output</CardTitle>
           <ConnectionStatus connected={isConnected} />
         </CardHeader>
         <CardContent>
           <ScrollArea className="h-96 font-mono text-sm">
             {messages.map((msg, i) => (
               <div key={i}>{msg.message}</div>
             ))}
           </ScrollArea>
         </CardContent>
       </Card>
     );
   }
   ```

3. **Implement Progress Tracking**
   ```typescript
   // components/research/progress-tracker.tsx
   export function ProgressTracker({ status, progress }: ProgressProps) {
     return (
       <div className="space-y-4">
         <Progress value={progress} />
         <div className="flex gap-4">
           <StatusIndicator label="Connecting" active={status === 'connecting'} />
           <StatusIndicator label="Running" active={status === 'running'} />
           <StatusIndicator label="Processing" active={status === 'processing'} />
           <StatusIndicator label="Complete" active={status === 'completed'} />
         </div>
       </div>
     );
   }
   ```

4. **Add Global State Management (Optional)**
   ```typescript
   // lib/store.ts
   import { create } from 'zustand';

   interface AppState {
     currentSessionId: string | null;
     setCurrentSessionId: (id: string) => void;
   }

   export const useAppStore = create<AppState>((set) => ({
     currentSessionId: null,
     setCurrentSessionId: (id) => set({ currentSessionId: id }),
   }));
   ```

**Deliverables:**
- Real-time log streaming with WebSocket
- Progress indicators and status updates
- Auto-reconnect logic
- Error handling and fallbacks
- Git branch: `feature/nextjs-migration-phase3`

---

### Phase 4: Testing & Quality Assurance (2-3 days)

**Goals:**
- Write unit tests for components
- Add integration tests
- E2E tests for critical flows
- Accessibility audit

**Tasks:**

1. **Setup Testing Infrastructure**
   ```bash
   npm install -D vitest @testing-library/react @testing-library/jest-dom
   npm install -D @playwright/test
   ```

2. **Unit Tests for Components**
   ```typescript
   // components/research/__tests__/research-form.test.tsx
   import { render, screen } from '@testing-library/react';
   import { ResearchForm } from '../research-form';

   describe('ResearchForm', () => {
     it('validates subject field', async () => {
       render(<ResearchForm />);
       // Test validation logic
     });
   });
   ```

3. **Integration Tests**
   ```typescript
   // __tests__/integration/research-flow.test.tsx
   describe('Research Flow', () => {
     it('submits research and displays results', async () => {
       // Test complete user flow
     });
   });
   ```

4. **E2E Tests with Playwright**
   ```typescript
   // e2e/research.spec.ts
   import { test, expect } from '@playwright/test';

   test('complete research workflow', async ({ page }) => {
     await page.goto('/');
     await page.fill('[name="subject"]', 'Test research topic');
     await page.click('button[type="submit"]');
     await expect(page.locator('.log-viewer')).toBeVisible();
   });
   ```

5. **Accessibility Audit**
   - Run Lighthouse CI
   - Test keyboard navigation
   - Screen reader compatibility
   - WCAG 2.1 AA compliance

**Deliverables:**
- 80%+ test coverage for components
- Integration tests for API interactions
- E2E tests for critical user flows
- Accessibility score 90+
- Git branch: `feature/nextjs-migration-phase4`

---

### Phase 5: Deployment & DevOps (3-4 days)

**Goals:**
- Containerize both services
- Configure reverse proxy
- Set up CI/CD pipeline
- Production deployment

**Tasks:**

1. **Create Dockerfiles**

   ```dockerfile
   # deploy/Dockerfile.frontend
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM node:18-alpine AS runner
   WORKDIR /app
   COPY --from=builder /app/next.config.js ./
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next/standalone ./
   COPY --from=builder /app/.next/static ./.next/static

   EXPOSE 3000
   CMD ["node", "server.js"]
   ```

   ```dockerfile
   # deploy/Dockerfile.backend
   FROM python:3.12-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 12656
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "12656"]
   ```

2. **Docker Compose Configuration**

   ```yaml
   # deploy/docker-compose.yml
   version: '3.8'

   services:
     backend:
       build:
         context: ../backend
         dockerfile: ../deploy/Dockerfile.backend
       ports:
         - "12656:12656"
       environment:
         - GOOGLE_API_KEY=${GOOGLE_API_KEY}
         - BRAVE_API_KEY=${BRAVE_API_KEY}
       volumes:
         - ./outputs:/app/outputs
       networks:
         - tk9-network

     frontend:
       build:
         context: ../frontend
         dockerfile: ../deploy/Dockerfile.frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://backend:12656
       depends_on:
         - backend
       networks:
         - tk9-network

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - frontend
         - backend
       networks:
         - tk9-network

   networks:
     tk9-network:
       driver: bridge
   ```

3. **Nginx Configuration**

   ```nginx
   # deploy/nginx.conf
   upstream frontend {
       server frontend:3000;
   }

   upstream backend {
       server backend:12656;
   }

   server {
       listen 80;
       server_name tk9.thinhkhuat.com;

       # Redirect HTTP to HTTPS
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name tk9.thinhkhuat.com;

       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;

       # API routes to FastAPI backend
       location /api/ {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # WebSocket routes
       location /ws/ {
           proxy_pass http://backend;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       # Next.js frontend
       location / {
           proxy_pass http://frontend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **CI/CD Pipeline (GitHub Actions)**

   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy Dashboard

   on:
     push:
       branches: [main]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Setup Node.js
           uses: actions/setup-node@v3
           with:
             node-version: '18'
         - name: Install dependencies
           run: cd frontend && npm ci
         - name: Run tests
           run: cd frontend && npm test
         - name: Run E2E tests
           run: cd frontend && npm run test:e2e

     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Build Docker images
           run: docker-compose -f deploy/docker-compose.yml build
         - name: Push to registry
           run: |
             docker-compose -f deploy/docker-compose.yml push

     deploy:
       needs: build
       runs-on: ubuntu-latest
       steps:
         - name: Deploy to production
           run: |
             ssh user@192.168.2.22 'cd /path/to/tk9 && docker-compose pull && docker-compose up -d'
   ```

**Deliverables:**
- Dockerized frontend and backend
- Reverse proxy configuration
- Automated CI/CD pipeline
- Production deployment on 192.168.2.22
- SSL/TLS certificates configured
- Git branch: `feature/nextjs-migration-phase5`

---

### Phase 6: Monitoring & Optimization (1-2 days)

**Goals:**
- Set up error tracking
- Add performance monitoring
- Optimize bundle size
- Configure caching

**Tasks:**

1. **Error Tracking (Sentry)**
   ```typescript
   // app/layout.tsx
   import * as Sentry from "@sentry/nextjs";

   Sentry.init({
     dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
     environment: process.env.NODE_ENV,
   });
   ```

2. **Performance Monitoring**
   ```typescript
   // next.config.js
   module.exports = {
     experimental: {
       optimizeCss: true,
     },
     compiler: {
       removeConsole: process.env.NODE_ENV === 'production',
     },
   };
   ```

3. **Bundle Analysis**
   ```bash
   npm install -D @next/bundle-analyzer
   ANALYZE=true npm run build
   ```

4. **Caching Strategy**
   ```typescript
   // app/api/sessions/route.ts
   export const revalidate = 60; // ISR: revalidate every 60 seconds
   ```

**Deliverables:**
- Error tracking dashboard
- Performance metrics
- Optimized bundle size (<500KB initial)
- Caching configuration
- Git branch: `feature/nextjs-migration-phase6`

---

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 1-2 days | Foundation & Setup |
| Phase 2 | 3-5 days | Core UI Components |
| Phase 3 | 2-3 days | WebSocket Integration |
| Phase 4 | 2-3 days | Testing & QA |
| Phase 5 | 3-4 days | Deployment & DevOps |
| Phase 6 | 1-2 days | Monitoring & Optimization |
| **Total** | **12-19 days** | **Full migration complete** |

**Buffer:** Add 20% buffer for unexpected issues = **15-23 days total**

---

## Risk Assessment & Mitigation

### Technical Risks

1. **CORS Issues**
   - **Risk:** FastAPI and Next.js communication issues
   - **Mitigation:** Configure CORS properly in Phase 1, test extensively
   - **Severity:** Medium

2. **WebSocket Connection Through Proxy**
   - **Risk:** Nginx/Caddy may not properly upgrade WebSocket connections
   - **Mitigation:** Test WebSocket routing early, configure proxy headers correctly
   - **Severity:** High (already known issue in current setup)

3. **Session Persistence**
   - **Risk:** Users lose work if connection drops
   - **Mitigation:** Implement local storage caching, auto-save draft state
   - **Severity:** Medium

4. **Build/Deploy Complexity**
   - **Risk:** Two-service deployment more complex than single service
   - **Mitigation:** Comprehensive Docker Compose setup, automated CI/CD
   - **Severity:** Low

### Operational Risks

1. **Service Orchestration**
   - **Risk:** Both services must be running for dashboard to work
   - **Mitigation:** Health checks, proper dependency management in Docker Compose
   - **Severity:** Medium

2. **Resource Usage**
   - **Risk:** Running two services increases memory/CPU usage
   - **Mitigation:** Monitor resource usage, optimize both services
   - **Severity:** Low

3. **Deployment Downtime**
   - **Risk:** Migration may cause temporary downtime
   - **Mitigation:** Blue-green deployment strategy, keep old dashboard available
   - **Severity:** Low

### Mitigation Strategies

1. **Parallel Running:**
   - Keep old dashboard at `/old` route during migration
   - Allow gradual user migration

2. **Feature Flags:**
   - Use feature flags to toggle between old and new components
   - Gradual rollout of new features

3. **Comprehensive Testing:**
   - Extensive E2E tests before production deployment
   - Load testing for WebSocket connections

4. **Rollback Plan:**
   - Maintain old Docker images
   - Quick rollback via Docker Compose
   - Database/file system compatibility

---

## Success Metrics

### Development Metrics

- **Code Quality:**
  - TypeScript coverage: 100%
  - Test coverage: >80%
  - ESLint errors: 0
  - Lighthouse score: >90

- **Performance:**
  - First Contentful Paint: <1.5s
  - Time to Interactive: <3.5s
  - Bundle size: <500KB initial
  - WebSocket latency: <100ms

### User Experience Metrics

- **Accessibility:**
  - WCAG 2.1 AA compliance
  - Keyboard navigation fully functional
  - Screen reader compatible

- **Functionality:**
  - All current features preserved
  - New features added (file preview, batch download, etc.)
  - Mobile responsive design

### Operational Metrics

- **Reliability:**
  - Uptime: >99.5%
  - Error rate: <0.1%
  - WebSocket reconnection success: >95%

- **Developer Experience:**
  - Build time: <30s
  - Hot reload time: <2s
  - CI/CD pipeline: <10 minutes

---

## Cost Analysis

### Development Costs

- **Engineering Time:** 15-23 days @ developer rate
- **Infrastructure:** Minimal (already have server)
- **Tools/Services:**
  - Sentry (error tracking): Free tier sufficient
  - Vercel Analytics: Free tier sufficient
  - GitHub Actions: Free tier sufficient

### Operational Costs

- **Increased Resource Usage:**
  - Memory: +~200MB (Node.js + Next.js)
  - CPU: +~10% (Next.js rendering)
  - Storage: +~50MB (Node modules, builds)

- **Maintenance:**
  - Two services to monitor instead of one
  - More complex deployment pipeline
  - Additional documentation required

### ROI Calculation

**Benefits:**
- Faster feature development: 2-3x faster with shadcn/ui
- Reduced bugs: TypeScript catches errors at compile-time
- Better UX: Professional UI improves user satisfaction
- Team velocity: Leveraging existing expertise accelerates development

**Break-Even Point:**
- Initial investment: 15-23 days
- Productivity gains: 2-3x faster feature development
- Break-even: After 2-3 major features or 1-2 months

---

## Alternative Approaches Considered

### 1. Lit/Vite Progressive Enhancement

**Pros:**
- Minimal architectural change
- Single service deployment
- Gradual migration path
- Lower operational complexity

**Cons:**
- Smaller component ecosystem
- Team learning curve
- Manual UI component development
- Limited scalability

**Verdict:** Rejected due to team's existing Next.js expertise and desire for superior UI/UX.

### 2. Keep Current Vanilla JS

**Pros:**
- Zero migration cost
- No new dependencies
- Proven in production

**Cons:**
- Technical debt accumulates
- Difficult to add complex features
- No type safety
- Poor developer experience

**Verdict:** Rejected due to long-term maintainability concerns.

### 3. React SPA (Without Next.js)

**Pros:**
- Simpler than Next.js
- Client-side only (no SSR complexity)
- Smaller bundle

**Cons:**
- Loses SSR/SSG benefits
- Reinventing Next.js features
- Less tooling/optimization

**Verdict:** Rejected because Next.js provides better DX without significant overhead.

---

## Dependencies & Prerequisites

### Technical Prerequisites

1. **Node.js 18+** installed on development and production machines
2. **npm or pnpm** for package management
3. **Docker & Docker Compose** for containerization
4. **Nginx or Caddy** for reverse proxy
5. **Git** for version control
6. **SSL/TLS certificates** for HTTPS

### Team Prerequisites

1. **Next.js expertise** (already have)
2. **TypeScript knowledge** (can learn incrementally)
3. **React experience** (already have)
4. **Docker/DevOps skills** (for deployment)

### Infrastructure Prerequisites

1. **Server access** to 192.168.2.22 (already have)
2. **Domain configuration** for tk9.thinhkhuat.com (already have)
3. **CI/CD pipeline** setup (GitHub Actions or equivalent)
4. **Monitoring tools** (Sentry, etc.)

---

## Conclusion & Recommendation

### Final Recommendation: Full Next.js Migration

After comprehensive analysis and consultation with Gemini AI, we strongly recommend proceeding with the **Full Next.js Migration** strategy.

### Key Reasons:

1. **Team Expertise:** Leverages existing Next.js knowledge for maximum velocity
2. **UI/UX Quality:** shadcn/ui provides professional components out-of-the-box
3. **Type Safety:** TypeScript catches errors at compile-time, improving reliability
4. **Long-term Scalability:** Solid foundation for future feature development
5. **Developer Experience:** Best-in-class tooling and hot reload
6. **Component Ecosystem:** Access to entire React ecosystem

### Trade-offs Accepted:

1. **Operational Complexity:** Two services instead of one (mitigated by Docker Compose)
2. **CORS Configuration:** Required for API communication (straightforward to set up)
3. **Initial Investment:** 15-23 days of development time (justified by long-term gains)

### Next Steps:

1. **Approval:** Get stakeholder approval for this proposal
2. **Planning:** Create detailed sprint plans for each phase
3. **Branch Creation:** Create `feature/nextjs-migration` branch
4. **Phase 1 Kickoff:** Begin with Foundation & Setup
5. **Regular Reviews:** Weekly progress reviews during migration

---

## Appendix A: Key Technologies Reference

### Frontend Stack

- **Next.js 14+:** https://nextjs.org/docs
- **React 18+:** https://react.dev/
- **TypeScript:** https://www.typescriptlang.org/
- **Tailwind CSS:** https://tailwindcss.com/
- **shadcn/ui:** https://ui.shadcn.com/

### Libraries & Tools

- **React Hook Form:** https://react-hook-form.com/
- **Zod:** https://zod.dev/
- **TanStack Query:** https://tanstack.com/query/latest
- **Zustand:** https://zustand-demo.pmnd.rs/
- **Vitest:** https://vitest.dev/
- **Playwright:** https://playwright.dev/

### Backend (Unchanged)

- **FastAPI:** https://fastapi.tiangolo.com/
- **Pydantic:** https://docs.pydantic.dev/
- **Uvicorn:** https://www.uvicorn.org/

### DevOps

- **Docker:** https://docs.docker.com/
- **Nginx:** https://nginx.org/en/docs/
- **GitHub Actions:** https://docs.github.com/en/actions

---

## Appendix B: Sample Component Code

### ResearchForm Component (TypeScript + shadcn/ui)

```typescript
// components/research/research-form.tsx
'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api-client';

const formSchema = z.object({
  subject: z
    .string()
    .min(3, 'Subject must be at least 3 characters')
    .max(1000, 'Subject must not exceed 1000 characters'),
  language: z.string(),
});

export function ResearchForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      subject: '',
      language: 'vi',
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const response = await apiClient.submitResearch(values);
      toast({
        title: 'Research Started',
        description: `Session ID: ${response.session_id}`,
      });
      // Navigate to session page or update UI
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit research request',
        variant: 'destructive',
      });
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="subject"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Research Subject</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter your research topic here..."
                  className="min-h-[100px]"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                {field.value.length}/1000 characters
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="language"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Output Language</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a language" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="vi">Vietnamese</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="zh">Chinese</SelectItem>
                  <SelectItem value="ja">Japanese</SelectItem>
                  <SelectItem value="ko">Korean</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full">
          Start Research
        </Button>
      </form>
    </Form>
  );
}
```

---

## Appendix C: Questions for Stakeholders

Before proceeding with this migration, please consider:

1. **Timeline:** Is a 15-23 day migration timeline acceptable?
2. **Resources:** Do we have dedicated developer time for this project?
3. **Risk Tolerance:** Are we comfortable with the two-service architecture?
4. **Feature Freeze:** Can we pause new features during migration?
5. **Budget:** Is there budget for monitoring tools (Sentry, etc.)?
6. **Deployment:** Do we have DevOps support for Docker/Nginx setup?
7. **User Impact:** Can we have a brief maintenance window for cutover?
8. **Rollback Plan:** Are we comfortable with the proposed rollback strategy?

---

**Document Status:** Proposal - Awaiting Approval
**Last Updated:** October 31, 2025
**Next Review:** Upon stakeholder feedback
**Approvers:** Project Owner, Tech Lead, DevOps Lead

---

**Prepared by:** Claude Code + Gemini AI Consultation
**Contact:** [Your contact information]
