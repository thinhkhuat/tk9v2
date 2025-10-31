# Web Dashboard Modernization - Quick Start Guide

**For Developers Starting the Migration**

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm or pnpm installed
- [ ] Docker & Docker Compose installed
- [ ] Git access to repository
- [ ] FastAPI backend running locally (port 12656)
- [ ] Read the full proposal document
- [ ] Approval from stakeholders

---

## Phase 1: Foundation Setup (Day 1)

### Step 1: Create Next.js Application

```bash
# Navigate to project root
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy

# Create frontend directory
mkdir -p frontend
cd frontend

# Initialize Next.js with TypeScript and Tailwind
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --use-npm \
  --import-alias "@/*"

# Answer prompts:
# √ Would you like to use ESLint? ... Yes
# √ Would you like to use Turbopack for next dev? ... Yes
# √ Would you like to customize the default import alias? ... No
```

### Step 2: Install shadcn/ui

```bash
# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Answer prompts:
# Style: Default
# Base color: Slate
# CSS variables: Yes
```

### Step 3: Install Additional Dependencies

```bash
npm install \
  @tanstack/react-query \
  zustand \
  react-hook-form \
  @hookform/resolvers \
  zod \
  date-fns \
  clsx \
  tailwind-merge

npm install -D \
  @types/node \
  vitest \
  @testing-library/react \
  @testing-library/jest-dom \
  @playwright/test
```

### Step 4: Configure Environment Variables

```bash
# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:12656
NEXT_PUBLIC_WS_URL=ws://localhost:12656
NODE_ENV=development
EOF
```

### Step 5: Configure FastAPI CORS

```bash
# Edit backend main.py
cd ../web_dashboard

# Add CORS middleware (if not already present)
```

```python
# web_dashboard/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://192.168.2.22:3000",  # Local network
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 6: Test Connection

```bash
# Terminal 1: Start FastAPI backend
cd web_dashboard
python main.py

# Terminal 2: Start Next.js dev server
cd frontend
npm run dev

# Open browser: http://localhost:3000
# Should see Next.js default page
```

---

## Phase 2: Project Structure (Day 1-2)

### Create Directory Structure

```bash
cd frontend

# Create component directories
mkdir -p components/{ui,research,sessions,files,layout}
mkdir -p lib
mkdir -p hooks
mkdir -p types
```

### Install shadcn/ui Components

```bash
# Core components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add form
npx shadcn-ui@latest add select
npx shadcn-ui@latest add label

# Additional components
npx shadcn-ui@latest add table
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add toast
```

### Create Type Definitions

```bash
# Create types/api.ts
cat > types/api.ts << 'EOF'
export interface ResearchRequest {
  subject: string;
  language: string;
  save_files?: boolean;
}

export interface ResearchResponse {
  session_id: string;
  status: string;
  message: string;
  websocket_url: string;
}

export interface FileInfo {
  filename: string;
  url: string;
  size: number;
  created: string;
}

export interface SessionStatus {
  session_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  files: FileInfo[];
  error_message?: string;
}

export interface LogMessage {
  type: 'log' | 'error' | 'completed' | 'files_ready';
  message: string;
  timestamp: number;
  session_id?: string;
}
EOF
```

### Create API Client

```bash
# Create lib/api-client.ts
cat > lib/api-client.ts << 'EOF'
import type { ResearchRequest, ResearchResponse, SessionStatus } from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:12656';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async submitResearch(data: ResearchRequest): Promise<ResearchResponse> {
    const response = await fetch(`${this.baseUrl}/api/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit research: ${response.statusText}`);
    }

    return response.json();
  }

  async getSessionStatus(sessionId: string): Promise<SessionStatus> {
    const response = await fetch(`${this.baseUrl}/api/session/${sessionId}`);

    if (!response.ok) {
      throw new Error(`Failed to get session status: ${response.statusText}`);
    }

    return response.json();
  }

  async getSessions() {
    const response = await fetch(`${this.baseUrl}/api/sessions`);

    if (!response.ok) {
      throw new Error(`Failed to get sessions: ${response.statusText}`);
    }

    return response.json();
  }

  getDownloadUrl(sessionId: string, filename: string): string {
    return `${this.baseUrl}/download/${sessionId}/${filename}`;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
EOF
```

---

## Phase 3: Build First Component (Day 2-3)

### Create Root Layout

```bash
# Edit app/layout.tsx
cat > app/layout.tsx << 'EOF'
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'TK9 Deep Research Dashboard',
  description: 'Multi-agent AI research system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-purple-500 to-purple-700">
          <header className="bg-white/10 backdrop-blur-sm border-b border-white/20">
            <div className="container mx-auto px-4 py-6">
              <h1 className="text-3xl font-bold text-white">
                🔍 TK9 Deep Research Dashboard
              </h1>
              <p className="text-white/80 mt-2">
                Multi-agent AI research system
              </p>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="mt-auto py-6 text-center text-white/60">
            <p>Powered by Multi-Agent AI System</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
EOF
```

### Create Home Page

```bash
# Edit app/page.tsx
cat > app/page.tsx << 'EOF'
import { ResearchForm } from '@/components/research/research-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto">
      <Card className="bg-white shadow-xl">
        <CardHeader>
          <CardTitle>Start New Research</CardTitle>
          <CardDescription>
            Enter your research topic and let our AI agents investigate it for you
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResearchForm />
        </CardContent>
      </Card>
    </div>
  );
}
EOF
```

### Create Research Form Component

```bash
# Create components/research/research-form.tsx
cat > components/research/research-form.tsx << 'EOF'
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
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { useRouter } from 'next/navigation';

