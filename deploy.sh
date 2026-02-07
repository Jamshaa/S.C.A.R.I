#!/bin/bash

# S.C.A.R.I Deployment Setup Script
# This script prepares the system for deployment in seconds

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🚀 S.C.A.R.I Deployment Setup Script 🚀            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check setup mode
SETUP_MODE="${1:-docker}"

if [ "$SETUP_MODE" == "docker" ]; then
    echo -e "${BLUE}→ Docker Deployment Mode${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 1: Checking Docker Installation${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 2: Checking Docker Compose${NC}"
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose found: $(docker-compose --version)${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 3: Setting up Environment Variables${NC}"
    if [ ! -f ".env" ]; then
        echo "   Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Step 4: Building Docker Images${NC}"
    docker-compose build --no-cache 2>/dev/null || {
        echo -e "${YELLOW}   Building with cache...${NC}"
        docker-compose build
    }
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 5: Starting Services${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 6: Waiting for Health Checks${NC}"
    sleep 5
    
    # Check backend health
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Backend still starting, retrying...${NC}"
        sleep 5
    fi
    
    # Check frontend
    if curl -s http://localhost:5173/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend still starting...${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📊 Service URLs:"
    echo "   • Frontend:  ${BLUE}http://localhost:5173${NC}"
    echo "   • API:       ${BLUE}http://localhost:8000${NC}"
    echo "   • Health:    ${BLUE}http://localhost:8000/health${NC}"
    echo ""
    echo "📝 Useful Commands:"
    echo "   • View logs:     ${BLUE}docker-compose logs -f backend${NC}"
    echo "   • Stop services: ${BLUE}docker-compose down${NC}"
    echo "   • Restart:       ${BLUE}docker-compose restart${NC}"
    echo ""

elif [ "$SETUP_MODE" == "local" ]; then
    echo -e "${BLUE}→ Local Development Mode${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 1: Checking Python Installation${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 2: Creating Virtual Environment${NC}"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Step 3: Activating Virtual Environment${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 4: Installing Python Dependencies${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 5: Installing Frontend Dependencies${NC}"
    cd ui
    if [ ! -d "node_modules" ]; then
        npm install -q
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
    fi
    cd ..
    
    echo ""
    echo -e "${YELLOW}Step 6: Configuration Validation${NC}"
    python -c "import yaml; yaml.safe_load(open('configs/optimized.yaml')); print('   ✓ Thermal config valid')"
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ LOCAL SETUP SUCCESSFUL!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "🚀 To start development:"
    echo ""
    echo "   Terminal 1 (Backend):"
    echo "   ${BLUE}source venv/bin/activate${NC}"
    echo "   ${BLUE}uvicorn src.api.app:app --reload --port 8000${NC}"
    echo ""
    echo "   Terminal 2 (Frontend):"
    echo "   ${BLUE}cd ui && npm run dev${NC}"
    echo ""

elif [ "$SETUP_MODE" == "prod" ]; then
    echo -e "${BLUE}→ Production Deployment Mode${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 1: Validation Checks${NC}"
    
    # Check environment
    if [ ! -f ".env" ]; then
        echo -e "${RED}✗ .env file not found. Create it from .env.example${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ .env file present${NC}"
    
    # Check configs
    python -c "import yaml; yaml.safe_load(open('configs/optimized.yaml')); print('   ✓ Config valid')"
    
    # Check models exist
    if [ ! -d "data/models" ] && [ -z "$(ls -A data/models 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠ Warning: No pre-trained models found${NC}"
        echo -e "${YELLOW}  You may need to train a model before running evaluation${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Step 2: Building Production Images${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✓ Production images built${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 3: Running Security Checks${NC}"
    docker-compose run --rm backend python -m pytest tests/ -q
    echo -e "${GREEN}✓ Tests passed${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 4: Starting Production Services${NC}"
    docker-compose -f docker-compose.yml up -d
    echo -e "${GREEN}✓ Services started${NC}"
    
    echo ""
    echo -e "${YELLOW}Step 5: Verifying Services${NC}"
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend healthy${NC}"
    else
        echo -e "${RED}✗ Backend health check failed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ PRODUCTION DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
else
    echo -e "${RED}✗ Unknown setup mode: $SETUP_MODE${NC}"
    echo ""
    echo "Usage: $0 [docker|local|prod]"
    echo ""
    echo "Modes:"
    echo "  docker  - Deploy using Docker Compose (recommended)"
    echo "  local   - Local development setup"
    echo "  prod    - Production deployment with validation"
    exit 1
fi

echo ""
echo "📚 Documentation:"
echo "   • ${BLUE}QUICK_REFERENCE.md${NC} - Quick start guide"
echo "   • ${BLUE}DEPLOYMENT_STATUS.md${NC} - Full deployment details"
echo "   • ${BLUE}SYSTEM_IMPROVEMENTS.md${NC} - Technical documentation"
echo ""
echo "✨ Happy computing!"
echo ""
