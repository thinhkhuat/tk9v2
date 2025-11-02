# TK9 V2 Dashboard - Production Quick Start

## 🚀 One-Command Start

```bash
cd web_dashboard && ./start_v2_dashboard.sh
```

## 📋 Pre-Flight Checklist

- [ ] `.env` file exists with real values (no placeholders)
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Ports 12689 & 8592 available

## 🔑 Required Environment Variables

Edit `web_dashboard/.env`:

```env
SUPABASE_URL=https://your-actual-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...actual_key
SUPABASE_ANON_KEY=eyJhbG...actual_key
JWT_SECRET=your-actual-long-secret-32plus-chars
```

## 🌐 Access URLs (After Start)

| Service | Local | Internal | Public |
|---------|-------|----------|--------|
| **Frontend** | http://localhost:8592 | http://192.168.2.22:8592 | https://tk9v2.thinhkhuat.com |
| **Backend** | http://localhost:12689 | http://192.168.2.22:12689 | - |
| **API Docs** | http://localhost:12689/docs | - | - |
| **Health** | http://localhost:12689/health | - | - |

## 🛑 Stop Services

Press `Ctrl+C` in the terminal (once)

## 📊 Monitor Logs

```bash
# Real-time monitoring
tail -f logs/backend_*.log    # Backend
tail -f logs/frontend_*.log   # Frontend
tail -f logs/*.log             # All

# Search for errors
grep -i error logs/*.log
```

## 🔧 Common Commands

```bash
# Health check
curl http://localhost:12689/health

# Check processes
ps aux | grep -E "main.py|vite"

# Check ports
lsof -i :12689
lsof -i :8592

# Force kill (if needed)
pkill -f "python.*main.py"
pkill -f "vite.*preview"
```

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | `lsof -ti:12689 \| xargs kill -9` |
| Missing env vars | Edit `.env` with real values |
| Build fails | Check `logs/frontend_*.log` |
| Backend dies | Check `logs/backend_*.log` |

## 📖 Full Documentation

See `PRODUCTION_DEPLOYMENT.md` for complete guide.

---

**Version**: 2.0-PRODUCTION | **Ports**: Backend 12689, Frontend 8592