const formSchema = z.object({
  subject: z
    .string()
    .min(3, 'Subject must be at least 3 characters')
    .max(1000, 'Subject must not exceed 1000 characters'),
  language: z.string(),
});

export function ResearchForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      subject: '',
      language: 'vi',
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsSubmitting(true);
      const response = await apiClient.submitResearch(values);

      // Navigate to session page
      router.push(`/research/${response.session_id}`);
    } catch (error) {
      console.error('Failed to submit research:', error);
      alert('Failed to submit research. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  const charCount = form.watch('subject').length;

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="subject"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Research Subject</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter your research topic here (e.g., 'Latest developments in quantum computing', 'Climate change impacts on agriculture', etc.)"
                  className="min-h-[120px] resize-none"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                <span className={charCount > 900 ? 'text-red-500' : ''}>
                  {charCount}/1000 characters
                </span>
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

        <Button
          type="submit"
          className="w-full"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Starting Research...' : 'Start Research'}
        </Button>
      </form>
    </Form>
  );
}
EOF
```

---

## Phase 4: WebSocket Integration (Day 3-4)

### Create WebSocket Hook

```bash
# Create hooks/use-websocket.ts
cat > hooks/use-websocket.ts << 'EOF'
import { useEffect, useRef, useState } from 'react';
import type { LogMessage } from '@/types/api';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:12656';

export function useWebSocket(sessionId: string) {
  const [messages, setMessages] = useState<LogMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    if (!sessionId) return;

    const connect = () => {
      const wsUrl = `${WS_BASE_URL}/ws/${sessionId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: LogMessage = JSON.parse(event.data);
          setMessages((prev) => [...prev, data]);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // Attempt to reconnect
        if (reconnectAttempts.current < 5) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  return { messages, isConnected, error };
}
EOF
```

### Create Session Page

```bash
# Create app/research/[sessionId]/page.tsx
mkdir -p app/research/[sessionId]
cat > app/research/[sessionId]/page.tsx << 'EOF'
'use client';

import { useParams } from 'next/navigation';
import { LogViewer } from '@/components/research/log-viewer';
import { ProgressTracker } from '@/components/research/progress-tracker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ResearchSessionPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <Card className="bg-white">
        <CardHeader>
          <CardTitle>Research in Progress</CardTitle>
          <p className="text-sm text-muted-foreground font-mono">
            Session ID: {sessionId}
          </p>
        </CardHeader>
        <CardContent>
          <ProgressTracker sessionId={sessionId} />
        </CardContent>
      </Card>

      <LogViewer sessionId={sessionId} />
    </div>
  );
}
EOF
```

---

## Testing Your Setup

### Manual Testing Checklist

```bash
# 1. Start backend
cd web_dashboard
python main.py

# 2. Start frontend
cd frontend
npm run dev

# 3. Open browser
open http://localhost:3000

# 4. Test form submission
# - Enter a research topic
# - Select language
# - Click "Start Research"
# - Should navigate to session page

# 5. Test WebSocket
# - Should see "Connected" status
# - Should see real-time log messages
# - Should see progress updates

# 6. Test file downloads
# - Wait for research to complete
# - Should see download links
# - Click download, file should download
```

### Automated Tests

```bash
# Run unit tests
npm run test

# Run E2E tests
npm run test:e2e

# Run linting
npm run lint

# Type checking
npm run type-check
```

---

## Common Issues & Solutions

### Issue: CORS Error

**Symptom:** Console shows CORS error when calling API

**Solution:**
```python
# Ensure CORS middleware is configured in backend
# web_dashboard/main.py should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: WebSocket Connection Failed

**Symptom:** WebSocket shows "Connection error" or fails to connect

**Solution:**
1. Check backend is running on port 12656
2. Check WebSocket URL is correct: `ws://localhost:12656/ws/{sessionId}`
3. Check browser console for specific error
4. Try direct WebSocket test: `wscat -c ws://localhost:12656/ws/test-session`

### Issue: Module Not Found

**Symptom:** Import errors like "Cannot find module '@/components/ui/button'"

**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check tsconfig.json has correct paths:
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### Issue: shadcn/ui Component Not Found

**Symptom:** Component import fails

**Solution:**
```bash
# Re-add the component
npx shadcn-ui@latest add button

# Check components.json exists
cat components.json
```

---

## Next Steps

Once Phase 1-4 are complete:

1. **Add More Components**
   - Session browser
   - File manager with preview
   - Settings page

2. **Improve UX**
   - Loading states
   - Error boundaries
   - Optimistic updates

3. **Add Tests**
   - Component unit tests
   - Integration tests
   - E2E tests

4. **Deployment**
   - Dockerize Next.js
   - Configure reverse proxy
   - Set up CI/CD

---

## Useful Commands

```bash
# Development
npm run dev              # Start dev server
npm run build           # Build for production
npm run start           # Start production server
npm run lint            # Run ESLint
npm run type-check      # TypeScript type checking

# Testing
npm run test            # Run unit tests
npm run test:watch      # Watch mode
npm run test:e2e        # E2E tests
npm run test:coverage   # Coverage report

# shadcn/ui
npx shadcn-ui@latest add [component]  # Add component
npx shadcn-ui@latest diff             # Check for updates

# Docker
docker-compose up -d    # Start all services
docker-compose logs -f  # View logs
docker-compose down     # Stop all services
```

---

## Getting Help

- **Full Documentation:** See `WEB_DASHBOARD_MODERNIZATION_PROPOSAL.md`
- **Next.js Docs:** https://nextjs.org/docs
- **shadcn/ui Docs:** https://ui.shadcn.com/docs
- **TypeScript Docs:** https://www.typescriptlang.org/docs

**Good luck with the migration!** 🚀
