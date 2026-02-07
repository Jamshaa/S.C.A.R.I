# 🚀 S.C.A.R.I Easy Deployment Guide

**Status:** ✅ **PRODUCTION READY** - Deploy in minutes!

---

## 📋 Quick Start (3 Options)

### Option 1: Docker (Recommended - 30 seconds)
```bash
# Clone or navigate to repository
cd S.C.A.R.I

# Run deployment script
bash deploy.sh docker

# Access services
# Frontend: http://localhost:5173
# API: http://localhost:8000
```

### Option 2: Local Development (2 minutes)
```bash
bash deploy.sh local

# Then run in separate terminals:
# Terminal 1: uvicorn src.api.app:app --reload --port 8000
# Terminal 2: cd ui && npm run dev
```

### Option 3: Production (with validation)
```bash
bash deploy.sh prod
```

---

## 🐳 Docker Deployment (Easiest)

### Requirements
- ✅ Docker Engine (20.10+)
- ✅ Docker Compose (2.0+)
- ✅ 4GB RAM minimum
- ✅ 2GB disk space

### Step-by-Step

#### 1️⃣ **Clone Repository**
```bash
git clone https://github.com/Jamshaa/S.C.A.R.I.git
cd S.C.A.R.I
```

#### 2️⃣ **Configure Environment**
```bash
# Copy example config
cp .env.example .env

# Edit .env if needed (optional - defaults work fine)
# nano .env
```

#### 3️⃣ **Start Services**
```bash
# One-line deployment
docker-compose up -d

# Or use auto-script
bash deploy.sh docker
```

#### 4️⃣ **Verify Deployment**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Test API health
curl http://localhost:8000/health
```

#### 5️⃣ **Access Services**
- 🌐 **Frontend:** http://localhost:5173
- 🔌 **API:** http://localhost:8000
- 📊 **API Docs:** http://localhost:8000/docs
- 💚 **Health Check:** http://localhost:8000/health

---

## 🐛 Troubleshooting Docker Deployment

### ❌ Port Already in Use
```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=5174

# Restart
docker-compose restart
```

### ❌ Out of Memory
```bash
# Increase Docker memory allocation
# Docker Desktop Settings → Resources → Memory (increase to 6GB+)

# Then restart
docker-compose restart
```

### ❌ Build Fails
```bash
# Clear all cached images
docker system prune -a

# Rebuild
docker-compose build --no-cache
```

### ❌ Services Won't Start
```bash
# Check logs for errors
docker-compose logs

# Restart all services
docker-compose down
docker-compose up -d
```

---

## 💻 Local Development Setup

### Requirements
- ✅ Python 3.10+
- ✅ Node.js 18+
- ✅ npm or yarn
- ✅ Virtual environment support

### Installation

#### 1️⃣ **Create Virtual Environment**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 2️⃣ **Install Backend**
```bash
pip install -r requirements.txt
```

#### 3️⃣ **Install Frontend**
```bash
cd ui
npm install
cd ..
```

#### 4️⃣ **Run Services**

Terminal 1 (Backend):
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn src.api.app:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd ui
npm run dev
```

---

## ⚙️ Configuration Guide

### Key Environment Variables

#### Backend `.env`
```ini
# Application
ENV=production
BACKEND_PORT=8000

# Thermal Settings
MAX_TEMP=60.0
MAX_FAN_POWER=550.0

# Training
TRAINING_TIMESTEPS=600000
CONFIG_FILE=configs/optimized.yaml

# Storage
MODEL_SAVE_DIR=./outputs/models
DATA_DIR=./data
```

#### Frontend `.env`
```ini
VITE_API_BASE=http://localhost:8000
NODE_ENV=production
```

### Thermal Configuration
Edit `configs/optimized.yaml`:
```yaml
physics:
  max_temp: 60.0          # Hard safety limit
  max_fan_power: 550.0    # Increase for better cooling
  max_pump_power: 100.0   # Liquid cooling capacity

reward:
  safe_threshold: 60.0    # Hard constraint
  energy_coefficient: 0.15 # Low = prioritize safety
```

---

## 🔍 Health Checks

