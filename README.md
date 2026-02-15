# S.C.A.R.I - Smart Cooling & AI-driven Resource Infrastructure

![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)
![Framework](https://img.shields.io/badge/Framework-Gymnasium-blue)
![Algorithm](https://img.shields.io/badge/Algorithm-PPO-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**S.C.A.R.I** es un framework de Reinforcement Learning para la **gestión térmica autónoma** de datacenters.

---

## 🔧 Primera Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/S.C.A.R.I.git
cd S.C.A.R.I

# 2. Crear entorno virtual Python
python -m venv venv

# 3. Activar entorno virtual
.\venv\Scripts\activate       # Windows
source venv/bin/activate      # Linux/Mac

# 4. Instalar dependencias Python
pip install -r requirements.txt

# 5. Instalar dependencias Frontend
cd ui
npm install
cd ..
```

---

## 🚀 Cómo Ejecutar

### 1. Backend (API)

```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Iniciar servidor
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

**URL**: http://127.0.0.1:8000

### 2. Frontend (Dashboard)

En otra terminal:

```bash
cd ui
npm run dev
```

**URL**: http://localhost:5173

---

## 📁 Estructura

```
S.C.A.R.I/
├── configs/           # Configuración de entrenamiento
├── data/models/       # Modelos entrenados (.zip)
├── src/
│   ├── api/           # Backend FastAPI
│   ├── envs/          # Simulación térmica
│   └── utils/         # Visualización y XAI
├── ui/                # Frontend React/Vite
└── outputs/eval/      # Resultados de evaluación
```

## 🎯 Características

- **Control Térmico Autónomo**: IA que se adapta a cambios de carga
- **Analítica de Sostenibilidad**: Seguimiento de CO2 y ahorro energético
- **Dashboard de IA Explicable**: Razonamiento de las decisiones
- **Interfaz Moderna**: Glassmorphism con modos claro/oscuro

## 📈 Rendimiento

PUE promedio: **1.011** | Ahorro energético: **~11%**

---

## 🐳 Docker (Opcional)

```bash
docker-compose up -d
```

---

**Documentación API**: http://localhost:8000/docs
