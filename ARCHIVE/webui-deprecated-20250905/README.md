# Deep Research MCP Web UI

A modern web interface for the Deep Research MCP system, providing real-time research execution with multi-agent orchestration.

## Architecture Overview

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **UI Library**: shadcn/ui components
- **Styling**: Tailwind CSS (production build)
- **Icons**: Lucide React
- **State Management**: Zustand
- **Real-time**: Socket.io client
- **Authentication**: Supabase Auth

### Backend (FastAPI + Python 3.11)
- **Framework**: FastAPI with WebSocket support
- **Queue System**: Celery + Redis
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Real-time**: Socket.io server
- **Integration**: Direct integration with existing multi_agents system

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis server
- Supabase project

### Backend Setup

1. Install dependencies:
```bash
cd webui/backend
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
python migrate.py
```

4. Start the server:
```bash
# Start Redis
redis-server

# Start Celery worker
celery -A main.celery_app worker --loglevel=info

# Start FastAPI server
python main.py
```

### Frontend Setup

1. Install dependencies:
```bash
cd webui/frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Run development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
npm start
```

## Features

### Core Features
- ✅ Real-time research progress tracking
- ✅ Multi-agent status visualization
- ✅ Research history with pagination
- ✅ File downloads (PDF, DOCX, Markdown)
- ✅ Multi-language support (50+ languages)
- ✅ Authentication via Supabase
- ✅ Responsive design

### Research Management
- Create new research sessions
- Monitor agent progress in real-time
- Cancel running research tasks
- View detailed agent logs
- Download generated reports

### User Features
- Personal research history
- Session management
- Preference settings
- Provider status monitoring

## Project Structure

```
webui/
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── research/     # Research-specific components
│   │   └── layout/       # Layout components
│   ├── stores/           # Zustand stores
│   ├── lib/              # Utilities and helpers
│   └── public/           # Static assets
│
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── auth.py          # Authentication
│   ├── database.py      # Database models
│   ├── models.py        # Pydantic models
│   ├── storage.py       # File storage
│   └── tasks.py         # Celery tasks
│
├── docker/              # Docker configuration
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   └── docker-compose.yml
│
└── docs/               # Documentation
    ├── API.md         # API documentation
    ├── DEPLOYMENT.md  # Deployment guide
    └── DEVELOPMENT.md # Development guide
```

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Redis
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Research Providers (from main project)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
TAVILY_API_KEY=tvly-...
BRAVE_API_KEY=...
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## API Endpoints

### Research Endpoints
- `POST /api/v1/research/sessions` - Create new research
- `GET /api/v1/research/sessions` - List sessions
- `GET /api/v1/research/sessions/{id}` - Get session details
- `POST /api/v1/research/sessions/{id}/cancel` - Cancel session
- `GET /api/v1/research/sessions/{id}/files/{filename}` - Download file

### Provider Endpoints
- `GET /api/v1/providers/llm` - List LLM providers
- `GET /api/v1/providers/search` - List search providers

### WebSocket Events
- `research_started` - Research task started
- `agent_progress` - Agent status update
- `research_completed` - Research finished
- `research_error` - Error occurred
- `file_ready` - File available for download

## Database Schema

See [Architecture Design](#) for complete database schema including:
- `user_profiles` - User settings and preferences
- `research_sessions` - Research task records
- `research_files` - Generated file records
- `agent_executions` - Agent execution logs
- `provider_stats` - Provider usage statistics

## Deployment

### Docker Deployment
```bash
cd webui/docker
docker-compose up -d
```

### Production Deployment

#### Frontend (Vercel)
```bash
npm run build
vercel deploy
```

#### Backend (Railway/Render)
```bash
docker build -t deep-research-api .
docker push your-registry/deep-research-api
```

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm run test
```

### Code Quality
```bash
# Backend
black .
isort .
mypy .

# Frontend
npm run lint
npm run type-check
```

## Integration with Existing System

The web UI integrates with the existing multi_agents system through:

1. **Minimal Wrapper**: `ResearchTaskWrapper` class wraps existing functionality
2. **Progress Callbacks**: Agents report progress via callbacks
3. **File Storage**: Publisher agent uploads to Supabase Storage
4. **State Management**: Preserves existing workflow state

## Roadmap

### Phase 1: MVP ✅
- Basic authentication
- Research submission
- Progress tracking
- File downloads

### Phase 2: Full Features (In Progress)
- Complete history management
- Advanced filtering
- Provider monitoring
- User preferences

### Phase 3: Optimization (Planned)
- Performance optimization
- Advanced caching
- Analytics dashboard
- Admin interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Create an issue in GitHub
- Check documentation in `/docs`
- Review architecture design document