### Automated Health Check
```bash
# Backend
curl http://localhost:8000/health

# Response should be:
{
  "status": "operating",
  "compute": {
    "device": "cuda or cpu",
    "torch_version": "2.x.x"
  },
  "storage": {
    "models_count": 0,
    "evaluations_count": 0
  }
}
```

### Container Health
```bash
# Check if all services are healthy
docker-compose ps

# Output should show: healthy for backend
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All logs
docker-compose logs -f
```

### Real-time Monitoring
```bash
# Watch resource usage
docker stats

# Detailed status
docker-compose ps -a
```

---

## 🚀 Deployment Commands

### Common Tasks

#### Start Services
```bash
docker-compose up -d
```

#### Stop Services
```bash
docker-compose down
```

#### Restart Services
```bash
docker-compose restart
```

#### Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up -d
```

#### Reset Everything
```bash
# Warning: This removes all data!
docker-compose down -v
docker system prune -a
```

#### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

---

## 🎯 Training Models with Docker

### Access Backend Container
```bash
# Interactive shell
docker-compose exec backend bash

# Or run command directly
docker-compose exec backend \
  python -m src.train \
  --timesteps 600000 \
  --config configs/optimized.yaml \
  --name scari_thermal_safe

# View outputs
docker-compose exec backend ls -la outputs/models/
```

---

## 📈 Performance Optimization

### Increase Concurrency
```yaml
# docker-compose.yml - increase worker threads
command: >
  uvicorn src.api.app:app 
  --host 0.0.0.0 
  --port 8000 
  --workers 4     # Add this
```

### Enable Caching
```bash
# In .env
CACHE_ENABLED=true
CACHE_TTL=3600
```

### GPU Support
```bash
# In docker-compose.yml backend service
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

## 🔐 Production Deployment

### Pre-Deployment Checklist
- [ ] `.env` file configured with production values
- [ ] SSL certificates in place (if using HTTPS)
- [ ] API key/secret configured
- [ ] CORS origins set correctly
- [ ] Database backups configured
- [ ] Monitoring setup complete
- [ ] Tests passing: `pytest tests/ -v`

### Production docker-compose
```bash
# Use production profile
docker-compose -f docker-compose.yml \
  --profile production \
  up -d
```

### Backup & Recovery
```bash
# Backup data
docker-compose exec backend \
  tar -czf backup.tar.gz data/ outputs/

# Restore
docker cp backup.tar.gz <container_id>:/app/
docker-compose exec backend tar -xzf backup.tar.gz
```

---

## 🆘 Support & Troubleshooting

### Check Service Status
```bash
# All services
docker-compose ps

# Specific service
docker-compose ps backend
```

### View Detailed Logs
```bash
# Last 50 lines
docker-compose logs --tail=50 backend

# With timestamps
docker-compose logs --timestamps backend

# Follow in real-time
docker-compose logs -f backend
```

### Common Issues

| Issue | Solution |
|-------|----------|
| **Port already in use** | Change `*_PORT` in `.env` |
| **Out of memory** | Increase Docker resources |
| **Slow startup** | Check logs with `docker-compose logs` |
| **API not responding** | Verify health: `curl http://localhost:8000/health` |
| **Frontend not loading** | Check `/health` endpoint, restart frontend |

---

## 📚 Documentation Links

- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **System Details:** [SYSTEM_IMPROVEMENTS.md](SYSTEM_IMPROVEMENTS.md)
- **Full Summary:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
- **Status:** [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)

---

## 🎓 Advanced Deployment

### Kubernetes Deployment
```bash
# Convert docker-compose to Kubernetes
kompose convert -f docker-compose.yml -o k8s/

# Deploy to cluster
kubectl apply -f k8s/
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
name: Deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push
        run: docker-compose build && docker-compose up -d
```

### Multi-Stage Deployment
```bash
# Staging
docker-compose -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.yml up -d
```

---

## ✨ Summary

| Method | Time | Complexity | Best For |
|--------|------|-----------|----------|
| **Docker** | 30s | Very Easy | Production, Everyone |
| **Local** | 2min | Easy | Development |
| **Kubernetes** | 5min | Hard | Enterprise |

**Recommended:** Use **Docker** for both development and production!

---

**Version:** S.C.A.R.I v2.0-thermal-safe  
**Status:** ✅ Production Ready  
**Last Updated:** 2024
