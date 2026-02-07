# S.C.A.R.I - Easy Deployment v2.0

**Deploy in seconds!** 🚀

> **Status:** ✅ Production Ready | **Version:** v2.0-thermal-safe | **License:** MIT

---

## ⚡ Quick Deploy (Pick One)

### 🐳 Docker (30 seconds - Recommended)
```bash
bash deploy.sh docker
# Open http://localhost:5173
```

### 💻 Local (2 minutes)
```bash
bash deploy.sh local
# Then run: uvicorn src.api.app:app --reload & cd ui && npm run dev
```

### 📋 Using Make
```bash
make deploy         # Full deployment
make local-dev      # Local development
make docker-logs    # View logs
make health         # Check health
```

---

## 🎯 What You Get

- ✅ **Thermal Control:** Hard <60°C safety limit
- ✅ **Modern UI:** Premium glassmorphism interface
- ✅ **Advanced Visualizations:** Real-time thermal charts
- ✅ **Production Ready:** Fully optimized & tested
- ✅ **Easy Deployment:** Docker, local, or production

---

## 📊 Service URLs

After deployment:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## 🔧 Configuration

### Environment Variables
```bash
# Edit .env
cp .env.example .env
nano .env  # Customize if needed
```

### Key Settings
```env
# Thermal safety
MAX_TEMP=60.0              # Hard limit (do not change)
MAX_FAN_POWER=550.0        # Increase for better control
MAX_PUMP_POWER=100.0       # Liquid cooling

# Frontend
VITE_API_BASE=http://localhost:8000
```

---

## 🚀 Common Commands

```bash
# Docker management
docker-compose up -d              # Start
docker-compose down               # Stop
docker-compose logs -f backend    # View logs
docker-compose restart            # Restart

# Using Make
make deploy                        # Full deploy
make docker-logs                   # View logs
make health                        # Check health
make test                          # Run tests
make clean                         # Cleanup
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port in use** | Change ports: `BACKEND_PORT=8001` in `.env` |
| **Out of memory** | Increase Docker memory (6GB+) in settings |
| **Services won't start** | Run `docker-compose logs` to see errors |
| **Frontend not loading** | Check `VITE_API_BASE` in `.env` |

---

## 📚 Full Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete setup guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands
- **[SYSTEM_IMPROVEMENTS.md](SYSTEM_IMPROVEMENTS.md)** - Technical details

---

## ✨ Features

### 🛡️ Thermal Safety
- Hard <60°C limit enforced at 3 levels
- 8-tier reward structure
- Conservative training parameters

### 🎨 Premium UI
- glassmorphism design
- Vibrant color palette
- Smooth animations
- Responsive mobile/tablet/desktop

### 📊 Advanced Visualizations
- Real-time thermal tracking
- Efficiency analysis
- Training progress
- Comprehensive dashboards

### ⚡ Production Ready
- 70% compression (72KB gzipped)
- Zero vulnerabilities
- Full test coverage
- Auto health checks

---

## 🎓 Development

```bash
# Setup local environment
make install              # Install dependencies
make local-dev           # Setup dev environment

# Development workflow
make test                # Run tests
make lint                # Lint code
make train               # Train model
make health              # Check health

# Training
make train               # Train thermal-safe model
make eval                # Evaluate model
make models              # List models
```

---

## 📋 Pre-Flight Checklist

- [ ] Docker installed (for Docker deployment)
- [ ] Python 3.10+ installed (for local deployment)
- [ ] Node.js 18+ installed (for frontend)
- [ ] `.env` file created
- [ ] At least 4GB RAM available
- [ ] Ports 8000, 5173 available

---

## 🚀 Production Deployment

```bash
# Production setup
bash deploy.sh prod

# Or with Make
make deploy ENV=production

# Monitor
make health
make docker-logs
```

---

## 🔐 Security Notes

- Change API keys in `.env`
- Configure CORS origins
- Use HTTPS in production
- Regular backups recommended
- Keep dependencies updated

---

## 📞 Support

For issues:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. View logs: `docker-compose logs -f`
3. Run health check: `make health`
4. Check configuration: `.env` settings

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Build Time | 2.31s |
| Frontend Bundle | 72KB (gzipped) |
| CSS Size | 2.79KB (gzipped) |
| Services | 3 (frontend, backend, optional nginx) |

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| v2.0 (thermal-safe) | 2024 | ✅ Current |
| v1.0 | 2024 | 🏁 Archived |

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 💡 Quick Tips

1. **First time?** → Use `bash deploy.sh docker` (easiest)
2. **Developing?** → Use `make local-dev` with two terminals
3. **Production?** → Use `bash deploy.sh prod` with validation 
4. **Troubleshooting?** → Check logs with `make docker-logs`

---

**Ready to deploy?** Run: `bash deploy.sh docker` ⚡

Happy computing! 🎉
